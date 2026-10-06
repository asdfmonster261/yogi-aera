#!/system/bin/sh
#
# wifi_stage.sh - load the phone's own WiFi driver for AERA's WLAN.
#
# Run by init at early-boot, after gpu_stage.sh. It copies the driver's firmware into
# RAM and loads the driver and the modules it needs, as stock does at boot, then sets
# sys.aera.wlan.ready so init may start the supplicant when AERA asks for WLAN.

NAME=wifi
LOG=/dev/logs/wifi_stage.log
. /system/bin/stage_lib.sh

attach vendor || fail "cannot map vendor$suffix"
attach vendor_dlkm || fail "cannot map vendor_dlkm$suffix"
# For rfkill, which cfg80211 needs and which is a GKI module.
attach system_dlkm || fail "cannot map system_dlkm$suffix"

# The other Pixel 11s ship both bcmdhd4383 and bcmdhd4390, and modules.load lists
# 4383 first. Load the one this phone's own insmod config names, as stock does.
drv=$(sed -n 's/^modprobe|\(bcmdhd[^ ]*\.ko\).*/\1/p' \
    $WORK/vendor_dlkm/etc/init.insmod.$(getprop ro.hardware).cfg 2> /dev/null | head -n 1)
[ -n "$drv" ] || drv=$(grep -m 1 '^bcmdhd' $WORK/vendor_dlkm/lib/modules/modules.load)
[ -n "$drv" ] || fail "vendor_dlkm has no bcmdhd driver"

# The PCIe PHY loads its firmware as it probes and fails for good if the file is not
# there yet. The driver picks its firmware, calibration and CLM files by name and asks
# for them when wlan0 comes up, long after the partitions are gone.
for fw in $WORK/vendor/firmware/*pcie_phy_fw* $WORK/vendor/firmware/*bcmdhd*; do
    put $fw /vendor/firmware/${fw##*/} || fail "cannot copy ${fw##*/}"
done
# The PCIe controllers look their PHY up when they probe, so modules.dep does not
# list it. Without it they stay deferred and the driver times out waiting for the
# power control of its slot.
load /vendor/lib/modules/phy-google-pcie.ko || fail "cannot load phy-google-pcie"
load /vendor/lib/modules/$drv || fail "cannot load ${drv%.ko}"

i=0
while [ ! -e /sys/class/net/wlan0 ] && [ $i -lt 50 ]; do
    sleep 0.1
    i=$((i + 1))
done
[ -e /sys/class/net/wlan0 ] || fail "${drv%.ko} is loaded but there is no wlan0"

release
setprop sys.aera.wlan.ready 1
echo "loaded ${drv%.ko}, staged $(echo $staged | wc -w) files, done at $(cut -d' ' -f1 /proc/uptime)s"
