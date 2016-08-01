#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_reg.py')

from myhdl import Signal, ConcatSignal, SignalType, always_comb, always_seq, intbv

from bus import SimpleBus

class Port(object):
    def __init__(self, width):
        self.width = width

        self.WR = Signal(False)
        self.WR_DATA = Signal(intbv(0)[width:])

        self.RD = Signal(False)
        self.RD_DATA = Signal(intbv(0)[width:])

        if 0:
            self.WR.read = True
            self.WR_DATA.read = True
            self.RD.read = True
            self.RD_DATA.driven = True

class Field(object):
    def __init__(self, name, description, port):
        self.name = name
        self.description = description
        self.port = port

    def gen_field(self, system):
        print "Field.gen", self.name, self.port.offset, self.port.width
        return []

    def gen(self, system):
        return self.gen_field(system)

class DummyField(Field):
    def __init__(self, width):
        port = Port(width)
        super(DummyField, self).__init__('', '', port)

    def gen(self, system):
        field_inst = super(DummyField, self).gen_field(system)

        @always_seq (system.CLK.posedge, system.RST)
        def seq():
            self.port.RD_DATA.next = 0

        return field_inst, seq

class RoField(Field):
    def __init__(self, name, description, signal):
        super(RoField, self).__init__(name, description,
                                      Port(len(signal)))
        self.signal = signal

    def gen_rofield(self, system):
        print "RoField.gen", self.name

        field_inst = super(RoField, self).gen_field(system)

        @always_seq (system.CLK.posedge, system.RST)
        def comb():
            if self.port.RD:
                self.port.RD_DATA.next = self.signal
            else:
                self.port.RD_DATA.next = 0

        return field_inst, comb

    def gen(self, system):
        return self.gen_rofield(system)

class RwField(RoField):
    def __init__(self, name, description, signal):
        super(RwField, self).__init__(name, description, signal)

    def gen_rwfield(self, system):
        print "RwField.gen", self.name

        rofield_inst = super(RwField, self).gen_rofield(system)

        @always_seq(system.CLK.posedge, system.RST)
        def seq():
            if self.port.WR:
                self.signal.next = self.port.WR_DATA

        return rofield_inst, seq

    def gen(self, system):
        return self.gen_rwfield(system)

class SimpleReg(object):
    # Set to true for multiple assignments to the same vector, 0 to
    # use ConcatSignal
    MULTI_ASSIGN = 0

    def __init__(self, system, name, description, fields = []):
        self.system = system

        self.name = name
        self.description = description
        self.fields = []

        self._bus = None
        self.data_width = 0

        self.add_fields(fields)

    def add_field(self, field):
        # We can't add more fields after we have generated the bus
        assert self._bus is None

        field.offset = self.data_width
        field.port.offset = self.data_width
        self.data_width += field.port.width

        assert(self.data_width <= 32)

        self.fields.append(field)

    def add_fields(self, fields):
        for field in fields:
            self.add_field(field)

    def bus(self):
        if self._bus is None:
            self._bus = SimpleBus(1, self.data_width)
        return self._bus

    def connect(self, bus, field):
        insts = []
        @always_comb
        def out_comb():
            field.port.WR.next = bus.WR
            field.port.WR_DATA.next = bus.WR_DATA[field.offset+field.port.width:field.offset]
            field.port.RD.next = bus.RD
        insts.append(out_comb)

        if self.MULTI_ASSIGN:
            @always_comb
            def in_comb():
                bus.RD_DATA.next[field.offset+field.port.width:field.offset] = field.port.RD_DATA
            insts.append(in_comb)

        return insts

    def gen(self):
        system = self.system
        bus = self.bus()

        insts = []

        for field in self.fields:
            field_inst = field.gen(system)
            insts.append(field_inst)

            connect_inst = self.connect(bus, field)
            # connect_inst = field.port.connect(bus)
            insts.append(connect_inst)

        if not self.MULTI_ASSIGN:
            # This does not work in simulation, but the verilog looks decent
            if len(self.fields) > 1:
                rd_data_array = []
                for field in self.fields:
                    rd_data_array.append(field.port.RD_DATA)
                rd_data = ConcatSignal(*reversed(rd_data_array))
            else:
                rd_data = self.fields[0].port.RD_DATA

            @always_comb
            def in_comb():
                bus.RD_DATA.next = rd_data
            insts.append(in_comb)

        return insts
