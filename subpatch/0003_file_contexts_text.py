from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "Android.mk: terminate the file_contexts.bin copy"
        self.target_file = "bootable/recovery/Android.mk"

        # The terminfo/nano lines are appended to this LOCAL_POST_INSTALL_CMD with +=, so
        # without a terminator their "mkdir -p .../system/etc/" becomes extra arguments to
        # this cp. The directory is then only there if another module made it first.
        self.CHANGES = [
            (
                r"""
     $(hide) cp ${SOONG_OUT_DIR}/.intermediates/system/sepolicy/file_contexts.concat.tmp/android_common/gen/file_contexts.concat.tmp $(TARGET_RECOVERY_ROOT_OUT)/file_contexts && cp $(PRODUCT_OUT)/obj/ETC/file_contexts.bin_intermediates/file_contexts.bin $(TARGET_RECOVERY_ROOT_OUT)/
""",
                r"""
     $(hide) cp ${SOONG_OUT_DIR}/.intermediates/system/sepolicy/file_contexts.concat.tmp/android_common/gen/file_contexts.concat.tmp $(TARGET_RECOVERY_ROOT_OUT)/file_contexts && cp $(PRODUCT_OUT)/obj/ETC/file_contexts.bin_intermediates/file_contexts.bin $(TARGET_RECOVERY_ROOT_OUT)/;
"""
            ),
        ]
