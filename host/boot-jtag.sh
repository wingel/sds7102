#! /bin/sh
cd "`dirname \"$0\"`"

# Kill openocd, it might be hung
killall -9 openocd 2>/dev/null
sleep 0.3
/opt/openocd/bin/openocd -f openocd.cfg &

# Wait for openocd to initialize and tell it to reset the SoC
sleep 0.3
echo reset | nc localhost 4444

# openocd usually loses connection to the SoC when it is reset so kill it again
killall -9 openocd

# Wait for some time, long enough for the bootloader on the SoC to
# initialize the DDR controller but not so long that it turns on the
# MMU which would confuse openocd.
#
# Start openocd again, tell it to initialize and halt the Soc
sleep 0.4
/opt/openocd/bin/openocd -f openocd.cfg -c init -c halt &

# openocd should now be running with the SoC halted
sleep 0.3
nc localhost 4444 <<EOF
# Disable interrupts just to be on the safe sidea
mww 0X4A000008 0xffffffff
mww 0X4A000048 0xffffffff
mww 0X4A00001C 0xffffffff

load_image ../linux/arch/arm/boot/zImage 0x31000000 bin
resume 0x31000000
EOF
