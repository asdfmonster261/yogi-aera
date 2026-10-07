#!/system/bin/sh
#
# aera_vb_graft.sh - put the running AERA back on a vendor_boot an install replaced.
#
# Run by the installer after an install when "Keep AERA installed" is on, once for
# each slot whose vendor_boot the install changed (an OTA writes the other slot's).
# Usage: aera_vb_graft.sh SOURCE TARGET
#   SOURCE  the running slot's vendor_boot, saved before the install
#   TARGET  the vendor_boot block device to write
#
# The image is SOURCE's container and AERA recovery fragment with TARGET's own
# first stage in place of SOURCE's, the same graft the aera-ak3 zip makes. Copying
# SOURCE whole would put this build's first stage on the other slot.

SRC=$1
DST=$2
MB=/system/bin/magiskboot
WORK=/tmp/aera-vb-graft

fail() {
    echo "E:vb_graft: $*"
    rm -rf $WORK
    exit 1
}

# magiskboot exits 3 after unpacking a vendor_boot; only 1 is an error.
unpack() {
    (cd $1 && $MB unpack vb.img >/dev/null 2>&1)
    [ $? != 1 ]
}

[ -f "$SRC" ] && [ -e "$DST" ] || fail "usage: $0 SOURCE TARGET"
rm -rf $WORK
mkdir -p $WORK/new $WORK/aera || fail "cannot create $WORK"

dd if=$DST of=$WORK/new/vb.img bs=1048576 2>/dev/null || fail "cannot read $DST"
cp $SRC $WORK/aera/vb.img || fail "cannot copy $SRC"
unpack $WORK/new && [ -f $WORK/new/vendor_ramdisk/ramdisk.cpio ] \
    || fail "$DST has no platform fragment"
unpack $WORK/aera && [ -f $WORK/aera/vendor_ramdisk/recovery.cpio ] \
    || fail "$SRC has no recovery fragment"
$MB cpio $WORK/aera/vendor_ramdisk/recovery.cpio "exists init.recovery.pixel_common.rc" \
    >/dev/null 2>&1 || fail "$SRC does not hold AERA"

# The new first stage, stripped as the zip strips it: no system/lib64 or res, no
# real toolbox binaries but init, and no device-typed vintf manifests.
RC=$WORK/aera/vendor_ramdisk/ramdisk.cpio
cp $WORK/new/vendor_ramdisk/ramdisk.cpio $RC || fail "cannot stage the first stage"
{ echo "rm -r system/lib64"; echo "rm -r res"; } > $WORK/cmds
$MB cpio $RC "ls system/bin" 2>/dev/null \
    | awk -F'\t' '$1 ~ /^-/ && $NF != "system/bin/init" { print "rm " $NF }' >> $WORK/cmds
$MB cpio $RC "ls system/etc/vintf/manifest" 2>/dev/null \
    | awk -F'\t' '$1 ~ /^-/ && $NF ~ /\.xml$/ { print $NF }' > $WORK/mans
while IFS= read -r p; do
    $MB cpio $RC "extract $p $WORK/m.xml" >/dev/null 2>&1 || continue
    grep -q 'type="device"' $WORK/m.xml && echo "rm $p" >> $WORK/cmds
done < $WORK/mans
set --
while IFS= read -r p; do set -- "$@" "$p"; done < $WORK/cmds
$MB cpio $RC "$@" >/dev/null 2>&1
$MB cpio $RC "exists system/bin/init" >/dev/null 2>&1 || fail "the stripped first stage has no init"

pb=$(wc -c < $RC)
rb=$(wc -c < $WORK/aera/vendor_ramdisk/recovery.cpio)
mib=$(( (pb + rb) / 1048576 ))
[ $mib -lt 100 ] || fail "recovery-mode ramdisk ${mib} MiB is over the ~100 MiB load limit"

(cd $WORK/aera && $MB repack vb.img out.img >/dev/null 2>&1)
[ -f $WORK/aera/out.img ] || fail "repack failed"
osz=$(wc -c < $WORK/aera/out.img)
psz=$(blockdev --getsize64 $DST 2>/dev/null) || psz=$(wc -c < $DST)
[ $osz -le $psz ] || fail "image is $osz bytes, $DST is $psz"

# The slot's new stock image is the way back if this one does not boot.
slot=${DST##*vendor_boot}
if [ -d /data/local/tmp ]; then
    cp $WORK/new/vb.img /data/local/tmp/vendor_boot$slot-update.img \
        && echo "I:vb_graft: stock image saved to /data/local/tmp/vendor_boot$slot-update.img"
fi

dd if=$WORK/aera/out.img of=$DST bs=1048576 2>/dev/null || fail "cannot write $DST"
sync
want=$(sha256sum $WORK/aera/out.img | cut -d' ' -f1)
got=$(head -c $osz $DST | sha256sum | cut -d' ' -f1)
[ "$want" = "$got" ] || fail "$DST does not read back as written"

echo "I:vb_graft: AERA grafted onto $DST (recovery-mode ramdisk ${mib} MiB)"
rm -rf $WORK
exit 0
