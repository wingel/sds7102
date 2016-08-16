#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_dpram.py')

from myhdl import Signal, intbv, always_seq, instances

from system import System
from bus import SimpleBus

class SimpleDpRam(object):
    """Dual port DRAM"""

    def __init__(self, system0, system1, addr_depth, data_width):
        self.addr_depth = addr_depth
        self.data_width = data_width

        self.system0 = system0
        self.system1 = system1
        self._bus0 = SimpleBus(addr_depth, data_width)
        self._bus1 = SimpleBus(addr_depth, data_width)

    def bus0(self):
        return self._bus0

    def bus1(self):
        return self._bus1

    def gen(self):
        system0 = self.system0
        bus0 = self.bus0()

        ram = [ Signal(intbv(0)[self.data_width:])
                for _ in range(self.addr_depth) ]

        @always_seq(system0.CLK.posedge, system0.RST)
        def seq0():
            if bus0.WR:
                ram[bus0.ADDR].next = bus0.WR_DATA

            if bus0.RD and bus0.ADDR < len(ram):
                bus0.RD_DATA.next = ram[bus0.ADDR]
            else:
                bus0.RD_DATA.next = 0

        system1 = self.system1
        bus1 = self.bus1()

        @always_seq(system1.CLK.posedge, system1.RST)
        def seq1():
            if bus1.WR:
                ram[bus1.ADDR].next = bus1.WR_DATA

            if bus1.RD and bus1.ADDR < len(ram):
                bus1.RD_DATA.next = ram[bus1.ADDR]
            else:
                bus1.RD_DATA.next = 0

        return instances()
