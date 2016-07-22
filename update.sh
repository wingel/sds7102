#! /bin/bash
set -e
set -x

cd "`dirname \"$0\"`"
cd misc
. settings.sh
cd ..

cd buildroot
git fetch
git checkout "$BUILDROOT_BRANCH"
# this is a tag without any changes so far, so don't try to merge
# git merge "origin/$BUILDROOT_BRANCH"
cd ..

cd linux
git fetch
git checkout "$LINUX_BRANCH"
git merge --ff-only "origin/$LINUX_BRANCH"
cd ..

cd myhdl
git fetch
# git checkout "$MYHDL_BRANCH"
git merge --ff-only "origin/$MYHDL_BRANCH"
cd ..

cd rhea
git fetch
# git checkout "$RHEA_BRANCH"
git merge --ff-only "origin/$RHEA_BRANCH"
cd ..
