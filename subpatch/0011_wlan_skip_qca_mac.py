from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "wlan: skip the Qualcomm MAC files when there is no Qualcomm WLAN"
        self.target_file = "bootable/recovery/wlan.cpp"

        self.CHANGES = [
            (
                r"""
    bool configured = false;
    const std::string setting = "read_mac_addr_from_mac_file";
""",
                r"""
    // Only Qualcomm's driver takes its MAC from these files. Without its config
    // there is nothing to prepare, and the driver supplies a MAC of its own.
    if (config_paths.empty())
        return true;

    bool configured = false;
    const std::string setting = "read_mac_addr_from_mac_file";
"""
            ),
        ]
