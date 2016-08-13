#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo.py')

from myhdl import (toVerilog, Simulation, traceSignals, instance, delay,
                   ResetSignal, intbv)

from timebase import nsec
from util import rename_interface
from fifo_async import AsyncFifo, DummyFifo
from clk import Clk
from rst import rstgen

import sys

class Harness(object):
    def __init__(self, fifo_depth = 8, data_width = 8):
        self.duration = 2000 * nsec

        self.stimuli = []

        wr_clk = Clk(37E6)
        self.stimuli.append(wr_clk.gen())

        rd_clk = Clk(100E6)
        self.stimuli.append(rd_clk.gen())

        rst = ResetSignal(True, True, True)
        self.stimuli.append(rstgen(rst, 20 * nsec))

        if 1:
            fifo = AsyncFifo(rst, wr_clk, rd_clk,
                             intbv(0)[data_width:], fifo_depth)
        else:
            fifo = DummyFifo(rst, rd_clk, intbv(0)[data_width:], 1, 2)

        self.dut = fifo

        @instance
        def writer():
            yield delay(50 * nsec)
            yield(wr_clk.posedge)
            v = 0x10
            while 1:
#                print "WR", hex(v)

                if not fifo.WR_FULL:
                    fifo.WR.next = 1
                    fifo.WR_DATA.next = v
                    yield(wr_clk.posedge)
                    fifo.WR.next = 0
                    fifo.WR_DATA.next = 0
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
                if not fifo.RD_EMPTY:
                    yield(delay(1))
                    v = fifo.RD_DATA
                    print "RD", hex(v)
                    fifo.RD.next = 1
                    yield(rd_clk.posedge)
                else:
                    fifo.RD.next = 0
                    yield(rd_clk.posedge)

                if 0:
                    yield delay(49 * nsec)
                    yield(rd_clk.posedge)

        self.stimuli.append(reader)

        # Any parameters you want to have at the top level
        self.args = rst, wr_clk, rd_clk

    def gen(self, reset, wr_clk, rd_clk):
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
