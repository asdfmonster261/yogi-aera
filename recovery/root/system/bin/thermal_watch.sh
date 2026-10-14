#!/system/bin/sh
# thermal_watch.sh -- retreat through cpu_caps.sh's levels on heat.
# Hottest milli-C zone: level 1 at 55 C, level 2 at 65 C, back below 48 C one
# level at a time. Readings land in /dev/logs/thermal.log.

LOG=/dev/logs/thermal.log
POLL=5      # seconds between readings
REPORT=6    # log a line every N polls

WARM=55
HOT=65
COOL=48

mkdir -p /dev/logs
: >> "$LOG"
log() { echo "[$(date '+%H:%M:%S' 2>/dev/null)] $*" >> "$LOG"; }

log "thermal_watch start: warm=${WARM}C hot=${HOT}C cool=${COOL}C poll=${POLL}s"

# Battery and cp zones are milli-C; others, like inner_brightness, report raw
# sensor values. Only readings above 5000 count.
to_c() { # $1 raw reading; echoes degrees C, or nothing when the scale is unusable
    case "$1" in ''|*[!0-9]*) return ;; esac
    [ "$1" -gt 5000 ] || return
    echo $(($1 / 1000))
}

for z in /sys/class/thermal/thermal_zone*; do
    [ -r "$z/temp" ] || continue
    raw=$(cat "$z/temp" 2>/dev/null)
    c=$(to_c "$raw")
    if [ -n "$c" ]; then note="${c}C"; else note="ignored, not milli-C"; fi
    log "zone ${z##*/} type=$(cat "$z/type" 2>/dev/null) temp=$raw $note"
done

read_max() { # echoes the hottest milli-C reading in degrees C
    m=0
    for z in /sys/class/thermal/thermal_zone*; do
        t=$(to_c "$(cat "$z/temp" 2>/dev/null)")
        [ -n "$t" ] && [ "$t" -gt "$m" ] && m=$t
    done
    echo "$m"
}

level=0
i=0
while :; do
    max=$(read_max)
    if [ "$max" -ge "$HOT" ] && [ "$level" -lt 2 ]; then
        level=2
        log "HOT ${max}C -> level 2 (schedutil, floor caps)"
        /system/bin/cpu_caps.sh 2
    elif [ "$max" -ge "$WARM" ] && [ "$level" -lt 1 ]; then
        level=1
        log "WARM ${max}C -> level 1 (tight caps)"
        /system/bin/cpu_caps.sh 1
    elif [ "$max" -lt "$COOL" ] && [ "$level" -gt 0 ]; then
        level=$((level - 1))
        log "cooled to ${max}C -> level $level"
        /system/bin/cpu_caps.sh "$level"
    fi
    setprop recovery.thermal.level "$level" 2>/dev/null
    setprop recovery.thermal.max "$max" 2>/dev/null
    i=$((i + 1))
    [ $((i % REPORT)) -eq 0 ] && log "max=${max}C level=$level"
    sleep "$POLL"
done
