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

     ./dibs.sh <NAME> <COMMAND> [ARG ...]

NAME is the path to the image, excluding the file extension.
COMMAND is the command to be executed.

##Commands##

* **defconfig [TARGET]**
    * Copies a default configuration file. TARGET specifies the configuration to use, if omitted the basename of NAME will be used.
* **build**
    * Build Debian image.
* **reconfigure**
    * Re-runs do_configure and post_install tasks.
* **shell**
    * Start a shell within the Debian image.
* **tarball**
    * Create tar.gz of image.
* **tarxz**
    * Create tar.xz of image.
* **qemu**
    * Run in qemu-system virtual machine.

##Examples##
    # Copy default configuration
    ./dibs.sh my-image defconfig nanopi

    # Build image
    ./dibs.sh my-image build

    # Explore or modify root file system image
    ./dib.sh my-image shell

    # Create tarball archive
    ./dibs.sh my-image tarball
