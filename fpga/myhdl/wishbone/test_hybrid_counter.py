#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_hybrid_counter.py')

from myhdl import Signal, ConcatSignal, intbv, instance, delay, SignalType

from timebase import timescale, nsec, usec, msec, sec
from wb import WbSlaveInterface
from hybrid_counter import HybridCounter
from rhea.system import Clock
from clk import Clk, clkgen
from rst import rstgen

def test(bus):
    freqs = [ 100E6, 133E6, 233E6 ]

    pin_array = [ ]
    pin_insts = [ ]
    for freq in freqs:
        pin = Clk(False, freq)
        pin_inst = pin.gen()
        pin_array.append(pin)
        pin_insts.append(pin_inst)

    pins = ConcatSignal(*pin_array)

    clk = bus.CLK_I
    rst = bus.RST_I

    rst_inst = rstgen(rst, 100 * nsec, clk)

    hc = HybridCounter(data_width = 16, async_width = 8)
    hc_inst = hc.gen(bus, pins)

    return pin_insts, rst_inst, hc_inst

def reader(bus, n, interval):
    @instance
    def inst():
        yield delay(300 * nsec)

        while 1:
            yield delay(interval - 1)
            yield bus.CLK_I.posedge

            bus.CYC_I.next = 1
            bus.STB_I.next = 1
            bus.WE_I.next = 0

            while 1:
                yield bus.CLK_I.posedge
                if bus.ACK_O or bus.ERR_O:
                    break

            if bus.ACK_O:
                print "ACK", hex(bus.ADR_I), hex(bus.DAT_O & ((1<<(len(bus.DAT_O)-1))-1))

            if bus.ERR_O:
                print "ERR", hex(bus.ADR_I)

            bus.CYC_I.next = 0
            bus.STB_I.next = 0

            bus.ADR_I.next = 0
            if bus.ADR_I != n - 1:
                bus.ADR_I.next = bus.ADR_I + 1

    return inst

def sim():
    from myhdl import Simulation, traceSignals
    import sys

    bus = WbSlaveInterface(addr_depth = 4, data_width = 16)
    bus.CLK_I = Clk(False, 50E6)
    clk_inst = bus.CLK_I.gen()

    test_inst = traceSignals(test, bus)

    extra_inst = []
    if 1:
        reader_inst = reader(bus, 4, 123 * nsec)
        extra_inst.append(reader_inst)

    sim = Simulation(clk_inst, test_inst, extra_inst)
    sim.run(5 * usec)
    print
    sys.stdout.flush()

def emit():
    from myhdl import toVerilog

    pins = Signal(intbv(0)[3:])

    test = HybridCounter()
    bus = test.create_bus(pins)

    toVerilog(test.gen, bus, pins)

    print
    print open('gen.v', 'r').read()
    print

if __name__ == '__main__':
    sim()
    emit()
