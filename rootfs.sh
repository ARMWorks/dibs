#!/bin/bash

##### BEGIN SETTINGS #####

SYSTEM=debian
ARCH=armhf
SUITE=testing
DEVICE=image.bin
HOSTNAME=unknown

###### END SETTINGS ######

TOP=$(dirname $(readlink -e $0))
CACHE=$TOP/cache/$SYSTEM-$ARCH-$SUITE
BUILD=$(readlink -e .)
ROOT=$BUILD/root
ROOT_LOCK=0

if [ $(id -u) -ne 0 ]; then
  echo Rerunning script with sudo...
  sudo $0 $@
  exit
fi

show_usage() {
  echo Usage:
  echo "  $0 setup"
  echo "  $0 shell"
  echo "  $0 qemu"
}

sanity_check() {
  OK=1
  if [ -z $(which qemu-arm-static) ]; then
    echo "qemu-arm-static is missing"
    echo "  Debian package: qemu-user-static"
    OK=0
  fi
  if [ -z $(which qemu-system-arm) ]; then
    echo "qemu-system-arm is missing"
    echo "  Debian package: qemu-system"
    OK=0
  fi
  if [ -z $(which debootstrap) ]; then
    echo "debootstrap is missing"
    echo "  Debian package: debootstrap"
    OK=0
  fi
  if [ $OK -eq 0 ]; then
    echo "Not OK"
    exit
  fi
}

setup_binfmt() {
  if [ ! -f /proc/sys/fs/binfmt_misc/arm ]; then
    if [ ! -f /proc/sys/fs/binfmt_misc/register ]; then
      if [ ! -d /proc/sys/fs/binfmt_misc ]; then
        sudo modprobe binfmt_misc
      fi
      sudo mount binfmt_misc -t binfmt_misc /proc/sys/binfmt_misc
    fi
    sudo sh -C "echo ':arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:' > /proc/sys/fs/binfmt_misc/register"
  fi
}

run_target() {
  setup_root
  chroot $ROOT $@
  teardown_root
}

setup_root() {
  if [ $ROOT_LOCK -eq 0 ]; then
    if [ ! -d $ROOT ]; then
      mkdir -p $ROOT
      if [[ $DEVICE == /dev/* ]]; then
        mount $DEVICE $ROOT
      else
        if [ ! -f $DEVICE ]; then
          sudo -u $SUDO_USER dd if=/dev/zero of=$DEVICE bs=1M seek=512 count=0 > /dev/null 2>&1
          LOOP=$(losetup --show -f $DEVICE)
          mkfs -t ext2 $LOOP > /dev/null 2>&1
        else
          LOOP=$(losetup --show -f $DEVICE)
        fi
        mount $LOOP $ROOT
      fi
      mkdir -p $ROOT/proc
      mount -t proc proc $ROOT/proc
      mkdir -p $ROOT/usr/bin
      cp /usr/bin/qemu-arm-static $ROOT/usr/bin
    fi
  fi
  ROOT_LOCK=$(expr $ROOT_LOCK + 1)
}

teardown_root() {
  if [ $ROOT_LOCK -gt 0 ]; then
    ROOT_LOCK=$(expr $ROOT_LOCK - 1)
    if [ $ROOT_LOCK -eq 0 ]; then
      if [ -d $ROOT ]; then
        rm $ROOT/usr/bin/qemu-arm-static
		umount $ROOT/proc
        umount $ROOT
        if [ -n $LOOP ]; then
          losetup -d $LOOP
        fi
        rmdir $ROOT
      fi
    fi
  fi
}

do_debootstrap() {
  case $SYSTEM in
    debian)
      MIRROR=http://mirrors.kernel.org/debian
      ;;
    *)
      echo Unknown SYSTEM selected
      exit
      ;;
  esac

  setup_root

  sudo -u $SUDO_USER mkdir -p $CACHE
  if [ "$(ls -A $CACHE)" ]; then
    mkdir -p $ROOT/var/cache/apt/archives
    cp -n $CACHE/*.deb $ROOT/var/cache/apt/archives
  fi

  debootstrap --variant=minbase --arch $ARCH --include=aptitude,kmod,udev $SUITE $ROOT $MIRROR
  mount -t proc proc $ROOT/proc

  sudo -u $SUDO_USER cp -n $ROOT/var/cache/apt/archives/*.deb $CACHE

  teardown_root
}

do_postconfig() {
  case $SYSTEM in
    debian)
      cat << __END__ > $ROOT/etc/apt/sources.list
deb http://mirrors.kernel.org/debian $SUITE main contrib non-free
deb-src http://mirrors.kernel.org/debian $SUITE main contrib non-free
deb http://security.debian.org/ $SUITE main contrib non-free
deb-src http://security.debian.org/ $SUITE main contrib non-free
__END__
      ;;
    *)
      ;;
  esac

  # set empty root password
  sed -i 's/\(root:\)[^:]*\(:\)/\1\2/' $ROOT/etc/shadow

  # set hostname and hosts file
  echo $HOSTNAME > $ROOT/etc/hostname
  cat > $ROOT/etc/hosts << __END__
127.0.0.1       localhost
127.0.1.1       $HOSTNAME

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
__END__
}

sanity_check

case $1 in
  setup)
    setup_root
    do_debootstrap
    do_postconfig
    teardown_root
    ;;
  shell)
	if [ ! -e $DEVICE ]; then
      echo Device or image does not exist
      exit
    fi
    setup_root
    setup_binfmt
    debian_chroot=$ARCH run_target /bin/bash
    teardown_root
    ;;
  qemu)
    sudo -u $SUDO_USER qemu-system-arm -machine vexpress-a9 -cpu cortex-a8 \
      -sd $DEVICE -kernel $TOP/vmlinuz-arm \
      -append "root=/dev/mmcblk0 rw rootwait" 
    ;;
  *)
    show_usage
    ;;
esac

