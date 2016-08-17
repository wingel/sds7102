#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo.test_fifo')

from myhdl import Signal, intbv, always_seq

class FifoMem(object):
    def __init__(self, wr_clk, rd_clk, addr_depth, data_width):

        self.addr_depth = addr_depth
        self.data_width = data_width

        self.WR_CLK = wr_clk
        self.WR = Signal(False)
        self.WR_ADDR = Signal(intbv(0, 0, addr_depth))
        self.WR_DATA = Signal(intbv(0)[data_width:])

        self.RD_CLK = rd_clk
        self.RD = Signal(False)
        self.RD_ADDR = Signal(intbv(0, 0, addr_depth))
        self.RD_DATA = Signal(intbv(0)[data_width:])

    def gen(self):
        mem = [ Signal(intbv(0)[self.data_width:])
                for _ in range(self.addr_depth) ]

        @always_seq (self.WR_CLK.posedge, None)
        def wr_inst():
            if self.WR:
                mem[self.WR_ADDR].next = self.WR_DATA

        @always_seq (self.RD_CLK.posedge, None)
        def rd_inst():
            self.RD_DATA.next = mem[self.RD_ADDR]

        return wr_inst, rd_inst
