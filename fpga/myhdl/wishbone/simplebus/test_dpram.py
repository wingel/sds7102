#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_dpram.py')

from myhdl import toVerilog, Simulation, traceSignals, instance, delay

from timebase import nsec
from util import rename_interface
from dpram import SimpleDpRam
from test_system import create_system
from test_bus import sb_write, sb_read

import sys

class Harness(object):
    def __init__(self, addr_depth, data_width):
        self.duration = 2000 * nsec

        self.stimuli = []

        self.system0, system0_inst = create_system()
        self.stimuli.append(system0_inst)

        self.system1, system1_inst = create_system()
        self.stimuli.append(system1_inst)

        self.dut = SimpleDpRam(self.system0, self.system1,
                               addr_depth, data_width)

        self.bus0 = self.dut.bus0()
        self.bus1 = self.dut.bus1()

        @instance
        def master():
            yield delay(99 * nsec)
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_write(self.system0, self.bus0, i + 1, (i + 1) * 2))
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_read(self.system1, self.bus1, i + 1))
                assert self.bus1.RD_DATA == (i + 1) * 2
            yield delay(99 * nsec)
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_write(self.system1, self.bus1, i + 1, (i + 7) * 2))
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_read(self.system0, self.bus0, i + 1))
                assert self.bus0.RD_DATA == (i + 7) * 2
        self.stimuli.append(master)

        #  Any parameters you want to have at the top level
        self.args = self.system0, self.system1, self.bus0, self.bus1

    def gen(self, system0, system1, bus0, bus1):
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
        Harness(5, 32).emit()

    if 1:
        Harness(5, 16).sim()

if __name__ == '__main__':
    main()
