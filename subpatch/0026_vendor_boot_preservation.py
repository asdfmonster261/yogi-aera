from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "install: keep AERA installed on vendor_boot recovery devices"
        self.target_file = "bootable/recovery/twrpinstall/twinstall.cpp"

        self.CHANGES = [
            (
                r"""
constexpr char kPreservationDirectory[] = "/tmp/aera-partition-preservation";
constexpr uint64_t kPreservationHeadroom = 16ULL * 1024ULL * 1024ULL;
""",
                r"""
constexpr char kPreservationDirectory[] = "/tmp/aera-partition-preservation";
constexpr uint64_t kPreservationHeadroom = 16ULL * 1024ULL * 1024ULL;
constexpr char kVendorBootGraft[] = "/system/bin/sh /system/bin/aera_vb_graft.sh";
"""
            ),
            (
                r"""
bool IsAeraRecoveryPackage(ZipArchiveHandle archive) {
	ZipEntry64 recovery_image;
	return FindEntry(archive, "recovery.img", &recovery_image) == 0 &&
""",
                r"""
bool IsAeraRecoveryPackage(ZipArchiveHandle archive) {
	ZipEntry64 recovery_image;
	// The repack installer for vendor_boot devices, so keeping AERA installed does
	// not graft the running AERA back over the one it brings.
	if (FindEntry(archive, "vendor_boot-aera.img", &recovery_image) == 0)
		return true;
	return FindEntry(archive, "recovery.img", &recovery_image) == 0 &&
"""
            ),
            (
                r"""
			PreservationError("the active slot could not be determined");
			return false;
		}
		if (preserve_recovery && !Add("AERA recovery", "recovery", slot)) {
""",
                r"""
			PreservationError("the active slot could not be determined");
			return false;
		}
		// A vendor_boot recovery shares the partition with each slot's own first stage.
		const char* recovery_partition =
				DataManager::GetIntValue("vendor_boot_recovery") == 1 ? "vendor_boot" : "recovery";
		if (preserve_recovery && !Add("AERA recovery", recovery_partition, slot)) {
"""
            ),
            (
                r"""
				LOGINFO("Partition protection: %s was not changed; no restore needed\n",
						target.label.c_str());
				continue;
			}
""",
                r"""
				LOGINFO("Partition protection: %s was not changed; no restore needed\n",
						target.label.c_str());
				continue;
			}
			if (target.partition == "vendor_boot") {
				// Only a ROM or OTA install puts AERA back. Any other zip that replaces
				// vendor_boot, such as another recovery, is left in place.
				if (DataManager::GetIntValue(AERA_ZIP_INSTALLER_CODE) == 0) {
					LOGINFO("Partition protection: not a ROM or OTA install, so vendor_boot is left as installed\n");
					continue;
				}
				const bool a = GraftIfReplaced(target, "A", target.slot_a, read_a,
						after_a, target.before_a);
				const bool b = GraftIfReplaced(target, "B", target.slot_b, read_b,
						after_b, target.before_b);
				if (!a || !b) success = false;
				continue;
			}
"""
            ),
            (
                r"""
private:
	bool Add(const std::string& label, const std::string& partition,
			const std::string& current_slot) {
""",
                r"""
private:
	// A copy would carry this slot's first stage onto the other slot, so AERA is
	// grafted onto each vendor_boot the install replaced and the rest are left alone.
	bool GraftIfReplaced(const PreservedPartition& target, const char* slot,
			const std::string& path, bool read, const std::string& after,
			const std::string& before) {
		if (!read) {
			PreservationError(std::string("vendor_boot on slot ") + slot +
					" could not be read");
			return false;
		}
		if (after == before) return true;
		PreservationStatus(std::string("Grafting AERA onto vendor_boot on slot ") + slot);
		if (TWFunc::Exec_Cmd(std::string(kVendorBootGraft) + " " + target.backup + " " +
				path) != 0) {
			PreservationError(std::string("AERA could not be grafted onto slot ") + slot);
			return false;
		}
		return true;
	}

	bool Add(const std::string& label, const std::string& partition,
			const std::string& current_slot) {
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES),
            # The toggle shows only where preservation is supported. Its default stays
            # off: the persisted default is still keyed on a recovery partition.
            ("bootable/recovery/data.cpp", [
                (
                    r"""
  #if defined(OF_AB_DEVICE_WITH_RECOVERY_PARTITION)
    mConst.SetValue(AERA_RECOVERY_PRESERVATION_SUPPORTED, "1");
""",
                    r"""
  #if defined(OF_AB_DEVICE_WITH_RECOVERY_PARTITION) || defined(AERA_VENDOR_BOOT_RECOVERY)
    mConst.SetValue(AERA_RECOVERY_PRESERVATION_SUPPORTED, "1");
"""
                ),
            ]),
            ("bootable/recovery/aeraui/scenes/tool_scene.cpp", [
                (
                    r"""
                     "Restore the running AERA recovery to both slots after ZIP installs",
""",
                    r"""
                     "Put AERA back on a slot after a ROM or OTA replaces its vendor_boot",
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
