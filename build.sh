#! /bin/bash
set -e
set -x

cd "`dirname \"$0\"`"
cd misc
. settings.sh
cd ..

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
    fpga_image=fpga/myhdl/xilinx/sds7102.bin

    if [ ! -f "$fpga_image" ]; then
        (cd fpga/myhdl && ./image.py || exit 1)
    fi
    [ -f "$fpga_image" ]
fi

target_fpga_image=buildroot/output/target/root/sds7102.bin

if [ "$fpga_image" -nt "$target_fpga_image" ]; then
    mkdir -p "`dirname \"$target_fpga_image\"`"
    cp "$fpga_image" "$target_fpga_image"
fi

if [ misc/buildroot.config -nt buildroot/.config ]; then
    if [ -f buildroot/.config ]; then
	mv buildroot/.config buildroot/.config.old
    fi
    cp misc/buildroot.config buildroot/.config
fi

make -C buildroot oldconfig
make -C buildroot
