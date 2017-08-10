#!/bin/bash

function reset_bt()
{
    BTWAKE=/proc/bluetooth/sleep/btwake
    if [ -f ${BTWAKE} ]; then
        echo 0 > ${BTWAKE}
    fi
    index=`rfkill list | grep $1 | cut -f 1 -d":"` 
    if [[ -n ${index}} ]]; then
        rfkill block ${index}
        sleep 1
        rfkill unblock ${index}
        sleep 1
    fi
}

rm -rf bt.log dl.log
while true; do
    killall -9 brcm_patchram_plus
    reset_bt "sunxi-bt"
    (/bin/brcm_patchram_plus -d --patchram /lib/firmware/ap6212/ --enable_hci --bd_addr c1:75:f1:b8:fa:99 --no2bytes --tosleep 5000 /dev/ttyS3 >bt.log 2>&1 &)
    echo "downloading..."
    sleep 15
    TIME=`date "+%H-%M-%S"`
    if grep "Done setting line discpline" bt.log>/dev/null; then
        echo "${TIME}: bt firmware download OK" | tee -a dl.log
    else
        echo "${TIME}: bt firmware download FAIL" | tee -a dl.log
    fi
    reset_bt "hci0"
    hciconfig hci0 up
    hciconfig
done

