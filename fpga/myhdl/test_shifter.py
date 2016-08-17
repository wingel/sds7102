#! /usr/bin/python
if __name__ == '__main__':
    import hacking
    hacking.reexec('test_shifter.py')

import sys

from myhdl import (Signal, ResetSignal, TristateSignal,
                   intbv, always_seq, always_comb, instance)

from common.system import System
from common.clk import Clk
from common.rst import rstgen
from common.timebase import nsec
from common.util import rename_interface

from wb import WbBus, WbMux
from regfile import RegFile, Port, Field, RoField, RwField
from test_wb import wb_write, wb_read
from shifter import Shifter, ShifterBus

def gen(system, wb_bus, shifter_bus):
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

    SCK   = shifter_bus.SCK
    SDO   = shifter_bus.SDO
    SDOE  = shifter_bus.SDOE
    CS    = shifter_bus.CS

    insts = []

    shifter = Shifter(system, shifter_bus, divider = 2, strict_sdoe = 0)
    insts.append(shifter.gen())

    mux = WbMux()
    mux.addr_depth = 4
    mux.data_width = 32
    addr = 0
    for reg in shifter.create_regs():
        mux.add(reg, addr)
        addr += 1

    insts.append(mux.gen(wb_bus))

    return insts

def setup():
    insts = []

    clk = Clk(50E6)
    insts.append(clk.gen())

    if 1:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, 100 * nsec, clk))
    else:
        rst = None

    system = System(clk, rst)

    bus = WbBus(system, addr_depth = 10, data_width = 32)
    rename_interface(bus, None)

    shifter_bus = ShifterBus(num_cs = 4)

    return insts, gen, [ system, bus, shifter_bus ]

def sim():
    from myhdl import Simulation, traceSignals, instance, delay

    insts, gen, args = setup()

    wb_bus = args[1]

    insts.append(traceSignals(gen, *args))

    cs = (1<<1)
    cpol = 0
    cpha = 0
    pulse = 1

    @instance
    def test():
        yield delay(149 * nsec)
        yield(wb_read(wb_bus, 0))
        yield(delay(29 * nsec))
        yield(wb_write(wb_bus, 0, 0x0000025))
        yield(delay(29 * nsec))
        yield(wb_read(wb_bus, 0))
        yield(delay(29 * nsec))
        yield(wb_write(wb_bus, 1,
                       6 | (cpha<<8) | (cpol<<9) | (pulse<<10) | (cs<<16)))

        while 1:
            yield(delay(29 * nsec))
            yield(wb_read(wb_bus, 1))

    insts.append(test)

    sim = Simulation(insts)
    sim.run(1500 * nsec)
    print
    sys.stdout.flush()

def emit():
    from myhdl import toVerilog

    insts, gen, args = setup()

    toVerilog(gen, *args)

    print
    print open('gen.v', 'r').read()
    print
    sys.stdout.flush()

def main():
    sim()
    emit()

if __name__ == '__main__':
    main()
