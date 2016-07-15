#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_spi_slave.py')

from myhdl import Signal, intbv, always_seq, always_comb

from ram import Ram
from spi_slave import SpiSlave, SpiInterface

from myhdl import instance, delay

def spi_test(bus, sclk_interval = 43):
    from myhdl import instance, delay

    @instance
    def logic():
        yield delay(200)

        bus.CS.next = 0
        bus.SCK.next = 0
        bus.SD_I.next = 0

        yield delay(sclk_interval)
        bus.CS.next = 1

        yield delay(sclk_interval)

        a = 0x1
        print "Reg Write Addr", hex(int(a))
        dd = a << 1
        for i in range(8):
            yield delay(sclk_interval)
            if dd & 0x80:
                bus.SD_I.next = 1
            else:
                bus.SD_I.next = 0
            dd <<= 1
            bus.SCK.next = 1

            yield delay(sclk_interval)
            bus.SCK.next = 0

        for j in range(0xae, 0xb1):
            dd = j
            print "Reg Write Data", hex(int(dd))
            for i in range(8):
                yield delay(sclk_interval)
                if dd & 0x80:
                    bus.SD_I.next = 1
                else:
                    bus.SD_I.next = 0
                dd <<= 1
                bus.SCK.next = 1

                yield delay(sclk_interval)
                bus.SCK.next = 0

        yield delay(sclk_interval)
        bus.CS.next = 0

        yield delay(sclk_interval)
        bus.CS.next = 1

        a = 0x1
        print "Reg Read Addr", hex(int(a))
        dd = (a << 1) | 1
        for i in range(8):
            yield delay(sclk_interval)
            if dd & 0x80:
                bus.SD_I.next = 1
            else:
                bus.SD_I.next = 0
            dd <<= 1
            bus.SCK.next = 1
            yield delay(sclk_interval)
            bus.SCK.next = 0

        yield delay(sclk_interval)

        for j in range(3):
            dd = 0
            for i in range(8):
                yield delay(sclk_interval)
                bus.SCK.next = 1

                yield delay(sclk_interval)
                dd <<= 1
                dd |= bus.SD_O
                bus.SCK.next = 0
            print "Reg Read Data", hex(int(dd))

        yield delay(sclk_interval)
        bus.CS.next = 0

    return logic

def top(clk, rst, spi_bus):
    from myhdl import instance, delay

    ram = Ram(addr_depth = 5, data_width = 8)

    wb_bus = ram.create_bus()
    wb_bus.CLK_I = clk

    if rst:
        wb_bus.RST_I = rst
    else:
        wb_bus.RST_I = None

    ram_inst = ram.gen(wb_bus)

    spi = SpiSlave()
    spi_inst = spi.gen(spi_bus, wb_bus)

    test_inst = spi_test(spi_bus)

    return ram_inst, spi_inst, test_inst
top.__name__ = 'test_spi_slave'

def sim():
    from myhdl import Simulation, traceSignals, ResetSignal
    from rhea.system import Clock
    import sys

    clk = Clock(0, 50E6)
    rst = ResetSignal(0, active = 1, async = 0)
    spi_bus = SpiInterface()

    clk_inst = clk.gen()

    @instance
    def rst_inst():
        rst.next = 1
        yield(delay(100))
        rst.next = 0

    test_inst = traceSignals(top, clk, rst, spi_bus)

    sim = Simulation(clk_inst, rst_inst, test_inst)
    sim.run(10000)
    print
    sys.stdout.flush()

def emit():
    from myhdl import toVerilog

    clk = Signal(False)
    rst = None
    spi_bus = SpiInterface()

    toVerilog(top, clk, rst, spi_bus)

    print
    print open('test_spi_slave.v', 'r').read()
    print

if __name__ == '__main__':
    sim()
    emit()
