#! /usr/bin/python
import os
import sys
import numpy
import time
from subprocess import Popen, PIPE
import random

GPA = tuple([ 0 + i for i in range(32) ])
GPB = tuple([ 32 + i for i in range(16) ])
GPC = tuple([ 64 + i for i in range(16) ])
GPD = tuple([ 96 + i for i in range(16) ])
GPE = tuple([ 128 + i for i in range(16) ])
GPF = tuple([ 160 + i for i in range(16) ])
GPH = tuple([ 224 + i for i in range(16) ])

class SDS(object):
    def __init__(self, host):
        self.p = Popen([ 'ssh', host, './sds-server' ],
                       stdin = PIPE, stdout = PIPE, stderr = sys.stderr,
                       universal_newlines = False)

        self.fi = self.p.stdout
        self.fo = self.p.stdin

        self.verbose = False

    def read_regs(self, addr, count):
        cmd = 'read_fpga 0x%x %u' % (addr, count)
        if self.verbose:
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
        cmd = 'write_fpga 0x%x %s' % (addr, ' '.join([ '0x%x' % v for v in data ]))
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

    def write_reg(self, addr, value):
        self.write_regs(addr, [ value ])

    def read_soc_regs(self, addr, count):
        cmd = 'read_soc 0x%x %u' % (addr, count)
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

        a = numpy.zeros(count, dtype = numpy.uint32)
        for i in range(count):
            s = self.fi.readline()
            a[i] = int(s, 0)

        return a

    def read_soc_reg(self, addr):
        return self.read_soc_regs(addr, 1)[0]

    def write_soc_regs(self, addr, data):
        cmd = 'write_soc 0x%x %s' % (addr, ' '.join([ '0x%x' % v for v in data ]))
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

    def write_soc_reg(self, addr, value):
        self.write_soc_regs(addr, [ value ])

    def read_ddr(self, addr, count):
        cmd = 'read_ddr 0x%x %u' % (addr, count)
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

        a = numpy.zeros(count, dtype = numpy.uint32)
        for i in range(count):
            s = self.fi.readline()
            a[i] = int(s, 0)

        return a

    def read_ddr_b(self, addr, count):
        cmd = 'read_ddr_b 0x%x %u' % (addr, count)
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

        a = numpy.fromfile(self.fi, dtype = numpy.uint32, count = count)

        return a

    def write_ddr(self, addr, data):
        cmd = 'write_ddr 0x%x %s' % (addr, ' '.join([ '0x%x' % v for v in data ]))
        if self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

    def set_gpio(self, pin, value):
        cmd = 'set_gpio %u %u' % (pin, value)
        if self.verbose:
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
        if self.verbose:
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

    def mig_reset(self):
        self.write_soc_reg(0x200, 1)
        print "ctrl 0x%08x" % self.read_soc_reg(0x200)
        self.write_soc_reg(0x200, 0)
        print "ctrl 0x%08x" % self.read_soc_reg(0x200)
        time.sleep(0.1)
        print "ctrl 0x%08x" % self.read_soc_reg(0x200)
        print

    def do_mig_capture(self, synthetic = 0):
        self.write_soc_reg(0x230, 0)
        time.sleep(0.1)

        if 1:
            self.mig_reset()
            time.sleep(0.1)

        v = 1
        if synthetic:
            v |= 2
        self.write_soc_reg(0x230, v)
        print "capture_status 0x%08x" % self.read_soc_reg(0x230)
        time.sleep(0.1)

        self.write_soc_reg(0x230, 0)
        print "capture_status 0x%08x" % self.read_soc_reg(0x230)
        time.sleep(0.1)

        print "p2"
        print "counts 0x%08x" % self.read_soc_reg(0x221)
        decode_mig_status(self.read_soc_reg(0x220))

        print "p3"
        print "counts 0x%08x" % self.read_soc_reg(0x229)
        decode_mig_status(self.read_soc_reg(0x228))

    def mig_capture(self, count, synthetic = 0):
        self.do_mig_capture(synthetic = synthetic)

        t0 = time.time()
        data = self.read_ddr_b(0, count)
        t = time.time()
        print "capture time", t - t0

        if 0:
            data2 = self.read_ddr_b(0, count)
            assert all(data == data2)

        if 0:
            chunk = 32

            data = data[:int(len(data) / (chunk * 2)) * (chunk * 2)]

            s = numpy.reshape(data, (len(data) / (chunk * 2), 2, chunk))
            s0 = numpy.reshape(s[:,0,:], len(data)/2)
            s1 = numpy.reshape(s[:,1,:], len(data)/2)

            if 0:
                print s0[:256]
                print s1[:256]

            if 0:
                # Check of synthetic data
                o = s0[0]
                for i in range(len(s0)):
                    d = s0[i] - (o + 2 * i)
                    if d:
                        print "bad s0", hex(i), d, s0[i-4:i+5]
                        o = s0[i] - 2 * i

                o = s1[0]
                for i in range(len(s1)):
                    d = s1[i] - (o + 2 * i)
                    if d:
                        print "bad s1", hex(i), d, s1[i-4:i+5]
                        o = s1[i] - 2 * i

            data = numpy.reshape(numpy.dstack((s0, s1)), len(s0)+len(s1))

            # print data[:512]

        return data

    def render(self, addr, count, scale):
        cmd = 'render 0x%x %u %u' % (addr, count, scale)
        if 1 or self.verbose:
            print cmd
        self.fo.write(cmd + '\n')
        self.fo.flush()

        a = numpy.fromfile(self.fi, dtype = numpy.uint32,
                           count = count * 0x100)

        return a

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

    def set_red_led(self, value):
        self.set_gpio(GPF[3], value)

    def set_green_led(self, value):
        assert value >= 0 and value <= 1
        v = self.read_soc_reg(0x108)
        if value:
            v |= (1<<0)
        else:
            v &= ~(1<<0)
        self.write_soc_reg(0x108, v)

    def set_white_led(self, value):
        assert value >= 0 and value <= 1
        v = self.read_soc_reg(0x108)
        if value:
            v |= (1<<1)
        else:
            v &= ~(1<<1)
        self.write_soc_reg(0x108, v)

    def fp_init(self):
        v = self.read_soc_reg(0x100)
        v |= 1
        self.write_soc_reg(0x100, v)
        time.sleep(0.1)
        v &= ~1
        self.write_soc_reg(0x100, v)

