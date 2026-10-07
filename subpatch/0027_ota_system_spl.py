from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "install: compare OTAs against the system's security patch level"
        self.target_file = "bootable/recovery/twrpinstall/twinstall.cpp"

        self.CHANGES = [
            (
                r"""
			ret_val = Run_Update_Binary(path, wipe_cache, AB_OTA_ZIP_TYPE);
""",
                r"""
			// update_engine calls an OTA a downgrade, and on an unlocked phone schedules a
			// data wipe for the next boot, when its security patch level is older than
			// ro.build.version.security_patch. The recovery's own value is a placeholder
			// for KeyMint, so compare against the running system's for the install.
			const std::string recovery_spl =
					android::base::GetProperty("ro.build.version.security_patch", "");
			std::string system_spl = TWFunc::Partition_Property_Get(
					"ro.build.version.security_patch", PartitionManager,
					PartitionManager.Get_Android_Root_Path(), "build.prop");
			if (system_spl.empty())
				system_spl = TWFunc::Partition_Property_Get("ro.vendor.build.security_patch",
						PartitionManager, "/vendor", "build.prop");
			if (!system_spl.empty()) {
				LOGINFO("OTA: comparing against the system's security patch level %s\n",
						system_spl.c_str());
				TWFunc::Property_Override("ro.build.version.security_patch", system_spl);
			} else {
				gui_print_color("warning", "The system's security patch level could not be read, so update_engine may schedule a data wipe.\n");
			}

			ret_val = Run_Update_Binary(path, wipe_cache, AB_OTA_ZIP_TYPE);

			if (!system_spl.empty() && !recovery_spl.empty())
				TWFunc::Property_Override("ro.build.version.security_patch", recovery_spl);
"""
            ),
        ]
