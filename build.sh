#!/bin/bash
#
# build.sh - AERA Recovery build script for the Tensor G6 (malibu) Pixels.
#
# Usage:
#   ./build.sh [--family malibu] [--notrm] [-j N] [--name TAG] [--patch N]
#
# Options:
#   --family FAMILY   Set SoC family before lunch (malibu).
#                     If omitted, defaults to malibu.
#   --notrm           Don't clean out/target/product/pixels before build.
#   -j N              Parallelism for make (default: $(nproc)).
#   --name TAG        Name tag for output files. Copies final .img/.zip to
#                     builds/AERA-<VERSION>-{TAG}-{family}.img/zip
#   --patch N         Set AERA_MAINTAINER_PATCH_VERSION (numbers only).
#                     E.g., "--patch 5" will result in version R1.0_5.

set -eo pipefail

# AERA's vendor build reads AERA_ and a handful of legacy OF_ names.
for var in ${!AERA_@} ${!FOX_@} ${!OF_@} ${!TARGET_@} ${!TW_@}; do     unset "$var"; done
unset DEVICE_BUILD_FLAG

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

FAMILY=""
CLEAN=true
JOBS="$(nproc)"
BUILD_NAME=""
PATCH_VERSION=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --family)
            shift
            FAMILY="${1:-}"
            if [[ -z "$FAMILY" ]]; then
                echo "ERROR: --family requires an argument (malibu)"
                exit 1
            fi
            case "$FAMILY" in
                malibu) ;;
                *)
                    echo "ERROR: unknown family '$FAMILY'. Valid: malibu"
                    exit 1
                    ;;
            esac
            shift
            ;;
        --notrm)
            CLEAN=false
            shift
            ;;
        -j)
            shift
            JOBS="${1:-$(nproc)}"
            shift
            ;;
        -j[0-9]*)
            JOBS="${1#-j}"
            shift
            ;;
        --name)
            shift
            BUILD_NAME="${1:-}"
            if [[ -z "$BUILD_NAME" ]]; then
                echo "ERROR: --name requires an argument"
                exit 1
            fi
            shift
            ;;
        --patch)
            shift
            PATCH_VERSION="${1:-}"
            if [[ -z "$PATCH_VERSION" || ! "$PATCH_VERSION" =~ ^[0-9]+$ ]]; then
                echo "ERROR: --patch requires a numeric argument (e.g., 5)"
                exit 1
            fi
            export AERA_MAINTAINER_PATCH_VERSION="$PATCH_VERSION"
            shift
            ;;
        -h|--help)
            sed -n '2,17p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=============================================="
echo "  AERA Recovery Build Script"
echo "=============================================="
echo "  Source root:   $SOURCE_ROOT"
echo "  Family:        ${FAMILY:-<interactive>}"
echo "  Name:          ${BUILD_NAME:-<auto>}"
echo "  Patch Version: ${AERA_MAINTAINER_PATCH_VERSION:-<not set>}"
echo "  Clean:         $CLEAN"
echo "  Jobs:          $JOBS"
echo "=============================================="

cd "$SOURCE_ROOT"

python device/google/pixels/patch.py --mod

if [ ! -f "external/guava/Android.bp" ] || [ ! -f "external/gflags/Android.bp" ]; then
    if ! repo sync -c -d --force-sync external/gflags external/guava; then
        echo "ERROR: repo sync failed. Please check your network connection and try again."
        exit 1
    fi
fi

PRODUCT_OUT="out/target/product/pixels"
if [[ "$CLEAN" == "true" && -d "$PRODUCT_OUT" ]]; then
    echo "[build] Cleaning $PRODUCT_OUT ..."
    rm -rf "$PRODUCT_OUT"
    echo "[build] Clean done."
fi

if [[ -n "$FAMILY" ]]; then
    export DEVICE_BUILD_FLAG="$FAMILY"
    echo "[build] Pre-set DEVICE_BUILD_FLAG=$FAMILY"
fi

echo "[build] Sourcing build/envsetup.sh ..."
set +e
source build/envsetup.sh

# bp2a is AERA's Android 16 release config.
echo "[build] Running lunch twrp_pixels-bp2a-eng ..."
lunch twrp_pixels-bp2a-eng
set -eo pipefail

echo "[build] DEVICE_BUILD_FLAG=${DEVICE_BUILD_FLAG:-<not set>}"

BUILD_TARGETS="adbd vendorbootimage"


echo "=============================================="
echo "  Build targets: $BUILD_TARGETS"
echo "  Parallelism:   -j$JOBS"
echo "=============================================="

mka $BUILD_TARGETS -j"$JOBS"

echo ""
echo "=============================================="
echo "  Build complete!"
echo "  Output: $SOURCE_ROOT/$PRODUCT_OUT/"
echo "=============================================="

BUILDS_DIR="$SOURCE_ROOT/builds"
mkdir -p "$BUILDS_DIR"

LATEST_IMG=$(find "$SOURCE_ROOT/$PRODUCT_OUT" -maxdepth 1 -name 'AERA-*.img' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
# AERA also writes a <name>_lite.zip beside the full one; take the full zip.
LATEST_ZIP=$(find "$SOURCE_ROOT/$PRODUCT_OUT" -maxdepth 1 -name 'AERA-*.zip' ! -name '*_lite.zip' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

FAMILY_TAG="${DEVICE_BUILD_FLAG:-unknown}"

if [[ -n "$LATEST_IMG" ]]; then
    AERA_PREFIX=$(basename "$LATEST_IMG" | cut -d'-' -f1,2)
elif [[ -n "$LATEST_ZIP" ]]; then
    AERA_PREFIX=$(basename "$LATEST_ZIP" | cut -d'-' -f1,2)
else
    AERA_PREFIX="AERA-UnknownVersion"
fi

if [[ -n "$BUILD_NAME" ]]; then
    IMG_DEST="$BUILDS_DIR/${AERA_PREFIX}-${BUILD_NAME}-${FAMILY_TAG}.img"
    ZIP_DEST="$BUILDS_DIR/${AERA_PREFIX}-${BUILD_NAME}-${FAMILY_TAG}.zip"
else
    IMG_DEST="$BUILDS_DIR/${AERA_PREFIX}-${FAMILY_TAG}.img"
    ZIP_DEST="$BUILDS_DIR/${AERA_PREFIX}-${FAMILY_TAG}.zip"
fi

if [[ -n "$LATEST_IMG" ]]; then
    cp "$LATEST_IMG" "$IMG_DEST"
    echo "[build] Copied: $IMG_DEST"
fi
if [[ -n "$LATEST_ZIP" ]]; then
    cp "$LATEST_ZIP" "$ZIP_DEST"
    echo "[build] Copied: $ZIP_DEST"
fi

if [[ -z "$LATEST_IMG" && -z "$LATEST_ZIP" ]]; then
    echo "[build] WARNING: No AERA artifacts found in $PRODUCT_OUT"
fi

echo "=============================================="
echo "  Artifacts in: $BUILDS_DIR/"
echo "=============================================="