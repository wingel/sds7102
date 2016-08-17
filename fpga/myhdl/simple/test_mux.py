#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_mux')

import sys

from myhdl import (ResetSignal, toVerilog, Simulation, traceSignals,
                   instance, delay)

from common.timebase import nsec
from common.clk import Clk
from common.rst import rstgen
from common.system import System
from common.util import rename_interface
from common.test_system import create_system

from .ram import Ram
from .mux import Mux
from .test_bus import sb_write, sb_read

class Harness(object):
    def __init__(self):
        self.duration = 1200 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        self.mux = Mux(self.system)

        self.ram1 = Ram(self.system, 11, 8)
        self.mux.add(self.ram1.bus())

        self.ram2 = Ram(self.system, 5, 16)
        self.mux.add(self.ram2.bus())

        print "ram1.addr", self.ram1.bus().addr
        print "ram2.addr", self.ram2.bus().addr

        self.bus = self.mux.bus()

        @instance
        def master():
            yield delay(99 * nsec)
            # Out of bounds write, just to make sure nothing dies
            yield(sb_write(self.system, self.bus, 10, 0x1234))

            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_write(self.system, self.bus, i + 1, (i + 1) * 2))
                yield(sb_write(self.system, self.bus, i + 17, (i + 1) * 3))

            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_read(self.system, self.bus, i + 1))
                assert self.bus.RD_DATA == (i + 1) * 2
                yield(sb_read(self.system, self.bus, i + 17))
                assert self.bus.RD_DATA == (i + 1) * 3

        self.stimuli.append(master)

        #  Any parameters you want to have at the top level
        self.args = self.system, self.bus

    def gen(self, system, bus):
        rename_interface(system, None)
        rename_interface(bus, None)

        # Expose signals to gtkwave
        CLK = system.CLK
        RST = system.RST
        ADDR = bus.ADDR
        WR = bus.WR
        WR_DATA = bus.WR_DATA
        RD = bus.RD
        RD_DATA = bus.RD_DATA

        insts = []
        insts.append(self.ram1.gen())
        insts.append(self.ram2.gen())
        insts.append(self.mux.gen())

        return insts

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
