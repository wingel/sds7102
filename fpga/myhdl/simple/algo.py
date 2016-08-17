#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_algo')

from myhdl import Signal, intbv, always_seq, always_comb

from common.system import System
from common.gray import gray_encoder

from .bus import Bus

class Algo(object):

    """ bus slave which returns some data based on the address.

    This slave is used to test reading over the SoC bus."""

    def __init__(self, system, addr_depth, data_width):
        self.system = system
        self._bus = Bus(addr_depth, data_width)

    def bus(self):
        return self._bus

    def gen(self):
        system = self.system
        bus = self.bus()

        insts = []

        bin_data = Signal(intbv(0)[(bus.data_width+1) / 2:])
        gray_data = Signal(intbv(0)[bus.data_width - len(bin_data):])

        @always_comb
        def bin_inst():
            bin_data.next = bus.ADDR & ((1<<len(bin_data))-1)
        insts.append(bin_inst)

        gray_inst = gray_encoder(bin_data, gray_data)
        insts.append(gray_inst)

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if bus.RD and bus.ADDR < bus.addr_depth:
                bus.RD_DATA.next = bin_data | (gray_data << len(bin_data))
            else:
                bus.RD_DATA.next = 0

        insts.append(seq)

        return insts
