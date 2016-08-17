#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo.test_fifo')

from myhdl import (Signal, ResetSignal, intbv,
                   always_seq, always_comb, instances)

from simple.reg import Reg, RoField

from ._mem import FifoMem

class SyncFifo(object):
    """FIFO"""

    def __init__(self, rst, clk, factory, depth):
        # Depth must be a power of two
        assert depth == depth & ~(depth - 1)
        self.depth = depth

        self.factory = factory

        self.WR_CLK = clk
        self.WR_RST = rst
        self.WR = Signal(False)
        self.WR_DATA = Signal(factory)
        self.WR_FULL = Signal(False)

        self.RD_CLK = clk
        self.RD_RST = rst
        self.RD = Signal(False)
        self.RD_DATA = Signal(factory)
        self.RD_EMPTY = Signal(False)

    def count_reg(self, system, name):
        rd = Signal(intbv(0)[16:])
        wr = Signal(intbv(0)[16:])

        reg = Reg(system,
                        '%s_fifo_counts' % name,
                        "Counts for SyncFifo %s", [
            RoField('rd_count', "", rd),
            RoField('wr_count', "", wr),
            ])
        reg_inst = reg.gen()

        @always_seq(self.WR_CLK.posedge, self.WR_RST)
        def wr_seq():
            if self.WR:
                wr.next = wr + 1

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def rd_seq():
            if self.RD:
                rd.next = rd + 1

        return reg.bus(), instances()

    def gen(self):
        mem = FifoMem(self.RD_CLK, self.WR_CLK,
                      self.depth, len(self.WR_DATA))
        mem_inst = mem.gen()

        ptr_init = intbv(0, 0, 2 * self.depth)

        # Gray encoded write and read pointers
        wr_ptr = Signal(ptr_init)
        rd_ptr = Signal(ptr_init)

        ################################################################
        # Write side of the FIFO

        wr_new = Signal(ptr_init)

        wr_sync_rd_ptr = Signal(ptr_init)

        # I don't think I need this one, but leave it in for th
        @always_seq(self.WR_CLK.posedge, self.WR_RST)
        def wr_sync_inst():
            wr_sync_rd_ptr.next = rd_ptr

        @always_comb
        def wr_new_comb():
            wr_new.next = wr_ptr
            if self.WR:
                wr_new.next = (wr_ptr + 1) & ((1<<len(wr_new))-1)

        @always_comb
        def wr_data_comb():
            mem.WR.next = 0
            mem.WR_ADDR.next = wr_ptr & (self.depth-1)
            mem.WR_DATA.next = self.WR_DATA
            if self.WR:
                mem.WR.next = 1

        @always_comb
        def wr_full_comb():
            self.WR_FULL.next = 0
            if wr_new ^ self.depth == wr_sync_rd_ptr:
                self.WR_FULL.next = 1

        @always_seq(self.WR_CLK.posedge, self.WR_RST)
        def wr_seq():
            wr_ptr.next = wr_new

        ################################################################
        # Read side of the FIFO

        rd_new = Signal(ptr_init)

        rd_sync_wr_ptr = Signal(ptr_init)

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def rd_sync_inst():
            rd_sync_wr_ptr.next = wr_ptr

        @always_comb
        def rd_new_comb():
            rd_new.next = rd_ptr
            if self.RD:
                rd_new.next = (rd_ptr + 1) & ((1<<len(rd_new))-1)

        @always_comb
        def rd_data_comb():
            mem.RD.next = 1
            mem.RD_ADDR.next = rd_new & (self.depth-1)
            self.RD_DATA.next = mem.RD_DATA

        @always_comb
        def rd_empty_comb():
            self.RD_EMPTY.next = 0
            if rd_new == rd_sync_wr_ptr:
                self.RD_EMPTY.next = 1

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def rd_seq():
            rd_ptr.next = rd_new

        return instances()
