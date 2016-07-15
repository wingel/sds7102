#! /bin/sh
set -e
set -x

cd "`dirname \"$0\"`"
. ./buildroot-settings.sh

cd ..

if [ ! -f linux/.config ]; then
    cp misc/linux.config linux/.config
    make -C linux CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm oldconfig
fi

make -C linux -j 4 CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm modules_prepare

make -C drivers

make -C apps

cp apps/activity buildroot/output/target/root
cp drivers/*.ko buildroot/output/target/root
