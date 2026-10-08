from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: describe Format Data as the stock factory reset"
        self.target_file = "bootable/recovery/aeraui/scenes/tool_scene.cpp"

        self.CHANGES = [
            (
                r"""
      "Resets storage encryption; Android may encrypt it again.\n"
      "Adopted storage, if present, may also be erased.", &lv_font_montserrat_24, kMutedStrong);
""",
                r"""
      "Like a stock factory reset, this also clears the Titan M keys.\n"
      "Android sets up /data again on its next boot.", &lv_font_montserrat_24, kMutedStrong);
"""
            ),
        ]

        self.FILES = [
            (self.target_file, self.CHANGES),
            ("bootable/recovery/aeraui/scenes/operation_scene.cpp", [
                (
                    r"""
    value.title = "Formatting data";
    value.explanation = "AERA is recreating the data volume and internal storage.";
    value.activity = "Removing encryption metadata and preparing a clean data volume.";
""",
                    r"""
    value.title = "Erasing data";
    value.explanation = "AERA is erasing internal storage the way a stock factory reset does.";
    value.activity = "Clearing userdata, its encryption keys, Titan M and Trusty storage.";
"""
                ),
                (
                    r"""
    i18n::BindLabel(scene.detail, "Data was formatted successfully. Reboot recovery before using /data again.");
    i18n::BindLabel(scene.activity_summary,
        "Android may need a moment to recreate shared storage on the next boot.");
""",
                    r"""
    i18n::BindLabel(scene.detail, "Data was erased. Reboot to Android, which sets up /data on its first boot.");
    i18n::BindLabel(scene.activity_summary,
        "/data has no file system until Android has booted once, so AERA can't use it before then.");
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
