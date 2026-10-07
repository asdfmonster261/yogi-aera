#
# Copyright (C) 2024-2026 The OrangeFox Recovery Project
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# device.mk — Package list, crypto config, and build props for Tensor-based Pixels.
# Covers malibu (Tensor G6): yogi (Pixel 11 Pro Fold) and its Pixel 11 siblings.

LOCAL_PATH := device/google/pixels

# Enable virtual A/B OTA
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/compression.mk)

# API & VNDK
PRODUCT_SHIPPING_API_LEVEL := 34
PRODUCT_TARGET_VNDK_VERSION := 34

# Dynamic Partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Boot control HAL (Pixel-specific implementation)
PRODUCT_PACKAGES += \
    android.hardware.boot@1.2-service-pixel \
    android.hardware.boot@1.2-impl-pixel

# Core packages
PRODUCT_PACKAGES += \
    fastbootd \
    update_engine \
    update_engine_sideload \
    update_verifier

# Vendor services
PRODUCT_PACKAGES += \
    vndservicemanager \
    vndservice \
    bootctl

# Libraries
PRODUCT_PACKAGES += \
    libtrusty \
    libsysutils \
    libhidltransport.vendor

# Decryption: Trusty's RPMB storage proxy (KeyMint waits on it) and a Weaver HAL
# that talks to the Titan M3 directly, for the credential-encrypted layer. The
# Weaver AIDL library only has a system variant, so the HAL is built for system
# and copied in, as bootctl is.
PRODUCT_PACKAGES += \
    recovery_storageproxyd
RECOVERY_BINARY_SOURCE_FILES += $(TARGET_OUT_EXECUTABLES)/recovery_weaver

# AERA's sandbox for its plugin apps (browser, Telegram, media and the rest); nothing
# requests it otherwise. The browser's engine runtime comes from its plugin rather
# than the image, which has no room for the 41 MB bundled one.
PRODUCT_PACKAGES += \
    aera-browser-jail

RECOVERY_LIBRARY_SOURCE_FILES += \
    $(TARGET_OUT_SHARED_LIBRARIES)/libsysutils.so

TARGET_RECOVERY_DEVICE_MODULES += libion
RECOVERY_LIBRARY_SOURCE_FILES += \
    $(TARGET_OUT_SHARED_LIBRARIES)/libion.so

# Crypto: FBE metadata decryption via Trusty TEE KeyMint
PRODUCT_PROPERTY_OVERRIDES += \
    ro.hardware.keystore=trusty \
    ro.hardware.gatekeeper=trusty

# Saved WiFi and NAS passwords: AERA's default key includes ro.boot.vbmeta.digest,
# which changes with every OTA and kernel flash, and every saved password with it.
# The stable key leaves the digest out and re-seals old entries it can still open.
PRODUCT_PROPERTY_OVERRIDES += \
    ro.aera.stable_secret_key=1

# Metadata
BOARD_USES_METADATA_PARTITION := true

# Virtual A/B
ENABLE_VIRTUAL_AB := true

# Build properties: defaults to yogi fingerprint, overridden per-device at runtime by runatboot.sh
PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="yogi-user 17 CD1A.260714.001.A9 15938155 release-keys" \
    BuildFingerprint=google/yogi/yogi:17/CD1A.260714.001.A9/15938155:user/release-keys \
    DeviceProduct=yogi

PRODUCT_SOONG_NAMESPACES += $(LOCAL_PATH)

# Firstage ramdisk fstab (conf-malibu/f2fs -> fstab.malibu*, Tensor G6, UFS 3c2d0000)
PRODUCT_PACKAGES += fstab.malibu.vendor_ramdisk
PRODUCT_PACKAGES += fstab.malibu-fips.vendor_ramdisk

# service \
# 	strace \

PRODUCT_PACKAGES += \
    linker.vendor_ramdisk \
    resize2fs.vendor_ramdisk \
    resize.f2fs.vendor_ramdisk \
    dump.f2fs.vendor_ramdisk \
    fsck.vendor_ramdisk \
    tune2fs.vendor_ramdisk \
    e2fsck.vendor_ramdisk

# AERA settings
$(call inherit-product, $(LOCAL_PATH)/aera_pixels.mk)
