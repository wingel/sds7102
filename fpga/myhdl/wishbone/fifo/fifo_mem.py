#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo.py')

from myhdl import Signal, intbv, always

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

        @always(self.WR_CLK.posedge)
        def wr_inst():
            if self.WR:
                mem[self.WR_ADDR].next = self.WR_DATA

        @always(self.RD_CLK.posedge)
        def rd_inst():
            self.RD_DATA.next = mem[self.RD_ADDR]

        return wr_inst, rd_inst
