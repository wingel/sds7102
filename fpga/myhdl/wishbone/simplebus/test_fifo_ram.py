#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo_ram.py')

from myhdl import toVerilog, Simulation, traceSignals, intbv, instance, delay, instances

from timebase import nsec
from util import rename_interface
from fifo_ram import FifoRam
from test_system import create_system
from test_bus import sb_write, sb_read

import sys
sys.path.append('../fifo')
from fifo_sync import SyncFifo
from fifo_async import AsyncFifo

class Harness(object):
    def __init__(self, addr_depth, data_width):
        self.duration = 1000 * nsec

        self.stimuli = []

        self.system, system_inst = create_system(reset_duration = 10)
        self.stimuli.append(system_inst)

        if 1:
            self.fifo = SyncFifo(self.system.RST, self.system.CLK,
                            intbv(0)[data_width:], 4)
        else:
            self.fifo = AsyncFifo(self.system.RST, self.system.CLK, self.system.CLK,
                            intbv(0)[data_width:], 2)

        self.dut = FifoRam('fifo', self.system, self.fifo, self.fifo,
                           addr_depth, data_width)

        self.bus = self.dut.bus()

        @instance
        def master():
            yield delay(99 * nsec)

            for i in range(len(self.dut._ram)):
                self.dut._ram[i].next = i

            yield self.system.CLK.posedge
            self.dut.wr_addr.next = 0x9
            self.dut.rd_addr.next = 0x2
            self.dut.rd_count.next = 0x06

        self.stimuli.append(master)

        #  Any parameters you want to have at the top level
        self.args = self.system, self.bus

    def gen(self, system, bus):
        # Expose signals to gtkwave
        CLK = system.CLK
        RST = system.RST
        ADDR = bus.ADDR
        WR = bus.WR
        WR_DATA = bus.WR_DATA
        RD = bus.RD
        RD_DATA = bus.RD_DATA

        fifo_inst = self.fifo.gen()

        # Create anything you want to be inside the DUT here
        dut_inst = self.dut.gen()

        return instances()

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
        Harness(32, 32).emit()

    if 1:
        Harness(16, 8).sim()

if __name__ == '__main__':
    main()
