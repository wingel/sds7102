#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo/test_fifo')

from myhdl import (Signal, ResetSignal, intbv,
                   always_seq, always_comb, instances)
from rhea.cores.misc import syncro

from common.gray import gray_encode
from common.rst import rst_sync

from ._mem import FifoMem

class AsyncFifo(object):
    """FIFO"""

    def __init__(self, rst, wr_clk, rd_clk, factory, depth):
        # Depth must be a power of two
        assert depth == depth & ~(depth - 1)
        self.depth = depth

        self.factory = factory

        self.RST = rst

        # These signals are in the WR_CLK domain
        self.WR_CLK = wr_clk
        if self.RST is None:
            self.WR_RST = None
        else:
            self.WR_RST = ResetSignal(True, True, False)
        self.WR = Signal(False)
        self.WR_DATA = Signal(factory)
        self.WR_FULL = Signal(False)

        # These signals are in the RD_CLK domain
        self.RD_CLK = rd_clk
        if self.RST is None:
            self.RD_RST = None
        else:
            self.RD_RST = ResetSignal(True, True, False)
        self.RD = Signal(False)
        self.RD_DATA = Signal(factory)
        self.RD_EMPTY = Signal(False)

    def gen(self):
        if self.RST is not None:
            wr_rst_inst = rst_sync(self.WR_CLK, self.RST, self.WR_RST)
            rd_rst_inst = rst_sync(self.RD_CLK, self.RST, self.RD_RST)

        mem = FifoMem(self.WR_CLK, self.RD_CLK, self.depth, len(self.WR_DATA))
        mem_inst = mem.gen()

        gray_init = intbv(0, 0, 2 * self.depth)

        # Gray encoded write and read pointers
        wr_gray = Signal(gray_init)
        rd_gray = Signal(gray_init)

        ################################################################
        # Write side of the FIFO

        wr_cur = Signal(gray_init)
        wr_new = Signal(gray_init)

        # Gray encoded read pointer synchronized to the write clock domain
        wr_sync_rd_gray = Signal(gray_init)

        wr_sync_inst = syncro(self.WR_CLK, rd_gray, wr_sync_rd_gray,
                              num_sync_ff = 2)

        @always_comb
        def wr_new_comb():
            wr_new.next = wr_cur
            if self.WR:
                wr_new.next = (wr_cur + 1) & ((1<<len(wr_new))-1)

        @always_comb
        def wr_data_comb():
            mem.WR.next = 0
            mem.WR_ADDR.next = wr_cur & ((1<<len(mem.WR_ADDR))-1)
            mem.WR_DATA.next = self.WR_DATA
            if self.WR:
                mem.WR.next = 1

        @always_comb
        def wr_full_comb():
            self.WR_FULL.next = 0
            if gray_encode(wr_new ^ self.depth) == wr_sync_rd_gray:
                self.WR_FULL.next = 1

        @always_seq(self.WR_CLK.posedge, self.WR_RST)
        def wr_seq():
            wr_cur.next = wr_new
            wr_gray.next = gray_encode(wr_new)

        ################################################################
        # Read side of the FIFO

        rd_cur = Signal(gray_init)
        rd_new = Signal(gray_init)

        # Gray encoded read pointer synchronized to the write clock domain
        rd_sync_wr_gray = Signal(gray_init)

        rd_sync_inst = syncro(self.RD_CLK, wr_gray, rd_sync_wr_gray,
                              num_sync_ff = 2)

        @always_comb
        def rd_new_comb():
            rd_new.next = rd_cur
            if self.RD:
                rd_new.next = (rd_cur + 1) & ((1<<len(rd_new))-1)

        @always_comb
        def rd_data_comb():
            mem.RD.next = 1
            mem.RD_ADDR.next = rd_new & ((1<<len(mem.RD_ADDR))-1)
            self.RD_DATA.next = mem.RD_DATA

        @always_comb
        def rd_empty_comb():
            self.RD_EMPTY.next = 0
            if gray_encode(rd_new) == rd_sync_wr_gray:
                self.RD_EMPTY.next = 1

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def rd_seq():
            rd_cur.next = rd_new
            rd_gray.next = gray_encode(rd_new)

        return instances()
