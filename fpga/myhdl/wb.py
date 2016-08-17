#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('wb.py')

from myhdl import Signal, SignalType, ResetSignal, intbv, always_seq, always_comb

class WbSlaveInterface(object):
    def __init__(self, addr_depth, data_width):
        addr_width = len(intbv(0, 0, addr_depth))
        sel_width = (data_width + 7) / 8

        self.CLK_I = Signal(False)
        self.RST_I = ResetSignal(0, active = 1, async = 0)

        self.CYC_I = Signal(False)
        self.STB_I = Signal(False)
        self.WE_I = Signal(False)

        self.ACK_O = Signal(False)
        self.ERR_O = Signal(False)
        self.RTY_O = Signal(False)

        self.ADR_I = Signal(intbv(0)[addr_width:])
        self.SEL_I = Signal(intbv(~0)[sel_width:])
        self.DAT_I = Signal(intbv(0)[data_width:])
        self.DAT_O = Signal(intbv(0)[data_width:])

class WbBus(WbSlaveInterface):
    def __init__(self, system, addr_depth, data_width):
        super(WbBus, self).__init__(addr_depth, data_width)

        self.system = system

        self.CLK_I = system.CLK
        self.RST_I = system.RST

def wb_slave_connect(dst, src):
    assert len(dst.ADR_I) <= len(src.ADR_I)
    assert len(dst.SEL_I) <= len(src.SEL_I)
    assert len(dst.DAT_I) <= len(src.DAT_I)
    assert len(dst.DAT_O) <= len(src.DAT_O)

    dst.RST_I = src.RST_I
    dst.CLK_I = src.CLK_I

    @always_comb
    def comb():
        dst.CYC_I.next = src.CYC_I
        dst.STB_I.next = src.STB_I
        dst.WE_I.next  = src.WE_I

        src.ACK_O.next = dst.ACK_O
        src.ERR_O.next = dst.ERR_O
        src.RTY_O.next = dst.RTY_O

        dst.ADR_I.next = src.ADR_I[len(dst.ADR_I):]
        dst.SEL_I.next = src.SEL_I[len(dst.SEL_I):]
        dst.DAT_I.next = src.DAT_I[len(dst.DAT_I):]
        src.DAT_O.next = dst.DAT_O

    return comb

class WbSlave(object):
    def __init__(self, addr_depth = 0, data_width = 0, async = False):
        self.addr = None
        self.addr_depth = addr_depth
        self.data_width = data_width

        self.async = async

    def check_args(self, *args):
        pass

    def create_bus(self, *args):
        self.check_args(*args)
        return WbSlaveInterface(self.addr_depth, self.data_width)

class WbSyncSlave(WbSlave):
    def __init__(self, async_slave):
        assert async_slave.async
        self._async_slave = async_slave

    def create_bus(self, *args):
        bus = self._async_slave.create_bus(*args)
        bus.async = False
        return bus

    def gen(self, sync_bus, *args):
        async_bus = self._async_slave.create_bus(*args)

        async_bus.RST_I = sync_bus.RST_I
        async_bus.CLK_I = sync_bus.CLK_I

        async_bus.CYC_I = sync_bus.CYC_I
        async_bus.WE_I  = sync_bus.WE_I

        async_bus.ADR_I = sync_bus.ADR_I
        async_bus.SEL_I = sync_bus.SEL_I
        async_bus.DAT_I = sync_bus.DAT_I

        @always_comb
        def sync_comb():
            async_bus.STB_I.next = (
                sync_bus.STB_I and
                not sync_bus.ACK_O and
                not sync_bus.ERR_O and
                not sync_bus.RTY_O)

        @always_seq(sync_bus.CLK_I.posedge, sync_bus.RST_I)
        def sync_seq():
            sync_bus.ACK_O.next = async_bus.ACK_O
            sync_bus.ERR_O.next = async_bus.ERR_O
            sync_bus.RTY_O.next = async_bus.RTY_O

            sync_bus.DAT_O.next = async_bus.DAT_O

        async_inst = self._async_slave.gen(async_bus)

        return sync_comb, sync_seq, async_inst

    def __getattr__(self, key):
        value = getattr(self._async_slave, key)
        print "WbSyncSlave.__getattr__(%s) -> %s" % (key, value)
        return value

class WbMux(WbSlave):
    def __init__(self):
        super(WbMux, self).__init__(addr_depth = 0, data_width = 0)

        self.slaves = []

    def add(self, slave, addr, *args):
        slave.check_args(*args)

        slave.addr = addr
        slave.args = args
        self.slaves.append(slave)

        print "call slave.check_args", slave

        slave.check_args(*args)

        print slave, slave.addr, slave.addr_depth, slave.data_width

        if self.addr_depth < slave.addr + slave.addr_depth:
            self.addr_depth = slave.addr + slave.addr_depth
        if self.data_width < slave.data_width:
            self.data_width = slave.data_width

    def gen(self, bus):
        addr_lo = []
        addr_hi = []

        cyc_i_arr = []
        stb_i_arr = []

        ack_o_arr = []
        rty_o_arr = []
        err_o_arr = []

        adr_i_arr = []
        dat_o_arr = []

        connect_insts = []
        slave_insts = []

        for slave in self.slaves:
            slave_bus = slave.create_bus(*slave.args)
            slave_bus.addr = slave.addr

            addr_lo.append(slave.addr)
            addr_hi.append(slave.addr + slave.addr_depth)

            internal_bus = self.create_bus()
            internal_bus.addr = slave.addr

            internal_bus.RST_I = bus.RST_I
            internal_bus.CLK_I = bus.CLK_I

            internal_bus.WE_I  = bus.WE_I

            internal_bus.SEL_I = bus.SEL_I
            internal_bus.DAT_I = bus.DAT_I

            cyc_i_arr.append(internal_bus.CYC_I)
            stb_i_arr.append(internal_bus.STB_I)

            ack_o_arr.append(internal_bus.ACK_O)
            err_o_arr.append(internal_bus.ERR_O)
            rty_o_arr.append(internal_bus.RTY_O)

            adr_i_arr.append(internal_bus.ADR_I)
            dat_o_arr.append(internal_bus.DAT_O)

            connect_insts.append(wb_slave_connect(slave_bus, internal_bus))

            slave_insts.append(slave.gen(slave_bus, *slave.args))

        addr_lo = tuple(addr_lo)
        addr_hi = tuple(addr_hi)

        print "addr_lo", addr_lo
        print "addr_hi", addr_hi

        @always_comb
        def out_inst():
            bus.ACK_O.next = 0
            bus.ERR_O.next = bus.CYC_I and bus.STB_I
            bus.RTY_O.next = 0

            bus.DAT_O.next = intbv(0xf00f1234)[self.data_width:]

            for i in range(len(self.slaves)):
                lo = addr_lo[i]
                hi = addr_hi[i]
                valid = bus.ADR_I >= lo and bus.ADR_I < hi

                cyc_i_arr[i].next = bus.CYC_I and valid
                stb_i_arr[i].next = bus.STB_I and valid

                adr_i_arr[i].next = intbv((bus.ADR_I - lo)) & ((1<<len(internal_bus.ADR_I))-1)

                if bus.CYC_I and bus.STB_I and valid:
                    bus.ACK_O.next = ack_o_arr[i]
                    bus.ERR_O.next = err_o_arr[i]
                    bus.RTY_O.next = rty_o_arr[i]

                    bus.DAT_O.next = dat_o_arr[i]

        return connect_insts, slave_insts, out_inst

if __name__ == '__main__':
    from test_wb import sim, emit
    sim()
    emit()
