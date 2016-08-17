#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_fifo_ram.py')

from myhdl import Signal, intbv, always_seq, always_comb, instances

from system import System
from bus import SimpleBus

from reg import SimpleReg, Port, Field

def flatten(x):
    result = []
    for el in x:
        if not el:
            pass
        elif isinstance(el, list) or isinstance(el, tuple):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

class FifoRam(object):
    """RAM a bit of RAM"""

    def __init__(self, name, system, out_fifo, in_fifo, addr_depth, data_width):
        self.system = system

        self.clk = self.system.CLK
        self.rst = self.system.RST

        self.addr_depth = addr_depth
        self.data_width = data_width

        self._bus = SimpleBus(addr_depth, data_width)

        self.out_fifo = out_fifo
        self.in_fifo = in_fifo

        assert out_fifo.WR_CLK == in_fifo.RD_CLK

        self.wr_addr = Signal(intbv(0, 0, addr_depth))
        self.rd_addr = Signal(intbv(0, 0, addr_depth))
        self.rd_count = Signal(intbv(0, 0, addr_depth + 1))

        self._wr_addr_port = Port(len(self.wr_addr))
        self._rd_addr_port = Port(len(self.rd_addr))
        self._rd_count_port = Port(len(self.rd_count))

        self._regs = [
            SimpleReg(system, '%s_wr_addr' % name, "", [
            Field('wr_addr', "Write Address", self._wr_addr_port),
            ]),
            SimpleReg(system, '%s_rd_addr' % name, "", [
            Field('rd_addr', "Read Address", self._rd_addr_port),
            ]),
            SimpleReg(system, '%s_rd_count' % name, "", [
            Field('rd_count', "Read Count", self._rd_count_port),
            ]),
            ]

        self._ram = [ Signal(intbv(0)[self.data_width:])
                      for _ in range(self.addr_depth) ]

    def regs_bus(self):
        return [ reg.bus() for reg in self._regs ]

    def regs_gen(self):
        insts = []
        for reg in self._regs:
            insts.append(reg.gen())
        return insts

    def bus(self):
        return self._bus

    def gen(self):
        system = self.system
        bus = self.bus()

        ram_addr = Signal(intbv(0, 0, self.addr_depth))
        fifo_wr = Signal(False)
        fifo_rd = Signal(False)

        fifo_rd_empty = Signal(False)

        @always_seq(system.CLK.posedge, system.RST)
        def mem_seq():
            if bus.WR:
                self._ram[bus.ADDR].next = bus.WR_DATA

            if bus.RD and bus.ADDR < len(self._ram):
                bus.RD_DATA.next = self._ram[bus.ADDR]
            else:
                bus.RD_DATA.next = 0

            fifo_rd_empty.next = self.in_fifo.RD_EMPTY

        @always_comb
        def fifo_comb():
            ram_addr.next = 0
            fifo_wr.next = 0
            fifo_rd.next = 0

            if not fifo_rd_empty:
                fifo_rd.next = 1
                ram_addr.next = self.wr_addr

            elif self.rd_count != 0 and not self.out_fifo.WR_FULL:
                fifo_wr.next = 1
                ram_addr.next = self.rd_addr

        @always_comb
        def fifo_rd_comb():
            self.in_fifo.RD.next = fifo_rd

        @always_seq(self.out_fifo.WR_CLK.posedge, self.out_fifo.WR_RST)
        def fifo_seq():
            self.out_fifo.WR.next = 0
            self.out_fifo.WR_DATA.next = 0x55

            if fifo_wr:
                self.out_fifo.WR.next = 1
                self.out_fifo.WR_DATA.next = self._ram[ram_addr]

                self.rd_addr.next = self.rd_addr + 1
                self.rd_count.next = self.rd_count - 1

            elif fifo_rd:
                self._ram[ram_addr].next = self.in_fifo.RD_DATA
                self.wr_addr.next = self.wr_addr + 1

            if self._wr_addr_port.WR:
                self.wr_addr.next = self._wr_addr_port.WR_DATA
            if self._rd_addr_port.WR:
                self.rd_addr.next = self._rd_addr_port.WR_DATA
            if self._rd_count_port.WR:
                self.rd_count.next = self._rd_count_port.WR_DATA

            if self._wr_addr_port.RD:
                self._wr_addr_port.RD_DATA.next = self.wr_addr
            else:
                self._wr_addr_port.RD_DATA.next = 0
            if self._rd_addr_port.RD:
                self._rd_addr_port.RD_DATA.next = self.rd_addr
            else:
                self._rd_addr_port.RD_DATA.next = 0
            if self._rd_count_port.RD:
                self._rd_count_port.RD_DATA.next = self.rd_count
            else:
                self._rd_count_port.RD_DATA.next = 0

        return instances()

