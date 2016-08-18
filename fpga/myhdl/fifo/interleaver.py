#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo.test_fifo')

from myhdl import (Signal, intbv,
                   always_seq, always_comb, instances)

from simple.reg import Reg, RoField

from ._mem import FifoMem

class FifoInterleaver(object):

    """Interleave data from a wide fifo into a narrower fifo"""

    def __init__(self, fifo, parts = 2):
        self.parent = fifo

        self.parts = parts

        assert len(self.parent.RD_DATA) % parts == 0
        self.data_width = len(self.parent.RD_DATA) / parts

        self.RD_CLK = self.parent.RD_CLK
        self.RD_RST = self.parent.RD_RST
        self.RD = Signal(False)
        self.RD_DATA = Signal(intbv(0)[self.data_width:])
        self.RD_EMPTY = Signal(False)

    def extract(self, s, i):
        lo = i * self.data_width
        hi = lo + self.data_width
        @always_comb
        def comb():
            s.next = self.parent.RD_DATA[hi:lo]

        return instances()

    def gen(self):
        idx = Signal(intbv(0, 0, self.parts))

        insts = []

        rd_parts = []
        for i in range(self.parts):
            s = Signal(intbv(0)[self.data_width:])
            insts.append(self.extract(s, i))
            rd_parts.append(s)

        @always_comb
        def comb():
            self.parent.RD.next = 0
            self.RD_DATA.next = rd_parts[idx]
            self.RD_EMPTY.next = self.parent.RD_EMPTY

            if self.RD and idx == self.parts - 1:
                self.parent.RD.next = 1

        @always_seq(self.RD_CLK.posedge, self.RD_RST)
        def seq():
            if self.RD:
                idx.next = 0
                if idx != self.parts - 1:
                    idx.next = idx + 1

        return instances()
