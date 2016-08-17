#! /usr/bin/python
from __future__ import absolute_import

if __name__ == '__main__':
    import hacking
    hacking.run_as_module('simple.test_reg')

import sys

from myhdl import (toVerilog, Simulation, traceSignals,
                   ResetSignal, Signal, intbv, instance, delay,
                   always_seq, always_comb)

from common.timebase import nsec
from common.clk import Clk
from common.rst import rstgen
from common.system import System
from common.util import rename_interface
from common.test_system import create_system

from .mux import Mux
from .reg import Reg, Port, Field, DummyField, RoField, RwField
from .test_bus import sb_write, sb_read

class Harness(object):
    def __init__(self):
        self.duration = 400 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        self.ro = Signal(False)
        self.rw = Signal(intbv(0)[2:])

        self.port1 = Port(4)
        self.port2 = Port(4)

        self.dut = Reg(self.system, 'reg', "A Register", [
            RoField('rofield', "Read Only Field", self.ro),
            RwField('rwfield', "Read/Write Field", self.rw),
            DummyField(1),
            Field('field1', "A Field", self.port1),
            Field('field2', "Another Field", self.port2),
            ])

        self.bus = self.dut.bus()

        @instance
        def master():
            yield delay(199 * nsec)
            yield(sb_read(self.system, self.bus, 0))
            assert self.bus.RD_DATA == 0x1f0
            yield(sb_write(self.system, self.bus, 0, 0x234))
            yield(sb_read(self.system, self.bus, 0))
            assert self.bus.RD_DATA == 0x3c5

        self.stimuli.append(master)

        #  Any parameters you want to have at the top level
        self.args = self.system, self.bus

    def gen(self, system, bus):
        # rename_interface(system, None)
        # rename_interface(bus, None)

        # Expose signals to gtkwave
        CLK = system.CLK
        RST = system.RST
        ADDR = bus.ADDR
        WR = bus.WR
        WR_DATA = bus.WR_DATA
        RD = bus.RD
        RD_DATA = bus.RD_DATA

        insts = []
        insts.append(self.dut.gen())

        val1 = Signal(intbv(0)[self.port1.width:])
        val2 = Signal(intbv(0)[self.port2.width:])

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if self.port1.WR:
                print "port1.WR"
                val1.next = self.port1.WR_DATA
            if self.port1.RD:
                print "port1.RD", val1
                self.port1.RD_DATA.next = ~val1
            else:
                self.port1.RD_DATA.next = 0

            if self.port2.WR:
                print "port2.WR"
                val2.next = self.port2.WR_DATA
            if self.port2.RD:
                print "port2.RD", val2
                self.port2.RD_DATA.next = val2 + 1
            else:
                self.port2.RD_DATA.next = 0
        insts.append(seq)

        @always_comb
        def comb():
            if self.rw:
                self.ro.next = 1
            else:
                self.ro.next = 0
        insts.append(comb)

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
