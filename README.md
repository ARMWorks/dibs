# DIBS - Debian Image Build System

DIBS is intended to build reproducable Debian images for embedded systems. It
allows for configuration and customization of the resulting system. While
building an image, it uses btrfs to take snapshots, allowing you to roll back
changes while developing and testing your image.

## Requirements

  * btrfs-progs
  * debootstrap
  * python3
  * qemu-user-static
  * ruamel.yaml

## Install

    sudo apt-get install btrfs-progs debootstrap python3 qemu-user-static
    git clone https://github.com/ARMWorks/dibs.git
    cd dibs
    git checkout v3
    pip install -r requirements.txt

## Usage

Commands:

```path/to/dibs.py config [-f] CONFIG```

```path/to/dibs.py build```

```path/to/dibs.py mount [-f]```

```path/to/dibs.py unmount [-f]```

```path/to/dibs.py shell```