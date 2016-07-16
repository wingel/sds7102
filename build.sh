#! /bin/bash
set -e
set -x

LINUX_REPO="https://github.com/wingel/linux.git"
LINUX_BRANCH="sds7102-v4"

BUILDROOT_REPO="https://github.com/wingel/buildroot.git"
BUILDROOT_BRANCH="2015.05"

MYHDL_REPO="https://github.com/wingel/myhdl.git"
MYHDL_BRANCH="sds7102"

RHEA_REPO="https://github.com/wingel/rhea.git"
RHEA_BRANCH="sds7102"

if [ -f misc/local-settings.sh ]; then
    . misc/local-settings.sh
fi

if [ ! -d buildroot ]; then
    git clone -b "$BUILDROOT_BRANCH" "$BUILDROOT_REPO" buildroot
fi

if [ ! -d linux ]; then
    git clone -b "$LINUX_BRANCH" "$LINUX_REPO" linux
fi

if [ ! -d myhdl ]; then
    git clone -b "$MYHDL_BRANCH" "$MYHDL_REPO" myhdl
fi

if [ ! -d rhea ]; then
    git clone -b "$RHEA_BRANCH" "$RHEA_REPO" rhea
fi

if [ -z "$XILINX" ]; then
    echo 1>&2 "XILINX environment variable is not set, using prebuilt FPGA image"
    fpga_image=misc/sds7102.bin
else
    fpga_image=fpga/myhdl/wishbone/xilinx/sds7102.bin

    if [ ! -f "$fpga_image" ]; then
        (cd fpga/myhdl/wishbone && ./image.py || exit 1)
    fi
    [ -f "$fpga_image" ]
fi

target_fpga_image=buildroot/output/target/root/sds7102.bin

if [ "$fpga_image" -nt "$target_fpga_image" ]; then
    mkdir -p "`dirname \"$target_fpga_image\"`"
    cp "$fpga_image" "$target_fpga_image"
fi

if [ ! -f buildroot/.config ]; then
    cp misc/buildroot.config buildroot/.config
    make -C buildroot oldconfig
fi

make -C buildroot
