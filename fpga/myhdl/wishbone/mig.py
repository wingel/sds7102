#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('mig.py')

from myhdl import Signal, ResetSignal, SignalType, instance, always_comb, always_seq, intbv, instances

from spartan6 import pll_adv, bufg, bufgce, bufpll_mcb, mcb_ui_top
from simplebus import SimpleReg, RwField, RoField, DummyField

def mig_with_tb(sys_rst_i, sys_clk_p, sys_clk_n,
                calib_done, error,
                mcb3_dram_ck, mcb3_dram_ck_n,
                mcb3_dram_ras_n, mcb3_dram_cas_n, mcb3_dram_we_n,
                mcb3_dram_ba, mcb3_dram_a, mcb3_dram_odt,
                mcb3_dram_dqs, mcb3_dram_dqs_n,
                mcb3_dram_udqs, mcb3_dram_udqs_n,
                mcb3_dram_dm, mcb3_dram_udm,
                mcb3_dram_dq,
                soc_clk, soc_clk_b = ''):

    sys_rst_i.read = True
    sys_clk_p.read = True
    sys_clk_n.read = True

    calib_done.driven = 'wire'
    error.driven = 'wire'

    mcb3_dram_ck.driven = 'wire'
    mcb3_dram_ck_n.driven = 'wire'

    mcb3_dram_ras_n.driven = 'wire'
    mcb3_dram_cas_n.driven = 'wire'
    mcb3_dram_we_n.driven = 'wire'

    mcb3_dram_ba.driven = 'wire'
    mcb3_dram_a.driven = 'wire'
    mcb3_dram_odt.driven = 'wire'

    mcb3_dram_dqs.read = True
    mcb3_dram_dqs.driven = 'wire'
    mcb3_dram_dqs_n.read = True
    mcb3_dram_dqs_n.driven = 'wire'

    mcb3_dram_udqs.read = True
    mcb3_dram_udqs.driven = 'wire'
    mcb3_dram_udqs_n.read = True
    mcb3_dram_udqs_n.driven = 'wire'

    mcb3_dram_dm.read = True
    mcb3_dram_dm.driven = 'wire'

    mcb3_dram_udm.read = True
    mcb3_dram_udm.driven = 'wire'

    mcb3_dram_dq.read = True
    mcb3_dram_dq.driven = 'wire'

    soc_clk.driven = 'wire'
    if isinstance(soc_clk_b, SignalType):
        soc_clk_b.driven = 'wire'

    @always_comb
    def comb():
        error = None
        if sys_rst_i:
            calib_done.next = 0
        else:
            calib_done.next = 1

    return comb

mig_with_tb.verilog_code = r'''
example_top #(
	.C3_CALIB_SOFT_IP("FALSE")
) mig_inst_internal (
         .c3_sys_rst_i                      ($sys_rst_i),

         .c3_sys_clk_p                      ($sys_clk_p),  // [input] differential p type clock from board
         .c3_sys_clk_n                      ($sys_clk_n),  // [input] differential n type clock from board

         .calib_done                     ($calib_done),
         .error                          ($error),

         .mcb3_dram_a                    ($mcb3_dram_a),
         .mcb3_dram_ba                   ($mcb3_dram_ba),
         .mcb3_dram_ras_n                ($mcb3_dram_ras_n),
         .mcb3_dram_cas_n                ($mcb3_dram_cas_n),
         .mcb3_dram_we_n                 ($mcb3_dram_we_n),
         .mcb3_dram_ck                   ($mcb3_dram_ck),
         .mcb3_dram_ck_n                 ($mcb3_dram_ck_n),
         .mcb3_dram_dq                   ($mcb3_dram_dq),
         .mcb3_dram_dqs                  ($mcb3_dram_dqs),
         .mcb3_dram_dqs_n                ($mcb3_dram_dqs_n),
         .mcb3_dram_udqs                 ($mcb3_dram_udqs),
         .mcb3_dram_udqs_n               ($mcb3_dram_udqs_n),
         .mcb3_dram_udm                  ($mcb3_dram_udm),
         .mcb3_dram_dm                   ($mcb3_dram_dm),
         .mcb3_dram_odt                  ($mcb3_dram_odt),
         .mcb3_dram_cke                  (),
         .mcb3_rzq			 (),
         .soc_clk                        ($soc_clk),
         .soc_clk_b                      ($soc_clk_b)
);
'''

