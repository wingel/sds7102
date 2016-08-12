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

    # This is ugly, I haven't figured out how to do a bidirectional
    # FIFO for dq and dm using DQS as a clock yet so I'm winging it
    # and hoping that the DQS timing won't change too much relative to
    # the DDR clock.  If I do this, and use C1 clocking for the IDDR2
    # blocks and have a register which takes data clocked on the
    # negative edge and then samples it on the positive edge I seem to
    # get att read/write SoC bus interface which works.
    #
    # This ought to be done properly, or at least use a calibrated
    # IODELAY2 instead of the ugliness with clocking things on the
    # wrong edge, but well it seems to work and I want to get on with
    # other things for the moment, so...

    di = 120
    do = 0

    dqs_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dqs',
                                            bus.DQS0_I,
                                            bus.DQS1_I,
                                            bus.DQS0_O,
                                            bus.DQS1_O,
                                            bus.DQS0_OE,
                                            bus.DQS1_OE,
                                            dqs,
                                            clk, clk_b,
                                            ddr_alignment = 'C0',
                                            srtype = 'ASYNC',
                                            odelay_value = do + 10)
    insts.append(dqs_iobuf_inst)

    dm_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dm',
                                           bus.DM0_I,
                                           bus.DM1_I,
                                           bus.DM0_O,
                                           bus.DM1_O,
                                           bus.DM0_OE,
                                           bus.DM1_OE,
                                           dm,
                                           clk, clk_b,
                                           ddr_alignment = 'C0',
                                           srtype = 'ASYNC',
                                           idelay_value = di,
                                           odelay_value = do)
    insts.append(dm_iobuf_inst)

    dq_iobuf_inst = iobuf_delay_ddr2_fixed(prefix + 'dq',
                                           bus.DQ0_I,
                                           bus.DQ1_I,
                                           bus.DQ0_O,
                                           bus.DQ1_O,
                                           bus.DQ0_OE,
                                           bus.DQ1_OE,
                                           dq,
                                           clk, clk_b,
                                           ddr_alignment = 'C0',
                                           srtype = 'ASYNC',
                                           idelay_value = di,
                                           odelay_value = do)
    insts.append(dq_iobuf_inst)

    return insts

