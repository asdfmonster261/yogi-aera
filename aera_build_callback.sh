#!/bin/bash
#
# aera_build_callback.sh - BOARD_RECOVERY_IMAGE_PREPARE hook for the malibu Pixels.
# Runs on the finished recovery root, before it is packed:
#   bash aera_build_callback.sh <TARGET_RECOVERY_ROOT_OUT> --second-call
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$1"

[ -d "$TARGET_DIR" ] || { echo "aera_build_callback: no recovery root at '$TARGET_DIR'" >&2; exit 1; }
[ "$2" = "--second-call" ] || exit 0

# vendorsetup.sh writes the platform here; make recipe shells do not reliably
# inherit DEVICE_BUILD_FLAG from the lunch session.
PLATFORM=""
[ -f "$SCRIPT_DIR/.build_platform.conf" ] && . "$SCRIPT_DIR/.build_platform.conf"
: "${PLATFORM:=malibu}"
echo "aera_build_callback: platform $PLATFORM"

# The stock Rust KeyMint and its VINTF fragment, for metadata decryption.
prebuilt="$SCRIPT_DIR/prebuilt/$PLATFORM"
mkdir -p "$TARGET_DIR/vendor"
cp -af "$prebuilt/bin" "$prebuilt/etc" "$TARGET_DIR/vendor/" || exit 1
chmod 755 "$TARGET_DIR"/vendor/bin/hw/*
