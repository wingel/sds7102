#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_ram.py')

from myhdl import toVerilog, Simulation, traceSignals, instance, delay

from timebase import nsec
from util import rename_interface
from ram import SimpleRam
from test_system import create_system
from test_bus import sb_write, sb_read

import sys

class Harness(object):
    def __init__(self, addr_depth, data_width):
        self.duration = 1000 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        self.dut = SimpleRam(self.system, addr_depth, data_width)

        self.bus = self.dut.bus()

        @instance
        def master():
            yield delay(99 * nsec)
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_write(self.system, self.bus, i + 1, (i + 1) * 2))
            for i in range(3):
                yield delay(99 * nsec)
                yield(sb_read(self.system, self.bus, i + 1))
                assert self.bus.RD_DATA == (i + 1) * 2
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
        Harness(5, 32).emit()

    if 1:
        Harness(5, 16).sim()

if __name__ == '__main__':
    main()
