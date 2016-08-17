#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_wb.py')

from myhdl import Signal, ResetSignal, intbv, always, always_seq, always_comb

from wb import WbSlave, WbSyncSlave, WbMux
from ram import AsyncRam

def wb_write(bus, adr, dat, timeout = 10):
    print "wb_write", hex(adr), hex(dat), timeout

    yield(bus.CLK_I.posedge)
    bus.CYC_I.next = 1
    bus.STB_I.next = 1
    bus.WE_I.next  = 1
    bus.ADR_I.next = adr
    bus.DAT_I.next = dat
    for t in range(timeout):
        yield(bus.CLK_I.posedge)
        if bus.ACK_O:
            print "write ACK", hex(bus.ADR_I), hex(bus.DAT_I)
            break
        elif bus.ERR_O:
            print "write ERR", hex(bus.ADR_I), hex(bus.DAT_I)
            break
        elif bus.RTY_O:
            print "write RTY", hex(bus.ADR_I), hex(bus.DAT_I)
    else:
        print "write timeout", hex(bus.ADR_I), hex(bus.DAT_I)

    bus.CYC_I.next = 0
    bus.STB_I.next = 0
    bus.WE_I.next  = 0

def wb_read(bus, adr, timeout = 10):
    print "wb_read", hex(adr), timeout

    from myhdl import instance

    yield(bus.CLK_I.posedge)
    bus.CYC_I.next = 1
    bus.STB_I.next = 1
    bus.WE_I.next  = 0
    bus.ADR_I.next = adr
    for t in range(timeout):
        yield(bus.CLK_I.posedge)
        if bus.ACK_O:
            print "read ACK", hex(bus.ADR_I), hex(bus.DAT_O)
            break
        elif bus.ERR_O:
            print "read ERR", hex(bus.ADR_I)
            break
        elif bus.RTY_O:
            print "read RTY", hex(bus.ADR_I)
    else:
        print "read timeout", hex(bus.ADR_I)

    bus.CYC_I.next = 0
    bus.STB_I.next = 0

def create_top():
    ram1 = AsyncRam(addr_depth = 5, data_width = 16)
    ram2 = AsyncRam(addr_depth = 9, data_width = 8)
    if 1:
        ram2 = WbSyncSlave(ram2)

    if 0:
        return ram1

    if 0:
        return ram2

    mux = WbMux()
    mux.add(ram1, addr = 2)
    mux.add(ram2, addr = 11)

    return mux

def master(bus):
    cnt = Signal(intbv(0)[16:])
    start_addr = Signal(intbv(0)[len(bus.ADR_I):])
    start_wr = Signal(False)
    start_rd = Signal(False)

    addr = Signal(intbv(0)[len(bus.DAT_I):])
    rd_data = Signal(intbv(0)[len(bus.DAT_I):])
    wr_data = Signal(intbv(0)[len(bus.DAT_I):])

    @always_seq (bus.CLK_I.posedge, bus.RST_I)
    def beh():
        start_wr.next = (cnt % 11) == 3
        start_rd.next = (cnt % 11) == 5 or (cnt % 11) == 8

        cnt.next = 0
        if cnt != 65535 - 1 - 1:
            cnt.next = cnt + 1

        if bus.ACK_O:
            if bus.WE_I:
                print "ACK", hex(int(bus.ADR_I)), "wr", hex(int(bus.DAT_I))
            else:
                print "ACK", hex(int(bus.ADR_I)), "rd", hex(int(bus.DAT_O))
                addr.next = bus.ADR_I
                rd_data.next = bus.DAT_O
        elif bus.ERR_O:
            print "ERR", hex(int(bus.ADR_I))
        elif bus.RTY_O:
            print "RTY", hex(int(bus.ADR_I))

        if not bus.CYC_I or bus.ACK_O or bus.ERR_O or bus.RTY_O:
            if start_wr or start_rd:
                bus.CYC_I.next = 1
                bus.STB_I.next = 1
                bus.ADR_I.next = start_addr

                if start_wr:
                    bus.DAT_I.next = cnt
                    bus.WE_I.next = 1
                else:
                    bus.DAT_I.next = intbv(0xdead)[len(bus.DAT_I):]
                    bus.WE_I.next = 0

                print "start_addr", start_addr, "addr_depth", intbv(~0)[len(bus.ADR_I):]
                start_addr.next = 0
                if start_addr != intbv(~0)[len(bus.ADR_I):]:
                    start_addr.next = start_addr + 1

            else:
                bus.ADR_I.next = 0
                bus.DAT_I.next = intbv(0xdead)[len(bus.DAT_I):]
                bus.WE_I.next = 0
                bus.CYC_I.next = 0
                bus.STB_I.next = 0

    return beh

def create_test():
    from rhea.system import Clock
    from myhdl import instance, delay

    top = create_top()
    bus = top.create_bus()

    bus.CLK_I = Clock(0, frequency = 50e6)

    @instance
    def rst_inst():
        bus.RST_I.next = 1
        yield(delay(100))
        bus.RST_I.next = 0

    clock_inst = bus.CLK_I.gen()

    # bus.SEL_I = Signal(intbv(2)[2:0])

    master_inst = master(bus)

    top_inst = top.gen(bus)

    return rst_inst, clock_inst, master_inst, top_inst

def sim():
    from myhdl import Simulation, traceSignals
    import sys

    test_inst = traceSignals(create_test)

    sim = Simulation(test_inst)
    sim.run(20000)
    print
    sys.stdout.flush()

def emit():
    from myhdl import toVerilog

    top = create_top()
    bus = top.create_bus()

    if 1:
        # Use this for an FPGA implementation
        bus.RST_I = None

    toVerilog(top.gen, bus)

    print
    print open('gen.v', 'r').read()

if __name__ == '__main__':
    sim()
    emit()
