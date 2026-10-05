from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "prebuilt/Android.mk: leave terminfo to the recovery module"
        self.target_file = "bootable/recovery/prebuilt/Android.mk"

        self.CHANGES = [
            (
                r"""
LOCAL_REQUIRED_MODULES := nano libncurses
LOCAL_POST_INSTALL_CMD += \
    mkdir -p $(TARGET_RECOVERY_ROOT_OUT)/system/etc/; \
    cp -rf $(TARGET_OUT_SYSTEM_EXT_ETC)/nano $(TARGET_RECOVERY_ROOT_OUT)/system/etc/; \
    cp -rf external/libncurses/lib/terminfo $(TARGET_RECOVERY_ROOT_OUT)/system/etc/;
include $(BUILD_PHONY_PACKAGE)
""",
                r"""
LOCAL_REQUIRED_MODULES := nano libncurses
# terminfo belongs to the recovery module, which replaces the whole tree. A second
# copy here could run during that rm -rf and fail the build.
LOCAL_POST_INSTALL_CMD += \
    mkdir -p $(TARGET_RECOVERY_ROOT_OUT)/system/etc/; \
    cp -rf $(TARGET_OUT_SYSTEM_EXT_ETC)/nano $(TARGET_RECOVERY_ROOT_OUT)/system/etc/;
include $(BUILD_PHONY_PACKAGE)
"""
            ),
        ]
