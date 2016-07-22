#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('regfile.py')

from myhdl import Signal, SignalType, always_comb, always_seq, intbv
from timebase import sec
from util import rename_interface
from wb import WbSlave

class Port(object):
    def __init__(self, value):
	self.STB   = Signal(False)
        self.WE    = Signal(False)
	self.DAT_I = Signal(value)
	self.DAT_O = Signal(value)

class Field(object):
    def __init__(self, system, name, description, port):
        self.system = system
        self.name = name
        self.description = description
        self.port = port

    def gen(self, bus):
        @always_comb
        def comb():
            self.port.STB.next = bus.STB_I
            self.port.WE.next = bus.WE_I
            self.port.DAT_I.next = bus.DAT_I[self.offset+self.width:self.offset]
            bus.DAT_O.next[self.offset+self.width:self.offset] = self.port.DAT_O

        return comb

class RoField(Field):
    def __init__(self, system, name, description, signal):
        super(RoField, self).__init__(system, name, description,
                                      Port(signal.val))
        self.signal = signal

    def gen(self, other):
        print "RoField.gen"

        field_inst = super(RoField, self).gen(other)

        # lost signals
        self.port.DAT_O._name = 'dat_o_%u' % id(self)
        self.port.DAT_O.driven = 1

        @always_comb
        def comb():
            self.port.DAT_O.next = self.signal

        return field_inst, comb

class RwField(RoField):
    def __init__(self, system, name, description, signal):
        super(RwField, self).__init__(system, name, description, signal)

    def gen(self, other):
        print "RwField.gen"

        rofield_inst = super(RwField, self).gen(other)

        @always_seq(self.system.CLK.posedge, self.system.RST)
        def seq():
            if self.port.STB and self.port.WE:
                self.signal.next = self.port.DAT_I

        return rofield_inst, seq

class DummyField(object):
    def __init__(self, name, description, width):
        self.name = name
        self.description = description
        self.port = Port(intbv(0)[width:])

    def gen(self, bus):
        return ()

class RegFile(WbSlave):
    def __init__(self, name, description, fields = []):
        super(RegFile, self).__init__()
        self.name = name
        self.description = description
        self.fields = []
        self.add_fields(fields)
        self.async = True

    def add_fields(self, fields):
        for field in fields:
            self.fields.append(field)

    def check_args(self):
        print "RegFile.check_args", self.addr_depth, self.data_width

        if self.addr_depth != 0:
            return

        self.addr_depth = 1
        self.data_width = 0
        for field in self.fields:
#            rename_interface(field.port, self.name + '_' + field.name)
            field.offset = self.data_width
            field.width = len(field.port.DAT_O)
            self.data_width += field.width

    def gen(self, bus):
        self.check_args()

        # Assign local signals so that they show up in gtkwave
        clk = bus.CLK_I
        rst = bus.RST_I
        stb = bus.STB_I
        ack = bus.ACK_O
        dat_i = bus.DAT_I
        dat_o = bus.DAT_O

        insts = []

        @always_comb
        def comb():
            bus.ACK_O.next = 1
            bus.ERR_O.next = 0
            bus.RTY_O.next = 0

        insts.append(comb)

        for f in self.fields:
            print f.name, f.offset, f.width

            #@always_comb
            #def comb():
            #    f.port.STB.next = bus.CYC_I and bus.STB_I
            #    f.port.WE.next = bus.WE_I
            #    f.port.DAT_I.next = bus.DAT_I[f.offset+f.width:f.offset]
            #    bus.DAT_O.next[f.offset+f.width:f.offset] = f.port.DAT_O
            # insts.append(comb)

            insts.append(f.gen(bus))

        return insts

if __name__ == '__main__':
    from test_regfile import main
    main()
