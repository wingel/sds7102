#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_ram')

from myhdl import Signal, intbv, always_seq, instances

from common.system import System

from .bus import Bus

class Ram(object):
    """ slave backed by a bit of RAM"""

    def __init__(self, system, addr_depth, data_width):
        self.system = system

        self.addr_depth = addr_depth
        self.data_width = data_width

        self._bus = Bus(addr_depth, data_width)

    def bus(self):
        return self._bus

    def gen(self):
        system = self.system
        bus = self.bus()

        ram = [ Signal(intbv(0)[self.data_width:])
                for _ in range(self.addr_depth) ]

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if bus.WR:
                ram[bus.ADDR].next = bus.WR_DATA

            if bus.RD and bus.ADDR < len(ram):
                bus.RD_DATA.next = ram[bus.ADDR]
            else:
                bus.RD_DATA.next = 0

        return instances()
