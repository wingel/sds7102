#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

from myhdl import Signal, intbv, always, always_seq, always_comb

from util import Packer
from simplebus import SimpleBus, SimpleReg, Port, Field, DummyField, RwField

class Entry(object):
    def __init__(self, nr_keys, ts_width):
        self.key = Signal(intbv(0, 0, nr_keys))
        self.pressed = Signal(False)
        self.ts = Signal(intbv(0)[ts_width:])

class FrontPanel(object):
    def __init__(self, system, fp_rst, fp_clk, fp_din, fp_green, fp_white,
                 fifo_depth = 256, data_width = 32,
                 nr_keys = 64, ts_width = 10, prescaler = 400):
        self.system = system

        self.fp_rst = fp_rst
        self.fp_clk = fp_clk
        self.fp_din = fp_din

        self.fp_green = fp_green
        self.fp_white = fp_white

        self.nr_keys = nr_keys

        self.prescaler = prescaler

        self.ts = Signal(intbv(0)[ts_width:])

        self.packer = Packer(Entry, nr_keys = nr_keys, ts_width = ts_width)

        self.fifo = [ Signal(intbv(0)[len(self.packer):])
                      for _ in range(fifo_depth) ]
        self.fifo_head = Signal(intbv(0, 0, len(self.fifo)))
        self.fifo_tail = Signal(intbv(0, 0, len(self.fifo)))

        self.fp_init = Signal(False)

        self.key_code = Port(((nr_keys-1).bit_length() + 7) & ~7)
        self.key_pressed = Port(1)
        self.key_valid = Port(1)
        self.key_ts = Port(ts_width)

        self._bus = None

        self.fp_green_tmp = Signal(False)
        self.fp_white_tmp = Signal(False)

        self.ctl_reg = SimpleReg(system, 'fp_ctl', "Frontpanel Control", [
            RwField('red', "Red LED", self.fp_green_tmp),
            RwField('white', "White LED", self.fp_white_tmp),
            DummyField(6),
            RwField('init', "Initialize frontpanel when true", self.fp_init),
            ])

        self.data_reg = SimpleReg(system, 'fp_data', "Frontpanel Data", [
            Field('key', "Keycode", self.key_code),
            Field('pressed', "Key pressed", self.key_pressed),
            Field('valid', "Key valid", self.key_valid),
            DummyField(6),
            Field('ts', "Key Timestamp", self.key_ts),
            ])

        self.ctl_bus = self.ctl_reg.bus()

        self.data_bus = self.data_reg.bus()

    def gen_scanner(self):
        insts = []

        cnt = Signal(intbv(0, 0, self.prescaler))

        rst = Signal(False)
        clk = Signal(False)

        idx = Signal(intbv(0, 0, self.nr_keys))

        elem = self.packer.create()
        packed = self.packer.pack(elem)

        first = Signal(False)
        last = Signal(intbv(0)[self.nr_keys:])

        ready = Signal(False)

        @always_comb
        def scanner_comb():
            self.fp_rst.next = rst
            self.fp_clk.next = clk
        insts.append(scanner_comb)

        @always_seq(self.system.CLK.posedge, self.system.RST)
        def scanner_seq():
            elem.key.next = idx
            elem.pressed.next = not self.fp_din
            elem.ts.next = self.ts

            if self.fp_init or not ready:
                ready.next = 1
                first.next = 1

                rst.next = 1
                idx.next = 0
                cnt.next = self.prescaler - 1
                clk.next = 1
                self.ts.next = 1
                self.fifo_head.next = self.fifo_tail

            else:
                next_head = 0
                if self.fifo_head != len(self.fifo) - 1:
                    next_head = self.fifo_head + 1

                if next_head != self.fifo_tail:
                    if cnt != 0:
                        cnt.next = cnt - 1

                    else:
                        cnt.next = self.prescaler - 1

                        if clk:
                            clk.next = 0
                        else:
                            clk.next = 1

                            if idx != self.nr_keys - 1:
                                rst.next = 0
                                idx.next = idx + 1

                            else:
                                rst.next = 1
                                idx.next = 0
                                first.next = 0
                                self.ts.next = self.ts + 1

                            if first or last[elem.key] != elem.pressed:
                                last.next[elem.key] = elem.pressed

                                self.fifo[self.fifo_head].next = packed
                                self.fifo_head.next = next_head

        insts.append(scanner_seq)

        return insts

    def gen(self):
        system = self.system

        insts = []

        scanner_inst = self.gen_scanner()
        insts.append(scanner_inst)

        tail_value = Signal(intbv(0)[len(self.packer):])

        elem = self.packer.create()
        unpack_inst = self.packer.unpack(tail_value, elem)
        insts.append(unpack_inst)

        req = Signal(False)

        insts.append(self.ctl_reg.gen())
        insts.append(self.data_reg.gen())

        @always_comb
        def tail_value_inst():
            tail_value.next = self.fifo[self.fifo_tail]
        insts.append(tail_value_inst)

        @always_seq(system.CLK.posedge, system.RST)
        def data_inst():
            self.key_code.RD_DATA.next = 0
            self.key_pressed.RD_DATA.next = 0
            self.key_valid.RD_DATA.next = 0
            self.key_ts.RD_DATA.next = 0

            if self.key_code.RD:
                if self.fifo_tail == self.fifo_head:
                    self.key_ts.RD_DATA.next = self.ts

                else:
                    self.key_code.RD_DATA.next = elem.key
                    self.key_pressed.RD_DATA.next = elem.pressed
                    self.key_valid.RD_DATA.next = 1
                    self.key_ts.RD_DATA.next = elem.ts

                    self.fifo_tail.next = 0
                    if self.fifo_tail != len(self.fifo) - 1:
                        self.fifo_tail.next = self.fifo_tail + 1

        insts.append(data_inst)

        @always_comb
        def led_inst():
            self.fp_green.next = self.fp_green_tmp
            self.fp_white.next = self.fp_white_tmp
        insts.append(led_inst)

        return insts
