#!/system/bin/sh
# thermal_watch.sh -- retreat through cpu_caps.sh's levels on CPU heat.
# Hottest CPU zone: level 1 at 55 C, level 2 at 65 C, back below 48 C one level
# at a time. The zones come from thermal_stage.sh. Readings land in
# /dev/logs/thermal.log.

LOG=/dev/logs/thermal.log
POLL=5      # seconds between readings
REPORT=6    # log a line every N polls

CPU_ZONES="BIG MID MIDLL DSU"
WARM=55
HOT=65
COOL=48

mkdir -p /dev/logs
: >> "$LOG"
log() { echo "[$(date '+%H:%M:%S' 2>/dev/null)] $*" >> "$LOG"; }

log "thermal_watch start: zones=$CPU_ZONES warm=${WARM}C hot=${HOT}C cool=${COOL}C poll=${POLL}s"

cpu_zone() { # $1 zone type; true when it is one of CPU_ZONES
    case " $CPU_ZONES " in *" $1 "*) return 0 ;; esac
    return 1
}

for z in /sys/class/thermal/thermal_zone*; do
    t=$(cat "$z/type" 2>/dev/null)
    cpu_zone "$t" && log "tracking ${z##*/} $t $(cat "$z/temp" 2>/dev/null)"
done

read_cpu() { # echoes the hottest CPU zone in degrees C, nothing if none reads
    m=""
    for z in /sys/class/thermal/thermal_zone*; do
        cpu_zone "$(cat "$z/type" 2>/dev/null)" || continue
        t=$(cat "$z/temp" 2>/dev/null)
        case "$t" in ''|*[!0-9]*) continue ;; esac
        t=$((t / 1000))
        if [ -z "$m" ] || [ "$t" -gt "$m" ]; then m=$t; fi
    done
    echo "$m"
}

level=0
i=0
blind=0
while :; do
    cpu=$(read_cpu)
    if [ -z "$cpu" ]; then
        [ "$blind" -eq 0 ] && log "no CPU zone readable, holding level $level"
        blind=1
        sleep "$POLL"
        continue
    fi
    blind=0
    if [ "$cpu" -ge "$HOT" ] && [ "$level" -lt 2 ]; then
        level=2
        log "HOT ${cpu}C -> level 2 (schedutil, floor caps)"
        /system/bin/cpu_caps.sh 2
    elif [ "$cpu" -ge "$WARM" ] && [ "$level" -lt 1 ]; then
        level=1
        log "WARM ${cpu}C -> level 1 (tight caps)"
        /system/bin/cpu_caps.sh 1
    elif [ "$cpu" -lt "$COOL" ] && [ "$level" -gt 0 ]; then
        level=$((level - 1))
        log "cooled to ${cpu}C -> level $level"
        /system/bin/cpu_caps.sh "$level"
    fi
    setprop recovery.thermal.level "$level" 2>/dev/null
    setprop recovery.thermal.cpu "$cpu" 2>/dev/null
    i=$((i + 1))
    [ $((i % REPORT)) -eq 0 ] && log "cpu=${cpu}C level=$level"
    sleep "$POLL"
done
