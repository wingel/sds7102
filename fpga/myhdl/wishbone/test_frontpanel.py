#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

from myhdl import Signal, ResetSignal, intbv, always, always_comb

from system import System
from timebase import timescale, nsec, usec, msec, sec
from clk import Clk
from rst import rstgen
from frontpanel import frontpanel
from util import rename_interface, mask

def setup(n, prescale):
    insts = []

    clk = Clk(50E6)
    insts.append(clk.gen())

    if 1:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, 100 * nsec, clk))
    else:
        rst = None

    system = System(clk, rst)

    fp_rst = Signal(False)
    fp_clk = Signal(False)
    fp_din = Signal(False)

    fp_dout = Signal(intbv(0)[n:])
    fp_cycle = Signal(False)

    fp = frontpanel
    rename_interface(fp, None)

    return insts, fp, [ system, fp_rst, fp_clk, fp_din, fp_dout, fp_cycle, prescale ]

def test(rst, clk, dout, count= 64):
    n = Signal(intbv(0, 0, count))

    @always (clk.negedge)
    def seq():
        if rst:
            n.next = 0

        elif n == count - 1:
            n.next = 0

        else:
            n.next += 1

    @always_comb
    def comb():
        if n.next % 2 == 1:
            dout.next = 1
        else:
            dout.next = 0

    return seq, comb

def sim():
    from myhdl import Simulation, traceSignals

    insts, test_gen, test_args = setup(n = 5, prescale = 3)

    test_inst = traceSignals(test_gen, *test_args)
    insts.append(test_inst)

    test_inst = test(test_args[1], test_args[2], test_args[3])
    insts.append(test_inst)

    sim = Simulation(*insts)
    sim.run(5 * usec)

def emit():
    from myhdl import toVerilog

    insts, gen, args = setup(n = 64, prescale = 64)

    toVerilog(gen, *args)

    print
    print open('frontpanel.v', 'r').read()

def main():
    import sys

    if 1:
        emit()
        sys.stdout.flush()

    if 1:
        sim()

if __name__ == '__main__':
    main()


