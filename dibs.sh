#!/bin/bash

DIBS=$(dirname $(readlink -e "$0"))

BUILT=1
CLEANUP=0
CLEANUP_BINFMT=0

run_as_user() {
    if [[ -n $SUDO_USER ]]; then
        sudo -u $SUDO_USER "$@"
    else
        "$@"
    fi
}

require_conf() {
    if [[ ! -f "${CONFIG}" ]]; then
        echo "You need a configuration file first! [Hint: use defconfig]"
        exit 1
    fi

    source "${CONFIG}"

    CACHE="${DIBS}/.cache/$SYSTEM-$SUITE-$ARCH"
}

require_image() {
    if [ ! -f "${IMAGE}" ]; then
        echo "${IMAGE} does not exist"
        exit 1
    fi
}

require_elevation() {
    if [[ $(id -u) -eq 0 ]]; then
        return;
    fi

    if [[ -z $(which sudo) ]]; then
        echo "Superuser privlidges are required for this operation."
        exit 1
    fi

    for e in "${BASH_ARGV[@]}"; do
        args=( "$e" "${args[@]}" )
    done
    exec sudo "$0" "${args[@]}"
}

require_rootfs() {
    if [[ $CLEANUP -ge 1 ]]; then
        return 0
    fi
    require_elevation
    CLEANUP=1

    if [[ ! -f "${IMAGE}" ]]; then
        run_as_user dd if=/dev/zero "of=${IMAGE}" bs=1M seek=$IMAGE_MB count=0 > /dev/null 2>&1
        mkfs -q -t ext4 "${IMAGE}"
    fi

    LOOP_DEVICE=$(losetup -f)
    losetup -P $LOOP_DEVICE "${IMAGE}"
    mkdir -p "$ROOTFS"
    mount -t ext4 $LOOP_DEVICE "$ROOTFS"
    mkdir -p "${ROOTFS}/proc"
    mount -t proc proc "${ROOTFS}/proc"
}

require_qemu() {
    if [[ $CLEANUP -ge 2 ]]; then
        return 0
    fi
    require_rootfs
    CLEANUP=2

    if [[ -z $(which qemu-arm-static) ]]; then
        echo "qemu-arm-static is missing"
        echo "Please install the qemu-user-static package"
        exit 1
    fi

    local qemu_arm_static=$(which qemu-arm-static)
    if [[ ! -f /proc/sys/fs/binfmt_misc/arm ]]; then
        CLEANUP_BINFMT=1
        if [[ ! -f /proc/sys/fs/binfmt_misc/register ]]; then
            modprobe binfmt_misc
            mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc
            CLEANUP_BINFMT=2
        fi
        echo -n ":arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:${qemu_arm_static}:" > /proc/sys/fs/binfmt_misc/register
    fi

    mkdir -p "$ROOTFS"$(dirname $qemu_arm_static)
    cp "$qemu_arm_static" "${ROOTFS}${qemu_arm_static}"
}

cleanup() {
    if [[ $CLEANUP -ge 2 ]]; then
        local qemu_arm_static=$(which qemu-arm-static)
        rm "${ROOTFS}${qemu_arm_static}"

        if [[ $CLEANUP_BINFMT -ge 1 ]]; then
            echo -n -1 > /proc/sys/fs/binfmt_misc/arm
        fi
        if [[ $CLEANUP_BINFMT -ge 2 ]]; then
            umount /proc/sys/fs/binfmt_misc
            modprobe -r binfmt_misc
        fi
    fi

    if [[ $CLEANUP -ge 1 ]]; then
        sync
        if [[ -d "${ROOTFS}/sys/kernel" ]]; then
            umount "${ROOTFS}/sys"
        fi
        if [[ -d "${ROOTFS}/proc/1" ]]; then
            umount "${ROOTFS}/proc"
        fi
        #umount "$ROOTFS"
        #losetup --detach $LOOP_DEVICE
        #rmdir "$ROOTFS"
    fi

    if [[ $BUILT -ne 1 ]]; then
        rm -f "${IMAGE}"
    fi
}

try() {
    local out=0
    local err=0

    while [[ ${1:0:1} = - ]]; do
        case ${1:1} in
            -out)
                out=1;;
            -err)
                err=1;;
            *)
                echo "unknown option $1 for try"
                exit 1
        esac
        shift
    done

    local output
    if [[ $out -ne 0 ]] && [[ $err -ne 0 ]]; then
        "$@"
    elif [[ $out -ne 0 ]]; then
        output=$("$@" 3>&1 1>&2 2>&3)
    elif [[ $err -ne 0 ]]; then
        output=$("$@")
    else
        output=$("$@" 2>&1)
    fi

    if [[ $? -ne 0 ]]; then
        echo "error running \"$@\""
        if [[ -n $output ]]; then
            echo "$output"
        fi
        exit 1
    fi
}

run_target() {
    require_qemu
    chroot "$ROOTFS" "$@"
}

