#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_mux.py')

from myhdl import Signal, intbv, always_comb, always_seq
from bus import Bus

class Mux(object):
    def __init__(self, system):
        self.system = system

        self.slaves = []
        self.addr = 0
        self.align = True
        self.pad = True

        self.addr = 0

        self.addr_depth = 0
        self.data_width = 0

        self._bus = None

    def bus(self):
        if self._bus is None:
            self._bus = Bus(self.addr_depth, self.data_width)
        return self._bus

    def add(self, slaves, addr = None, align = None, pad = None):
        if isinstance(slaves, Bus):
            self.add_one(slaves, addr, align, pad)
        else:
            for slave in slaves:
                self.add_one(slave, addr, align, pad)
                addr = self.addr

    def add_one(self, slave, addr = None, align = None, pad = None):
        # We can't add more slaves if we have created our bus
        assert self._bus is None

        natural_size = 1 << (slave.addr_depth - 1).bit_length()

        if align is None:
            align = slave.align

        if align is None:
            align = self.align

        if align == True:
            align = natural_size

        if pad is None:
            pad = self.pad

        if pad == True:
            pad = natural_size

        if addr is None:
            addr = self.addr

        print "Mux.add", addr, align, pad

        assert not align or not (align & (align - 1))
        assert not pad or not (pad & (pad - 1))

        if align:
            addr = (addr + align - 1) & ~(align - 1)

        slave.addr = addr

        if pad:
            addr = (addr + pad - 1) & ~(pad - 1)

        self.addr = addr + pad

        if self.addr_depth < self.addr:
            self.addr_depth = self.addr

        if self.data_width < slave.data_width:
            self.data_width = slave.data_width

        self.slaves.append(slave)

    def connect(self, i, slave):
        insts = []
        @always_comb
        def addr_comb():
            print len(slave.ADDR), self.addr_array[i], len(self.addr_array[i])
            slave.ADDR.next = self.addr_array[i] & ((1<<len(slave.ADDR))-1)
        insts.append(addr_comb)
        @always_comb
        def wr_comb():
            slave.WR.next = self.wr_array[i]
        insts.append(wr_comb)
        @always_comb
        def wr_data_comb():
            slave.WR_DATA.next = self.wr_data_array[i] & ((1<<len(slave.WR_DATA))-1)
        insts.append(wr_data_comb)
        @always_comb
        def rd_comb():
            slave.RD.next = self.rd_array[i]
        insts.append(rd_comb)
        @always_comb
        def rd_data_comb():
            self.rd_data_array[i].next = slave.RD_DATA
        insts.append(rd_data_comb)
        return insts

    def gen(self):
        system = self.system
        bus = self.bus()
        slaves = self.slaves

        insts = []

        addr_lo = []
        addr_hi = []

        n = len(slaves)
        print "number of slaves", n
        self.addr_array = [ Signal(intbv(0)[len(bus.ADDR):]) for _ in range(n) ]
        self.wr_array = [ Signal(False) for _ in range(n) ]
        self.wr_data_array = [ Signal(intbv(0)[bus.data_width:]) for _ in range(n) ]
        self.rd_array = [ Signal(False) for _ in range(n) ]
        self.rd_data_array = [ Signal(intbv(0)[bus.data_width:]) for _ in range(n+1) ]

        for i, slave in enumerate(slaves):
            addr_lo.append(slave.addr)
            addr_hi.append(slave.addr + slave.addr_depth)

            connect_inst = self.connect(i, slave)
            insts.append(connect_inst)

        addr_lo = tuple(addr_lo)
        addr_hi = tuple(addr_hi)

        @always_comb
        def comb():
            rd_data = intbv(0)[len(bus.RD_DATA):]

            for i in range(len(slaves)):
                lo = addr_lo[i]
                hi = addr_hi[i]
                sel = bus.ADDR >= lo and bus.ADDR < hi

                self.addr_array[i].next = (bus.ADDR - lo) & ((1<<len(bus.ADDR))-1)
                self.wr_array[i].next = sel and bus.WR
                self.wr_data_array[i].next = bus.WR_DATA
                self.rd_array[i].next = sel and bus.RD

                rd_data |= self.rd_data_array[i]

            bus.RD_DATA.next = rd_data
        insts.append(comb)

        return insts
