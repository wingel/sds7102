#! /bin/sh
set -e
set -x

cd "`dirname \"$0\"`"
. ./buildroot-settings.sh

cd ..

make -C linux -j 4 CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm
