from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: load the GPU driver named by ro.hardware.egl into the sphal namespace"
        self.target_file = "bootable/recovery/aeraui/core/gpu_renderer.cpp"

        self.CHANGES = [
            (
                r"""
#include <dlfcn.h>
#include <unistd.h>

#include <cstring>
""",
                r"""
#include <dlfcn.h>
#include <sys/system_properties.h>
#include <unistd.h>

#include <cstring>
#include <string>
"""
            ),
            (
                r"""
constexpr char kLogTag[] = "AeraGpu";
constexpr char kEglDriver[] = "/vendor/lib64/egl/libEGL_adreno.so";
constexpr char kGlesDriver[] = "/vendor/lib64/egl/libGLESv2_adreno.so";
constexpr char kNativeWindowLibrary[] = "/vendor/lib64/libnativewindow.so";
""",
                r"""
constexpr char kLogTag[] = "AeraGpu";
constexpr char kNativeWindowLibrary[] = "/vendor/lib64/libnativewindow.so";
constexpr char kAllocatorInstance[] =
    "android.hardware.graphics.allocator.IAllocator/default";
"""
            ),
            (
                r"""
void DisplayResolutionChanged(lv_event_t* event) {
""",
                r"""
// The driver follows ro.hardware.egl, as Android's EGL loader does. Trees that never
// set it keep the Adreno libraries this renderer was written against.
std::string DriverPath(const char* api) {
  char egl[PROP_VALUE_MAX] = {};
  if (__system_property_get("ro.hardware.egl", egl) <= 0)
    std::strcpy(egl, "adreno");
  return std::string("/vendor/lib64/egl/lib") + api + "_" + egl + ".so";
}

// A vendor driver can need a newer libc++ than the recovery's, so load it the way
// Android loads one into a system process: into the sphal namespace when the linker
// config has one, and with a plain dlopen otherwise.
void* LoadVendorLibrary(const char* path) {
  using LoadSphalLibrary = void* (*)(const char*, int);
  static const LoadSphalLibrary load_sphal = [] {
    void* vndksupport = dlopen("libvndksupport.so", RTLD_NOW | RTLD_LOCAL);
    return vndksupport == nullptr
               ? nullptr
               : reinterpret_cast<LoadSphalLibrary>(
                     dlsym(vndksupport, "android_load_sphal_library"));
  }();
  if (load_sphal != nullptr)
    return load_sphal(path, RTLD_NOW | RTLD_GLOBAL);
  return dlopen(path, RTLD_NOW | RTLD_GLOBAL);
}

// libui waits forever on a declared allocator that never registers, and aborts the
// process when it cannot load the mapper, so allocate only once one is serving.
bool AllocatorReady() {
  void* binder = dlopen("libbinder_ndk.so", RTLD_NOW | RTLD_LOCAL);
  if (binder == nullptr)
    return false;
  auto is_declared = reinterpret_cast<bool (*)(const char*)>(
      dlsym(binder, "AServiceManager_isDeclared"));
  auto check_service = reinterpret_cast<void* (*)(const char*)>(
      dlsym(binder, "AServiceManager_checkService"));
  auto dec_strong = reinterpret_cast<void (*)(void*)>(
      dlsym(binder, "AIBinder_decStrong"));
  if (is_declared == nullptr || check_service == nullptr ||
      dec_strong == nullptr)
    return false;
  // Without an AIDL declaration libui looks for a HIDL allocator, as it always did.
  if (!is_declared(kAllocatorInstance))
    return true;
  for (int attempt = 0; attempt < 40; ++attempt) {
    if (void* service = check_service(kAllocatorInstance)) {
      dec_strong(service);
      return true;
    }
    usleep(50 * 1000);
  }
  return false;
}

void DisplayResolutionChanged(lv_event_t* event) {
"""
            ),
            (
                r"""
  egl_library_ = dlopen(kEglDriver, RTLD_NOW | RTLD_GLOBAL);
  if (egl_library_ == nullptr) {
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Adreno EGL unavailable: %s", dlerror());
    return false;
  }
  gles_library_ = dlopen(kGlesDriver, RTLD_NOW | RTLD_GLOBAL);
  if (gles_library_ == nullptr) {
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Adreno GLES unavailable: %s", dlerror());
    Shutdown();
    return false;
  }
  nativewindow_library_ = dlopen(kNativeWindowLibrary, RTLD_NOW | RTLD_GLOBAL);
""",
                r"""
  const std::string egl_driver = DriverPath("EGL");
  egl_library_ = LoadVendorLibrary(egl_driver.c_str());
  if (egl_library_ == nullptr) {
    __android_log_print(ANDROID_LOG_WARN, kLogTag, "%s unavailable: %s",
                        egl_driver.c_str(), dlerror());
    return false;
  }
  const std::string gles_driver = DriverPath("GLESv2");
  gles_library_ = LoadVendorLibrary(gles_driver.c_str());
  if (gles_library_ == nullptr) {
    __android_log_print(ANDROID_LOG_WARN, kLogTag, "%s unavailable: %s",
                        gles_driver.c_str(), dlerror());
    Shutdown();
    return false;
  }
  nativewindow_library_ = LoadVendorLibrary(kNativeWindowLibrary);
"""
            ),
            (
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Adreno EGL bootstrap is incomplete");
""",
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "EGL bootstrap is incomplete");
"""
            ),
            (
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "no compatible Adreno pbuffer config");
""",
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "no compatible pbuffer config");
"""
            ),
            (
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Adreno context creation failed: %#x", eglGetError());
""",
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "context creation failed: %#x", eglGetError());
"""
            ),
            (
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "Adreno native-buffer image import is unavailable");
""",
                r"""
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "native-buffer image import is unavailable");
"""
            ),
            (
                r"""
  auto allocate_buffer = reinterpret_cast<AllocateHardwareBuffer>(
      dlsym(nativewindow_library_, "AHardwareBuffer_allocate"));
""",
                r"""
  if (!AllocatorReady()) {
    __android_log_print(ANDROID_LOG_WARN, kLogTag,
                        "graphics allocator is not serving");
    Shutdown();
    return false;
  }
  auto allocate_buffer = reinterpret_cast<AllocateHardwareBuffer>(
      dlsym(nativewindow_library_, "AHardwareBuffer_allocate"));
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES),
            # The engine names the backend in its own log lines.
            ("bootable/recovery/aeraui/core/engine.cpp", [
                (
                    r"""gpu_accelerated_ ? "zero-copy Adreno/LVGL"
""",
                    r"""gpu_accelerated_ ? "zero-copy GPU/LVGL"
"""
                ),
                (
                    r""""Adreno rejected the LVGL frame");
""",
                    r""""GPU rejected the LVGL frame");
"""
                ),
            ]),
        ]

    # BaseSubPatch handles one file; this change spans two.
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
