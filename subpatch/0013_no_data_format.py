from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "recovery: refuse to format /data and hide Format Data"
        self.target_file = "bootable/recovery/partition.cpp"

        self.CHANGES = [
            (
                r"""
bool TWPartition::Wipe_Encryption() {
	bool Save_Data_Media = Has_Data_Media;
	bool ret = false;
	std::string the_wipe_fs;

	if (TWFunc::Block_Operations_Until_Reboot())
		return false;
""",
                r"""
bool TWPartition::Wipe_Encryption() {
	bool Save_Data_Media = Has_Data_Media;
	bool ret = false;
	std::string the_wipe_fs;

	if (TWFunc::Block_Operations_Until_Reboot())
		return false;

	// Formatting /data is off until it can be done safely: a format of yogi's zoned,
	// multi-device /data never worked and is suspected in damage to its UFS. Refuse
	// before /data is unmounted or its mappings are torn down.
	if (Mount_Point == "/data") {
		gui_err("format_data_disabled=Formatting /data is disabled on this device.");
		return false;
	}
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES + [
                # The same refusal where every other path into mkfs ends: a file system
                # change, or a restore made on a different file system.
                (
                    r"""
bool TWPartition::Wipe_EXT4() {
#ifdef USE_EXT4
""",
                    r"""
bool TWPartition::Wipe_EXT4() {
	if (Mount_Point == "/data") {
		gui_err("format_data_disabled=Formatting /data is disabled on this device.");
		return false;
	}
#ifdef USE_EXT4
"""
                ),
                (
                    r"""
bool TWPartition::Wipe_F2FS() {
	std::string f2fs_command;

	if (!UnMount(true))
		return false;
""",
                    r"""
bool TWPartition::Wipe_F2FS() {
	std::string f2fs_command;

	if (Mount_Point == "/data") {
		gui_err("format_data_disabled=Formatting /data is disabled on this device.");
		return false;
	}

	if (!UnMount(true))
		return false;
"""
                ),
            ]),
            ("bootable/recovery/aeraui/scenes/tool_scene.cpp", [
                (
                    r"""
                   [state] { Open(state, Action::kWipe); });
  WorkflowModeCard(state->screen, landscape ? 550 : 714, card_y,
                   landscape ? 470 : 662, LV_SYMBOL_TRASH, "Format Data",
                   "Erase internal storage and reset encryption.", format,
                   [state] { Open(state, Action::kFormatData); });
}
""",
                    r"""
                   [state] { Open(state, Action::kWipe); });
  // No Format Data card: formatting /data is disabled on this device.
}
"""
                ),
            ]),
            ("bootable/recovery/aeraui/scenes/fastboot_scene.cpp", [
                (
                    r"""
  constexpr std::array<Destination, 5> destinations{{
""",
                    r"""
  // No Format Data destination: formatting /data is disabled on this device.
  constexpr std::array<Destination, 4> destinations{{
"""
                ),
                (
                    r"""
      {LV_SYMBOL_POWER, "Power off", "Shut down the device",
       Action::kPowerOff},
      {LV_SYMBOL_TRASH, "Format Data", "Erase internal storage and encryption",
       Action::kFormatData},
  }};
""",
                    r"""
      {LV_SYMBOL_POWER, "Power off", "Shut down the device",
       Action::kPowerOff},
  }};
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
