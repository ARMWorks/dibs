#!/bin/bash

##### BEGIN SETTINGS #####

SYSTEM=debian
ARCH=armhf
SUITE=testing
DEVICE=image.bin

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

  debootstrap --variant=minbase --arch $ARCH --include=aptitude $SUITE $ROOT $MIRROR
  mount -t proc proc $ROOT/proc

  sudo -u $SUDO_USER cp -n $ROOT/var/cache/apt/archives/*.deb $CACHE

  teardown_root
}


#cat << __END__ > $ROOTDIR/etc/apt/sources.list
#deb http://security.debian.org/ $SUITE/updates main contrib non-free
#deb-src http://security.debian.org/ $SUITE/updates main contrib non-free
#deb http://mirrors.kernel.org/debian/ $SUITE main contrib non-free
#deb-src http://mirrors.kernel.org/debian/ $SUITE main contrib non-free
#__END__
#sudo chroot $ROOTDIR apt-get update

#if [ ! -f "$BUILD/vmlinuz" ]; then
#  mkdir -p $BUILD/tmp
#  wget $MIRROR/pool/main/l/linux/linux-image-3.2.0-4-vexpress_3.2.32-1_armhf.deb -O $BUILD/tmp/kernel.deb
#  dpkg-deb -x $BUILD/tmp/*.deb $BUILD/tmp
#  sudo -u $SUDO_USER cp $BUILD/tmp/boot/vmlinuz* $BUILD/vmlinuz
#  rm -r $BUILD/tmp
#fi

case $1 in
  setup)
    do_debootstrap

    #init_binfmt
    #cp post-install.sh $ROOTDIR
    #run_target /bin/sh /post-install.sh
    #rm $ROOTDIR/post-install.sh
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
    echo Not yet implemented
    exit
    ;;
  *)
    show_usage
    ;;
esac