class MigPort(object):
    def __init__(self, mig, clk, data_width = 32):
        self.mig = mig

        self.cmd_clk = clk
        self.cmd_en = Signal(False)
        self.cmd_instr = Signal(intbv(0)[3:])
        self.cmd_bl = Signal(intbv(0)[6:])
        self.cmd_byte_addr = Signal(intbv(0)[29:])
        self.cmd_empty = Signal(False)
        self.cmd_full = Signal(False)

        self.wr_clk = clk
        self.wr_en = Signal(False)
        self.wr_mask = Signal(intbv(0)[data_width/8:])
        self.wr_data = Signal(intbv(0)[data_width:])
        self.wr_full = Signal(False)
        self.wr_empty = Signal(False)
        self.wr_count = Signal(intbv(0)[7:])
        self.wr_underrun = Signal(False)
        self.wr_error = Signal(False)

        self.rd_clk = clk
        self.rd_en = Signal(False)
        self.rd_data = Signal(intbv(0)[data_width:])
        self.rd_full = Signal(False)
        self.rd_empty = Signal(False)
        self.rd_count = Signal(intbv(0)[7:])
        self.rd_overflow = Signal(False)
        self.rd_error = Signal(False)

    def status_reg(self, system, name):
        # Port status register, all the status bits from cmd, wr and rd

        reg = SimpleReg(system,
                        'mig_status_%s' % name,
                        "MIG status for port %s" % name, [
            RoField('rd_count', "", self.rd_count),
            DummyField(1),
            RoField('rd_empty', "", self.rd_empty),
            RoField('rd_full', "", self.rd_full),
            RoField('rd_error', "", self.rd_error),
            RoField('rd_overflow', "", self.rd_overflow),
            RoField('wr_count', "", self.wr_count),
            DummyField(1),
            RoField('wr_empty', "", self.wr_empty),
            RoField('wr_full', "", self.wr_full),
            RoField('wr_error', "", self.wr_error),
            RoField('wr_underrun', "", self.wr_underrun),
            RoField('cmd_empty', "", self.cmd_empty),
            RoField('cmd_full', "", self.cmd_full),
        ])
        reg_inst = reg.gen()

        return reg.bus(), instances()

    def count_reg(self, system, name):
        # Just a count of MIG read/write strobes for debugging
        rd = Signal(intbv(0)[16:])
        wr = Signal(intbv(0)[16:])

        reg = SimpleReg(system,
                        'mig_counts_%s' % name,
                        "MIG counts for port %s", [
            RoField('rd_count', "", rd),
            RoField('wr_count', "", wr),
            ])
        reg_inst = reg.gen()

        @always_seq(self.wr_clk.posedge, self.mig.rst)
        def wr_seq():
            if self.wr_en:
                wr.next = wr + 1

        @always_seq(self.rd_clk.posedge, self.mig.rst)
        def rd_seq():
            if self.rd_en:
                rd.next = rd + 1

        return reg.bus(), instances()

