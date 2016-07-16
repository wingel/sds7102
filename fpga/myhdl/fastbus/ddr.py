#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('ddr.py')

from myhdl import Signal, intbv, always, always_seq, always_comb

from util import mask, lsh

class DdrBus(object):
    def __init__(self, ba_width, a_width, d_width):
        self.ba_width = ba_width
        self.a_width = a_width
        self.d_width = d_width

        self.CS_B = Signal(True)
        self.RAS_B = Signal(True)
        self.CAS_B = Signal(True)
        self.WE_B = Signal(True)
        self.BA = Signal(intbv(~0)[ba_width:])
        self.A = Signal(intbv(~0)[a_width:])

        self.DQS0_O = Signal(intbv(0)[d_width:])
        self.DQS0_I = Signal(intbv(0)[d_width:])
        self.DQS0_OE = Signal(False)

        self.DM0_I = Signal(intbv(0)[d_width:])
        self.DM0_O = Signal(intbv(0)[d_width:])
        self.DM0_OE = Signal(intbv(0)[d_width:])

        self.DQ0_I = Signal(intbv(~0)[d_width * 8:])
        self.DQ0_O = Signal(intbv(~0)[d_width * 8:])
        self.DQ0_OE = Signal(False)

        self.DQS1_O = Signal(intbv(0)[d_width:])
        self.DQS1_I = Signal(intbv(0)[d_width:])
        self.DQS1_OE = Signal(False)

        self.DM1_I = Signal(intbv(0)[d_width:])
        self.DM1_O = Signal(intbv(0)[d_width:])
        self.DM1_OE = Signal(intbv(0)[d_width:])

        self.DQ1_I = Signal(intbv(~0)[d_width * 8:])
        self.DQ1_O = Signal(intbv(~0)[d_width * 8:])
        self.DQ1_OE = Signal(False)

def ddr_connect(bus, clk, clk_b, rst,
                cs_b, ras_b, cas_b, we_b, ba, a,
                dqs, dm, dq, prefix = ''):
    from spartan6 import iobuf_delay_ddr2_fixed

    insts = []

    @always_seq (clk.posedge, rst)
    def ctl_seq():
        bus.CS_B.next = cs_b
        bus.RAS_B.next = ras_b
        bus.CAS_B.next = cas_b
        bus.WE_B.next = we_b
        bus.BA.next = ba
        bus.A.next = a
    insts.append(ctl_seq)

    dqs_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dqs',
                                            bus.DQS0_I,
                                            bus.DQS1_I,
                                            bus.DQS0_O,
                                            bus.DQS1_O,
                                            bus.DQS0_OE,
                                            bus.DQS1_OE,
                                            dqs,
                                            clk,
                                            ddr_alignment = 'C0',
                                            srtype = 'ASYNC',
                                            odelay_value = 10)
    insts.append(dqs_iobuf_inst)

    dm_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dm',
                                           bus.DM0_I,
                                           bus.DM1_I,
                                           bus.DM0_O,
                                           bus.DM1_O,
                                           bus.DM0_OE,
                                           bus.DM1_OE,
                                           dm,
                                           clk,
                                           ddr_alignment = 'C0',
                                           srtype = 'ASYNC',
                                           odelay_value = 0)
    insts.append(dm_iobuf_inst)

    dq_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dq',
                                           bus.DQ0_I,
                                           bus.DQ1_I,
                                           bus.DQ0_O,
                                           bus.DQ1_O,
                                           bus.DQ0_OE,
                                           bus.DQ1_OE,
                                           dq,
                                           clk,
                                           ddr_alignment = 'C0',
                                           srtype = 'ASYNC',
                                           odelay_value = 0)
    insts.append(dq_iobuf_inst)

    return insts

class DdrSource(object):
    def __init__(self, system, addr_width, data_width):
        self.system = system

        self.ADR = Signal(intbv(0)[addr_width:])
        self.RD = Signal(True)
        self.DAT = Signal(intbv(0)[data_width:])

    def gen(self, *args):
        @always_seq (self.system.CLK.posedge, self.system.RST)
        def seq():
            if self.RD:
                self.DAT.next = self.ADR & mask(self.DAT)
        return seq

