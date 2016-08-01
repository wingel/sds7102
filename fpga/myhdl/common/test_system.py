#! /usr/bin/python
from timebase import nsec
from myhdl import ResetSignal
from clk import Clk
from rst import rstgen
from system import System

def create_system(clk_freq = 100E6, reset_duration = 99 * nsec):
    insts = []

    clk = Clk(clk_freq)
    insts.append(clk.gen())

    if reset_duration is None:
        rst = None
    else:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, reset_duration, clk))

    system = System(clk, rst)

    return system, insts
