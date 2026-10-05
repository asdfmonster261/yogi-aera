#!/system/bin/sh
#
# gpu_stage.sh - copy the phone's own PowerVR stack into RAM for AERA's GPU renderer.
#
# Run by init at early-boot, before the recovery service. It maps vendor, vendor_dlkm
# and system read-only under dm names of its own, copies the driver, its firmware and
# everything they link into the ramdisk, loads the kernel module, then drops every
# mount and mapping again, so no partition is left busy. The renderer loads the driver
# into the sphal linker namespace, so anything the driver links has to end up under
# /vendor/lib64 unless the recovery shares it (see /system/etc/ld.config.txt).

LOG=/dev/logs/gpu_stage.log
WORK=/dev/aera-gpu
ALLOCATOR=bin/hw/pixel.gralloc.allocator-service

mkdir -p /dev/logs $WORK
exec >> $LOG 2>&1
echo "start at $(cut -d' ' -f1 /proc/uptime)s"

suffix=$(getprop ro.boot.slot_suffix)
egl=$(getprop ro.hardware.egl)
case $suffix in
    _a) slot=0 ;;
    _b) slot=1 ;;
    *) echo "no slot suffix"; exit 1 ;;
esac
[ -n "$egl" ] || { echo "ro.hardware.egl is not set"; exit 1; }
shared=" $(sed -n 's/^namespace\.sphal\.link\.default\.shared_libs = //p' /system/etc/ld.config.txt | tr : ' ') "
[ "$shared" != "  " ] || { echo "ld.config.txt has no sphal namespace"; exit 1; }

maps=""
mounts=""
staged=""

release() {
    for m in $mounts; do umount $m || echo "could not unmount $m"; done
    for d in $maps; do dmctl delete $d > /dev/null || echo "could not delete $d"; done
    rm -rf $WORK
}

fail() {
    echo "failed: $*"
    # A half-staged driver is worse than none: without one the renderer stays on
    # its software path.
    for f in $staged; do rm -f $f; done
    release
    exit 1
}
trap 'fail "timed out"' TERM

# Map partition $1 of the booted slot from super's metadata and mount it read-only
# on $2. AERA maps the same partitions itself later, under their own names.
attach() {
    local name=aera_gpu_$1 table dev i=0
    # At early-boot this has failed with nothing logged, where the same steps later
    # succeed, so keep every error and give it a few seconds.
    while :; do
        table=$(lpdump --slot=$slot /dev/block/by-name/super | awk -v p=$1$suffix '
            $1 == "Name:" { cur = $2; next }
            cur == p && $4 == "linear" { printf "linear %d %d /dev/block/by-name/%s %d ", $1, $3 - $1 + 1, $5, $6 }')
        [ -n "$table" ] && dmctl create $name -ro $table > /dev/null && break
        echo "$1$suffix not mappable at $(cut -d' ' -f1 /proc/uptime)s, table '$table'"
        i=$((i + 1))
        [ $i -lt 20 ] || return 1
        sleep 0.25
    done
    maps="$name $maps"
    dev=$(dmctl getpath $name)
    i=0
    while [ ! -b "$dev" ] && [ $i -lt 50 ]; do
        sleep 0.1
        i=$((i + 1))
    done
    mkdir -p $2
    mount -t erofs -o ro $dev $2 2> /dev/null || mount -t ext4 -o ro $dev $2 || return 1
    mounts="$2 $mounts"
    echo "$1$suffix mapped at $dev"
}

V=$WORK/vendor
D=$WORK/vendor_dlkm
S=$WORK/system
attach vendor $V || fail "cannot map vendor$suffix"
attach vendor_dlkm $D || fail "cannot map vendor_dlkm$suffix"
attach system $S || fail "cannot map system$suffix"
[ -d $S/system/lib64 ] && S=$S/system

# Copy $1 to $2, leaving anything the ramdisk already has alone.
put() {
    [ -e $2 ] && return 0
    mkdir -p ${2%/*}
    cp -p $1 $2 || return 1
    staged="$staged $2"
}

# pvrsrvkm asks for its firmware while it probes.
for fw in $V/firmware/rgx.*; do
    put $fw /vendor/firmware/${fw##*/} || fail "cannot copy ${fw##*/}"
done

load() {
    local mod=$1 dep
    grep -q "^$(echo ${mod%.ko} | tr - _) " /proc/modules && return 0
    for dep in $(sed -n "s|.*/$mod: *||p" $D/lib/modules/modules.dep); do
        load ${dep##*/} || return 1
    done
    insmod $D/lib/modules/$mod
}
load pvrsrvkm.ko || fail "cannot load pvrsrvkm"

queue=""
seen=" "
want() {
    put $1 $2 || fail "cannot copy $1"
    queue="$queue $2"
}
for f in lib64/egl/libEGL_$egl.so lib64/egl/libGLESv2_$egl.so lib64/hw/mapper.pixel.so $ALLOCATOR; do
    [ -f $V/$f ] || fail "vendor has no $f"
    want $V/$f /vendor/$f
done
# libIMGegl opens the GLESv1 library by path instead of linking it.
f=lib64/egl/libGLESv1_CM_$egl.so
[ -f $V/$f ] && want $V/$f /vendor/$f
[ -f $V/etc/powervr.ini ] && put $V/etc/powervr.ini /vendor/etc/powervr.ini

while [ -n "$queue" ]; do
    set -- $queue
    f=$1
    shift
    queue="$*"
    for lib in $(readelf -d $f | sed -n 's/.*(NEEDED).*\[\(.*\)\]/\1/p'); do
        case "$seen$shared" in *" $lib "*) continue ;; esac
        seen="$seen$lib "
        src=""
        for dir in lib64 lib64/egl lib64/hw; do
            [ -f $V/$dir/$lib ] && { src=$V/$dir/$lib; dst=/vendor/$dir/$lib; break; }
        done
        # The rest comes from system: libnativewindow, libui and the graphics HIDL
        # libraries, which the recovery does not have in any version.
        if [ -z "$src" ] && [ -f $S/lib64/$lib ]; then
            src=$S/lib64/$lib
            dst=/vendor/lib64/$lib
        fi
        [ -n "$src" ] || fail "$lib, needed by ${f##*/}, is on neither vendor nor system"
        want $src $dst
    done
done

# libIMGegl opens its GLES libraries under /system/vendor, which only Android has.
[ -e /system/vendor ] || ln -s /vendor /system/vendor

release
start aera_gpu_allocator
echo "staged $(echo $staged | wc -w) files, done at $(cut -d' ' -f1 /proc/uptime)s"
