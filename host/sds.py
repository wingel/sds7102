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

def main():
    sds = SDS('sds')

    sds.capture(16)

if __name__ == '__main__':
    main()
