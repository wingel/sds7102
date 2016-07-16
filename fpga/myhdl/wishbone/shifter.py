#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('shifter.py')

import sys

from myhdl import Signal, intbv, enum, always_seq, always_comb

from system import System
from wb import WbSlaveInterface
from clk import Clk
from rst import rstgen
from timebase import nsec
from regfile import RegFile, Port, Field, RoField, RwField, DummyField
from util import rename_interface

class ShifterBus(object):
    def __init__(self, num_cs):
        self.SCK = Signal(False)
        self.SDO = Signal(False)
        self.SDOE = Signal(False)
        self.CS = Signal(intbv(0)[num_cs:])

class Shifter(object):
    def __init__(self, system, bus, divider, width = 32, strict_sdoe = True):
        self.system = system
        self.bus = bus

        self.states = enum(
            "IDLE", "START", "PRE", "FIRST", "SECOND", "POST", "PULSE")
        self.state = Signal(self.states.IDLE)

        self.divider = divider
        self.strict_sdoe = strict_sdoe

        self.data_reg = Signal(intbv(0)[width:])

        self.count = Signal(intbv(0)[8:])
        self.count_port = Port(self.count.val)
        self.cpha_reg = Signal(False)
        self.cpol_reg = Signal(False)
        self.pulse_reg = Signal(False)
        self.cs_reg = Signal(self.bus.CS.val)

        self.div_val = Signal(intbv(0, 0, self.divider + 1))

    def create_regs(self):
        return [
            RegFile('data', "Shifter Data", [
            RwField(self.system, 'data', "Read/Write Field", self.data_reg),
            ]),

            RegFile('ctl', "Shifter Control", [
            Field(self.system, 'count', "Number of bits to shift out", self.count_port),
            RwField(self.system, 'cpha', "CPHA", self.cpha_reg),
            RwField(self.system, 'cpol', "CPOL", self.cpol_reg),
            RwField(self.system, 'pulse', "Nonzero if the chip should be a pulse after all bits have been shifted out", self.pulse_reg),
            DummyField('reserved', 'Must be zero', 5),
            RwField(self.system, 'cs', "Chip select", self.cs_reg),
            ]),
        ]

    def gen(self):
        @always_seq (self.system.CLK.posedge, self.system.RST)
        def seq():
            self.div_val.next = self.divider

            if self.state == self.states.IDLE:
                if self.count_port.STB and self.count_port.WE:
                    self.count.next = self.count_port.DAT_I

                    self.state.next = self.states.START

            elif self.state == self.states.START:
                self.state.next = self.states.PRE
                self.bus.SCK.next = 0 ^ self.cpol_reg

            elif self.div_val:
                self.div_val.next = self.div_val - 1

            elif self.state == self.states.PRE:
                self.bus.SCK.next = 0 ^ self.cpol_reg

                if not self.pulse_reg:
                    self.bus.CS.next = self.cs_reg

                if not self.cpha_reg:
                    if self.count:
                        self.count.next = self.count - 1

                if not self.cpha_reg or not self.strict_sdoe:
                    if self.count:
                        self.bus.SDO.next = self.data_reg[self.count - 1]
                        self.bus.SDOE.next = 1
                    else:
                        self.bus.SDOE.next = 0

                if self.count:
                    self.state.next = self.states.FIRST
                else:
                    self.state.next = self.states.POST

            elif self.state == self.states.FIRST:
                self.bus.SCK.next = 1 ^ self.cpol_reg

                if self.cpha_reg:
                    if self.count != 0:
                        self.bus.SDO.next = self.data_reg[self.count - 1]
                        self.bus.SDOE.next = 1
                        self.count.next = self.count - 1
                    else:
                        if self.strict_sdoe:
                            self.bus.SDOE.next = 0

                self.state.next = self.states.SECOND

            elif self.state == self.states.SECOND:
                self.bus.SCK.next = 0 ^ self.cpol_reg

                if not self.cpha_reg:
                    if self.count != 0:
                        self.bus.SDO.next = self.data_reg[self.count - 1]
                        self.count.next = self.count - 1
                    else:
                        if self.strict_sdoe:
                            self.bus.SDOE.next = 0

                if self.count:
                    self.state.next = self.states.FIRST
                else:
                    self.state.next = self.states.POST

            elif self.state == self.states.POST and self.pulse_reg:
                self.bus.CS.next = self.cs_reg

                self.state.next = self.states.PULSE

            else:
                self.bus.SCK.next = 0 ^ self.cpol_reg
                self.bus.CS.next = 0
                self.bus.SDOE.next = 0
                self.state.next = self.states.IDLE

        @always_comb
        def comb():
            self.count_port.DAT_O.next = self.count

        return seq, comb

if __name__ == '__main__':
    from test_shifter import main
    main()
