#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_bus')

import sys

from myhdl import toVerilog, Simulation, traceSignals, Signal, intbv, instance, always_seq, delay

from common.timebase import nsec
from common.util import rename_interface
from common.test_system import create_system

from .bus import Bus

class Harness(object):
    def __init__(self, addr_depth, data_width):
        self.duration = 1000 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        self.bus = Bus(addr_depth, data_width)

        @instance
        def master():
            yield delay(99 * nsec)
            yield delay(99 * nsec)
            yield(sb_write(self.system, self.bus, 1, 2))
            yield delay(99 * nsec)
            yield(sb_read(self.system, self.bus, 1))
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

        data = Signal(intbv(0)[bus.data_width:])

        # Create anything you want to be inside the DUT here
        @always_seq(system.CLK.posedge, system.RST)
        def inst():
            if bus.WR:
                data.next = bus.WR_DATA
            if bus.RD:
                bus.RD_DATA.next = data
            else:
                bus.RD_DATA.next = 0

        return inst

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

def sb_write(system, bus, addr, data):
    yield(system.CLK.posedge)
    bus.ADDR.next = addr
    bus.WR.next = 1
    bus.WR_DATA.next = data

    yield(system.CLK.posedge)
    print "sb_write", hex(bus.ADDR), '<-', hex(bus.WR_DATA)

    bus.ADDR.next = 0
    bus.WR.next = 0
    bus.WR_DATA.next = 0

    yield(system.CLK.posedge)

def sb_read(system, bus, addr):
    yield(system.CLK.posedge)
    bus.ADDR.next = addr
    bus.RD.next = 1

    yield(system.CLK.posedge)
    print "sb_read", hex(bus.ADDR)

    bus.ADDR.next = 0
    bus.RD.next = 0

    yield(system.CLK.posedge)

    print "sb_read", hex(bus.ADDR), "->", hex(bus.RD_DATA)

def main():
    if 1:
        Harness(16, 32).emit()

    if 1:
        Harness(8, 16).sim()

if __name__ == '__main__':
    main()
