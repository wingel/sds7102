#! /bin/sh
LINUX_REPO="https://github.com/wingel/linux.git"
LINUX_BRANCH="sds7102-v4"

BUILDROOT_REPO="https://github.com/wingel/buildroot.git"
BUILDROOT_BRANCH="2015.05"

MYHDL_REPO="https://github.com/wingel/myhdl.git"
MYHDL_BRANCH="sds7102"

RHEA_REPO="https://github.com/wingel/rhea.git"
RHEA_BRANCH="sds7102"

if [ -f local-settings.sh ]; then
    . local-settings.sh
fi
