#! /bin/sh
set -x

rmmod fpga
rmmod gpios
rmmod regs
insmod fpga.ko
insmod gpios.ko
insmod regs.ko

echo "Loading FPGA"
cat sds7102.bin >/dev/fpga
