from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: choose the NAS SSH key from storage"
        self.target_file = "bootable/recovery/aeraui/include/aeraui/backend.hpp"

        self.CHANGES = [
            (
                r"""
NasStatus RecoveryNasStatus();
bool RecoverySetNasConfig(const NasConfig &config, std::string *error);
int RecoveryRunNas(const NasRequest &request);
""",
                r"""
NasStatus RecoveryNasStatus();
bool RecoverySetNasConfig(const NasConfig &config, std::string *error);
int RecoveryRunNas(const NasRequest &request);
// The SFTP login key, kept in root-only recovery storage. Import accepts only an
// unencrypted private key.
bool RecoveryNasKeyInstalled();
bool RecoveryImportNasKey(const std::string &path, std::string *error);
bool RecoveryRemoveNasKey();
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES),
            ("bootable/recovery/aeraui/platform/aera_backend.cpp", [
                (
                    r"""
constexpr const char *kNasProfilePath =
    "/data/media/0/AERA/network_storage.conf";
""",
                    r"""
constexpr const char *kNasProfilePath =
    "/data/media/0/AERA/network_storage.conf";
// NasManager hands this file to rclone as the SFTP key_file.
constexpr const char *kNasKeyDirectory = "/data/recovery/AERA/nas";
constexpr const char *kNasKeyPath = "/data/recovery/AERA/nas/ssh_key";
"""
                ),
                (
                    r"""
NasStatus RecoveryNasStatus() {
  NasStatus status;
""",
                    r"""
bool RecoveryNasKeyInstalled() { return access(kNasKeyPath, R_OK) == 0; }

bool RecoveryImportNasKey(const std::string &path, std::string *error) {
  const auto fail = [error](const char *message) {
    if (error != nullptr) *error = message;
    return false;
  };
  std::ifstream input(path, std::ios::binary);
  if (!input) return fail("The file could not be opened.");
  std::string key(16 * 1024 + 1, '\0');
  input.read(&key[0], static_cast<std::streamsize>(key.size()));
  key.resize(static_cast<size_t>(input.gcount()));
  if (key.size() > 16 * 1024)
    return fail("The file is too large to be an SSH private key.");
  if (key.compare(0, 4, "ssh-") == 0 || key.compare(0, 6, "ecdsa-") == 0 ||
      key.compare(0, 3, "sk-") == 0)
    return fail("That is a public key. Choose the private key, the file without .pub.");
  if (key.compare(0, 11, "-----BEGIN ") != 0 ||
      key.find("PRIVATE KEY-----") == std::string::npos)
    return fail("The file is not an SSH private key.");
  // An OpenSSH key without a passphrase names the cipher "none" at the start of
  // its body, and PEM keys mark encryption in the header. rclone is given no
  // passphrase, so an encrypted key could never log in.
  const bool openssh =
      key.find("-----BEGIN OPENSSH PRIVATE KEY-----") != std::string::npos;
  if ((openssh && key.find("b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9u") ==
                      std::string::npos) ||
      key.find("ENCRYPTED") != std::string::npos)
    return fail("The key has a passphrase. AERA cannot ask for one, so use a key without.");
  if (!TWFunc::Recursive_Mkdir(kNasKeyDirectory, false) ||
      chmod(kNasKeyDirectory, 0700) != 0)
    return fail("The key could not be saved in recovery storage.");
  const std::string temporary = std::string(kNasKeyPath) + ".tmp";
  const int fd = open(temporary.c_str(),
                      O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW | O_CLOEXEC,
                      0600);
  if (fd < 0) return fail("The key could not be saved in recovery storage.");
  size_t written = 0;
  while (written < key.size()) {
    const ssize_t count = write(fd, key.data() + written, key.size() - written);
    if (count < 0 && errno == EINTR) continue;
    if (count <= 0) break;
    written += static_cast<size_t>(count);
  }
  const bool saved = written == key.size() && fsync(fd) == 0;
  close(fd);
  if (!saved || rename(temporary.c_str(), kNasKeyPath) != 0) {
    unlink(temporary.c_str());
    return fail("The key could not be saved in recovery storage.");
  }
  return true;
}

bool RecoveryRemoveNasKey() {
  return unlink(kNasKeyPath) == 0 || errno == ENOENT;
}

NasStatus RecoveryNasStatus() {
  NasStatus status;
"""
                ),
            ]),
            ("bootable/recovery/aeraui/scenes/nas_scene.cpp", [
                (
                    r"""
#include <algorithm>
#include <string>

#include "phone_keyboard.hpp"
""",
                    r"""
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <dirent.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

#include "phone_keyboard.hpp"
"""
                ),
                (
                    r"""
void SelectProtocol(NasUi *state, const char *type) {
  if (state->snapshot.mounted) {
""",
                    r"""
// The SSH key chooser browses storage for the SFTP private key. Keys are a few
// KiB, so bigger files are left out, which also keeps photo folders short.
constexpr off_t kKeyFileLimit = 16 * 1024;
constexpr int kKeySheetPad = 48;

struct KeyChooser {
  NasUi *nas = nullptr;
  lv_obj_t *overlay = nullptr;
  lv_obj_t *path_label = nullptr;
  lv_obj_t *list = nullptr;
  std::string path = "/sdcard";
};

struct KeyEntry {
  std::string name;
  std::string path;
  bool directory = false;
  off_t size = 0;
};

void FillKeyList(KeyChooser *chooser);

// A row's tap must not rebuild the list the row belongs to, so opening a folder
// rebuilds it once the tap has finished.
void RebuildKeyList(void *data) {
  FillKeyList(static_cast<KeyChooser *>(data));
}

void ImportKey(KeyChooser *chooser, const std::string &path) {
  std::string error;
  if (!RecoveryImportNasKey(path, &error)) {
    Sheet(chooser->nas->screen, "Not a usable key", error);
    return;
  }
  NasUi *state = chooser->nas;
  Close(chooser->overlay);
  Populate(state);
  Sheet(state->screen, "SSH key installed",
        "AERA saved its own copy, which only the recovery can read. Delete the "
        "original from storage? Apps on Android that can read your files can "
        "read it there.",
        [path] { unlink(path.c_str()); }, 0, false,
        SheetPresentation::kStandard, "Swipe to delete");
}

void FillKeyList(KeyChooser *chooser) {
  lv_obj_clean(chooser->list);
  i18n::BindLabel(chooser->path_label, chooser->path.c_str());
  std::vector<KeyEntry> entries;
  if (chooser->path != "/") {
    const size_t slash = chooser->path.find_last_of('/');
    entries.push_back({"..", slash == 0 ? "/" : chooser->path.substr(0, slash),
                       true, 0});
  }
  const size_t first = entries.size();
  if (DIR *directory = opendir(chooser->path.c_str())) {
    const bool hidden = RecoveryPreference(Preference::kHiddenFiles);
    while (dirent *item = readdir(directory)) {
      const std::string name = item->d_name;
      if (name == "." || name == ".." || (name[0] == '.' && !hidden)) continue;
      const std::string path =
          (chooser->path == "/" ? std::string() : chooser->path) + "/" + name;
      struct stat info {};
      if (stat(path.c_str(), &info) != 0) continue;
      const bool folder = S_ISDIR(info.st_mode);
      if (!folder && (!S_ISREG(info.st_mode) || info.st_size > kKeyFileLimit))
        continue;
      entries.push_back({name, path, folder, info.st_size});
      if (entries.size() >= 300) break;
    }
    closedir(directory);
  }
  std::sort(entries.begin() + static_cast<std::ptrdiff_t>(first), entries.end(),
            [](const KeyEntry &a, const KeyEntry &b) {
              if (a.directory != b.directory) return a.directory;
              return a.name < b.name;
            });
  int y = 0;
  for (const auto &entry : entries) {
    const std::string detail = entry.name == ".." ? "Up one folder"
        : entry.directory ? "Folder"
        : Size(static_cast<uint64_t>(entry.size));
    Row(chooser->list, y, entry.directory ? LV_SYMBOL_DIRECTORY : LV_SYMBOL_FILE,
        entry.name, detail, [chooser, entry] {
          if (!entry.directory) {
            ImportKey(chooser, entry.path);
            return;
          }
          chooser->path = entry.path;
          lv_async_call(RebuildKeyList, chooser);
        });
    y += 180;
  }
  if (entries.size() == first) {
    auto *empty = Label(chooser->list, "No folders or small files here",
                        &lv_font_montserrat_24, kMuted);
    lv_obj_set_pos(empty, 0, y + 40);
  }
}

void OpenKeyChooser(NasUi *state) {
  auto *chooser = new KeyChooser;
  chooser->nas = state;
  auto *overlay = lv_obj_create(state->screen);
  chooser->overlay = overlay;
  lv_obj_set_user_data(overlay, &kModalMarker);
  Clear(overlay);
  lv_obj_set_size(overlay, LV_PCT(100), LV_PCT(100));
  lv_obj_set_style_bg_color(overlay, lv_color_black(), 0);
  lv_obj_set_style_bg_opa(overlay, LV_OPA_60, 0);
  lv_obj_add_event_cb(overlay, [](lv_event_t *event) {
    auto *chooser = static_cast<KeyChooser *>(lv_event_get_user_data(event));
    lv_async_call_cancel(RebuildKeyList, chooser);
    delete chooser;
  }, LV_EVENT_DELETE, chooser);

  const int height =
      std::min(2400, static_cast<int>(lv_obj_get_height(state->screen)) - 200);
  const int inner = height - 2 * kKeySheetPad;
  auto *sheet = lv_obj_create(overlay);
  Panel(sheet, 48, kMainSheet);
  lv_obj_set_size(sheet, 1312, height);
  lv_obj_align(sheet, LV_ALIGN_BOTTOM_MID, 0, -64);
  lv_obj_set_style_pad_all(sheet, kKeySheetPad, 0);
  auto *title = Label(sheet, "Choose SSH key", &lv_font_montserrat_48, kText);
  lv_obj_set_width(title, 1180);
  auto *hint = Label(sheet,
      "Pick the private key, the file without .pub. It must have no passphrase.",
      &lv_font_montserrat_24, kMuted);
  lv_obj_set_pos(hint, 0, 76);
  lv_obj_set_width(hint, 1180);
  chooser->path_label = Label(sheet, "", &lv_font_montserrat_24, kMutedStrong);
  lv_obj_set_pos(chooser->path_label, 0, 180);
  lv_obj_set_width(chooser->path_label, 1216);
  lv_label_set_long_mode(chooser->path_label, LV_LABEL_LONG_DOT);

  chooser->list = lv_obj_create(sheet);
  Clear(chooser->list);
  lv_obj_set_pos(chooser->list, 0, 240);
  lv_obj_set_size(chooser->list, 1216, inner - 240 - 116 - 32);
  lv_obj_add_flag(chooser->list, LV_OBJ_FLAG_SCROLLABLE);
  lv_obj_set_scroll_dir(chooser->list, LV_DIR_VER);
  lv_obj_set_scrollbar_mode(chooser->list, LV_SCROLLBAR_MODE_ACTIVE);
  lv_obj_set_style_bg_color(chooser->list, kAccent, LV_PART_SCROLLBAR);
  lv_obj_set_style_width(chooser->list, 5, LV_PART_SCROLLBAR);

  const bool installed = RecoveryNasKeyInstalled();
  auto *cancel = Button(sheet, "Cancel", [overlay] { Close(overlay); });
  lv_obj_set_pos(cancel, 0, inner - 116);
  lv_obj_set_size(cancel, installed ? 580 : 1216, 116);
  if (installed) {
    auto *remove = Button(sheet, "Remove key", [state, overlay] {
      Close(overlay);
      Sheet(state->screen, "Remove the SSH key?",
            "AERA deletes its copy. SFTP then needs a password or a new key.",
            [state] {
              RecoveryRemoveNasKey();
              Populate(state);
            }, 0, false, SheetPresentation::kStandard, "Swipe to remove");
    });
    lv_obj_set_pos(remove, 636, inner - 116);
    lv_obj_set_size(remove, 580, 116);
  }
  FillKeyList(chooser);
  AnimateEnter(sheet, 0, 42);
}

void AddKeyCard(NasUi *state, int x, int y) {
  auto *card = lv_button_create(state->scene.list);
  Panel(card, 30, kMainSheet);
  Interactive(card, kMainSelected);
  lv_obj_set_pos(card, x, y);
  lv_obj_set_size(card, 640, 160);
  lv_obj_set_style_transform_scale(card, 256, LV_STATE_PRESSED);
  lv_obj_set_style_border_width(card, 1, 0);
  lv_obj_set_style_border_color(card, kMainLine, 0);
  lv_obj_set_style_border_opa(card, LV_OPA_30, 0);
  OnClick(card, [state] {
    if (state->busy) return;
    if (state->snapshot.mounted) {
      Sheet(state->screen, "Network storage is mounted",
            "Unmount it before changing its connection settings.");
      return;
    }
    OpenKeyChooser(state);
  });
  auto *name = Label(card, "SSH key", &lv_font_montserrat_24, kMuted);
  lv_obj_set_pos(name, 30, 26);
  auto *copy = Label(card, RecoveryNasKeyInstalled() ? "Installed" : "Not set",
                     &lv_font_montserrat_32, kText);
  lv_obj_set_pos(copy, 30, 78);
  auto *edit = Label(card, LV_SYMBOL_RIGHT, &lv_font_montserrat_24,
                     kMutedStrong);
  lv_obj_align(edit, LV_ALIGN_RIGHT_MID, -28, 0);
  AnimateEnter(card, 20 + static_cast<uint32_t>(y / 10), 9);
}

void SelectProtocol(NasUi *state, const char *type) {
  if (state->snapshot.mounted) {
"""
                ),
                (
                    r"""
  } else {
    AddCacheCard(state, 672, y);
  }
}
""",
                    r"""
  } else {
    AddCacheCard(state, 672, y);
    y += 180;
    AddKeyCard(state, 0, y);
  }
}
"""
                ),
            ]),
        ]

    # BaseSubPatch handles one file; this change spans three.
    def _each(self, step):
        for self.target_file, self.CHANGES in self.FILES:
            step()
        self.target_file, self.CHANGES = self.FILES[0]

    def check(self):
        self._each(super().check)

    def mod(self):
        self._each(super().mod)

    def list_changes(self):
        self._each(super().list_changes)
