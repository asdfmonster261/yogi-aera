from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "recovery: log and drop startup recovery commands"
        self.target_file = "bootable/recovery/twrp.cpp"

        self.CHANGES = [
            (
                r"""
	if ((DataManager::GetIntValue(TW_IS_ENCRYPTED) == 0 || skip_decryption || !PartitionManager.Storage_Is_Encrypted()) && (TWFunc::Path_Exists(SCRIPT_FILE_TMP) || TWFunc::Path_Exists(orsFile))) {
		OpenRecoveryScript::Run_OpenRecoveryScript();
	}
""",
                r"""
	if ((DataManager::GetIntValue(TW_IS_ENCRYPTED) == 0 || skip_decryption || !PartitionManager.Storage_Is_Encrypted()) && (TWFunc::Path_Exists(SCRIPT_FILE_TMP) || TWFunc::Path_Exists(orsFile))) {
		// The script runner opens a page of the old interface, which AERA does not
		// have, so it only waits on the running UI; when that UI exits for a reboot,
		// startup carries on instead. Log what was asked and drop it.
		for (const std::string& script : {std::string(SCRIPT_FILE_TMP), orsFile}) {
			std::string commands;
			if (TWFunc::read_file(script, commands) != 0)
				continue;
			LOGINFO("Ignoring recovery commands from %s:\n%s\n", script.c_str(), commands.c_str());
			unlink(script.c_str());
		}
	}
"""
            ),
        ]
