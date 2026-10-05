#
#	This file is part of the OrangeFox Recovery Project
# 	Copyright (C) 2020-2026 The OrangeFox Recovery Project
#
#	OrangeFox is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	any later version.
#
#	OrangeFox is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
# 	This software is released under GPL version 3 or any later version.
#	See <http://www.gnu.org/licenses/>.
#
# 	Please maintain this if you use this script or any part of it
#

# vendorsetup.sh - AERA build variables for the Pixel 11 (malibu) family.
# Sourced by build/envsetup.sh. AERA's build reads these from the environment;
# the settings that only make reads are in aera_pixels.mk.

FDEVICE="pixels"

aera_get_target_device() {
local chkdev=$(echo "$BASH_SOURCE" | grep -w $FDEVICE)
   if [ -n "$chkdev" ]; then
      AERA_BUILD_DEVICE="$FDEVICE"
   else
      chkdev=$(set | grep BASH_ARGV | grep -w $FDEVICE)
      [ -n "$chkdev" ] && AERA_BUILD_DEVICE="$FDEVICE"
   fi
}

if [ -z "$1" -a -z "$AERA_BUILD_DEVICE" ]; then
   aera_get_target_device
fi

if [ "$1" = "$FDEVICE" -o "$AERA_BUILD_DEVICE" = "$FDEVICE" ]; then
	if [ -z "${DEVICE_BUILD_FLAG:-}" ]; then
		export DEVICE_BUILD_FLAG="malibu"
	fi
	echo "  Building for platform: $DEVICE_BUILD_FLAG"

	# Make recipe shells do not reliably inherit the lunch environment, so
	# aera_build_callback.sh reads the platform from this file.
	echo "PLATFORM=$DEVICE_BUILD_FLAG" > "$(gettop)/device/google/pixels/.build_platform.conf"

	export AERA_BUILD_TYPE=Beta
	export AERA_BUILD_STATUS=Unofficial
	export USE_CCACHE=1
	export TARGET_ARCH=arm64
	export LC_ALL=C

	export AERA_VIRTUAL_AB_DEVICE=1
	export AERA_AB_DEVICE=1
	export AERA_VENDOR_BOOT_RECOVERY=1
	export AERA_RECOVERY_VENDOR_BOOT_PARTITION="/dev/block/platform/3c2d0000.ufs/by-name/vendor_boot"
	export AERA_VANILLA_BUILD=1

	export TARGET_DEVICE_ALT="yogi,cubs,grizzly,kodiak"
	export AERA_TARGET_DEVICES="$TARGET_DEVICE_ALT"

	export AERA_REPLACE_TOOLBOX_GETPROP=1
	export AERA_USE_BASH_SHELL=1
	export AERA_BASH_TO_SYSTEM_BIN=1
	export AERA_USE_UPDATED_MAGISKBOOT=1
	export AERA_USE_BUSYBOX_BINARY=1
	export AERA_DELETE_MAGISK_ADDON=1

	export AERA_ENABLE_APP_MANAGER=1
	export AERA_DELETE_AROMAFM=1
	export AERA_DELETE_INITD_ADDON=1

	export AERA_ENABLE_KERNELSU_SUPPORT=1
	export AERA_ENABLE_KERNELSU_NEXT_SUPPORT=1

	# lgz packs the recovery ramdisk: the host build runs in aera_build_callback.sh and
	# the static device build goes into the ramdisk, where init unpacks with it at boot.
	# Z7_ST because the LZMA SDK's threading sources are not built.
	lgz="$(gettop)/device/google/pixels/selfcode/lgz"
	lzma="$(gettop)/external/lzma/C"
	lzma_srcs="$lzma/Alloc.c $lzma/LzFind.c $lzma/LzmaDec.c $lzma/LzmaEnc.c $lzma/Lzma2Dec.c $lzma/Lzma2Enc.c $lzma/CpuArch.c"
	clang_ver=$(sed -n 's/.*ClangDefaultVersion *= *"\(clang-r[0-9a-z]*\)".*/\1/p' "$(gettop)/build/soong/cc/config/global.go")
	if [ "$lgz/lgzv3.c" -nt "$lgz/lgz_host_bin" ]; then
		gcc -O3 -pipe -fopenmp -flto -march=native -I"$lzma" -DZ7_ST \
			-o "$lgz/lgz_host_bin" "$lgz/lgzv3.c" $lzma_srcs || echo "  lgz: host build failed"
	fi
	if [ "$lgz/lgzv3.c" -nt "$lgz/lgz_device" ]; then
		"$(gettop)/prebuilts/clang/host/linux-x86/$clang_ver/bin/clang" \
			--target=aarch64-unknown-linux-musl --rtlib=compiler-rt -static -s -O2 \
			--sysroot="$(gettop)/prebuilts/build-tools/sysroots/aarch64-unknown-linux-musl" \
			-I"$lzma" -DZ7_ST -o "$lgz/lgz_device" "$lgz/lgzv3.c" $lzma_srcs || echo "  lgz: device build failed"
	fi
	unset lgz lzma lzma_srcs clang_ver

	# Tensor recovery uses AIDL KeyMint; a stray keymaster version forces the legacy path.
	unset AERA_DEFAULT_KEYMASTER_VERSION OF_DEFAULT_KEYMASTER_VERSION

	export | grep -E 'AERA_|OF_|TARGET_|TW_'
	if [ -n "$AERA_BUILD_LOG_FILE" -a -f "$AERA_BUILD_LOG_FILE" ]; then
		export | grep -E 'AERA_|OF_|TARGET_|TW_' >> "$AERA_BUILD_LOG_FILE"
	fi
fi
