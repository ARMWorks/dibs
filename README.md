#Debian Image Build System#

##Requirements##

 * debootstrap
 * qemu-user-static

##Install##
    sudo apt-get install debootstrap qemu-user-static
    git clone https://github.com/ARMWorks/dibs.git
    cd dibs

##Usage##

DIBS has several features along with building a debian root file system image.

     ./dibs.sh <NAME> <COMMAND>

NAME refers to the board, in this case nanopi, command is the command to be executed.

##Commands##

* **defconfig**
    * Set config file to use.
* **build**
    * Build Debian image.
* **reconfigure**
    * Applies changes made to config file, except adding packages.
* **shell**
    * Open shell in Debian image
* **tarball**
    * Create tar.gz of image.
* **tarxz**
    * Create tar.xz of image.
* **qemu**
    * Run in qemu-system virtual machine.

##Examples##
    # Set configuration
    ./dibs.sh nanopi defconfig

    # Build image
    ./dibs.sh nanopi build

    # Explore or modify root file system image
    ./dib.sh nanopi shell

    # Create tarball archive
    ./dibs.sh nanopi tarball