do_debootstrap() {
    if [ -f "${IMAGE}" ]; then
        echo "${IMAGE} already exists!"
        exit 1
    fi

    BUILT=0

    require_qemu

    if [[ -z $(which debootstrap) ]]; then
        echo "debootstrap is missing"
        echo "Please install the debootstrap package"
        exit 1
    fi

    if [[ -d "$CACHE" ]]; then
        mkdir -p "${ROOTFS}/var/cache/apt/archives"
        cp -n "${CACHE}/"*.deb "${ROOTFS}/var/cache/apt/archives"
    fi

    local packages=$(echo "$EXTRA_PACKAGES" | awk -v ORS=, '{ print $1 }' | sed 's/,$/\n/')
    if [[ "$packages" ]]; then
        try --out debootstrap --variant=minbase --arch=$ARCH --include="$packages" $SUITE "$ROOTFS" $MIRROR
    else
        try --out debootstrap --variant=minbase --arch=$ARCH $SUITE "$ROOTFS" $MIRROR
    fi

    run_as_user mkdir -p "$CACHE"
    run_as_user cp -n "${ROOTFS}/var/cache/apt/archives/"*.deb "$CACHE"
    rm "${ROOTFS}/var/cache/apt/archives/"*.deb

    BUILT=1
}

do_configure() {
    case $SYSTEM in
        debian)
            cat > "${ROOTFS}/etc/apt/sources.list" << EOF
deb http://httpredir.debian.org/debian $SUITE main contrib non-free
#deb-src http://httpredir.debian.org/debain $SUITE main contrib non-free
deb http://httpredir.debian.org/debian/ $SUITE-updates main contrib non-free
#deb-src http://httpredir.debian.org/debian/ stretch-updates main
deb http://security.debian.org/debian-security $SUITE/updates main contrib non-free
#deb-src http://security.debian.org/debian-security $SUITE/updates main
EOF
            ;;
        *)
            ;;
    esac

    rm -rf "${ROOTFS}/var/lib/apt/lists/"*
    rm -rf "${ROOTFS}/var/log/"*

    # set empty root password
    sed -i 's/\(root:\)[^:]*\(:\)/\1\2/' "${ROOTFS}/etc/shadow"

    # set hostname and hosts file
    echo $HOSTNAME > "${ROOTFS}/etc/hostname"
    cat > "${ROOTFS}/etc/hosts" << EOF
127.0.0.1       localhost
127.0.1.1       $HOSTNAME

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

    if [[ -n $LOCALE ]]; then
        local lang=$(echo ${LOCALE} | sed 's/^\([^_]\+\)\(_.\+\)\?$/\1/')
        if [[ -d "${ROOTFS}/usr/share/locale" ]]; then
            (cd "${ROOTFS}/usr/share/locale";
             find . -maxdepth 1 ! -name $lang -a ! -name "$lang*" -a ! -name "." -type d -exec rm -r "{}" \;)
        fi
        if [[ -x "${ROOTFS}/usr/sbin/locale-gen" ]]; then
            sed -i 's/^\([^#].*\)$/# \1/' "${ROOTFS}/etc/locale.gen"
            sed -i 's/^# \('$LOCALE' .\+\)$/\1/' "${ROOTFS}/etc/locale.gen"
            run_target /usr/sbin/locale-gen
        fi
        if [[ -x "${ROOTFS}/usr/sbin/update-locale" ]]; then
            run_target /usr/sbin/update-locale LANG=$LOCALE
        fi
    else
        rm -r "${ROOTFS}/usr/share/locale/"*
    fi

    declare -Ff post_install > /dev/null && post_install
}

show_usage() {
    echo "Usage: $0 NAME COMMAND"
    echo
    echo "COMMAND is one of:"
    echo "  defconfig [target]"
    echo "  build"
    echo "  reconfigure"
    echo "  shell"
    echo "  tarball"
    echo "  tarxz"
    echo "  qemu"
    exit 1
}

trap cleanup EXIT

if [[ -z "$1" ]]; then
    show_usage
fi


NAME="$1"
CONFIG="${NAME}.conf"
IMAGE="${NAME}.img"
ROOTFS="${NAME}_rootfs"

case $2 in
    defconfig)
        mkdir -p $(dirname "${NAME}")
        target=${3:-$(basename "${NAME}")}
        default="${DIBS}/targets/default.conf"
        if [[ -r "${DIBS}/targets/${target}.conf" ]]; then
            default="${DIBS}/targets/${target}.conf"
        fi
        cp "${default}" "${CONFIG}"
        echo "\${DIBS}${default#${DIBS}} copied to ${CONFIG}"
        ;;
    build)
        require_conf
        do_debootstrap
        do_configure
        ;;
    reconfigure)
        require_image
        require_conf
        require_rootfs
        do_configure
        ;;
    shell)
        require_image
        debian_chroot=$(basename "$IMAGE") run_target /bin/bash
        ;;
    tarball)
        require_image
        require_rootfs
        tar -cpzf "${NAME}.tar.gz" --one-file-system -C "$ROOTFS" --exclude "lost+found" .
        if [[ -n $SUDO_USER ]]; then
            chown $SUDO_USER "${NAME}.tar.gz"
        fi
        ;;
    tarxz)
        require_image
        require_rootfs
        tar -cpJf "${NAME}.tar.xz" --one-file-system -C "$ROOTFS" --exclude "lost+found" .
        if [[ -n $SUDO_USER ]]; then
            chown $SUDO_USER "${NAME}.tar.xz"
        fi
        ;;
    qemu)
        require_image
        if [[ -z $(which qemu-system-arm) ]]; then
            echo "qemu-system-arm is missing"
            echo "Please install the qemu-system package"
            exit 1
        fi

        try qemu-system-arm -machine vexpress-a9 -cpu cortex-a9 \
            -kernel "${DIBS}/qemu/vmlinuz-3.10.79.0-1-linaro-lsk-vexpress" \
            -append "root=/dev/mmcblk0 rw rootwait" \
            -drive "file=${IMAGE},if=sd,format=raw,cache=writeback"
        ;;
    *)
        show_usage
        ;;
esac
