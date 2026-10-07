### AnyKernel3 script - AERA recovery installer for the Pixel 11 (malibu) family (repack)

### AnyKernel setup
properties() { '
kernel.string=AERA recovery for the Pixel 11 (malibu) family - repack into your own vendor_boot
do.devicecheck=0
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
'; } # end properties

# This installs AERA by REPACKING, not by flashing a prebuilt image. On the
# device it reads the live vendor_boot, grafts AERA's recovery fragment onto
# THIS device's own first-stage, and writes the result back to the active slot. So
# one zip adapts to whatever stock vendor_boot the user is on, and it needs no
# fastboot: it runs from KernelFlasher (a proper AnyKernel3 zip) or a custom recovery.
#
# Why graft onto the stock first-stage: malibu devices merge recovery into a single
# vendor_boot platform fragment, and AERA's own generic first-stage cannot
# finish the device's boot. So the platform must be the device's own, first-stage only
# (its stock-recovery bulk removed) so the recovery-mode ramdisk stays under the
# bootloader's ~100 MiB load limit, with AERA's recovery fragment beside it.
#
# vendor_boot is covered by a hash descriptor in the main vbmeta, not a chained
# footer like boot, and this bootloader is unlocked, so there is no footer to
# preserve and nothing to sign. magiskboot rebuilds the header on repack.
#
# magiskboot here is the arm64 build from Magisk; AK3 ships a 32-bit one that is
# dead on this 64-bit-only device. build-aera-ak3.sh swaps it in and asserts arch.

# shell variables
BLOCK=vendor_boot;
IS_SLOT_DEVICE=1;

RUN_SLOT=$(grep '^androidboot.slot_suffix = ' /proc/bootconfig 2>/dev/null | cut -d'"' -f2);

# Right after an update the bootloader is set to boot the other slot, while
# bootconfig still names this one, so installing here would leave the updated slot
# with stock recovery. The Pixel boot control service keeps that state in devinfo.
# Read it directly: AK3 mounts Android's /system over the recovery's, so the
# recovery's bootctl is out of reach. Take the other slot only in the exact state an
# update leaves (other slot active, bootable, never marked successful, retries left;
# this one inactive). Anything else, an unreadable devinfo included, keeps the
# running slot.
updated_slot() {
  local run other tries next;
  set -- $(dd if=/dev/block/by-name/devinfo bs=128 count=1 2>/dev/null | od -An -tu1 -v);
  [ $# -eq 128 ] && [ "$1 $2 $3 $4" = "68 69 86 73" ] || return 1;
  # A/B data needs devinfo version 3.3 or later.
  [ $(( ($6 << 24) | ($5 << 16) | ($8 << 8) | $7 )) -ge 196611 ] || return 1;
  # Slot records at bytes 48 and 52: retry count, then flags (1 unbootable,
  # 2 successful, 4 active).
  case "$RUN_SLOT" in
    _a) run=${50}; other=${54}; tries=${53}; next=_b;;
    _b) run=${54}; other=${50}; tries=${49}; next=_a;;
    *) return 1;;
  esac;
  [ $((other & 7)) -eq 4 ] && [ "$tries" -gt 0 ] && [ $((run & 4)) -eq 0 ] || return 1;
  echo $next;
}
SLOT_TARGET=$RUN_SLOT; UPDATED=;
v=$(updated_slot) && { SLOT_TARGET=$v; UPDATED=1; };

# In a TWRP-based recovery the toolbox getprop is a symlink needing
# LD_LIBRARY_PATH, which AK3 unsets, so getprop ro.boot.slot_suffix returns empty and
# setup_ak aborts with "Unable to determine active slot". The slot is in
# /proc/bootconfig as androidboot.slot_suffix regardless. Read boot props from there;
# anything else falls through to the real binary (which works in a booted flasher).
getprop() {
  local k="$1" v;
  case "$k" in
    ro.boot.slot_suffix)
      [ "$SLOT_TARGET" ] && { echo "$SLOT_TARGET"; return 0; };;
    ro.boot.*)
      v=$(grep "^androidboot.${k#ro.boot.} = " /proc/bootconfig 2>/dev/null | cut -d'"' -f2);
      [ "$v" ] && { echo "$v"; return 0; };;
  esac;
  /system/bin/getprop "$@" 2>/dev/null;
}

# import functions/variables and setup patching - see for reference (DO NOT REMOVE)
. tools/ak3-core.sh;

