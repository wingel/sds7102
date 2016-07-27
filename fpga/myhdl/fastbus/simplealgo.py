#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_simplealgo.py')

from myhdl import Signal, intbv, always_seq, always_comb

from system import System
from simplebus import SimplePort
from gray import gray_encoder

class SimpleAlgo(object):
    """Simple read-only bus slave which returns the address as the data"""

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
        insts = []

        b = Signal(intbv(0)[16:])
        g = Signal(intbv(0)[16:])

        @always_comb
        def b_inst():
            b.next = port.ADDR & ((1<<16)-1)
        insts.append(b_inst)

        gray_inst = gray_encoder(b, g)
        insts.append(gray_inst)

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if port.RD and port.ADDR < self.addr_depth:
                port.RD_DATA.next = b | (g << 16)
            else:
                port.RD_DATA.next = 0

        insts.append(seq)

        return insts
