#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_simplealgo.py')

from myhdl import ResetSignal
from timebase import timescale, nsec, usec, msec, sec
from clk import Clk
from rst import rstgen
from system import System
from simplebus import SimplePort
from simplealgo import SimpleAlgo

def setup():
    insts = []

    clk = Clk(100E6)
    insts.append(clk.gen())

    if 1:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, 100 * nsec, clk))
    else:
        rst = None

    system = System(clk, rst)

    ram = SimpleAlgo(system, 1<<16, 32)
    return ram.gen, ram.args(), []

def emit():
    from myhdl import toVerilog

    gen, args, insts = setup()

    toVerilog(gen, *args)

    print
    print open('gen.v', 'r').read()

def main():
    import sys

    if 1:
        emit()
        sys.stdout.flush()

    if 0:
        sim()

if __name__ == '__main__':
    main()
