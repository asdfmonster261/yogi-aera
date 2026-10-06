#!/system/bin/sh
#
# aera_otg.sh - keep the AoC's host vote up and /dev/block/otg-usb on the attached stick.
#
# Run by init as aera_otg once otg_stage.sh has put aocd and its libraries in /tmp/aoc.

LOGF=/tmp/recovery.log
RAM=/tmp/aoc

log() { echo "I:otg: $1" >> "$LOGF"; }

aoc_ready() {
    [ "$(cat /sys/devices/platform/*.aoc/verify_aoc_responsive 2>/dev/null)" = responsive ]
}

usb_control() {
    for f in $(find /sys/devices/platform/*.aoc -name services 2>/dev/null); do
        cat "$f" 2>/dev/null
    done | grep -q usb_control
}

# The stick's sdX letter drifts across attach and detach, so /usb_otg points at a
# symlink kept on whichever removable USB disk is attached.
usb_disk() {
    for d in /sys/block/sd*; do
        [ "$(cat "$d/removable" 2>/dev/null)" = 1 ] || continue
        readlink -f "$d/device" 2>/dev/null | grep -q usb || continue
        b=/dev/block/${d##*/}
        if [ -b "${b}1" ]; then echo "${b}1"; else echo "$b"; fi
        return 0
    done
    return 1
}

# aocd's startup is flaky: an instance may start usb_control, sit idle without it, or
# die, and a fresh one eventually gets it up. So relaunch until usb_control appears,
# killing the previous attempt first. usb_control stays up once started.
mkdir -p /dev/socket
voted=0
while true; do
    if usb_control; then
        [ $voted = 1 ] || { voted=1; log "aocd up; AOC vote live"; }
    elif aoc_ready; then
        kill $(pidof aocd) 2>/dev/null
        LD_LIBRARY_PATH=$RAM/lib:/system/lib64 $RAM/aocd > /dev/null 2>&1 &
        sleep 4
        usb_control && { voted=1; log "aocd up; AOC vote live"; }
    fi
    p=$(usb_disk)
    if [ -n "$p" ] && [ -b "$p" ]; then
        [ "$(readlink /dev/block/otg-usb 2>/dev/null)" = "$p" ] || {
            ln -sf "$p" /dev/block/otg-usb
            log "otg-usb -> $p"
        }
    fi
    sleep 3
done
