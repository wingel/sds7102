#! /bin/sh

# Warning, this script will remove _everything_ that isn't checked in.

git clean -fdx
for i in linux buildroot myhdl rhea; do
    (cd $i && git clean -fdx)
done