def decode_mig_status(v):
    print "dram status  0x%08x" % v
    print "cmd_full     %u" % ((v >> 25) & 1)
    print "cmd_empty    %u" % ((v >> 24) & 1)
    print "wr_underrun  %u" % ((v >> 23) & 1)
    print "wr_error     %u" % ((v >> 22) & 1)
    print "wr_full      %u" % ((v >> 21) & 1)
    print "wr_empty     %u" % ((v >> 20) & 1)
    print "wr_count     %u" % ((v >> 12) & 0x7f)
    print "rd_overflow  %u" % ((v >> 11) & 1)
    print "rd_error     %u" % ((v >> 10) & 1)
    print "rd_full      %u" % ((v >> 9) & 1)
    print "rd_empty     %u" % ((v >> 8) & 1)
    print "rd_count     %u" % ((v >> 0) & 0x7f)
    print

def main():
    sds = SDS('sds')

    if 1:
        sds.mig_reset()

        sds.write_ddr(0, [ 0xff ] *  2048)

        if 1:
            return

        print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
        print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)
        print "0x122 -> 0x%08x" % sds.read_soc_reg(0x122)

        print "0x130 -> 0x%08x" % sds.read_soc_reg(0x130)
        print "0x131 -> 0x%08x" % sds.read_soc_reg(0x131)
        print "0x132 -> 0x%08x" % sds.read_soc_reg(0x132)
        print "0x134 -> 0x%08x" % sds.read_soc_reg(0x134)
        print "0x135 -> 0x%08x" % sds.read_soc_reg(0x135)

        decode_mig_status(sds.read_soc_reg(0x134))

        zeros = [ 0 ] * 1024
        sds.write_soc_regs(0x8000, zeros)

        n = 64
        rd_data = sds.read_soc_regs(0x8000, n)
        print rd_data

        src_addr = 0x20
        dst_addr = 0x10
        count = 0x300

        sds.write_soc_reg(0x130, src_addr)
        sds.write_soc_reg(0x120, dst_addr)

        print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
        print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)
        print "0x122 -> 0x%08x" % sds.read_soc_reg(0x122)

        print "0x130 -> 0x%08x" % sds.read_soc_reg(0x130)
        print "0x131 -> 0x%08x" % sds.read_soc_reg(0x131)
        print "0x132 -> 0x%08x" % sds.read_soc_reg(0x132)
        print "0x134 -> 0x%08x" % sds.read_soc_reg(0x134)
        print "0x135 -> 0x%08x" % sds.read_soc_reg(0x135)

        decode_mig_status(sds.read_soc_reg(0x134))

        sds.write_soc_reg(0x131, count)

        print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
        print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)
        print "0x122 -> 0x%08x" % sds.read_soc_reg(0x122)

        print "0x130 -> 0x%08x" % sds.read_soc_reg(0x130)
        print "0x131 -> 0x%08x" % sds.read_soc_reg(0x131)
        print "0x132 -> 0x%08x" % sds.read_soc_reg(0x132)
        print "0x134 -> 0x%08x" % sds.read_soc_reg(0x134)
        print "0x135 -> 0x%08x" % sds.read_soc_reg(0x135)

        decode_mig_status(sds.read_soc_reg(0x134))

        ram_data = sds.read_soc_regs(0x8000 + dst_addr, count)
        print ram_data

        ddr_data = sds.read_ddr(src_addr, count)
        print ddr_data

        assert all(ram_data == ddr_data)

    if 0:
        wr_data = [ random.randrange(100) for _ in range(16) ]
        sds.write_soc_regs(0x8010, wr_data)

        print wr_data

        rd_data = sds.read_soc_regs(0x8000, n)
        print rd_data

        assert all(rd_data[0x10:0x10 + len(wr_data)] == wr_data)

        if 1:
            sds.write_soc_reg(0x120, 0x28)
            sds.write_soc_reg(0x121, 0x14)

            print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
            print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)

            sds.write_soc_reg(0x122, 0x8)

            print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
            print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)
            print "0x122 -> 0x%08x" % sds.read_soc_reg(0x122)

            time.sleep(1)

            print "0x120 -> 0x%08x" % sds.read_soc_reg(0x120)
            print "0x121 -> 0x%08x" % sds.read_soc_reg(0x121)
            print "0x122 -> 0x%08x" % sds.read_soc_reg(0x122)

            rd_data = sds.read_soc_regs(0x8000, n)
            print rd_data

            assert all(rd_data[0x28 : 0x28 + 0x8] == wr_data[4:4+8])

def hd(a):
    w = 8
    for i in range(0, len(a), w):
        s = "%06x " % i
        n = len(a) - i
        if n > w:
            n = w
        for j in range(n):
            s += " %08x" % a[i + j]
        print s

if __name__ == '__main__':
    main()
