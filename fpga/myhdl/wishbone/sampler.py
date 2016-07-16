#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('sampler.py')

from myhdl import Signal, intbv, always, always_seq, always_comb

from wb import WbSlave

class Sampler(WbSlave):
    def __init__(self, addr_depth, sample_clk, sample_data, sample_enable,
                 skip_cnt = 0):
        data_width = len(sample_data)
        super(Sampler, self).__init__(addr_depth, data_width, async = True)

        self.ram = [ Signal(intbv(0)[data_width:]) for _ in range(addr_depth) ]

        self.sample_clk = sample_clk
        self.sample_data = sample_data
        self.sample_enable = sample_enable

        self.skip_cnt = skip_cnt

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

        sample_skip = Signal(intbv(0, 0, self.skip_cnt + 1))
        sample_addr = Signal(intbv(0, 0, self.addr_depth+1))
        @always(self.sample_clk.posedge)
        def inst():
            if self.sample_enable:
                if sample_addr < self.addr_depth:
                    if sample_skip == self.skip_cnt:
                        self.ram[sample_addr].next = self.sample_data
                        sample_addr.next = sample_addr + 1
                        sample_skip.next = 0
                    else:
                        sample_skip.next = sample_skip + 1
            else:
                sample_addr.next = 0

        return comb, seq, inst
