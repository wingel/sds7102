#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

from myhdl import Signal, intbv, always, always_seq, always_comb

from wb import WbSlave
from system import System
from util import Packer

class Entry(object):
    def __init__(self, nr_keys = 64, ts_width = 10):
        self.key = Signal(intbv(0, 0, nr_keys))
        self.pressed = Signal(False)
        self.ts = Signal(intbv(0)[ts_width:])

class FrontPanel(WbSlave):
    def __init__(self, system, rst, clk, din, init, addr_depth, data_width,
                 nr_keys = 64, prescaler = 64, ts_width = 10):
        print "FrontPanel", rst, clk, din
        print addr_depth, data_width, nr_keys, prescaler, ts_width

        super(FrontPanel, self).__init__(addr_depth, data_width)

        self.system = system

        self.fp_rst = rst
        self.fp_clk = clk
        self.fp_din = din
        self.fp_init = init

        self.nr_keys = nr_keys
        self.prescaler = prescaler

        self.ts = Signal(intbv(0)[ts_width:])

        self.packer = Packer(Entry, nr_keys = nr_keys, ts_width = ts_width)

        self.fifo = [ Signal(intbv(0)[len(self.packer):])
                      for _ in range(self.addr_depth) ]
        self.fifo_head = Signal(intbv(0, 0, len(self.fifo)))
        self.fifo_tail = Signal(intbv(0, 0, len(self.fifo)))

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
                self.ts.next = 0
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

    def gen(self, bus):
        insts = []

        system = System(bus.CLK_I, bus.RST_I)

        scanner_inst = self.gen_scanner()
        insts.append(scanner_inst)

        tail_value = Signal(intbv(0)[len(self.packer):])

        elem = self.packer.create()
        unpack_inst = self.packer.unpack(tail_value, elem)
        insts.append(unpack_inst)

        ts_shift = self.data_width - len(self.ts)

        req = Signal(False)

        @always_comb
        def tail_value_inst():
            tail_value.next = self.fifo[self.fifo_tail]
        insts.append(tail_value_inst)

        @always_comb
        def req_inst():
            req.next = (bus.CYC_I and bus.STB_I and
                        not bus.ACK_O and not bus.ERR_O and not bus.RTY_O)
        insts.append(req_inst)

        @always_seq(bus.CLK_I.posedge, bus.RST_I)
        def wb_inst():
            bus.ACK_O.next = 0
            bus.ERR_O.next = 0
            bus.RTY_O.next = 0
            # bus.DAT_O.next = intbv(0xdeadbeef)[len(bus.DAT_O):]

            if req:
                bus.ACK_O.next = 1

            if req and not bus.WE_I:
                if self.fifo_tail == self.fifo_head:
                    bus.DAT_O.next = self.ts << ts_shift

                else:
                    bus.DAT_O.next = ((elem.ts << ts_shift) |
                                      (1 << 9) |
                                      (elem.pressed << 8) |
                                      (elem.key))

                    self.fifo_tail.next = 0
                    if self.fifo_tail != len(self.fifo) - 1:
                        self.fifo_tail.next = self.fifo_tail + 1

        insts.append(wb_inst)

        return insts
