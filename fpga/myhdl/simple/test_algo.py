#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_algo')

import sys

from myhdl import toVerilog, Simulation, traceSignals, instance, delay

from common.timebase import nsec
from common.util import rename_interface
from common.test_system import create_system

from .algo import Algo
from .test_bus import sb_write, sb_read

class Harness(object):
    def __init__(self, addr_depth, data_width):
        self.duration = 1000 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        self.dut = Algo(self.system, addr_depth, data_width)

        self.bus = self.dut.bus()

        @instance
        def master():
            yield delay(99 * nsec)
            for i in range(5):
                yield delay(99 * nsec)
                yield(sb_read(self.system, self.bus, 1 + i))
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
        Harness(1<<16, 32).emit()

    if 1:
        Harness(1<<8, 16).sim()

if __name__ == '__main__':
    main()
