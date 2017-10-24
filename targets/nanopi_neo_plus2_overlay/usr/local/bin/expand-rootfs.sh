#!/bin/bash

try() {
    output=$("$@" 2>&1)
    if [ $? -ne 0 ]; then
        echo "error running \"$@\""
        echo "$output"
        exit 1
    fi
}

show_usage() {
    echo "Usage: $0 [-s SWAPSIZE]" >&2
    echo "Where SWAPSIZE is a number in megabytes" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -s|--swap)
            SWAP_SIZE_MB="$2"
            shift
        ;;
        *)
            show_usage
        ;;
    esac
    shift
done

BLOCK_DEVICE=/dev/mmcblk0

if [[ ! -b ${BLOCK_DEVICE}p1 ]]; then
    echo "1st partition missing. Refusing to continue." >&2
    exit 1
fi

if [[ ! -b ${BLOCK_DEVICE}p2 ]]; then
    echo "2nd partition missing. Refusing to continue." >&2
    exit 1
fi

if [[ -b ${BLOCK_DEVICE}p3 ]]; then
    echo "3rd partition exists. Refusing to continue." >&2
    exit 1
fi

if [[ -b ${BLOCK_DEVICE}p4 ]]; then
    echo "4th partition exists. Refusing to continue." >&2
    exit 1
fi

DEVICE_NAME=$(basename ${BLOCK_DEVICE})
DEVICE_SIZE=$(cat /sys/block/${DEVICE_NAME}/size)
P1_POSITION=$(cat /sys/block/${DEVICE_NAME}/${DEVICE_NAME}p1/start)
P1_SIZE=$(cat /sys/block/${DEVICE_NAME}/${DEVICE_NAME}p1/size)
P2_POSITION=$(cat /sys/block/${DEVICE_NAME}/${DEVICE_NAME}p2/start)
P2_SIZE=$(cat /sys/block/${DEVICE_NAME}/${DEVICE_NAME}p2/size)

if [[ $P1_POSITION -gt $P2_POSITION ]]; then
    echo "1st partition comes after 2nd partition. Refusing to continue." >&2
    exit 1
fi

let FREE_SIZE=$DEVICE_SIZE-$P2_POSITION-$P2_SIZE

if [[ "$SWAP_SIZE_MB" -gt 0 ]]; then
    MAKE_SWAP=1
    let P3_SIZE=$SWAP_SIZE_MB*2048
    let P3_POSITION=$DEVICE_SIZE-$P3_SIZE
    if [[ $P3_SIZE -gt $FREE_SIZE ]]; then
        echo "Swap size larger than available space. Refusing to continue." >&2
        exit 1
    fi
    let FREE_SIZE=$FREE_SIZE-$P3_SIZE
else
    MAKE_SWAP=0
fi

let P2_SIZE=$P2_SIZE+$FREE_SIZE

if [[ $MAKE_SWAP -eq 1 ]]; then
	sfdisk -u S --Linux --no-reread ${BLOCK_DEVICE} >/dev/null 2>&1 << EOF
${P1_POSITION},${P1_SIZE},0x0C,-
${P2_POSITION},${P2_SIZE},0x83,-
${P3_POSITION},${P3_SIZE},0x82,-
EOF

    try partprobe ${BLOCK_DEVICE}

    try mkswap ${BLOCK_DEVICE}p3

    echo "/dev/mmcblk0p3 none swap sw 0 0" >> /etc/fstab

    try swapon /dev/mmcblk0p3
else
	sfdisk -u S --Linux --no-reread ${BLOCK_DEVICE} >/dev/null 2>&1 << EOF
${P1_POSITION},${P1_SIZE},0x0C,-
${P2_POSITION},${P2_SIZE},0x83,-
EOF
fi

try resizepart ${BLOCK_DEVICE} 2 ${P2_SIZE}

try resize2fs -f ${BLOCK_DEVICE}p2
