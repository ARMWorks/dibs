# Debian Image Build System #

## Requirements ##

 * binfmt-support
 * build-essential
 * debootstrap
 * multistrap
 * qemu
 * qemu-user-binfmt
 * qemu-user-static

## Install ##
    sudo apt-get install binfmt-support build-essential debootstrap multistrap qemu qemu-user-binfmt qemu-user-static
    git clone --recursive https://github.com/ARMWorks/dibs.git
    cd dibs

## Usage ##

To enter a dibs shell, you source the activate script:

    . path/to/dibs/activate

This will leave you at a shell like this:

    [DIBS] jkent@quark:~/Desktop$

You can leave the dibs shell at any time by typing: 

    deactivate

