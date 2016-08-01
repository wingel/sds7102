#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_ddr.py')

from myhdl import Signal, ResetSignal, intbv, instance, delay, SignalType

from timebase import timescale, nsec, usec, msec, sec
from system import System
from ddr import Ddr, DdrBus, ddr_connect
from simplebus import SimpleAlgo
from clk import Clk
from rst import rstgen
from util import rename_interface, mask

def setup(addr_depth = 1024, data_width = 16):
    insts = []

    clk = Clk(100E6)
    insts.append(clk.gen())

    if 1:
        rst = ResetSignal(0, active = 1, async = 0)
        insts.append(rstgen(rst, 100 * nsec, clk))
    else:
        rst = None

    system = System(clk, rst)

    bus = DdrBus(2, 12, 2)
    rename_interface(bus, None)

    sa = SimpleAlgo(system, 24, 32)
    sa_inst = sa.gen()
    insts.append(sa_inst)

    ddr = Ddr()

    return insts, ddr.gen, [ system, bus, sa.bus() ]

def reader(system, bus, n, interval):
    @instance
    def inst():
        yield delay(200 * nsec)

        addr = Signal(intbv(0x10)[len(bus.A):])

        while 1:
            yield system.CLK.posedge

            bus.CS_B.next = 0
            bus.RAS_B.next = 0
            bus.A.next = 0x4
            bus.BA.next = 0x2

            yield system.CLK.posedge

            bus.CS_B.next = 1
            bus.RAS_B.next = 1
            bus.A.next = ~0 & mask(bus.A)
            bus.BA.next = ~0 & mask(bus.BA)

            yield system.CLK.posedge

            bus.CS_B.next = 0
            bus.CAS_B.next = 0
            bus.A.next = addr
            bus.BA.next = 0

            yield system.CLK.posedge

            bus.CS_B.next = 1
            bus.CAS_B.next = 1
            bus.A.next = ~0 & mask(bus.A)
            bus.BA.next = ~0 & mask(bus.BA)

            addr.next = 0
            if addr != n - 1:
                addr.next = addr + 4

            yield system.CLK.posedge

            bus.CS_B.next = 0
            bus.CAS_B.next = 0
            bus.A.next = addr

            yield system.CLK.posedge

            bus.CS_B.next = 1
            bus.CAS_B.next = 1
            bus.A.next = ~0 & mask(bus.A)

            addr.next = 0
            if addr != n - 1:
                addr.next = addr + 4

            yield delay(interval - 1)

    return inst

def sim():
    from myhdl import Simulation, traceSignals

    insts, test_gen, test_args = setup()

    test_inst = traceSignals(test_gen, *test_args)
    insts.append(test_inst)

    if 1:
        reader_inst = reader(test_args[0], test_args[1], 64, 123 * nsec)
        insts.append(reader_inst)

    sim = Simulation(*insts)
    sim.run(5 * usec)

def emit():
    from myhdl import toVerilog

    insts, gen, args = setup()

    toVerilog(gen, *args)

    print
    print open('gen.v', 'r').read()

def emit_connect():
    from myhdl import toVerilog

    bus = DdrBus(2, 12, 2)
    rename_interface(bus, 'bus')

    soc_clk = Signal(False)
    soc_clk_b = Signal(False)

    soc_cs = Signal(False)
    soc_ras = Signal(False)
    soc_cas = Signal(False)
    soc_we = Signal(False)
    soc_ba = Signal(False)
    soc_a = Signal(False)

    soc_dqs = Signal(intbv(0)[bus.d_width:])
    soc_dm = Signal(intbv(0)[bus.d_width:])
    soc_dq = Signal(intbv(0)[bus.d_width * 8:])

    toVerilog(ddr_connect, bus, soc_clk, soc_clk_b, None,
              soc_cs, soc_ras, soc_cas, soc_we, soc_ba, soc_a,
              soc_dqs, soc_dm, soc_dq)

    print
    print open('ddr_connect.v', 'r').read()

def main():
    import sys

    if 1:
        emit_connect()
        sys.stdout.flush()

    if 1:
        emit()
        sys.stdout.flush()

    if 1:
        sim()

if __name__ == '__main__':
    main()
