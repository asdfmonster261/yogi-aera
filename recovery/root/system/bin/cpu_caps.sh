#!/system/bin/sh
# cpu_caps.sh <level> -- cap every cpufreq policy for the recovery session.
# 0 is the steady state, 1 and 2 are thermal_watch.sh's retreat levels. The
# governor is left alone except at level 2, which drops to schedutil and stays
# there when the caps relax again.

LOG=/dev/logs/cpu_caps.log

share() { # $1 level, $2 cluster class (0 little, 1 mid, 2 prime)
    case "$1$2" in
        00) echo 45 ;; 01) echo 55 ;; 02) echo 55 ;;
        10) echo 30 ;; 11) echo 35 ;; 12) echo 35 ;;
        20) echo 22 ;; 21) echo 25 ;; 22) echo 25 ;;
    esac
}

LEVEL="${1:-0}"
case "$LEVEL" in
    0|1|2) ;;
    *) echo "usage: cpu_caps.sh <0|1|2>" >&2; exit 1 ;;
esac

mkdir -p /dev/logs

for p in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$p" ] || continue
    max=$(cat "$p/cpuinfo_max_freq" 2>/dev/null)
    [ -n "$max" ] || continue

    # Cluster class from the ceiling: little <= 2.8 GHz, mid <= 3.5 GHz.
    if [ "$max" -le 2800000 ]; then cls=0
    elif [ "$max" -le 3500000 ]; then cls=1
    else cls=2
    fi

    target=$((max * $(share "$LEVEL" "$cls") / 100))
    min=$(cat "$p/cpuinfo_min_freq" 2>/dev/null)
    if [ -n "$min" ] && [ "$target" -lt "$min" ]; then target=$min; fi

    cap=""
    for f in $(cat "$p/scaling_available_frequencies" 2>/dev/null); do
        if [ "$f" -le "$target" ] && { [ -z "$cap" ] || [ "$f" -gt "$cap" ]; }; then
            cap=$f
        fi
    done
    [ -n "$cap" ] || cap=$target

    if [ "$LEVEL" -eq 2 ]; then
        echo schedutil > "$p/scaling_governor" 2>/dev/null
    fi
    if echo "$cap" > "$p/scaling_max_freq" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S' 2>/dev/null)] level $LEVEL: ${p##*/} max=$max cap=$cap gov=$(cat "$p/scaling_governor" 2>/dev/null)" >> "$LOG"
    else
        echo "[$(date '+%H:%M:%S' 2>/dev/null)] level $LEVEL: ${p##*/} FAILED cap=$cap" >> "$LOG"
    fi
done

exit 0
