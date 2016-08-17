#! /usr/bin/python
from myhdl import Signal, intbv, always, always_seq, always_comb, instances

from fifo.async import AsyncFifo
from fifo.dummy import DummyFifo

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

class FifoSampler(object):
    def __init__(self, sample_clk, sample_data, sample_enable,
                 count, fifo, overflow):
        self.sample_clk = sample_clk
        self.sample_data = sample_data
        self.sample_enable = sample_enable

        self.count = count
        self.fifo = fifo
        self.overflow = overflow

    def gen(self):
        count = Signal(intbv(0, 0, self.count + 1))

        D = 8
        d = Signal(intbv(0, 0, D))

        @always(self.sample_clk.posedge)
        def sample_seq():
            self.fifo.WR.next = 0
            self.fifo.WR_DATA.next = self.sample_data

            if self.sample_enable:
                if d != 0:
                    d.next = d - 1
                elif count != self.count:
                    if self.fifo.WR_FULL:
                        self.overflow.next = 1
                    else:
                        self.fifo.WR.next = 1
                    count.next = count + 1

            else:
                d.next = D - 1
                count.next = 0
                self.overflow.next = 0

        return sample_seq

# This one could actually be split into two parts, one part that does
# the writing and another part that writes the command and address
# whenever the fifo becomes full enough
class MigFifoWriter(object):
    def __init__(self, system, fifo, port, enable, base, chunk, stride):
        self.system = system

        self.fifo = fifo

        self.port = port
        self.enable = enable

        self.base = base
        self.chunk = chunk
        self.stride = stride

    def gen(self):
        fifo = self.fifo
        port = self.port

        addr = Signal(intbv(self.base)[len(port.cmd_byte_addr):])
        chunk = Signal(intbv(0, 0, self.chunk))

        @always(self.system.CLK.posedge)
        def seq():
            port.cmd_en.next = 0
            port.cmd_byte_addr.next = addr << 2
            port.cmd_instr.next = 0
            port.cmd_bl.next = self.chunk - 1

            port.wr_en.next = 0
            port.wr_mask.next = 0

            self.fifo.RD.next = 0

            if not self.enable:
                addr.next = self.base

            else:
                # We can not use wr_full since it is registered and
                # shows the full status once cycle too late.  Use the
                # count instead and keep a bit of a margin.

                if (not fifo.RD_EMPTY and
                    not port.cmd_full and
                    port.wr_count < 60):
                    self.fifo.RD.next = 1
                    port.wr_en.next = 1

                    if chunk == self.chunk - 1:
                        chunk.next = 0
                        port.cmd_en.next = 1
                        addr.next = addr + self.stride

                    else:
                        chunk.next = chunk + 1

        @always_comb
        def comb():
            port.wr_data.next = self.fifo.RD_DATA

        return instances()

_n = 0

class MigSampler(object):
    def __init__(self, sample_clk, sample_data, sample_enable,
                 system, port, overflow,
                 base = 0, chunk = 32, stride = 32,
                 count = 4 * 1024 * 1024, fifo_depth = 512):
        self.sample_clk = sample_clk
        self.sample_data = sample_data
        self.sample_enable = sample_enable

        self.system = system
        self.port = port
        self.overflow = overflow

        self.count = count
        self.fifo_depth = fifo_depth
        self.base = base
        self.chunk = chunk
        self.stride = stride

    def gen(self):
        rst = Signal(False)

        @always_comb
        def rst_inst():
            rst.next = not self.sample_enable

        if 1:
            fifo = AsyncFifo(rst = rst, wr_clk = self.sample_clk,
                             rd_clk = self.system.CLK,
                             factory = self.sample_data.val,
                             depth = self.fifo_depth)
        else:
            global _n
            fifo = DummyFifo(rst = rst,
                             rd_clk = self.system.CLK,
                             factory = self.sample_data.val,
                             base = _n, inc = 2)
            _n = _n + 1

        fifo_inst = fifo.gen()

        sampler = FifoSampler(sample_clk = self.sample_clk,
                              sample_data = self.sample_data,
                              sample_enable = self.sample_enable,
                              count = self.count,
                              fifo = fifo,
                              overflow = self.overflow)
        sampler_inst = sampler.gen()

        writer = MigFifoWriter(self.system, fifo, self.port,
                               self.sample_enable,
                               base = self.base,
                               chunk = self.chunk,
                               stride = self.stride)
        writer_inst = writer.gen()

        return instances()