MB=$AKHOME/tools/magiskboot;
AVB=$AKHOME/vendor_boot-aera.img;
AVBSHA=__AVBSHA__;
BKDIR=/data/local/tmp;
WORK=$AKHOME/repack;

sha_of() { $bb sha256sum "$1" 2>/dev/null | $bb cut -d' ' -f1; }

# magiskboot returns non-error, non-zero codes for some image kinds (3 for a
# vendor_boot, which is what we unpack); only 1 is a real failure.
mb() { local rc=0; "$MB" "$@" >/dev/null 2>&1 || rc=$?; [ "$rc" != 1 ]; }

# AK3's own do.devicecheck is unreliable in a recovery (unset LD_LIBRARY_PATH
# breaks the toolbox getprop, then build.prop paths do not match the mount layout).
# /proc/bootconfig carries androidboot.hardware with no mount or getprop needed.
check_device() {
  local dev;
  dev=$($bb grep '^androidboot.hardware = ' /proc/bootconfig 2>/dev/null | $bb cut -d'"' -f2);
  [ "$dev" ] || dev=$($bb sed -n 's/.*androidboot\.hardware=\([^ ]*\).*/\1/p' /proc/cmdline 2>/dev/null);
  [ "$dev" ] || dev=$(getprop ro.product.device 2>/dev/null);
  case "$dev" in yogi|cubs|grizzly|kodiak) ;; *) abort "  ! device is '${dev:-unknown}', not a Pixel 11 (malibu). Aborting.";; esac;
  DEVICE="$dev";
}

# Strip a platform ramdisk cpio to the device's first-stage: drop system/lib64, res, the
# real toolbox binaries (keep init and the toybox symlinks), and any device-typed
# vintf manifest, whose HALs went with those binaries. Everything is
# magiskboot's own cpio plus busybox awk to read the ls output; no system cpio.
strip_platform() {
  local RC=$1 p;
  { echo "rm -r system/lib64"; echo "rm -r res"; } > "$WORK/cmds";
  "$MB" cpio "$RC" "ls system/bin" 2>/dev/null \
    | $bb awk -F'\t' '$1 ~ /^-/ && $NF != "system/bin/init" { print "rm " $NF }' >> "$WORK/cmds";
  "$MB" cpio "$RC" "ls system/etc/vintf/manifest" 2>/dev/null \
    | $bb awk -F'\t' '$1 ~ /^-/ && $NF ~ /\.xml$/ { print $NF }' > "$WORK/mans";
  while IFS= read -r p; do
    "$MB" cpio "$RC" "extract $p $WORK/m.xml" >/dev/null 2>&1 || continue;
    $bb grep -q 'type="device"' "$WORK/m.xml" && echo "rm $p" >> "$WORK/cmds";
  done < "$WORK/mans";
  set --;
  while IFS= read -r p; do set -- "$@" "$p"; done < "$WORK/cmds";
  "$MB" cpio "$RC" "$@" >/dev/null 2>&1 || true;
}

ui_print " ";
ui_print "  AERA recovery for the Pixel 11 family (repack installer)";
ui_print "  grafts AERA onto your own vendor_boot first-stage";
ui_print " ";
if [ "$UPDATED" ]; then
  ui_print "  slot   : $SLOT, made active by an update (running $RUN_SLOT)";
else
  ui_print "  slot   : ${SLOT:-none}";
fi;

check_device;
ui_print "  device : $DEVICE";

[ -f "$AVB" ] || abort "  ! AERA image missing from zip. Aborting.";
[ "$(sha_of "$AVB")" = "$AVBSHA" ] || abort "  ! AERA image checksum mismatch - zip corrupt or modified. Aborting.";
ui_print "  aera   : checksum OK";

[ -e "$BLOCK" ] || abort "  ! vendor_boot partition not found ($BLOCK). Aborting.";

$bb rm -rf "$WORK"; $bb mkdir -p "$WORK/stock" "$WORK/aera";

# The inactive slot is not a fallback under Virtual A/B, so this backup and
# fastboot are the way back.
$bb dd if="$BLOCK" of="$WORK/stock/vb.img" bs=1048576 2>/dev/null || abort "  ! could not read vendor_boot. Aborting.";
if [ "$UPDATED" ]; then
  # The updated slot now holds that update's own stock vendor_boot, the one to go
  # back to, so take it fresh.
  bk=$BKDIR/vendor_boot$SLOT-update.img;
  $bb cp -f "$WORK/stock/vb.img" "$bk" && ui_print "  backup : $bk" || abort "  ! refusing to write without a backup. Aborting.";
