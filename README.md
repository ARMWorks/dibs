# Debian Image Build System #

## Requirements ##

 * build-essential
 * multistrap
 * qemu-user-static

## Install ##
    sudo apt-get install build-essential multistrap qemu-user-static
    git clone --recursive https://github.com/ARMWorks/dibs.git
    cd dibs

## Usage ##

To enter a dibs shell, run the shell script as root:

    $ sudo path/to/dibs/init_dibs

This will leave you at a shell like this:

    [DIBS] root@quark:/home/jkent/Desktop#

You can leave the dibs shell with a Ctrl-C or exit.
Alternatively you can stay in an elevated shell with:

	# deactivate
