#!/bin/bash

# Copyright (C) Guangzhou FriendlyARM Computer Tech. Co., Ltd.
# (http://www.friendlyarm.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, you can access it online at
# http://www.gnu.org/licenses/gpl-2.0.html.

# Automatically re-run script under sudo if not root
if [ $(id -u) -ne 0 ]; then
	echo "Re-running script under sudo..."
	sudo "$0" "$@"
	exit
fi

# ----------------------------------------------------------
# base setup

true ${TOP:=$(pwd)}

true ${RAW_FILE:=$1}
true ${DIR_BASE:=$2}
true ${RAW_SIZE_MB:=$3}
true ${RAW_SIZE_MB:=40}   # 40MB

if [ -z "${RAW_FILE}" -o -z "${DIR_BASE}" ]; then
	echo "Usage: $0 <output image> <boot path>"
	exit 1
fi

# ----------------------------------------------------------
# Create zero file

BLOCK_SIZE=1024
let RAW_SIZE=(${RAW_SIZE_MB}*${BLOCK_SIZE})

echo "Creating RAW image: ${RAW_FILE} (${RAW_SIZE_MB} MB)"
echo "---------------------------------"

if [ -f ${RAW_FILE} ]; then
	rm -f ${RAW_FILE}
fi

dd if=/dev/zero of=${RAW_FILE} bs=${BLOCK_SIZE} count=0 \
	seek=${RAW_SIZE} || exit 1

if [ $? -ne 0 ]; then
	echo "Error: ${RAW_FILE}: Create RAW file failed"
	exit 1
fi

# ----------------------------------------------------------
# Setup loop device

LOOP_DEVICE=$(losetup -f)

echo "Using device: ${LOOP_DEVICE}"

if losetup ${LOOP_DEVICE} ${RAW_FILE}; then
	sleep 1
else
	echo "Error: attach ${LOOP_DEVICE} failed, stop now."
	rm ${RAW_FILE}
	exit 1
fi

#----------------------------------------------------------
# local functions

FA_RunCmd() {
	[ "$V" = "1" ] && echo "+ ${@}"
	eval $@ || {
		losetup -d ${LOOP_DEVICE}
		exit -1
	}
}

# ----------------------------------------------------------
# Fusing all

FA_RunCmd mkfs.vfat ${LOOP_DEVICE} -n boot

MNT=/tmp/media_vfat
mkdir -p ${MNT}
FA_RunCmd mount -t vfat ${LOOP_DEVICE} ${MNT}

[ -d ${DIR_BASE} ] && cp ${DIR_BASE}/* ${MNT}/ -avf
RET=$?
sync
sleep 2

FA_RunCmd umount ${MNT}
umount /media/root/BOOT > /dev/null 2>&1

# cleanup
losetup -d ${LOOP_DEVICE} > /dev/null 2>&1

if [ ${RET} -ne 0 ]; then
	echo "Error: ${RAW_FILE}: Build boot image failed, cleanup"
	rm -f ${RAW_FILE}
	exit 1
fi

echo "---------------------------------"
echo "RAW image successfully created (`date +%T`)."
ls -l ${RAW_FILE}
echo "Tip: You can compress it to save disk space."

