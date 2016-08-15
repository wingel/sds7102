#! /usr/bin/python

import time
import random

from sds import SDS, decode_mig_status

def main():
    sds = SDS('sds')

    # sds.capture(16)

    if 1:
        print "counts 0x%08x" % sds.read_soc_reg(0x212)
        decode_mig_status(sds.read_soc_reg(0x211))

    if 1:
        print "Reset"
        sds.write_soc_reg(0x200, 1)
        print "ctrl 0x%08x" % sds.read_soc_reg(0x200)
        sds.write_soc_reg(0x200, 0)
        print "ctrl 0x%08x" % sds.read_soc_reg(0x200)
        time.sleep(0.1)
        print "ctrl 0x%08x" % sds.read_soc_reg(0x200)
        print

    decode_mig_status(sds.read_soc_reg(0x211))

    n = 3
    o = 10
    if 1:
        print "write to FIFO"
        for i in range(n):
            sds.write_soc_reg(0x218, 0xf00f0000 + i)
            time.sleep(0.1)
        print "counts 0x%08x" % sds.read_soc_reg(0x212)
        decode_mig_status(sds.read_soc_reg(0x211))

        print "write to DDR"
        sds.write_soc_reg(0x210, o | ((n-1)<<24) | (0<<30))
        time.sleep(0.1)
        print "counts 0x%08x" % sds.read_soc_reg(0x212)
        decode_mig_status(sds.read_soc_reg(0x211))

    sds.write_ddr(20, [ 0xdeadbeef, 0xfeedf00f ])

    n = 31
    o = 0
    if 1:
        print "read from DDR"
        sds.write_soc_reg(0x210, o | ((n-1)<<24) | (1<<30))
        time.sleep(0.1)
        print "counts 0x%08x" % sds.read_soc_reg(0x212)
        decode_mig_status(sds.read_soc_reg(0x211))

        print "read from FIFO"
        for i in range(n):
            print "rd %2d -> 0x%08x" % (i, sds.read_soc_reg(0x218))
        time.sleep(0.1)
        print "counts 0x%08x" % sds.read_soc_reg(0x212)
        decode_mig_status(sds.read_soc_reg(0x211))

    data = sds.read_ddr(0, 32)
    for i in range(len(data)):
        print "%2d -> 0x%08x" % (i, data[i])

    n = 0x100
    o = 0x100
    wr_data = [ random.randrange(1<<32) for _ in range(n) ]
    sds.write_ddr(o, wr_data)
    rd_data = sds.read_ddr(o, n)

    assert all(wr_data == rd_data)

if __name__ == '__main__':
    main()
