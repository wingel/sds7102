#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('image.py')

from pprint import pprint

from myhdl import (Signal, TristateSignal, ConcatSignal,
                   intbv, always_comb, always_seq)
from rhea.cores.misc import syncro

from spartan6 import startup_spartan6, bufg

from system import System
from spi_slave import SpiInterface, SpiSlave
from wb import WbMux
from hybrid_counter import HybridCounter
from util import tristate

def top(din, init_b, cclk,
        bank0, bank1, bank2, bank3):
    insts = []

    # Clock generator using STARTUP_SPARTAN primitive
    clk_unbuf = Signal(False)
    clk_unbuf_inst = startup_spartan6('startup_inst', cfgmclk = clk_unbuf)
    insts.append(clk_unbuf_inst)

    clk_buf = Signal(False)
    clk_inst = bufg('bufg_clk', clk_unbuf, clk_buf)
    insts.append(clk_inst)

    system = System(clk_buf, None)

    mux = WbMux()

    # Rename and adapt external SPI bus signals
    slave_spi_bus = SpiInterface()
    slave_cs = Signal(False)
    slave_cs_inst = syncro(clk_buf, din, slave_spi_bus.CS)
    insts.append(slave_cs_inst)
    slave_sck_inst = syncro(clk_buf, cclk, slave_spi_bus.SCK)
    insts.append(slave_sck_inst)
    slave_sdioinst = tristate(init_b,
                              slave_spi_bus.SD_I,
                              slave_spi_bus.SD_O, slave_spi_bus.SD_OE)
    insts.append(slave_sdioinst)

    ####################################################################
    # Random stuff

    if 1:
        pins = ConcatSignal(cclk, bank3, bank2, bank1, bank0)
        hc = HybridCounter()
        mux.add(hc, 0, pins)

    wb_slave = mux

    # Create the wishbone bus
    wb_bus = wb_slave.create_bus()
    wb_bus.CLK_I = clk_buf
    wb_bus.RST_I = None

    # Create the SPI slave
    spi = SpiSlave()
    spi.addr_width = 32
    spi.data_width = 32

    wb_inst = wb_slave.gen(wb_bus)
    insts.append(wb_inst)

    slave_spi_inst = spi.gen(slave_spi_bus, wb_bus)
    insts.append(slave_spi_inst)

    return insts

def impl():
    from rhea.build.boards import get_board

    brd = get_board('sds7102')
    flow = brd.get_flow(top = top)
    flow.run()
    info = flow.get_utilization()
    pprint(info)

if __name__ == '__main__':
    impl()
