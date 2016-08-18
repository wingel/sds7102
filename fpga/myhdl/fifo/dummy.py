#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo.test_fifo')

from myhdl import (Signal, ResetSignal, intbv,
                   always_seq, always_comb, instances)

from common.rst import rst_sync

class DummyFifo(object):
    def __init__(self, rst, rd_clk, factory, base, inc):
        self.factory = factory
        self.base = base
        self.inc = inc

        self.RD_RST = rst

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
        if self.RD_RST is None:
            rd_rst = None
        else:
            rd_rst = ResetSignal(True, True, False)

            rd_rst_inst = rst_sync(self.RD_CLK, self.RD_RST, rd_rst)

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

class _DummyFifoInternal(object):
    def __init__(self, rst, clk, count = 0, skip = 0):
        self.count = count
        self.skip = skip

        self.rst = rst
        self.clk = clk

        self.strobe = Signal(False)
        self.busy = Signal(False)

    def gen_internal(self):
        self.cur_count = Signal(intbv(0, 0, self.count + 1))
        self.cur_skip = Signal(intbv(0, 0, self.skip + 1))

        self.new_count = Signal(intbv(0, 0, self.count + 1))
        self.new_skip = Signal(intbv(0, 0, self.skip + 1))

        @always_comb
        def comb():
            self.new_count.next = self.cur_count
            self.new_skip.next = self.cur_skip

            if self.cur_skip != 0:
                self.new_skip.next = self.cur_skip - 1

            elif self.cur_count != self.count:
                if self.strobe:
                    self.new_count.next = self.cur_count + 1
                    self.new_skip.next = self.skip

        @always_seq(self.clk.posedge, self.rst)
        def seq():
            self.cur_count.next = self.new_count
            self.cur_skip.next = self.new_skip

        @always_comb
        def busy_comb():
            self.busy.next = 1
            if self.new_count != self.count and self.new_skip == 0:
                self.busy.next = 0

        return instances()

class DummyWriteFifo(_DummyFifoInternal):
    def __init__(self, rst, clk, factory, count = 0, skip = 0):
        _DummyFifoInternal.__init__(self, rst, clk, count, skip)

        self.WR_CLK = clk
        self.WR_RST = rst
        self.WR = Signal(False)
        self.WR_DATA = Signal(factory)
        self.WR_FULL = Signal(True)

    def gen(self):
        internal_inst = self.gen_internal()

        @always_comb
        def comb():
            self.strobe.next = self.WR
            self.WR_FULL.next = self.busy

        return instances()

class DummyReadFifo(_DummyFifoInternal):
    def __init__(self, rst, clk, factory,
                 count = 0, skip = 0,
                 base = 0, increment = 1):
        _DummyFifoInternal.__init__(self, rst, clk, count, skip)

        self.RD_CLK = clk
        self.RD_RST = rst
        self.RD = Signal(False)
        self.RD_DATA = Signal(factory)
        self.RD_EMPTY = Signal(True)

        self.base = base
        self.increment = increment

    def gen(self):
        internal_inst = self.gen_internal()

        value = Signal(intbv(0)[len(self.RD_DATA):])

        @always_comb
        def comb():
            self.strobe.next = self.RD
            self.RD_EMPTY.next = self.busy
            self.RD_DATA.next = self.base + value

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def seq():
            if self.RD:
                value.next = value + self.increment

        return instances()
