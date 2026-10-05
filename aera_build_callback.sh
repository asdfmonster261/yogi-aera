#!/bin/bash
#
# aera_build_callback.sh - BOARD_RECOVERY_IMAGE_PREPARE hook for the malibu Pixels.
# Runs on the finished recovery root, before it is packed:
#   bash aera_build_callback.sh <TARGET_RECOVERY_ROOT_OUT> --second-call
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$1"

fail() { echo "aera_build_callback: $*" >&2; exit 1; }

[ -d "$TARGET_DIR" ] || fail "no recovery root at '$TARGET_DIR'"
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
chmod 755 "$TARGET_DIR"/vendor/bin/hw/* || exit 1

# LGZ. The recovery-mode ramdisk only loads below ~100 MiB, so binaries, libraries
# and fonts are LZMA-packed here and unpacked by init at boot (subpatch 0001).
# init and everything it links must stay as they are, or nothing can unpack them.
lgz_host="$SCRIPT_DIR/selfcode/lgz/lgz_host_bin"
lgz_device="$SCRIPT_DIR/selfcode/lgz/lgz_device"
[ -x "$lgz_host" ] && [ -f "$lgz_device" ] || fail "lgz binaries missing; vendorsetup.sh builds them"
grep -aq '\[LGZ\] Starting early decompression' "$TARGET_DIR/system/bin/init" ||
    fail "init has no LGZ hook; did subpatch 0001 apply?"

# The build's PATH sandbox has no readelf, so use the clang prebuilt's.
top=$(cd "$SCRIPT_DIR/../../.." && pwd)
clang_ver=$(sed -n 's/.*ClangDefaultVersion *= *"\(clang-r[0-9a-z]*\)".*/\1/p' "$top/build/soong/cc/config/global.go")
readelf="$top/prebuilts/clang/host/linux-x86/$clang_ver/bin/llvm-readelf"
[ -x "$readelf" ] || fail "no llvm-readelf at '$readelf'"

keep=" init linker linker64 lgz "
queue="system/bin/init"
while [ -n "$queue" ]; do
    f=${queue%% *}; queue=${queue#"$f"}; queue=${queue# }
    for lib in $("$readelf" -d "$TARGET_DIR/$f" | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p'); do
        case "$keep" in *" $lib "*) continue ;; esac
        keep="$keep$lib "
        [ -f "$TARGET_DIR/system/lib64/$lib" ] && queue="${queue:+$queue }system/lib64/$lib"
    done
done
case "$keep" in *" libc.so "*) ;; *) fail "could not work out which libraries init links" ;; esac

manifest="$TARGET_DIR/lgz_compressed_files.txt"
echo "# <mode> <path> of every file init unpacks at boot" > "$manifest"
before=0 after=0 count=0
while IFS= read -r f; do
    case "$keep" in *" ${f##*/} "*) continue ;; esac
    mode=$(stat -c%a "$f")
    magic=$(head -c 7 "$f" | od -An -tx1 | tr -d ' \n')
    # Already packed by an earlier run over the same root (--notrm): "UCOMP01".
    if [ "$magic" = 55434f4d503031 ]; then
        echo "$mode /${f#"$TARGET_DIR"/}" >> "$manifest"
        continue
    fi
    case "$f" in
        */twres/fonts/*.ttf|*/twres/fonts/*.otf) ;;
        */twres/fonts/*) continue ;;
        *) [ "${magic:0:8}" = 7f454c46 ] || continue ;;
    esac
    size=$(stat -c%s "$f")
    [ "$size" -ge 4096 ] || continue
    "$lgz_host" compress "$f" "$f.lgz" > /dev/null 2>&1 || { rm -f "$f.lgz"; continue; }
    packed=$(stat -c%s "$f.lgz")
    if [ "$packed" -lt "$size" ]; then
        mv -f "$f.lgz" "$f" && chmod "$mode" "$f" || exit 1
        echo "$mode /${f#"$TARGET_DIR"/}" >> "$manifest"
        before=$((before + size)) after=$((after + packed)) count=$((count + 1))
    else
        rm -f "$f.lgz"
    fi
done < <(find "$TARGET_DIR/system/bin" "$TARGET_DIR/system/lib64" "$TARGET_DIR/vendor/bin" \
             "$TARGET_DIR/vendor/lib64" "$TARGET_DIR/sbin" "$TARGET_DIR/twres/fonts" -type f 2>/dev/null | sort)
install -m 755 "$lgz_device" "$TARGET_DIR/system/bin/lgz" || exit 1
echo "aera_build_callback: lgz packed $count files, $((before >> 20)) MiB -> $((after >> 20)) MiB"
