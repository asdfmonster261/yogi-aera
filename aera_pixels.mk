#
# Copyright (C) 2024-2026 The OrangeFox Recovery Project
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# aera_pixels.mk - AERA settings for the Pixel 11 (malibu) family, inherited by device.mk.

AERA_MAINTAINER := asdfmonster261

AERA_SCREEN_H := 2400
AERA_STATUS_H := 130
AERA_STATUS_INDENT_LEFT := 80
AERA_STATUS_INDENT_RIGHT := 80
AERA_HIDE_NOTCH := 1
AERA_CLOCK_POS := 1
AERA_ALLOW_DISABLE_NAVBAR := 0
AERA_OPTIONS_LIST_NUM := 6
AERA_USE_GREEN_LED := 0

# The LM3644 flash LED is driven over I2C by a script, not a sysfs LED.
AERA_FL_PATH1 := cmd:/system/bin/torch_ctl.sh

AERA_USE_LZ4_COMPRESSION := 1
AERA_NO_TREBLE_COMPATIBILITY_CHECK := 1
AERA_ENABLE_LPTOOLS := 1
AERA_RECOVERY_AB_FULL_REFLASH_RAMDISK := 1
AERA_USE_LEGACY_BATTERY_SERVICES := 1

# Tears down the userdata dm device before a /data format; without it make_f2fs
# refuses the raw device as in use.
AERA_USE_DMCTL := 1

AERA_QUICK_BACKUP_LIST := /boot;/vendor_boot;/data;
AERA_UNBIND_SDCARD_F2FS := 1
AERA_BIND_MOUNT_SDCARD_ON_FORMAT := 1
AERA_DYNAMIC_FULL_SIZE := 8531214336
AERA_FORCE_DATA_FORMAT_F2FS := 1
