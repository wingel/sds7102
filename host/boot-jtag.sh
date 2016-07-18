#! /bin/bash
cd "`dirname \"$0\"`"

# Newer versions of openocd are much faster.  It takes 10 seconds to
# load a 5MByte image with openocd-0.10 instead of 30 seconds with
# openocd-0.7 which is the version that comes with Linux Mint.
#
# Use the openocd-0.10 I have compiled and put in /opt by default and
# fall back to the system openocd if that one can't be found.

for OPENOCD in /opt/openocd/bin/openocd openocd; do
    if [ -x "$OPENOCD" ]; then
	break
    fi
done

echo "Using $OPENOCD"

# Kill openocd, it might be hung
killall -9 openocd 2>/dev/null
sleep 0.3
$OPENOCD -f openocd.cfg &

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
$OPENOCD -f openocd.cfg -c init -c halt &

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
