from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "partitionmanager: give vold the extra userdata devices from the fstab"
        self.target_file = "bootable/recovery/partitionmanager.cpp"

        self.CHANGES = [
            (
                r"""
			std::vector<std::string> user_devices;
			std::vector<bool> device_aliased;
			if (android::vold::fscrypt_mount_metadata_encrypted(Decrypt_Data->Actual_Block_Device, Decrypt_Data->Mount_Point, false, false, Decrypt_Data->Current_File_System, false, user_devices, device_aliased, 0, TWFunc::Path_Exists(additional_fstab) ? additional_fstab : "")) {
""",
                r"""
			// On a normal boot fs_mgr hands vold the /data entry's extra devices. vold
			// does not look them up itself, so without them a multi-device /data is
			// opened with the wrong key and only its first device.
			std::vector<std::string> user_devices;
			std::vector<bool> device_aliased;
			bool is_zoned = false;
			android::fs_mgr::Fstab data_fstab;
			if (TWFunc::Path_Exists(additional_fstab) &&
				android::fs_mgr::ReadFstabFromFile(additional_fstab, &data_fstab)) {
				const auto* entry = android::fs_mgr::GetEntryForMountPoint(&data_fstab, Decrypt_Data->Mount_Point);
				if (entry != nullptr) {
					user_devices = entry->user_devices;
					device_aliased.assign(entry->device_aliased.begin(), entry->device_aliased.end());
					is_zoned = entry->fs_mgr_flags.is_zoned;
				}
			}
			if (android::vold::fscrypt_mount_metadata_encrypted(Decrypt_Data->Actual_Block_Device, Decrypt_Data->Mount_Point, false, false, Decrypt_Data->Current_File_System, is_zoned, user_devices, device_aliased, 0, TWFunc::Path_Exists(additional_fstab) ? additional_fstab : "")) {
"""
            ),
        ]
