#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

from myhdl import Signal, intbv, always, always_seq, always_comb

from wb import WbSlave
from system import System

def frontpanel(system, rst, clk, din, dout, cycle, prescaler = 64):
    cnt = Signal(intbv(0, 0, prescaler))

    clk_reg = Signal(False)

    n = Signal(intbv(0, 0, len(dout)))

    @always_seq(system.CLK.posedge, system.RST)
    def seq():
        if cnt != 0:
            cnt.next = cnt - 1
            return

        cnt.next = prescaler - 1

        if clk_reg:
            clk_reg.next = 0
            clk.next = 0
            return

        clk.next = 1
        clk_reg.next = 1

        dout.next[n] = not din

        if n != len(dout) - 1:
            cycle.next = 0
            rst.next = 0
            n.next = n + 1

        else:
            cycle.next = 1
            rst.next = 1
            n.next = 0

    return seq

class FrontPanel(WbSlave):
    def __init__(self, rst, clk, din, addr_depth, data_width, count = 64, prescaler = 64):
        assert addr_depth & 1 == 0

        super(FrontPanel, self).__init__(addr_depth, data_width)

        self.fp_rst = rst
        self.fp_clk = clk
        self.fp_din = din

        self.count = count

        self.prescaler = prescaler

    def gen(self, bus):
        insts = []

        fp_dout = Signal(intbv(0)[self.count:])
        fp_last = Signal(intbv(0)[self.count:])
        fp_cycle = Signal(False)

        data = [ Signal(intbv(0)[self.count:]) for _ in range(self.addr_depth / 2) ]
        idx = Signal(intbv(0, 0, len(data)))

        system = System(bus.CLK_I, bus.RST_I)

        frontpanel_inst = frontpanel(system,
                                     self.fp_rst, self.fp_clk, self.fp_din,
                                     fp_dout, fp_cycle, self.prescaler)
        insts.append(frontpanel_inst)

        @always_seq(bus.CLK_I.posedge, bus.RST_I)
        def seq():
            if fp_cycle and fp_last != fp_dout:
                data[idx].next = fp_dout
                fp_last.next = fp_dout
                if idx != len(data) - 1:
                    idx.next = idx + 1
                else:
                    idx.next = 0
        insts.append(seq)

        req = Signal(False)

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
            bus.DAT_O.next = intbv(0xdeadbeef)[len(bus.DAT_O):]

            if req:
                if bus.ADR_I < self.addr_depth:
                    bus.ACK_O.next = 1
                else:
                    bus.ERR_O.next = 1

                if 1 or not bus.WE_I and bus.ADR_I < self.addr_depth:
                    if bus.ADR_I & 1:
                        bus.DAT_O.next = data[bus.ADR_I >> 1][64:32]
                    else:
                        bus.DAT_O.next = data[bus.ADR_I >> 1][32:0]
        insts.append(wb_inst)

        return insts
