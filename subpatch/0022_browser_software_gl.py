from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: run the browser on llvmpipe where there is no KGSL"
        self.target_file = "bootable/recovery/aeraui/features/browser/jail_main.cpp"

        self.CHANGES = [
            (
                r"""
  auto *jail = minijail_new();
  if (!jail) Die("minijail_new");
""",
                r"""
  // Adreno phones composite on the GPU through KGSL. Anything without it, such as a
  // PowerVR phone, gets Mesa's llvmpipe instead of failing to bind the device.
  const bool kgsl = access("/dev/kgsl-3d0", F_OK) == 0;
  auto *jail = minijail_new();
  if (!jail) Die("minijail_new");
"""
            ),
            (
                r"""
    Check(minijail_bind(jail, "/dev/kgsl-3d0", "/dev/kgsl-3d0", 1),
          "browser GPU device");
""",
                r"""
    if (kgsl)
      Check(minijail_bind(jail, "/dev/kgsl-3d0", "/dev/kgsl-3d0", 1),
            "browser GPU device");
"""
            ),
            (
                r"""
    const_cast<char *>("VK_DRIVER_FILES=/usr/share/vulkan/icd.d/freedreno_icd.json"),
    const_cast<char *>("MESA_LOADER_DRIVER_OVERRIDE=zink"),
""",
                r"""
    const_cast<char *>(kgsl ? "VK_DRIVER_FILES=/usr/share/vulkan/icd.d/freedreno_icd.json"
                            : "LIBGL_ALWAYS_SOFTWARE=1"),
    const_cast<char *>(kgsl ? "MESA_LOADER_DRIVER_OVERRIDE=zink" : "GALLIUM_DRIVER=llvmpipe"),
"""
            ),
        ]
