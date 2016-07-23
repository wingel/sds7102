#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

import sys
from myhdl import (Signal, ResetSignal, intbv,
                   always, always_comb, instance, delay)

from timebase import timescale, nsec, usec, msec, sec
from system import System
from clk import Clk
from rst import rstgen
from wb import WbBus, WbMux
from util import rename_interface, mask
from test_wb import wb_write, wb_read
from frontpanel import FrontPanel

def fake_panel(rst, clk, dout, nr_keys):
    print "fake_panel", type(rst), type(clk), type(dout), type(nr_keys)

    insts = []

    keys = Signal(intbv(0)[nr_keys:])

    n = Signal(intbv(0, 0, nr_keys))

    @instance
    def src():
        yield delay(1234 * nsec)
        keys.next[0] = 1
        yield delay(1234 * nsec)
        keys.next[0] = 0

        yield delay(1234 * nsec)
        keys.next[nr_keys - 1] = 1
        yield delay(1234 * nsec)
        keys.next[nr_keys - 1] = 0

        yield delay(1234 * nsec)
        keys.next[nr_keys / 2] = 1
        yield delay(1234 * nsec)
        keys.next[nr_keys / 2] = 0

    insts.append(src)

    @always (clk.negedge)
    def seq():
        if rst:
            n.next = 0

        elif n == nr_keys - 1:
            n.next = 0

        else:
            n.next += 1
    insts.append(seq)

    @always_comb
    def comb():
        if rst:
            dout.next = not keys[0]
        else:
            dout.next = not keys[n]
    insts.append(comb)

    return insts

def gen(system, wb_bus, fp_rst, fp_clk, fp_din, fp_init, nr_keys, prescaler):
    # Make signals visible in simulation
    RST_I = wb_bus.RST_I
    CLK_I = wb_bus.CLK_I
    CYC_I = wb_bus.CYC_I
    STB_I = wb_bus.STB_I
    WE_I  = wb_bus.WE_I
    ACK_O = wb_bus.ACK_O
    ADR_I = wb_bus.ADR_I
    DAT_I = wb_bus.DAT_I
    DAT_O = wb_bus.DAT_O

    insts = []

    frontpanel = FrontPanel(system, fp_rst, fp_clk, fp_din, fp_init, 5, 32, nr_keys, prescaler, ts_width = 8)
    insts.append(frontpanel.gen(wb_bus))

    return insts

def setup(nr_keys, prescaler):
    insts = []

    clk = Clk(50E6)
    insts.append(clk.gen())

    if 1:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, 100 * nsec, clk))
    else:
        rst = None

    system = System(clk, rst)

    wb_bus = WbBus(system, addr_depth = 10, data_width = 32)
    rename_interface(wb_bus, None)

    fp_rst = Signal(False)
    fp_clk = Signal(False)
    fp_din = Signal(False)
    fp_init = Signal(False)

    return insts, gen, [ system, wb_bus, fp_rst, fp_clk, fp_din, fp_init, nr_keys, prescaler ]

def sim():
    from myhdl import Simulation, traceSignals, instance, delay

    insts, gen, args = setup(nr_keys = 5, prescaler = 2)

    wb_bus = args[1]

    insts.append(traceSignals(gen, *args))

    if 1:
        fake_panel_inst = fake_panel(args[2], args[3], args[4], args[6])
        insts.append(fake_panel_inst)

    cs = (1<<1)
    cpol = 0
    cpha = 0
    pulse = 1

    @instance
    def test():
        yield delay(2999 * nsec)
        yield(wb_read(wb_bus, 0))

        while 1:
            yield(delay(999 * nsec))
            yield(wb_read(wb_bus, 1))

    insts.append(test)

    sim = Simulation(insts)
    sim.run(15000 * nsec)
    print
    sys.stdout.flush()

def emit():
    from myhdl import toVerilog

    insts, gen, args = setup(nr_keys = 64, prescaler = int(50E6 / 300E3 / 3))

    toVerilog(gen, *args)

    print
    print open('gen.v', 'r').read()
    print
    sys.stdout.flush()

def main():
    if 1:
        emit()
        sys.stdout.flush()

    if 1:
        sim()

if __name__ == '__main__':
    main()
