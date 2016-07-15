#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('ram.py')

from myhdl import Signal, intbv, always_seq, always_comb

from wb import WbSlave

class AsyncRam(WbSlave):
    def __init__(self, addr_depth, data_width):
        super(AsyncRam, self).__init__(addr_depth, data_width, async = True)

        self.ram = [ Signal(intbv(0)[data_width:]) for _ in range(addr_depth) ]

    def gen(self, bus):
        @always_seq(bus.CLK_I.posedge, bus.RST_I)
        def ram_write_inst():
            if bus.CYC_I and bus.STB_I and bus.WE_I:
                if bus.ADR_I < len(self.ram):
                    # When I try to synthesize the following with
                    # Xlinx ISE I get "h is not a constant"
                    # for sel in range(len(bus.SEL_I)):
                    #     if bus.SEL_I[sel]:
                    #         l = sel * 8
                    #         h = sel * 8 + 8
                    #         self.ram[bus.ADR_I].next[h:l] = bus.DAT_I[h:l]
                    self.ram[bus.ADR_I].next = bus.DAT_I

        @always_comb
        def ram_read_inst():
            if bus.CYC_I and bus.STB_I and not bus.WE_I and bus.ADR_I < len(self.ram):
                bus.DAT_O.next = self.ram[bus.ADR_I]
            else:
                bus.DAT_O.next = intbv(0xdeadbeef)[len(bus.DAT_O):]

        @always_comb
        def ram_ack_inst():
            if bus.CYC_I and bus.STB_I:
                bus.ACK_O.next = 1
            else:
                bus.ACK_O.next = 0

        return ram_write_inst, ram_read_inst, ram_ack_inst

class Ram(WbSlave):
    def __init__(self, addr_depth, data_width):
        super(Ram, self).__init__(addr_depth, data_width, async = True)

        self.ram = [ Signal(intbv(0)[data_width:]) for _ in range(addr_depth) ]

    def gen(self, bus):
        req = Signal(False)

        @always_comb
        def comb():
            req.next = (bus.CYC_I and bus.STB_I and
                        not bus.ACK_O and not bus.ERR_O and not bus.RTY_O)

        @always_seq(bus.CLK_I.posedge, bus.RST_I)
        def seq():
            bus.ACK_O.next = 0
            bus.ERR_O.next = 0
            bus.RTY_O.next = 0
            bus.DAT_O.next = intbv(0xdeadbeef)[len(bus.DAT_O):]

            if req:
                if bus.ADR_I < len(self.ram):
                    bus.ACK_O.next = 1
                else:
                    bus.ERR_O.next = 1

                if bus.WE_I and bus.ADR_I < len(self.ram):
                    # When I try to synthesize the following with
                    # Xlinx ISE I get "h is not a constant"
                    # for sel in range(len(bus.SEL_I)):
                    #     if bus.SEL_I[sel]:
                    #         l = sel * 8
                    #         h = sel * 8 + 8
                    #         self.ram[bus.ADR_I].next[h:l] = bus.DAT_I[h:l]

                    # so do this instead
                    self.ram[bus.ADR_I].next = bus.DAT_I

                # In simulation this ought to be protected by the
                # check for len(self.ram) above, but if I do that
                # Xilinx ISE won't synthesize a block RAM.
                # Disable the check for now
                if 1 or not bus.WE_I and bus.ADR_I < len(self.ram):
                    bus.DAT_O.next = self.ram[bus.ADR_I]

        return comb, seq

if __name__ == '__main__':
    from test_wb import sim, emit
    sim()
    emit()
