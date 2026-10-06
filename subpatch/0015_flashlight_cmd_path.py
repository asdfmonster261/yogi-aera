from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: switch the flashlight through a cmd: script"
        self.target_file = "bootable/recovery/aeraui/platform/aera_backend.cpp"

        self.CHANGES = [
            (
                r"""
  std::string first = DataManager::GetStrValue("of_fl_path_1");
  std::string second = DataManager::GetStrValue("of_fl_path_2");
  if (first.empty() && second.empty()) {
""",
                r"""
  std::string first = DataManager::GetStrValue("of_fl_path_1");
  std::string second = DataManager::GetStrValue("of_fl_path_2");
  // A cmd: path names a script that switches the light itself when given on or
  // off, for flash LEDs that have no LED class device to write.
  if (first.compare(0, 4, "cmd:") == 0) {
    if (TWFunc::Exec_Cmd(first.substr(4) + (enabled ? " on" : " off")) != 0)
      return false;
    DataManager::SetValue("of_flash_on", enabled ? "1" : "0");
    return true;
  }
  if (first.empty() && second.empty()) {
"""
            ),
        ]
