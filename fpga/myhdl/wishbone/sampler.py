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
        super(Sampler, self).__init__(addr_depth, data_width)

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

        sample_addr = Signal(intbv(0, 0, self.addr_depth+1))

        if self.skip_cnt:
            sample_skip = Signal(intbv(0, 0, self.skip_cnt + 1))
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
        else:
            @always(self.sample_clk.posedge)
            def inst():
                if self.sample_enable:
                    if sample_addr < self.addr_depth:
                        sample_addr.next = sample_addr + 1
                else:
                    sample_addr.next = 0

        return comb, seq, inst

class MigSampler(object):
    def __init__(self, port, base, chunk, stride, count,
                 sample_clk, sample_data, sample_enable,
                 fifo_overflow, cmd_overflow):
        self.port = port
        self.base = base
        self.chunk = chunk
        self.stride = stride
        self.count = count
        self.sample_clk = sample_clk
        self.sample_data = sample_data
        self.sample_enable = sample_enable

        self.fifo_overflow = fifo_overflow
        self.cmd_overflow = cmd_overflow

    def gen(self):
        fifo_size = 512

        fifo = [ Signal(intbv(0)[32:]) for _ in range(fifo_size) ]
        fifo_head = Signal(intbv(0, 0, fifo_size))
        fifo_tail = Signal(intbv(0, 0, fifo_size))

        addr = Signal(intbv(0, 0, self.count * self.chunk))
        cnt = Signal(intbv(0, 0, self.count+1))
        cnk = Signal(intbv(0, 0, self.chunk))

        @always(self.sample_clk.posedge)
        def sample_seq():
            self.port.cmd_en.next = 0
            self.port.cmd_byte_addr.next = addr << 2
            self.port.cmd_instr.next = 0
            self.port.cmd_bl.next = self.chunk - 1

            self.port.wr_en.next = 0
            self.port.wr_data.next = self.sample_data
            self.port.wr_mask.next = 0

            if self.sample_enable:
                if cnt < self.count:
                    fifo_next = (fifo_head + 1) & (fifo_size - 1)
                    if fifo_next != fifo_tail:
                        fifo[fifo_head].next = self.sample_data
                        fifo_head.next = fifo_next
                    else:
                        self.fifo_overflow.next = 1

                if fifo_head != fifo_tail:
                    if not self.port.wr_full:
                        self.port.wr_en.next = 1
                        self.port.wr_data.next = fifo[fifo_tail]
                        fifo_tail.next = (fifo_tail.next + 1) & (fifo_size - 1)

                    if fifo_tail & (self.chunk - 1) == self.chunk - 1:
                        self.port.cmd_en.next = 1
                        addr.next = addr + self.stride
                        cnt.next = cnt + 1

                        if self.port.cmd_full:
                            self.cmd_overflow.next = 1

            else:
                cnk.next = 0
                cnt.next = 0
                addr.next = self.base

                fifo_head.next = 0
                fifo_tail.next = 0

                self.fifo_overflow.next = 0
                self.cmd_overflow.next = 0

        return sample_seq
