#! /usr/bin/python
import os
import sys
import numpy
import time
from subprocess import Popen, PIPE

GPA = tuple([ 0 + i for i in range(32) ])
GPB = tuple([ 32 + i for i in range(16) ])
GPC = tuple([ 64 + i for i in range(16) ])
GPD = tuple([ 96 + i for i in range(16) ])
GPE = tuple([ 128 + i for i in range(16) ])
GPH = tuple([ 224 + i for i in range(16) ])

class SDS(object):
    def __init__(self, host):
        self.p = Popen([ 'ssh', host, './sds-server' ],
                       stdin = PIPE, stdout = PIPE, stderr = sys.stderr)

        self.fi = self.p.stdout
        self.fo = self.p.stdin

    def read_regs(self, addr, count):
        cmd = 'read_fpga 0x%x %u' % (addr, count)
        print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

        a = numpy.zeros(count, dtype = numpy.uint32)
        for i in range(count):
            s = self.fi.readline()
            a[i] = int(s, 0)

        return a

    def read_reg(self, addr):
        return self.read_regs(addr, 1)[0]

    def write_regs(self, addr, data):
        cmd = 'write_fpga 0x%x %s' % (addr, ' '.join([ hex(v) for v in data ]))
        print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

    def write_reg(self, addr, value):
        self.write_regs(addr, [ value ])

    def set_gpio(self, pin, value):
        cmd = 'set_gpio %u %u' % (pin, value)
        print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

    def atten(self, channel, value):
        assert channel >= 0 and channel < 2
        assert value >= 0 and value < 2

        if channel:
            a = GPE[1]
            b = GPH[12]
        else:
            a = GPA[15]
            b = GPA[1]

        self.set_gpio(a, 1 - value)
        self.set_gpio(b, value)

    def acdc(self, channel, value):
        assert channel >= 0 and channel < 2
        assert value >= 0 and value < 2

        if channel:
            a = GPD[8]
        else:
            a = GPA[0]

        self.set_gpio(a, value)

    def mux(self, channel, value):
        assert channel >= 0 and channel < 2
        assert value >= 0 and value < 4

        if channel:
            a0 = GPH[9]
            a1 = GPH[11]
        else:
            a0 = GPC[5]
            a1 = GPC[6]

        self.set_gpio(a0, value & 1)
        self.set_gpio(a1, (value & 2) >> 1)

    def odd_relay(self, value):
        assert value >= 0 and value < 2
        self.set_gpio(GPE[3], value)

    def ext_relay(self, value):
        assert value >= 0 and value < 2
        self.set_gpio(GPC[7], value)

    def shifter(self, cs, bits, value, cpol = 0, cpha = 0, pulse = 0):
        assert cpol >= 0 and cpol < 2
        assert cpha >= 0 and cpha < 2
        assert pulse >= 0 and pulse < 2
        assert cs >= 0 and pulse < 6
        assert bits >= 0 and bits <= 32
        data = [ value,
                 bits | (cpha<<8) | (cpol<<9) | (pulse<<10) | (1<<16<<cs) ]
        self.write_regs(0x210, data)
        time.sleep(0.1)

    def bu2506(self, channel, value):
        assert channel >= 0 and channel < 16
        assert value >= 0 and value < 1024
        v = channel | (value << 4)
        v2 = 0
        for i in range(14):
            v2 <<= 1
            if v & (1<<i):
                v2 |= 1
        print "bu2506 0x%04x 0x%04x" % (v, v2)
        self.shifter(0, 14, v2, pulse = 1)

    def adf4360(self, value):
        self.shifter(1, 24, value, pulse = 1)

    def adc08d500(self, value):
        self.shifter(2, 32, value, cpol = 1, cpha = 1)

    def lmh6518(self, channel, value):
        assert channel >= 0 and channel < 2
        if channel:
            self.shifter(4, 24, value)
        else:
            self.shifter(3, 24, value)

    def dac8532(self, channel, value):
        assert channel >= 0 and channel < 2
        assert value >= 0 and value < 65536
        if channel:
            base = 0x100000
        else:
            base = 0x240000
        self.shifter(5, 24, base | value, cpha = 1)

    def capture(self, count):
        self.write_reg(0x230, 0)
        self.write_reg(0x230, 1)
        time.sleep(0.1)
        data0 = self.read_regs(0x4000, count)
        data1 = self.read_regs(0x6000, count)

        data = numpy.dstack((data0, data1))[0].reshape(len(data0)+len(data1))

        print data0
        print data1
        print data

        return data

    def soc(self, count):
        """Get a SoC bus trace"""

        self.write_reg(0x231, 0)
        self.write_reg(0x231, 1)
        time.sleep(0.1)

        # Single Data Rate (SDR) signals
        sdr0 = self.read_regs(0x2000, count)
        sdr1 = sdr0
        sdr = numpy.dstack((sdr1, sdr0))[0].reshape(len(sdr0)+len(sdr1))

        print sdr0
        print sdr1
        print sdr

        # Registered copies of SDR signals
        reg0 = self.read_regs(0x2000, count)
        reg1 = reg0
        reg = numpy.dstack((reg1, reg0))[0].reshape(len(reg0)+len(reg1))

        print reg0
        print reg1
        print reg

        # Double Data Rate DDR signals
        ddr0 = self.read_regs(0x3000, count)
        ddr1 = self.read_regs(0x3800, count)
        ddr = numpy.dstack((ddr1, ddr0))[0].reshape(len(ddr0)+len(ddr1))

        print ddr0
        print ddr1
        print ddr

        return sdr, reg, ddr

def main():
    sds = SDS('sds')

    # sds.capture(16)

    print "0x250 -> 0x%08x" % sds.read_reg(0x250)

    sds.write_reg(0x250, 0)

    for i in range(10):
        print "0x250 -> 0x%08x" % sds.read_reg(0x250)
        time.sleep(0.1)

if __name__ == '__main__':
    main()
