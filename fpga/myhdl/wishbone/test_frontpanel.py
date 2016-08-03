#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_frontpanel.py')

import sys
from myhdl import (Signal, ResetSignal, intbv,
                   always, always_comb, instance, delay)

from myhdl import toVerilog, Simulation, traceSignals, instance, delay

from timebase import nsec
from util import rename_interface
from test_system import create_system
from simplebus import SimpleMux, sb_write, sb_read

import sys

from frontpanel import FrontPanel

def fake_panel(fp_rst, fp_clk, fp_dout, nr_keys):
    print "fake_panel", type(fp_rst), type(fp_clk), type(fp_dout), type(nr_keys)

    insts = []

    keys = Signal(intbv(0)[nr_keys:])

    n = Signal(intbv(0, 0, nr_keys))

    @instance
    def src():
        yield delay(2345 * nsec)
        keys.next[0] = 1
        yield delay(2345 * nsec)
        keys.next[0] = 0

        yield delay(2345 * nsec)
        keys.next[nr_keys - 1] = 1
        yield delay(5234 * nsec)
        keys.next[nr_keys - 1] = 0

        yield delay(2345 * nsec)
        keys.next[nr_keys / 2] = 1
        yield delay(2345 * nsec)
        keys.next[nr_keys / 2] = 0

    insts.append(src)

    @always (fp_clk.negedge)
    def seq():
        if fp_rst:
            n.next = 0

        elif n == nr_keys - 1:
            n.next = 0

        else:
            n.next += 1
    insts.append(seq)

    @always_comb
    def comb():
        if fp_rst:
            fp_dout.next = not keys[0]
        else:
            fp_dout.next = not keys[n]
    insts.append(comb)

    return insts

class Harness(object):
    def __init__(self, fifo_depth = 5, data_width = 32, nr_keys = 7, ts_width = 8, prescaler = 2):
        self.duration = 30000 * nsec

        self.stimuli = []

        self.system, system_inst = create_system()
        self.stimuli.append(system_inst)

        fp_rst = Signal(False)
        fp_clk = Signal(False)
        fp_din = Signal(False)
        fp_din = Signal(False)

        fp_green = Signal(False)
        fp_white = Signal(False)

        self.mux = SimpleMux(self.system)

        self.fp = FrontPanel(self.system,
                             fp_rst, fp_clk, fp_din, fp_green, fp_white,
                             fifo_depth = fifo_depth, data_width = 32,
                             nr_keys = nr_keys, ts_width = 8,
                             prescaler = prescaler,
                             nr_overscan = 4, overscan = 4)
        self.mux.add(self.fp.ctl_bus)
        self.mux.add(self.fp.data_bus)

        self.bus = self.mux.bus()

        self.stimuli.append(fake_panel(fp_rst, fp_clk, fp_din, nr_keys = nr_keys))

        @instance
        def master():
            yield delay(299 * nsec)
            while 1:
                yield delay(99 * nsec)
                yield(sb_read(self.system, self.bus, 1))
        self.stimuli.append(master)

        #  Any parameters you want to have at the top level
        self.args = ( self.system, self.bus,
                      fp_rst, fp_clk, fp_din, fp_green, fp_white )

    def gen(self, system, bus, fp_rst, fp_clk, fp_din, fp_green, fp_white):
        # rename_interface(system, None)
        # rename_interface(bus, None)

        # Expose signals to gtkwave
        CLK = system.CLK
        RST = system.RST
        ADDR = bus.ADDR
        WR = bus.WR
        WR_DATA = bus.WR_DATA
        RD = bus.RD
        RD_DATA = bus.RD_DATA

        insts = []
        insts.append(self.fp.gen())
        insts.append(self.mux.gen())

        return insts

    def emit(self):
        toVerilog(self.gen, *self.args)
        print open('gen.v', 'r').read()
        sys.stdout.flush()

    def sim(self):
        insts = []

        insts.append(traceSignals(self.gen, *self.args))
        insts += self.stimuli

        sim = Simulation(insts)
        sim.run(self.duration)
        print
        sys.stdout.flush()

def main():
    if 1:
        Harness(fifo_depth = 5, nr_keys = 13, ts_width = 8, data_width = 24, prescaler = 2).emit()

    if 1:
        Harness(fifo_depth = 5, nr_keys = 13, ts_width = 8, data_width = 24, prescaler = 2).sim()

if __name__ == '__main__':
    main()