class Ddr(object):
    def __init__(self):
        self.CL = 3	# CAS latency

    def gen(self, system, ddr_bus, simple_bus):
        aw = len(ddr_bus.A) + len(ddr_bus.BA) + 10

        clk = system.CLK
        rst = system.RST

        assert self.CL >= 3

        rds = [ Signal(False) for i in range(self.CL+1) ]
        rds_reg = [ Signal(False) for i in range(len(rds)-1) ]

        wrs = [ Signal(False) for i in range(self.CL+3) ]
        wrs_reg = [ Signal(False) for i in range(len(wrs)-1) ]

        adrs = [ Signal(intbv(0)[aw:]) for i in range(self.CL+3) ]
        adrs_reg = [ Signal(intbv(0)[aw:]) for i in range(len(adrs)-1) ]

        insts = []

        adr_hi = Signal(intbv(0)[len(ddr_bus.A) + len(ddr_bus.BA):])
        adr_hi_reg = Signal(intbv(0)[len(ddr_bus.A) + len(ddr_bus.BA):])

        rd = Signal(False)
        @always_comb
        def rd_comb():
            rd.next = not ddr_bus.CS_B and ddr_bus.RAS_B and not ddr_bus.CAS_B and ddr_bus.WE_B
        insts.append(rd_comb)

        @always_comb
        def rds_comb():
            rds[0].next = rd
            for i in range(0, len(rds)-1):
                rds[i+1].next = rds_reg[i]
        insts.append(rds_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def rds_seq():
            for i in range(len(rds_reg)):
                rds_reg[i].next = rds[i]
        insts.append(rds_seq)

        wr = Signal(False)
        @always_comb
        def wr_comb():
            wr.next = not ddr_bus.CS_B and ddr_bus.RAS_B and not ddr_bus.CAS_B and not ddr_bus.WE_B
        insts.append(wr_comb)

        @always_comb
        def wrs_comb():
            wrs[0].next = wr
            for i in range(0, len(wrs)-1):
                wrs[i+1].next = wrs_reg[i]
        insts.append(wrs_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def wrs_seq():
            for i in range(len(wrs_reg)):
                wrs_reg[i].next = wrs[i]
        insts.append(wrs_seq)

        @always_comb
        def adrs_comb():
            for i in range(0, len(adrs)-1):
                adrs[i+1].next = adrs_reg[i]
            adrs[0].next = (adr_hi << 10) | ddr_bus.A[10:]
        insts.append(adrs_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def adrs_seq():
            for i in range(len(adrs)-1):
                adrs_reg[i].next = adrs[i]
        insts.append(adrs_seq)

        @always_comb
        def adr_hi_comb():
            adr_hi.next = adr_hi_reg
            if not ddr_bus.CS_B and not ddr_bus.RAS_B and ddr_bus.CAS_B and ddr_bus.WE_B:
                adr_hi.next = ((ddr_bus.A << len(ddr_bus.BA)) | ddr_bus.BA) & ((1<<len(adr_hi))-1)
        insts.append(adr_hi_comb)

        @always_seq (system.CLK.posedge, system.RST)
        def adr_hi_seq():
            for i in range(len(adrs)-1):
                adrs_reg[i].next = adrs[i]
            adr_hi_reg.next = adr_hi
        insts.append(adr_hi_seq)

        wr_data = Signal(intbv(0)[32:])
        wr_mask = Signal(intbv(0)[2:0])
        @always_seq (system.CLK.posedge, system.RST)
        # @always_comb
        def wr_data_seq():
            wr_data.next = (ddr_bus.DQ0_I << 16) | ddr_bus.DQ1_I
            wr_mask.next = (ddr_bus.DM0_I << 16) | ddr_bus.DM1_I
        insts.append(wr_data_seq)

        # Send requests to the simple_bus
        @always_comb
        def simple_bus_seq():
            simple_bus.ADDR.next = 0
            simple_bus.RD.next = 0
            simple_bus.WR.next = 0
            simple_bus.WR_DATA.next = wr_data

            if rds[self.CL-3]:
                simple_bus.ADDR.next = (adrs[self.CL-3]>>1) & ((1<<len(simple_bus.ADDR))-1)
                simple_bus.RD.next = 1

            elif rds[self.CL-2]:
                simple_bus.ADDR.next = ((adrs[self.CL-2]>>1)+1) & ((1<<len(simple_bus.ADDR))-1)
                simple_bus.RD.next = 1

            if wrs[self.CL+1]:
                simple_bus.ADDR.next = (adrs[self.CL+1]>>1) & ((1<<len(simple_bus.ADDR))-1)
                if not wr_mask[0] or not wr_mask[1]:
                    simple_bus.WR.next = 1

            elif wrs[self.CL+2]:
                simple_bus.ADDR.next = ((adrs[self.CL+2]>>1)+1) & ((1<<len(simple_bus.ADDR))-1)
                if not wr_mask[0] or not wr_mask[1]:
                    simple_bus.WR.next = 1

        insts.append(simple_bus_seq)

        @always_comb
        def out_seq():
            ddr_bus.DQS0_O.next = 0
            ddr_bus.DQS1_O.next = 0

            ddr_bus.DQS0_OE.next = 0
            ddr_bus.DQS1_OE.next = 0

            # Speed things up by always letting simple_bus*.RD_DATA out
            ddr_bus.DQ0_O.next = simple_bus.RD_DATA[16:0]
            ddr_bus.DQ1_O.next = simple_bus.RD_DATA[32:16]

            ddr_bus.DQ0_OE.next = 0
            ddr_bus.DQ1_OE.next = 0

            if rds[self.CL-2] or rds[self.CL-1]:
                ddr_bus.DQS0_O.next = (1<<len(ddr_bus.DQS0_O))-1
                ddr_bus.DQS1_O.next = 0

                ddr_bus.DQS0_OE.next = 1
                ddr_bus.DQS1_OE.next = 1

                ddr_bus.DQ0_OE.next = 1
                ddr_bus.DQ1_OE.next = 1

            elif rds[self.CL-3]:
                ddr_bus.DQS0_OE.next = 1
                ddr_bus.DQS1_OE.next = 1

            elif rds[self.CL-0]:
                ddr_bus.DQS0_OE.next = 1
                ddr_bus.DQS1_OE.next = 0

        insts.append(out_seq)

        return insts

if __name__ == '__main__':
    from test_ddr import main
    main()