class Mig(object):
    def __init__(self, clkin):
        self.clkin = clkin

        self.rst = ResetSignal(True, True, True)

        # Memory data transfer clock period (ps)
        self.MEMCLK_PERIOD = 3000

        self.DIVCLK_DIVIDE = 1
        self.CLKFBOUT_MULT = 6    # 133 / 1 * 6 = 800 MHz
        self.CLKFBOUT_MULT = 5    # 133 / 1 * 5 = 666 MHz

        self.CLKOUT0_DIVIDE = 1
        self.CLKOUT1_DIVIDE = 1
        self.CLKOUT2_DIVIDE = 20
        self.CLKOUT3_DIVIDE = 10

        self.calib_done = Signal(False)

        self.soc_clk = Signal(False)
        self.soc_clk_b = Signal(False)

        self.mcbx_dram_clk = Signal(False)
        self.mcbx_dram_clk_n = Signal(False)
        self.mcbx_dram_cke = ''

        self.mcbx_dram_ras_n = Signal(False)
        self.mcbx_dram_cas_n = Signal(False)
        self.mcbx_dram_we_n = Signal(False)

        self.mcbx_dram_ba = Signal(intbv(0)[2:])
        self.mcbx_dram_addr = Signal(intbv(0)[13:])

        self.mcbx_dram_dqs = Signal(False)
        self.mcbx_dram_dqs_n = Signal(False)
        self.mcbx_dram_udqs = Signal(False)
        self.mcbx_dram_udqs_n = Signal(False)

        self.mcbx_dram_udm = Signal(False)
        self.mcbx_dram_ldm = Signal(False)
        self.mcbx_dram_dq = Signal(intbv(0)[16:])

        self.mcbx_dram_odt = ''
        self.mcbx_dram_ddr3_rst = ''

        self.mcbx_rzq = ''
        self.mcbx_zio = ''

        self.ports = [ None for _ in range(6) ]

    def control_reg(self, system):
        reg = SimpleReg(system, 'mig_control', "MIG control", [
            RwField('reset', "Reset", self.rst),
            RoField('calib_done', "Calib Done", self.calib_done),
        ])
        reg_inst = reg.gen()

        return reg.bus(), reg_inst

    def gen(self):
        INCLK_PERIOD = ((self.MEMCLK_PERIOD * self.CLKFBOUT_MULT) /
                          (self.DIVCLK_DIVIDE * self.CLKOUT0_DIVIDE * 2))

        CLK_PERIOD_NS = INCLK_PERIOD / 1000.0

        CLK_2X_DIVIDE = 1
        C_CLKOUT2_DIVIDE = 20
        C_CLKOUT3_DIVIDE = 10
        SOC_CLK_DIVIDE = self.CLKFBOUT_MULT

        clkfbout_clkfbin = Signal(False)
        clk_2x_0 = Signal(False)
        clk_2x_180 = Signal(False)

        clk0_bufg = Signal(False)
        clk0_bufg_in = Signal(False)

        mcb_drp_clk = Signal(False)
        mcb_drp_clk_bufg_in = Signal(False)

        soc_clk_bufg_in = Signal(False)
        soc_clk_b_bufg_in = Signal(False)

        locked = Signal(False)

        RST_SYNC_NUM = 25

        insts = []
        pll_adv_inst = pll_adv(
            'mig_pll_adv_inst',

            # Do not pass the reset the PLL, since PLL is used to
            # generate the SoC clock resetting it will break things
            rst                 = 0,

            DIVCLK_DIVIDE       = self.DIVCLK_DIVIDE,
            CLKFBOUT_MULT       = self.CLKFBOUT_MULT,

            clkin1		= self.clkin,
            CLKIN1_PERIOD       = CLK_PERIOD_NS,
            CLKIN2_PERIOD       = CLK_PERIOD_NS,

            clkfbin		= clkfbout_clkfbin,
            clkfbout		= clkfbout_clkfbin,

            clkout0		= clk_2x_0,
            CLKOUT0_DIVIDE      = CLK_2X_DIVIDE,
            CLKOUT0_PHASE       = 0.000,

            clkout1		= clk_2x_180,
            CLKOUT1_DIVIDE      = CLK_2X_DIVIDE,
            CLKOUT1_PHASE       = 180.000,

            clkout2		= clk0_bufg_in,
            clkout3		= mcb_drp_clk_bufg_in,
            CLKOUT2_DIVIDE      = C_CLKOUT2_DIVIDE,
            CLKOUT3_DIVIDE      = C_CLKOUT3_DIVIDE,

            clkout4		= soc_clk_bufg_in,
            CLKOUT4_DIVIDE      = SOC_CLK_DIVIDE,
            CLKOUT4_PHASE       = 0.000,

            clkout5             = soc_clk_b_bufg_in,
            CLKOUT5_DIVIDE      = SOC_CLK_DIVIDE,
            CLKOUT5_PHASE       = 180.000,

            locked		= locked,

            BANDWIDTH           = "OPTIMIZED",
            )
        insts.append(pll_adv_inst)

        clk0_bufg_inst = bufg('clk0_bufg_inst', clk0_bufg_in, clk0_bufg)
        insts.append(clk0_bufg_inst)

        mcb_drp_clk_bufg_inst = bufgce('mcb_drp_clk_bufg_inst', mcb_drp_clk_bufg_in, mcb_drp_clk, locked)
        insts.append(mcb_drp_clk_bufg_inst)

        soc_clk_bufg_inst = bufgce('soc_clk_bufg_inst', soc_clk_bufg_in, self.soc_clk, locked)
        insts.append(soc_clk_bufg_inst)

        soc_clk_b_bufg_inst = bufgce('soc_clk_b_bufg_inst', soc_clk_b_bufg_in, self.soc_clk_b, locked)
        insts.append(soc_clk_b_bufg_inst)

        sysclk_2x = Signal(False)
        sysclk_2x_180 = Signal(False)

        pll_ce_0 = Signal(False)
        pll_ce_90 = Signal(False)

        bufpll_mcb_locked = Signal(False)

        bufpll_mcb_inst = bufpll_mcb(
            'bufpll_mcb_inst',
            gclk = mcb_drp_clk,
            pllin0 = clk_2x_0,
            pllin1 = clk_2x_180,
            locked = locked,

            ioclk0 = sysclk_2x,
            ioclk1 = sysclk_2x_180,
            serdesstrobe0 = pll_ce_0,
            serdesstrobe1 = pll_ce_90,
            lock = bufpll_mcb_locked
            )
        insts.append(bufpll_mcb_inst)

        powerup_pll_locked = Signal(False)

        @always_seq (mcb_drp_clk.posedge, self.rst)
        def pll_locked_inst():
            if bufpll_mcb_locked:
                powerup_pll_locked.next = 1
        insts.append(pll_locked_inst)

        syn_clk0_powerup_pll_locked = Signal(False)

        @always_seq (clk0_bufg.posedge, self.rst)
        def syn_clk0_locked_inst():
            if bufpll_mcb_locked:
                syn_clk0_powerup_pll_locked.next = 1
        insts.append(syn_clk0_locked_inst)

        kwargs = {}

        def merge(prefix, dst, src):
            if src is None:
                return

            if not isinstance(src, dict):
                src = vars(src)

            for k, v in src.items():
                if isinstance(v, SignalType):
                    dst[prefix + k] = v

        for i, port in enumerate(self.ports):
            merge('p%u_' % i, kwargs, port)

        mcb_ui_inst = mcb_ui_top('mcb_ui_top_inst',
                                 mcbx_dram_clk = self.mcbx_dram_clk,
                                 mcbx_dram_clk_n = self.mcbx_dram_clk_n,
                                 mcbx_dram_cke = self.mcbx_dram_cke,
                                 mcbx_dram_ras_n = self.mcbx_dram_ras_n,
                                 mcbx_dram_cas_n = self.mcbx_dram_cas_n,
                                 mcbx_dram_we_n = self.mcbx_dram_we_n,
                                 mcbx_dram_ba = self.mcbx_dram_ba,
                                 mcbx_dram_addr = self.mcbx_dram_addr,
                                 mcbx_dram_dqs = self.mcbx_dram_dqs,
                                 mcbx_dram_dqs_n = self.mcbx_dram_dqs_n,
                                 mcbx_dram_udqs = self.mcbx_dram_udqs,
                                 mcbx_dram_udqs_n = self.mcbx_dram_udqs_n,
                                 mcbx_dram_ldm = self.mcbx_dram_ldm,
                                 mcbx_dram_udm = self.mcbx_dram_udm,
                                 mcbx_dram_dq = self.mcbx_dram_dq,
                                 mcbx_dram_odt = self.mcbx_dram_odt,
                                 mcbx_dram_ddr3_rst = self.mcbx_dram_ddr3_rst,
                                 mcbx_rzq = self.mcbx_rzq,
                                 mcbx_zio = self.mcbx_zio,

                                 sys_rst = self.rst,

                                 ui_clk = mcb_drp_clk,

                                 sysclk_2x = sysclk_2x,
                                 sysclk_2x_180 = sysclk_2x_180,

                                 pll_ce_0 = pll_ce_0,
                                 pll_ce_90 = pll_ce_90,
                                 pll_lock = bufpll_mcb_locked,

                                 uo_done_cal = self.calib_done,

                                 C_CALIB_SOFT_IP	= "FALSE",
                                 C_MEM_ADDR_ORDER       = "ROW_BANK_COLUMN",

                                 C_PORT_ENABLE          = "6'b111111",
                                 C_PORT_CONFIG          =  "B32_B32_W32_W32_W32_R32",

                                 C_ARB_ALGORITHM        = 0,
                                 C_ARB_NUM_TIME_SLOTS   = 12,
                                 C_ARB_TIME_SLOT_0      = "18'o012345",
                                 C_ARB_TIME_SLOT_1      = "18'o123450",
                                 C_ARB_TIME_SLOT_2      = "18'o234501",
                                 C_ARB_TIME_SLOT_3      = "18'o345012",
                                 C_ARB_TIME_SLOT_4      = "18'o450123",
                                 C_ARB_TIME_SLOT_5      = "18'o501234",
                                 C_ARB_TIME_SLOT_6      = "18'o012345",
                                 C_ARB_TIME_SLOT_7      = "18'o123450",
                                 C_ARB_TIME_SLOT_8      = "18'o234501",
                                 C_ARB_TIME_SLOT_9      = "18'o345012",
                                 C_ARB_TIME_SLOT_10     = "18'o450123",
                                 C_ARB_TIME_SLOT_11     = "18'o501234",

                                 C_NUM_DQ_PINS = 16,
                                 C_MEM_ADDR_WIDTH = 13,
                                 C_MEM_BANKADDR_WIDTH = 2,

                                 C_MEM_TYPE = "DDR2",
                                 C_MEM_DENSITY = "512Mb",
                                 C_MEM_BURST_LEN        = 4,
                                 C_MEM_CAS_LATENCY      = 5,
                                 C_MEM_NUM_COL_BITS     = 10,
                                 C_MEM_DDR2_3_PA_SR     = "FULL",
                                 C_SKIP_IN_TERM_CAL     = 1,

                                 **kwargs
                                 )
        insts.append(mcb_ui_inst)

        return insts

def gen(mig, port):
    return mig.gen()

def main():
    from myhdl import toVerilog
    from util import rename_interface
    from clk import Clk

    clk = Clk(133E6)

    mig = Mig(clk)
    rename_interface(mig, None)

    port = MigPort(mig, mig.fast_clk)
    mig.ports[0] = port
    rename_interface(port, 'p0')

    toVerilog(gen, mig, port)

    print
    print open('gen.v', 'r').read()

if __name__ == '__main__':
    main()
