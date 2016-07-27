#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_simplemux.py')

from myhdl import ResetSignal
from timebase import timescale, nsec, usec, msec, sec
from clk import Clk
from rst import rstgen
from system import System
from simplebus import SimplePort
from simpleram import SimpleRam
from simplemux import SimpleMux

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

    mux = SimpleMux(system)

    ram1 = SimpleRam(system, 5, 16)
    insts.append(ram1.gen(*ram1.args()))
    mux.add(ram1.port())

    ram2 = SimpleRam(system, 11, 32)
    mux.add(ram2.port())
    insts.append(ram2.gen(*ram2.args()))

    return mux.gen, mux.args(), insts

def emit():
    from myhdl import toVerilog

    gen, args, insts = setup()

    print args

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
