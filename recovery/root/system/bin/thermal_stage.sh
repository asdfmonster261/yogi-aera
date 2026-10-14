#!/system/bin/sh
#
# thermal_stage.sh - load the CPU temperature sensors from the phone's own vendor_dlkm.
#
# Run by init at early-boot. Without google_thermal_sensor the recovery has no CPU
# thermal zones at all, and thermal_watch.sh has nothing to track.

NAME=thermal
LOG=/dev/logs/thermal_stage.log
. /system/bin/stage_lib.sh

attach vendor_dlkm || fail "cannot map vendor_dlkm$suffix"
load google_thermal_sensor.ko || fail "cannot load google_thermal_sensor"

release
echo "done at $(cut -d' ' -f1 /proc/uptime)s"
