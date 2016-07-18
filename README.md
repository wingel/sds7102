Christer Weinigel's SDS7102 repository
======================================

NEWS
====

I've updated from the old 3.12.61 kernel to the latest stable 4.4.14
kernel.  If you have used the old kernel you'll have to run
"update.sh" as described below in the build section.

Introduction
============

This is a port of Linux and buildroot to the OWON SDS7102
oscilloscope.  The CPU part of the scope is a Samsung S3C2416 system
on a chip (SoC) with a bit of memory and a connection to a Xilinx
Spartan 6 FPGA which performs most of the signal processing.

I have written a long series of blog posts about how I have reverse
engineered the scope and ported Linux to it.  The first blog post in
the series is
[here](http://blog.weinigel.se/2016/05/01/sds7102-hacking.html).

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

Dependencies
============

This project depends on a couple of other projects.  The biggest ones
are the following:

 * A Linux distribution and all the tools that comes with it.  I'm
   using Linux Mint 17.3, but any modern distribution should do.
   You'll have to install this on your own and make sure that gcc,
   make, git and some other things are installed.  I don't know
   exactly what is needed but the build will fail and you'll have to
   figure it out if that happens.

 * You will need about 5.5 gigabytes of free disk space.  About 2.5
   gigabytes for buildroot, 2.5 gigabytes for the Linux kernel and
   couple of hundred megabytes for all the rest, downloads in the dl
   directory, myhdl, rhea and a few more things.

 * buildroot provides an ARM toolchain and a ramdisk with useful
   tools.  buildroot is branched from the tag "2015.05" of the
   [Busybox git repository](https://git.buildroot.net/buildroot).
   Buildroot in turn includes hudreds of other projects such as
   busybox and uclibc that are very useful on an embedded system.

 * The Linux kernel provides most of the hardware support.  It is
   branched from the tag "v4.4.14" of the [Linux stable git
   repository](https://git.kernel.org/cgit/linux/kernel/git/stable/linux-stable.git).
   This was the newest longtime kernel in the stable tree at the moment.

 * MyHDL is a Python based hardware description language (HDL) which
   is used some FPGA images that are used for testing.  It is branched
   from the master at that time from the [MyHDL git
   repository](https://github.com/jandecaluwe/myhdl).

 * Rhea is a collection of MyHDL cores and tools.  It is mostly used
   for some build scripts that produce Spartan 6 bitstream images from
   my MyHDL test programs.  It is branched from the master at that
   time from the [Rhea git
   repository](https://github.com/cfelton/rhea).

 * If you want to rebuild the FPGA image you will need the Xilinx ISE
   Design Sofware for Linux.

buildroot, linux, myhdl and rhea are automatically downloaded when you
run the build script.

Xilinx ISE
==========

Xilinx has a free version of the Xilinx ISE called WebPACK which can
be used to synthesize the FPGA image.  Download it from their [web
site](http://www.xilinx.com/products/design-tools/ise-design-suite/ise-webpack.html).
You will need a Xilinx account and a free license key to be able to
use it.  Install ISE according to their instructions.

Source the settings script and make sure that you can run the ISE
desktop.  On my Linux machine ISE 14.7 is installed in /opt/Xilinx and
run the following commands:

    . /opt/Xilinx/14.7/ISE_DS/settings64.sh
    ise

If everything works as it should this should start the ISE Project
Navigator.  If you haven't installed the license key yet, ISE will
complain about that.

Building
========

To get a copy of this project, clone it from github with:

    git clone https://github.com/wingel/sds7102.git
    cd sds7102

If you have cloned this repository before you might have old versions.
To get the latest version, run the following script:

    ./update.sh

I've just updated the Linux kernel to 4.4.14, if you were using the
old 3.12 kernel you will have to remove the .config file in the Linux
directory:

    rm linux/.config

Use the following command to download all dependencies (such as the
Linux kernel) and then build everything:

    ./build.sh

On my machine, an Intel i7-2600 with 32Gbytes of RAM and a Samsung 850
EVO SSD, a clean build from scratch takes about 10 minutes.

If you have sourced the Xilinx ISE settings file, the build script
will automatically detect that the XILINX environment variable is set
and synthesize a FPGA image from source, otherwise it will use the
prebuilt image from "misc/sds7102.bin".

Since synthesizing an FPGA image takes a long time the script will
only do it once even if the FPGA sources have changed.  If you want to
resynthesize the FPGA image, remove
"fpga/myhdl/wishbone/xilinx/sds7102.bin" and run "build.sh" again.

If you are working on the Linux drivers or the applications you can
rebuild only those parts by running make in the respective
directories.

    cd apps
    make

    cd drivers
    make

I'm using ccache to speed up repeated builds.  This is because I like
to do a "git clean -fdx" followed by "./build.sh" to see if everything
builds correctly from scratch.  I have placed the ccache directory
under the .git directory so that it won't be removed when I do the
"git clean".  If you have changed the compiler options in buildroot
(for example the ABI or floating point options) and want to make sure
that the new compiler is used, you can remove the ccache directory:

    rm -rf .git/ccache

Running
=======

For the moment you will need a JTAG adapter that works with openocd to
load Linux on the SDS7102.  I use a [Bus Blaster
MIPS](https://www.seeedstudio.com/item_detail.html?p_id=2258) just
because I had one lying around.

You will need to connect your JTAG adapter to the JTAG pads on the
main board on the SDS7102.  I have written a bit about how to do it
[here](http://blog.weinigel.se/2016/05/06/sds7102-hacking-2.html).

It's also a very good idea to be able to see the output from the
serial console which I've written a bit about
[here](http://blog.weinigel.se/2016/05/01/sds7102-hacking.html)

I use a FTDI FT-232R-3V3 cable which I've connected to the serial
port.  In that case the colors of the wires shown in the picture in my
blog post match the colors of the wires on the FTDI cable.

Since Linux is loaded into RAM this does not affect the OWON firmware
in flash.  You can just power off and on the scope to use the normal
firmware.  There is of course a risk that a bug in the kernel will
mess up the flash, or if you manage to somehow use the MTD devices in
Linux to write to flash memory, but I haven't managed to mess up my
scope so far.

To load Linux, modify the first line of the script host/boot-jtag.sh
to match your JTAG adapter and if you have built everything as shown
above you should be able to just run the script to download Linux into
RAM on the SDS7102 and execute it:

    ./host/boot-jtag.sh

If you are successful you should see something like this on the serial
console and the Linux penguin should show up on the display of the
scope.  If it fails, try again.

    SamSung MCU S3C2440
    Program Ver 1.0(2006613)
     FCLK = 400000000Hz,  USB Crystal Type : 12M
    ****************************
    *          LOADBOOT        *
    *                          *
    *          LILLIPUT        *
    *           (2004)         *
    ****************************
    Boot to load (Y/N)?
    Wait for Enter . . . . . . . . . . . . . . . . . . . . . . .
    ******************************
    LILLIPUT
    Uncompressing Linux... done, booting the kernel.
    Warning: Neither atags nor dtb found
    Booting Linux on physical CPU 0x0
    Linux version 3.12.61+ (wingel@zoo) (gcc version 4.8.4 (Buildroot 2015.05) ) #1 Fri Jul 15 18:50:24 CEST 2016
    CPU: ARM926EJ-S [41069265] revision 5 (ARMv5TEJ), cr=00053177


TODO I really should make the display the default console so that you
can just connect a keyboard to the USB port and use the scope as a
small Linux computer.

If you have an ethernet cable connected the scope will request an IP
address using DHCP and you should be able to log into the scope using
ssh.  My scope ends up on IP 192.168.1.42, so this is how I do it:

    ssh root@192.168.1.42

the default password is "root".

Run the initialization script:

    ./init-sds.sh

This loads a couple of device drivers and loads the FPGA image.

If any GPIO pins on the SoC change a message will be printed to the
console with information about what has changed.

To watch for changes on the FPGA pins, run the "activity" application
which reads the edge counters from the FPGA.

Device Drivers and Applications
===============================

fpga.ko is a driver which can be used to load an FPGA image into the
Xilinx FPGA.  To load an FPGA image, first insmod the kernel module
and copy the FPGA .bin or .bit file to /dev/fpga:

    insmod fpga.ko
    cat sds7102.bin >/dev/fpga

This is done if you run the init-sds.sh script.

gpios.ko is the device driver I used to [find GPIO pins on the
SoC](http://blog.weinigel.se/2016/05/28/sds7102-gio-pins.html).  Just
insmod the kernel module and it will print a message to the console
when one of the GPIO pins that are listed in the source has changed
state.

    insmod gpios.ko

This is also done if you run the init-sds.sh script.

regs.ko is a device driver for accessing registes in my FPGA image
using a SPI-like bus which uses three of the pins that are normally
used for configuring the FPGA.

    insmod regs.ko

This is also done if you run the init-sds.sh script.

activity is an application that reads out the edge counter for the
pins of the FPGA and prints it every second:

    ./activity

sds-server is an application which is used by the host tools to access
resources on the scope.  It can currently modify GPIO pins (using the
/sys/class/gpio interface in the Linux kernel) and access registers on
the FPGA.  To see how it works, look at the source or host/sds.py.

The firmware can now capture samples from the ADC and control the
analog frontend.  This means that you can make a capture without ever
having to boot the OWON firmware.  To do that, run the capture
application on a Linux PC:

    ./host/capture.py root@scope-ip-address

The capture application will log onto the scope using ssh and run the
"sds-server" application which gives acess to the registers and the
GPIOs on the scope.  Unless you have set up public key login as
described below you will have to enter the password for the scope,
"root".  If everything goes well you should get a screen showing a
waveform.  You can play around with the settings in capture.py to see
how they affect the capture.  You'll need the data sheets for the
components in the AFE to know how to change some of the values.

It's possible to trace the SoC bus signals using host/trace_soc.py.
Run it like this:

    ./host/trace_soc.py root@scope-ip-address

It will write a called "soc.vcd" will be visualised with gtkwave:

    gtkwave soc.vcd

There is some code called "soc_frob" in drivers/regs.c which tries to
generate test patterns on the SoC bus.

Synthesizing MyHDL code with ISE
================================

Sometimes it can be useful to use ISE to synthesize an image from
sds7102.v and sds7102.ucf created by image.py.  There is an ISE
project in fpga/ise/wishbone with symlinks to the MyHDL generated
files.  After running "image.py" to generate those files, open
the ise/wishbone project in ISE and synthesize the normal way.
This way you can look at the floorplan and other things that are
hard to do outside of ISE.

SSH tips
========

The scope will generate a new ssh host key every time it boots which
can be a bit frustrating since ssh will warn about it changing.  To
work around that I have the following lines in my $HOME/.ssh/config
which tells ssh not to check the host keys, to log in as the root user
and also adds a symbolic name for the IP address:

    Host			sds
	HostName		192.168.1.42
	User		root
	UserKnownHostsFile  /dev/null
	StrictHostKeyChecking no

After this I can just log onto the scope like this:

    ssh sds

Another thing you can do is to set up public key authentication on the
scope so that you don't have to type a password every time you log in.

If you haven't done so before, use "ssh-keygen" to create a new ssh
key.  Then add the key to the list of users that are authorized to log
in using public key authentication in the template for the ramdisk:

    cat $HOME/.ssh/id_rsa.pub >>overlay/root/.ssh/authorized_keys

and then rebuild the image with:

    ./build.sh

Boot the new image and you should automatically be logged in when you
ssh to the scope.
