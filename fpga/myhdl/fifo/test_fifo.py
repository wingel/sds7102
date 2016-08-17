#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('fifo.test_fifo')

import sys

from myhdl import (toVerilog, Simulation, traceSignals, instance, delay,
                   ResetSignal, intbv)

from common.timebase import nsec
from common.util import rename_interface
from common.clk import Clk
from common.rst import rstgen

from .sync import SyncFifo
from .async import AsyncFifo
from .dummy import DummyFifo, DummyWriteFifo, DummyReadFifo

class Harness(object):
    def __init__(self, fifo_depth = 8, data_width = 8):
        self.duration = 2000 * nsec

        self.stimuli = []

        rd_clk = Clk(100E6)
        self.stimuli.append(rd_clk.gen())
        wr_clk = rd_clk

        rst = ResetSignal(True, True, False)
        self.stimuli.append(rstgen(rst, 20 * nsec, rd_clk))

        if 0:
            rd_clk = Clk(37E6)
            self.stimuli.append(rd_clk.gen())

            fifo = AsyncFifo(rst, wr_clk, rd_clk,
                             intbv(0)[data_width:], fifo_depth)

        elif 1:
            rd_fifo = SyncFifo(rst, rd_clk, intbv(0)[data_width:], fifo_depth)
            wr_fifo = rd_fifo

            self.dut = wr_fifo

        elif 1:
            rd_fifo = DummyReadFifo(rst, rd_clk, intbv(0)[data_width:],
                                    count = 4, skip = 1,
                                    base = 1, increment = 2)

            wr_fifo = DummyWriteFifo(rst, wr_clk, intbv(0)[data_width:],
                                     count = 3, skip = 2)

            self.dut = wr_fifo

        else:
            fifo = DummyFifo(rst, rd_clk, intbv(0)[data_width:], 1, 2)

        @instance
        def writer():
            yield delay(50 * nsec)
            yield(wr_clk.posedge)
            v = 0x10
            while 1:
#                print "WR", hex(v)

                if not wr_fifo.WR_FULL:
                    wr_fifo.WR.next = 1
                    wr_fifo.WR_DATA.next = v
                    yield(wr_clk.posedge)
                    wr_fifo.WR.next = 0
                    wr_fifo.WR_DATA.next = 0
                    v += 1
                else:
                    yield(wr_clk.posedge)

                if 0:
                    yield delay(49 * nsec)
                    yield(wr_clk.posedge)

                if v == 0x20:
                    break

        self.stimuli.append(writer)

        @instance
        def reader():
            yield delay(400 * nsec)
            yield(rd_clk.posedge)
            while 1:
                if not rd_fifo.RD_EMPTY:
                    yield(delay(1))
                    v = rd_fifo.RD_DATA
                    print "RD", hex(v)
                    rd_fifo.RD.next = 1
                    yield(rd_clk.posedge)
                else:
                    rd_fifo.RD.next = 0
                    yield(rd_clk.posedge)

                if 0:
                    yield delay(49 * nsec)
                    yield(rd_clk.posedge)

        self.stimuli.append(reader)

        # Any parameters you want to have at the top level
        self.args = rst, rd_clk, wr_clk

    def gen(self, rst, rd_clk, wr_clk):
        # Create anything you want to be inside the DUT here
        return self.dut.gen()

    def emit(self):
        toVerilog(self.gen, *self.args)
        print open('gen.v', 'r').read()
        sys.stdout.flush()

    def sim(self):
        insts = []

        insts.append(traceSignals(self.gen, *self.args))
        insts += self.stimuli

        sim = Simulation(insts)
        sim.run(self.duration)
        print
        sys.stdout.flush()

def main():
    if 1:
        Harness().emit()

    if 1:
        Harness().sim()

if __name__ == '__main__':
    main()