class Ddr(object):
    def __init__(self, source0, source1):
        self.source0 = source0
        self.source1 = source1

        self.CL = 3	# CAS latency

    def gen(self, system, bus):
        aw = len(bus.A) + len(bus.BA) + 10

        clk = system.CLK
        rst = system.RST

        assert self.CL >= 3

        rds = [ Signal(False) for i in range(self.CL+1) ]
        rds_reg = [ Signal(False) for i in range(self.CL+0) ]

        adrs = [ Signal(intbv(0)[aw:]) for i in range(self.CL-1) ]
        adrs_reg = [ Signal(intbv(0)[aw:]) for i in range(self.CL-2) ]

        src0 = self.source0
        src1 = self.source1

        insts = []

        src0_inst = src0.gen()
        insts.append(src0_inst)
        src1_inst = src1.gen()
        insts.append(src1_inst)

        adr_hi = Signal(intbv(0)[len(bus.A) + len(bus.BA):])
        adr_hi_reg = Signal(intbv(0)[len(bus.A) + len(bus.BA):])

        @always_comb
        def rds_comb():
            for i in range(0, len(rds)-1):
                rds[i+1].next = rds_reg[i]

            rds[0].next = 0
            if not bus.CS_B and bus.RAS_B and not bus.CAS_B and bus.WE_B:
                rds[0].next = 1
        insts.append(rds_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def rds_seq():
            for i in range(len(rds_reg)):
                rds_reg[i].next = rds[i]
        insts.append(rds_seq)

        @always_comb
        def adrs_comb():
            for i in range(0, len(adrs)-1):
                adrs[i+1].next = adrs_reg[i]
            adrs[0].next = (adr_hi << 10) | bus.A[10:]
        insts.append(adrs_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def adrs_seq():
            for i in range(len(adrs)-1):
                adrs_reg[i].next = adrs[i]
        insts.append(adrs_seq)

        @always_comb
        def adr_hi_comb():
            adr_hi.next = adr_hi_reg
            if not bus.CS_B and not bus.RAS_B and bus.CAS_B and bus.WE_B:
                adr_hi.next = ((bus.A << len(bus.BA)) | bus.BA) & ((1<<len(adr_hi))-1)
        insts.append(adr_hi_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def adr_hi_seq():
            for i in range(len(adrs)-1):
                adrs_reg[i].next = adrs[i]
            adr_hi_reg.next = adr_hi
        insts.append(adr_hi_seq)

        # Send requests to the source
        # @always_seq (system.CLK.posedge, system.RST)
        @always_comb
        def src_seq():
            src0.ADR.next = 0
            src0.RD.next = 0

            src1.ADR.next = 0
            src1.RD.next = 0

            if rds[self.CL-3]:
                src0.ADR.next = adrs[self.CL-3] & ((1<<len(src0.ADR))-1)
                src0.RD.next = 1

                src1.ADR.next = (adrs[self.CL-3] + 1) & ((1<<len(src1.ADR))-1)
                src1.RD.next = 1

            elif rds[self.CL-2]:
                src0.ADR.next = (adrs[self.CL-2] + 2) & ((1<<len(src0.ADR))-1)
                src0.RD.next = 1

                src1.ADR.next = (adrs[self.CL-2] + 3) & ((1<<len(src1.ADR))-1)
                src1.RD.next = 1

        insts.append(src_seq)

        @always_comb
        def out_seq():
            bus.DQS0_O.next = 0
            bus.DQS1_O.next = 0

            bus.DQS0_OE.next = 0
            bus.DQS1_OE.next = 0

            # Speed things up by always letting src*.DAT out
            bus.DQ0_O.next = src0.DAT
            bus.DQ1_O.next = src1.DAT

            bus.DQ0_OE.next = 0
            bus.DQ1_OE.next = 0

            if rds[self.CL-2] or rds[self.CL-1]:
                bus.DQS0_O.next = (1<<len(bus.DQS0_O))-1
                bus.DQS1_O.next = 0

                bus.DQS0_OE.next = 1
                bus.DQS1_OE.next = 1

                bus.DQ0_OE.next = 1
                bus.DQ1_OE.next = 1

            elif rds[self.CL-3]:
                bus.DQS0_OE.next = 1
                bus.DQS1_OE.next = 1

        insts.append(out_seq)

        return insts

if __name__ == '__main__':
    from test_ddr import main
    main()
