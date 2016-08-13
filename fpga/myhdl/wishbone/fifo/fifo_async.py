#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo.py')

from myhdl import (Signal, ResetSignal, intbv,
                   always_seq, always_comb, instances)
from rhea.cores.misc import syncro

from fifo_mem import FifoMem
from gray import GrayIncrementer, gray_encode, gray_decode
from rst import rst_sync

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
            wr_rst = None
            rd_rst = None
        else:
            wr_rst = ResetSignal(True, True, False)
            rd_rst = ResetSignal(True, True, False)

            wr_rst_inst = rst_sync(self.WR_CLK, self.RST, wr_rst)
            rd_rst_inst = rst_sync(self.RD_CLK, self.RST, rd_rst)

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

        @always_seq(self.WR_CLK.posedge, wr_rst)
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

        @always_seq(self.RD_CLK.posedge, rd_rst)
        def rd_seq():
            rd_cur.next = rd_new
            rd_gray.next = gray_encode(rd_new)

        return instances()

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
