#!/bin/sh

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
DEVICE=/dev/ttySAC1
BAUD=115200
MAC=aa:22:33:44:55:66

echo > $DEVICE
brcm_patchram_plus --patchram /lib/firmware/ap6210/bcm20702a.hcd --bd_addr $MAC --no2bytes --tosleep 5000 --baudrate $BAUD $DEVICE
sleep 1
exec hciattach -n $DEVICE any $BAUD