else
  bk=$BKDIR/vendor_boot-before.img;
  if [ ! -f "$bk" ]; then
    $bb cp -f "$WORK/stock/vb.img" "$bk" && ui_print "  backup : $bk" || abort "  ! refusing to write without a backup. Aborting.";
  else
    ui_print "  backup : $bk (kept existing)";
  fi;
fi;

# AERA's image has two fragments: a generic platform we discard, and the
# recovery we keep.
( cd "$WORK/stock" && mb unpack vb.img ) || abort "  ! stock unpack failed. Aborting.";
[ -f "$WORK/stock/vendor_ramdisk/ramdisk.cpio" ] || abort "  ! stock vendor_boot has no platform fragment. Aborting.";
$bb cp -f "$AVB" "$WORK/aera/vb.img";
( cd "$WORK/aera" && mb unpack vb.img ) || abort "  ! AERA unpack failed. Aborting.";
[ -f "$WORK/aera/vendor_ramdisk/recovery.cpio" ] || abort "  ! AERA image is not a two-fragment vendor_boot. Aborting.";

RC="$WORK/aera/vendor_ramdisk/ramdisk.cpio";
$bb cp -f "$WORK/stock/vendor_ramdisk/ramdisk.cpio" "$RC";
ui_print "  stripping stock platform to first-stage...";
strip_platform "$RC";

"$MB" cpio "$WORK/aera/vendor_ramdisk/recovery.cpio" "exists init.recovery.pixel_common.rc" >/dev/null 2>&1 \
  || abort "  ! recovery fragment missing our recovery init. Aborting.";
pb=$($bb wc -c < "$RC"); rb=$($bb wc -c < "$WORK/aera/vendor_ramdisk/recovery.cpio");
mib=$(( (pb + rb) / 1048576 ));
ui_print "  recovery-mode ramdisk : ${mib} MiB";
[ "$mib" -lt 100 ] || abort "  ! ramdisk ${mib} MiB exceeds the ~100 MiB load limit (strip failed?). Aborting.";

( cd "$WORK/aera" && mb repack vb.img out.img ) || abort "  ! repack failed. Aborting.";
[ -f "$WORK/aera/out.img" ] || abort "  ! repack produced no image. Aborting.";

# vendor_boot is not chained, so the image need not fill the partition, but it must
# fit. Refuse to write one larger than the partition.
PSZ=$($bb blockdev --getsize64 "$BLOCK" 2>/dev/null); [ "$PSZ" ] || PSZ=$($bb wc -c < "$WORK/stock/vb.img");
OSZ=$($bb wc -c < "$WORK/aera/out.img");
[ "$OSZ" -le "$PSZ" ] || abort "  ! repacked vendor_boot $OSZ > partition $PSZ. Aborting.";

ui_print "  writing vendor_boot$SLOT ($OSZ bytes)...";
$bb dd if="$WORK/aera/out.img" of="$BLOCK" bs=1048576 || abort "  ! vendor_boot write failed. Aborting.";
$bb sync;

$bb rm -rf "$WORK/verify"; $bb mkdir -p "$WORK/verify";
$bb dd if="$BLOCK" of="$WORK/verify/vb.img" bs=1048576 2>/dev/null;
( cd "$WORK/verify" && mb unpack vb.img ) || abort "  ! read-back unpack failed. Aborting.";
if "$MB" cpio "$WORK/verify/vendor_ramdisk/recovery.cpio" "exists init.recovery.pixel_common.rc" >/dev/null 2>&1; then
  ui_print "  verify : OK";
else
  ui_print "  verify : MISMATCH";
  ui_print "    restore with:";
  ui_print "    dd if=$bk of=$BLOCK bs=1048576";
  abort "  ! verification failed. Aborting.";
fi;

$bb rm -rf "$WORK";

ui_print " ";
if [ "$UPDATED" ]; then
  ui_print "  Done. $SLOT boots next; reboot to recovery to run AERA there.";
else
  ui_print "  Done. Reboot to recovery to run AERA.";
fi;
ui_print " ";
ui_print "  Backup is at $bk - pull it to a PC now:";
ui_print "    adb pull $bk";
ui_print " ";
ui_print "  If recovery does not boot, from fastboot restore stock:";
ui_print "    fastboot flash vendor_boot$SLOT <stock vendor_boot.img>";
ui_print "  Do NOT change slots and do NOT flash the bootloader.";
ui_print " ";
