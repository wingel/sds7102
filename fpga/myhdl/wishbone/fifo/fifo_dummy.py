#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo.py')

from myhdl import (Signal, ResetSignal, intbv,
                   always_seq, always_comb, instances)

class DummyFifo(object):
    def __init__(self, rst, rd_clk, factory, base, inc):
        self.factory = factory
        self.base = base
        self.inc = inc

        self.RST = rst

        # These signals are in the WR_CLK domain
        self.WR_CLK = Signal(False)
        self.WR = Signal(False)
        self.WR_DATA = Signal(factory)
        self.WR_FULL = Signal(False)

        # These signals are in the RD_CLK domain
        self.RD_CLK = rd_clk
        self.RD = Signal(False)
        self.RD_DATA = Signal(factory)
        self.RD_EMPTY = Signal(False)

    def gen(self):
        if self.RST is None:
            rd_rst = None
        else:
            rd_rst = ResetSignal(True, True, False)

            rd_rst_inst = rst_sync(self.RD_CLK, self.RST, rd_rst)

        cnt = Signal(intbv(self.base)[16:])

        @always_seq(self.RD_CLK.posedge, rd_rst)
        def rd_seq():
            if self.RD:
                cnt.next = cnt + self.inc

        @always_comb
        def rd_comb():
            self.RD_DATA.next = cnt & ((1<<len(self.RD_DATA))-1)

            # self.RD_EMPTY.next = self.RD

        return instances()
