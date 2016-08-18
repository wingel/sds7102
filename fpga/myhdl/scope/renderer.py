#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('scope.test_renderer')

from myhdl import (Signal, intbv, always_comb, always_seq, instances)

from simple.bus import Bus

class Renderer(object):
    def __init__(self, system,
                 sample_width, accumulator_width):

        self.system = system

        self.sample_width = sample_width
        self.accumulator_width = accumulator_width

        self.STROBE = Signal(False)
        self.SAMPLE = Signal(intbv(0)[sample_width:])

        self._bus = Bus(addr_depth = 1 << sample_width,
                        data_width = self.accumulator_width)

    def bus(self):
        return self._bus

    def gen(self):
        system = self.system
        bus = self.bus()

        mem = [ Signal(intbv(0)[self.accumulator_width:])
                for _ in range(1<<self.sample_width) ]

        inc = Signal(False)
        inc_idx = Signal(intbv(0)[self.sample_width:])
        inc_val = Signal(intbv(0)[self.accumulator_width:])

        @always_seq(system.CLK.posedge, system.RST)
        def contributions_inst():
            bus.RD_DATA.next = 0

            if bus.WR:
                mem[bus.ADDR].next = bus.WR_DATA
            elif inc:
                inc.next = 0
                mem[inc_idx].next = inc_val

            if bus.RD:
                bus.RD_DATA.next = mem[bus.ADDR]
            elif self.STROBE:
                inc.next = 1
                inc_idx.next = self.SAMPLE
                inc_val.next = mem[self.SAMPLE].next + 1

        return instances()
