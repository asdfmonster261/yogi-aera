from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "keystore2: use a KeyMint newer than this keystore as-is"
        self.target_file = "system/security/keystore2/src/globals.rs"

        self.CHANGES = [
            (
                r"""
    let keymint = match hal_version {
        Some(400) | Some(300) | Some(200) => {
""",
                r"""
    let keymint = match hal_version {
        // A KeyMint newer than this keystore (v5 on an Android 17 vendor) still serves
        // the older AIDL calls, so it is used as-is too.
        Some(v) if v >= 200 => {
"""
            ),
        ]
