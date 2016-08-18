#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('scope.test_renderer')

import sys

from myhdl import (ResetSignal, toVerilog, Simulation, traceSignals,
                   instance, delay, instances)

from common.timebase import nsec
from common.clk import Clk
from common.rst import rstgen

from .renderer import Renderer

duration = 1000 * nsec

rst = ResetSignal(True, True, False)
clk = Clk(100E6)

args = [ rst, clk ]

def gen(rst, clk):
    global renderer

    renderer = Renderer(rst, clk,
                        num_samples = 2, sample_width = 4,
                        num_accumulators = 1<<4,
                        accumulator_width = 8)
    renderer_inst = renderer.gen()

    return instances()

def stimuli():
    clk_inst = clk.gen()
    rstgen_inst = rstgen(rst, 33 * nsec, clk)

    @instance
    def inst():
        yield delay(100 * nsec)

        yield clk.posedge
        renderer.samples[0].next = 3
        renderer.samples[1].next = 7
        renderer.strobe.next = 1
        yield clk.posedge
        renderer.samples[0].next = 0
        renderer.samples[1].next = 0
        renderer.strobe.next = 0

        yield clk.posedge
        renderer.samples[0].next = 7
        renderer.samples[1].next = 4
        renderer.strobe.next = 1
        yield clk.posedge
        renderer.samples[0].next = 0
        renderer.samples[1].next = 0
        renderer.strobe.next = 0

    return instances()

def emit():
    toVerilog(gen, *args)
    print open('gen.v', 'r').read()
    sys.stdout.flush()

def sim():
    insts = []
    insts.append(traceSignals(gen, *args))
    insts.append(stimuli())
    sim = Simulation(insts)
    sim.run(duration)
    print
    sys.stdout.flush()

def main():
    if 1:
        emit()

    if 1:
        sim()

if __name__ == '__main__':
    main()
