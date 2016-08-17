#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_util.py')

from myhdl import Signal, intbv, always

from clk import Clk
from util import Packer

class Interface(object):
    def __init__(self, n):
        self.a = Signal(False)
        self.b = Signal(intbv(0)[n:])
        self.c = Signal(False)

def test(clk):
    insts = []

    p = Packer(Interface, 3)

    src = p.create()

    packed = p.pack(src)

    dst = p.create()
    unpack_inst = p.unpack(packed, dst)
    insts.append(unpack_inst)

    @always (clk)
    def test_inst():
        src.a.next = 1
        src.b.next = 1
        src.c.next = 1

        print dst.a
        print dst.b
        print dst.c

    insts.append(test_inst)

    print 'insts', insts

    return insts

def emit():
    from myhdl import toVerilog

    clk = Clk(50E6)

    toVerilog(test, clk)

    print
    print open('test.v', 'r').read()

def main():
    import sys

    if 1:
        emit()

if __name__ == '__main__':
    main()
