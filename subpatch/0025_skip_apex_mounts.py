from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "partitions: skip the APEX setup mounts when APEX is left out"
        self.target_file = "bootable/recovery/partitionmanager.cpp"

        self.CHANGES = [
            (
                r"""
			if (sys->Get_Super_Status()) {
				sys->Mount(Display_Error);
				if (ven) {
					ven->Mount(Display_Error);
				}
	#ifdef TW_EXCLUDE_APEX
				LOGINFO("Apex is disabled in this build\n");
	#else
				twrpApex apex;
""",
                r"""
			if (sys->Get_Super_Status()) {
	#ifdef TW_EXCLUDE_APEX
				// Nothing needs them mounted without APEX. Mounting vendor here also races
				// the early UI: GPU libraries loaded while it covers /vendor keep it busy,
				// and zip installs then fail to unmount it.
				LOGINFO("Apex is disabled in this build\n");
	#else
				sys->Mount(Display_Error);
				if (ven) {
					ven->Mount(Display_Error);
				}
				twrpApex apex;
"""
            ),
        ]
