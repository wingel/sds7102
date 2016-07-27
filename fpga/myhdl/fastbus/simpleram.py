#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_simplebus.py')

from myhdl import Signal, intbv, always_seq

from system import System
from simplebus import SimplePort

class SimpleRam(object):
    def __init__(self, system, addr_depth, data_width):
        self.system = system
        self._port = None

        self.addr_depth = addr_depth
        self.data_width = data_width

    def port(self):
        if self._port is None:
            self._port = SimplePort(self.addr_depth, self.data_width)
        return self._port

    def args(self):
        return self.system, self.port()

    def gen(self, system, port):
        ram = [ Signal(intbv(0)[self.data_width:])
                for _ in range(self.addr_depth) ]

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if port.WR:
                ram[port.ADDR].next = port.WR_DATA

            # Disable the if statement since it would make the RAM
            # asynchronous read which stops it from being block RAM
            if 0 or port.RD and port.ADDR < self.addr_depth:
                port.RD_DATA.next = ram[port.ADDR]
            else:
                port.RD_DATA.next = 0

        return seq

class SimpleDpRam(object):
    def __init__(self, system, addr_depth, data_width):
        self.system = system
        self.port1 = SimplePort(addr_depth, data_width)
        self.port2 = SimplePort(addr_depth, data_width)

        self.addr_depth = addr_depth
        self.data_width = data_width

    def args(self):
        return self.system, self.port1, self.port2

    def gen(self, system, port1, port2):
        ram = [ Signal(intbv(0)[self.data_width:])
                for _ in range(self.addr_depth) ]

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if port1.WR:
                ram[port1.ADDR].next = port1.WR_DATA

            if port2.WR:
                ram[port2.ADDR].next = port2.WR_DATA

            # Trying to have an if port.RD apparently makes this an asynchronous read
            # if port.RD:
            port1.RD_DATA.next = ram[port1.ADDR]
            port2.RD_DATA.next = ram[port2.ADDR]

        return seq
