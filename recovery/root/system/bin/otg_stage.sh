#!/system/bin/sh
#
# otg_stage.sh - stage the phone's own AoC daemon for USB-OTG host mode.
#
# Run by init at early-boot, after wifi_stage.sh. The Type-C port only turns host
# when the AoC votes host as well, and the AoC does that only while its usb_control
# service runs, which aocd starts. This copies aocd and the vendor libraries it links
# into /tmp/aoc, loads aoc_usb_driver.ko and starts aera_otg, which runs aocd.

NAME=otg
LOG=/dev/logs/otg_stage.log
OUT=/tmp/aoc
. /system/bin/stage_lib.sh

attach vendor || fail "cannot map vendor$suffix"
attach vendor_dlkm || fail "cannot map vendor_dlkm$suffix"
V=$WORK/vendor

[ -f $V/bin/aocd ] || fail "vendor has no aocd"
put $V/bin/aocd $OUT/aocd || fail "cannot copy aocd"

# Everything aocd links comes from vendor where vendor has it, since its libbase and
# libc++ are newer than the recovery's. Bionic and liblog come from the recovery.
queue=$OUT/aocd
seen=" "
while [ -n "$queue" ]; do
    set -- $queue
    f=$1
    shift
    queue="$*"
    for lib in $(readelf -d $f | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p'); do
        case "$seen" in *" $lib "*) continue ;; esac
        seen="$seen$lib "
        if [ -f $V/lib64/$lib ]; then
            put $V/lib64/$lib $OUT/lib/$lib || fail "cannot copy $lib"
            queue="$queue $OUT/lib/$lib"
        elif [ ! -f /system/lib64/$lib ]; then
            fail "$lib, needed by ${f##*/}, is on neither vendor nor the recovery"
        fi
    done
done

load /vendor/lib/modules/aoc_usb_driver.ko || fail "cannot load aoc_usb_driver"

release
start aera_otg
echo "staged $(echo $staged | wc -w) files, done at $(cut -d' ' -f1 /proc/uptime)s"
