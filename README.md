Christer Weinigel's SDS7102 repository
======================================

This is a port of Linux and buildroot to the OWON SDS7102
oscilloscope.  The CPU part of the scope is a Samsung S3C2416 system
on a chip (SoC) with a bit of memory and a connection to a Xilinx
Spartan 6 FPGA which performs most of the signal processing.

Status so far:

Linux boots on the scope together with a buildroot based ramdisk and
supports most of the hardware connected to the SoC:

 * LCD display is functional

 * USB host (full speed) is functional

 * USB slave (full speed and high speed) is functional

 * Ethernet (10/100 MBit) is functional.  I haven't been able to get
   the hsspi driver to work so it uses the bitbanging spi-gpio driver
   for the moment.  This will use a lot of CPU and limit the ethernet
   performance.

 * The VGA output does not work.  The Chrontel VGA controller has to
   be configured first.

 * It's possible to configure the FPGA from the SoC using the Xilinx
   Slave Serial protocol.  The SoC DDR2 memory bus is supposed to
   provide a high speed bus to the FPGA from the Soc but is not
   working yet.  Three of the GPIO pins used for configuration can be
   used to communicate with the FPGA when the bitstream has been
   loaded.  This is slow but works.

Building
========

You'll need a Linux computer.  I'm using Linux Mint 17.3, but any
modern distribution should do.

You will need about 6 GBytes of free disk space.  About 3 GBytes for
buildroot.  About 2.5 GBytes for the Linux kernel.  Another 0.5 GBytes
for all the rest, downloads in the dl directory, myhdl, rhea and a few
more things.

After cloning this repoistory, use the following command to download
all dependencies (such as the Linux kernel) and then build everything:

    ./build.sh

On my machine, an Intel i7-2600 with 32Gbytes of RAM and a Samsung 850
EVO SSD, a clean build from scratch takes about 10 minutes.

If you are working on the Linux drivers or the applications you can
rebuild only those parts by running make in the directories.

    cd apps
    make

    cd drivers
    make

Dependencies
============

buildroot provides an ARM toolchain and a ramdisk with useful tools.
buildroot is branched from the tag "2015.05" at
https://git.buildroot.net/buildroot .

The Linux kernel provides most of the hardware support.  It is
branched from the tag "v3.12.61" of the Linux stable repo at
https://git.kernel.org/cgit/linux/kernel/git/stable/linux-stable.git .
I can't remember why I started from this specific version of the Linux
kernel, but I probably found some Linux tree which were supposed to
support the s3c2416 and used that as a base for my changes.

MyHDL is a Python based hardware description language (HDL) which is
used some FPGA images that are used for testing.  It is branched from
the master at that time from https://github.com/jandecaluwe/myhdl .

Rhea is a collection of MyHDL cores and tools.  It is mostly used for
some build scripts that produce Spartan 6 bitstream images from my
MyHDL test programs.  It is branched from the master at that time from
https://github.com/cfelton/rhea .
