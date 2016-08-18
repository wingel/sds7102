#! /usr/bin/python
from myhdl import Signal, ConcatSignal, intbv, always, always_seq, always_comb, instances

from fifo.async import AsyncFifo
from fifo.dummy import DummyFifo, DummyReadFifo
from fifo.interleaver import FifoInterleaver

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

        @always(self.sample_clk.posedge)
        def sample_seq():
            self.fifo.WR.next = 0
            self.fifo.WR_DATA.next = self.sample_data

            if self.sample_enable:
                if count != self.count:
                    if self.fifo.WR_FULL:
                        self.overflow.next = 0
                    else:
                        self.fifo.WR.next = 1
                    count.next = count + 1

            else:
                count.next = 0
                self.overflow.next = 1

        return sample_seq

# This one could actually be split into two parts, one part that does
# the writing and another part that writes the command and address
# whenever the fifo becomes full enough
class MigFifoWriter(object):
    def __init__(self, fifo, port, base, chunk, stride):
        assert id(fifo.RD_CLK) == id(port.wr_clk)

        self.fifo = fifo

        self.port = port

        self.base = base
        self.chunk = chunk
        self.stride = stride

    def gen(self):
        fifo = self.fifo
        port = self.port

        addr = Signal(intbv(self.base)[len(port.cmd_byte_addr):])
        chunk = Signal(intbv(0, 0, self.chunk))

        @always_seq(fifo.RD_CLK.posedge, fifo.RD_RST)
        def seq():
            port.cmd_en.next = 0
            port.cmd_byte_addr.next = addr << 2
            port.cmd_instr.next = 0
            port.cmd_bl.next = self.chunk - 1

            port.wr_en.next = 0
            port.wr_mask.next = 0

            self.fifo.RD.next = 0

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

# For some reason MyHdl won't give some instances unique names so use
# this hack to force unique names
def uniqify(s, v, d):
    d['%s_%u' % (s, id(v))] = v

class MigSampler(object):
    def __init__(self, sample_clk, sample_data, sample_enable,
                 mig_port, overflow,
                 count, fifo_depth,
                 base, chunk, stride,
                 split):
        self.sample_clk = sample_clk
        self.sample_data = sample_data
        self.sample_enable = sample_enable

        self.mig_port = mig_port

        self.overflow = Signal(False)

        self.count = count
        self.fifo_depth = fifo_depth

        self.base = base
        self.chunk = chunk
        self.stride = stride

        self.split = split

    def gen(self):
        # I need this otherwise MyHDL will not make this a unique
        # instance and I'll get errors about conflicting definitions
        # in the verilog code
        dummy = Signal(False)
        @always_seq(self.sample_clk.posedge, None)
        def dummy_inst():
            dummy.next = self.overflow

        wr_fifo = AsyncFifo(rst = self.mig_port.mig.rst,
                            wr_clk = self.sample_clk,
                            rd_clk = self.mig_port.wr_clk,
                            factory = self.sample_data.val,
                            depth = self.fifo_depth)
        wr_fifo_inst = wr_fifo.gen()

        if 0:
            if self.base:
                n = 1
            else:
                n = 0

            rd_fifo = DummyReadFifo(rst = self.mig_port.mig.rst,
                                    clk = self.mig_port.wr_clk,
                                    factory = self.sample_data.val,
                                    count = self.count, skip = 0,
                                    base = n, increment = 2)
            rd_fifo_inst = rd_fifo.gen()

        elif self.split:
            rd_fifo = FifoInterleaver(wr_fifo)
            rd_fifo_inst = rd_fifo.gen()

        else:
            rd_fifo = wr_fifo

        sampler = FifoSampler(sample_clk = self.sample_clk,
                              sample_data = self.sample_data,
                              sample_enable = self.sample_enable,
                              count = self.count,
                              fifo = wr_fifo,
                              overflow = self.overflow)
        sampler_inst = sampler.gen()

        writer = MigFifoWriter(fifo = rd_fifo,
                               port = self.mig_port,
                               base = self.base,
                               chunk = self.chunk,
                               stride = self.stride)
        writer_inst = writer.gen()

        return instances()

class MigSampler2(object):
    def __init__(self,
                 sample_clk, sample_data_0, sample_data_1, sample_enable,
                 mig_port_0, mig_port_1, overflow_0, overflow_1,
                 count = 64,
                 fifo_depth = 256):

        self.sample_clk = sample_clk
        self.sample_data_0 = sample_data_0
        self.sample_data_1 = sample_data_1
        self.sample_enable = sample_enable

        self.mig_port_0 = mig_port_0
        self.mig_port_1 = mig_port_1

        self.overflow_0 = overflow_0
        self.overflow_1 = overflow_1

        self.count = count
        self.fifo_depth = fifo_depth

        self.chunk = 32

    def gen(self):
        adc_data = ConcatSignal(self.sample_data_0, self.sample_data_1)

        enable_0 = Signal(False)
        enable_1 = Signal(False)
        enable_cnt = Signal(intbv(0, 0, self.chunk))

        assert self.chunk % 2 == 0
        half_chunk = self.chunk / 2

        @always_comb
        def enable_comb():
            enable_0.next = 0
            enable_1.next = 0

            if self.sample_enable:
                sel = enable_cnt < half_chunk
                enable_0.next = sel
                enable_1.next = not sel

        @always_seq(self.sample_clk.posedge, None)
        def enable_seq():
            if not self.sample_enable:
                enable_cnt.next = 0
            else:
                enable_cnt.next = 0
                if enable_cnt != self.chunk - 1:
                    enable_cnt.next = enable_cnt + 1

        sampler_0 = MigSampler(sample_clk = self.sample_clk,
                               sample_data = adc_data,
                               sample_enable = enable_0,

                               mig_port = self.mig_port_0,
                               overflow = self.overflow_0,

                               count = self.count,
                               fifo_depth = self.fifo_depth,

                               base = 0,
                               chunk = self.chunk,
                               stride = 2 * self.chunk,

                               split = True)
        sampler_0_inst = sampler_0.gen()

        sampler_1 = MigSampler(sample_clk = self.sample_clk,
                               sample_data = adc_data,
                               sample_enable = enable_1,

                               mig_port = self.mig_port_1,
                               overflow = self.overflow_1,

                               count = self.count,
                               fifo_depth = self.fifo_depth,

                               base = self.chunk,
                               chunk = self.chunk,
                               stride = 2 * self.chunk,

                               split = True)
        sampler_1_inst = sampler_1.gen()

        return instances()
