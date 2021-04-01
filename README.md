# DIBS - Debian Image Build System

DIBS is intended to build reproducable Debian images for embedded systems. It allows for configuration and customization of the resulting system. While building an image, it uses btrfs to take snapshots, allowing you to roll back changes while developing and testing your image.

## Requirements

  * btrfs-progs
  * debootstrap
  * python3
  * qemu-user-static

## Install

    sudo apt-get install btrfs-progs debootstrap python3 qemu-user-static
    git clone https://github.com/ARMWorks/dibs.git
    git checkout v3
    cd dibs

## Usage

TODO