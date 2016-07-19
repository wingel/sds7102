#! /bin/bash
set -e
set -x

cd "`dirname \"$0\"`"
. ./buildroot-settings.sh

cd ..

if [ ! -f linux/.config ]; then
    cp misc/linux.config linux/.config
    make -C linux CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm oldconfig
fi

make -C linux -j 4 CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm modules

make -C drivers CROSS_COMPILE="$CROSS_COMPILE"

make -C apps CROSS_COMPILE="$CROSS_COMPILE"

cp apps/{activity,sds-server} buildroot/output/target/root
cp drivers/*.ko buildroot/output/target/root
