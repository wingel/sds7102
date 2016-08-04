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

    """Module for the SDS7102 front panel.

    The rotary encoders are very noisy.  They are the first 16
    switches scanned by the front panel, so add an overscan mode where
    the first 16 switches are scanned four times for each time all the
    rest of the buttons are scanned.

    When a switch is closed there is a hard pulldown to ground which
    is quite fast.  The pull-up is slower, probably due to capacitance
    on the front panel PCB.  Stretch the active pulses (which are
    active low on the input, but active high internally in the
    frontpanel scanner) so that this is hidden from the user.

    These two together make the frontpanel decently useful.  There are
    still false movements of the rotary encoders, but it's not too
    bad.  Higher level code will have to handle acceleration anyway
    and if it does it should just ignore occasional reversals of
    direction when the rotation speed is high."""

    def __init__(self, system, fp_rst, fp_clk, fp_din,
                 fifo_depth = 64,
                 data_width = 32,
                 nr_keys = 64,
                 ts_width = 16,
                 prescaler = 400,
                 nr_overscan_keys = 16, overscan_ratio = 16,
                 stretch = 7):
        self.system = system

        self.fp_rst = fp_rst
        self.fp_clk = fp_clk
        self.fp_din = fp_din

        self.nr_keys = nr_keys

        self.prescaler = prescaler
        self.nr_overscan_keys = nr_overscan_keys
        self.overscan_ratio = overscan_ratio
        self.stretch = stretch

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

        self.ctl_reg = SimpleReg(system, 'fp_ctl', "Frontpanel Control", [
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

        overscan_cnt = Signal(intbv(0, 0, self.overscan_ratio))

        rst = Signal(False)
        clk = Signal(False)

        idx = Signal(intbv(0, 0, self.nr_keys))

        elem = self.packer.create()
        packed = self.packer.pack(elem)

        first = Signal(False)
        last = Signal(intbv(0)[self.nr_keys:])

        stretch = [ Signal(intbv(0, 0, self.stretch + 1))
                    for _ in range(self.nr_keys) ]

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

                overscan_cnt.next = 0

                for i in range(len(stretch)):
                    stretch[i].next = 0

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

                            if (idx == self.nr_keys - 1 or
                                (overscan_cnt != 0 and
                                 idx == self.nr_overscan_keys - 1)):
                                rst.next = 1
                                idx.next = 0
                                first.next = 0
                                self.ts.next = self.ts + 1

                                if overscan_cnt:
                                    overscan_cnt.next = overscan_cnt - 1
                                else:
                                    overscan_cnt.next = self.overscan_ratio - 1

                            else:
                                rst.next = 0
                                idx.next = idx + 1

                            if stretch[elem.key] != 0:
                                stretch[elem.key].next = stretch[elem.key] - 1
                            elif first or last[elem.key] != elem.pressed:
                                last.next[elem.key] = elem.pressed

                                self.fifo[self.fifo_head].next = packed
                                self.fifo_head.next = next_head

                            if elem.pressed:
                                stretch[elem.key].next = self.stretch

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

        return insts
