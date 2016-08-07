#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('image.py')

from pprint import pprint

from myhdl import (Signal, ResetSignal, TristateSignal, ConcatSignal,
                   intbv, always_comb, always_seq)
from rhea.cores.misc import syncro

from spartan6 import (startup_spartan6, bufg,
                      ibufds, ibufgds, ibufgds_diff_out, ibufds_vec, iddr2)

from system import System
from spi_slave import SpiInterface, SpiSlave
from wb import WbMux
from hybrid_counter import HybridCounter
from util import tristate
from regfile import RegFile, Field, RoField, RwField, Port
from ddr import Ddr, DdrBus, ddr_connect
from simplebus import SimpleMux, SimpleAlgo, SimpleRam
from sampler import Sampler
from shifter import Shifter, ShifterBus
from ram import Ram
from mig import Mig, mig_with_tb
from frontpanel import FrontPanel

from simplebus import SimpleReg
from simplebus import RwField as SimpleRwField

def top(din, init_b, cclk,
        ref_clk,
        soc_clk_p, soc_clk_n, soc_cs, soc_ras, soc_cas, soc_we, soc_ba, soc_a,
        soc_dqs, soc_dm, soc_dq,
        adc_clk_p, adc_clk_n, adc_dat_p, adc_dat_n, adc_ovr_p, adc_ovr_n,
        shifter_sck, shifter_sdo,
        bu2506_ld, adf4360_le, adc08d500_cs, lmh6518_cs, dac8532_sync,
        trig_p, trig_n, ba7406_vd, ba7406_hd, ac_trig,
        probe_comp, ext_trig_out,
        i2c_scl, i2c_sda,
        fp_rst, fp_clk, fp_din, led_green, led_white,
        mcb3_dram_ck, mcb3_dram_ck_n,
        mcb3_dram_ras_n, mcb3_dram_cas_n, mcb3_dram_we_n,
        mcb3_dram_ba, mcb3_dram_a, mcb3_dram_odt,
        mcb3_dram_dqs, mcb3_dram_dqs_n, mcb3_dram_udqs, mcb3_dram_udqs_n,
        mcb3_dram_dm, mcb3_dram_udm, mcb3_dram_dq,
        bank2):
    insts = []

    # Clock generator using STARTUP_SPARTAN primitive
    clk_unbuf = Signal(False)
    clk_unbuf_inst = startup_spartan6('startup_inst', cfgmclk = clk_unbuf)
    insts.append(clk_unbuf_inst)

    clk_buf = Signal(False)
    clk_inst = bufg('bufg_clk', clk_unbuf, clk_buf)
    insts.append(clk_inst)

    spi_system = System(clk_buf, None)

    mux = WbMux()

    # Rename and adapt external SPI bus signals
    slave_spi_bus = SpiInterface()
    slave_cs = Signal(False)
    slave_cs_inst = syncro(clk_buf, din, slave_spi_bus.CS)
    insts.append(slave_cs_inst)
    slave_sck_inst = syncro(clk_buf, cclk, slave_spi_bus.SCK)
    insts.append(slave_sck_inst)
    slave_sdioinst = tristate(init_b,
                              slave_spi_bus.SD_I,
                              slave_spi_bus.SD_O, slave_spi_bus.SD_OE)
    insts.append(slave_sdioinst)

    ####################################################################
    # DDR memory

    # The DDR memory controller uses the SoC clk as the input to its
    # PLL.  It also generates soc_clk.
    soc_clk = Signal(False)
    soc_clk._name = 'soc_clk' # Must match name of timing spec in ucf file
    soc_clk_b = Signal(False)
    soc_clk_b._name = 'soc_clk_b' # Must match name of timing spec in ucf file

    dram_rst = ResetSignal(val = False, active = True, async = True)
    dram_calib_done = Signal(False)
    dram_error = Signal(False)

    dram_ctl = RegFile('dram_ctl', "DRAM control", [
        RwField(spi_system, 'dram_rst_i', "Reset", dram_rst),
        RoField(spi_system, 'dram_calib_done', "Calib flag", dram_calib_done),
#        RoField(spi_system, 'dram_error', "Error flag", dram_error),
        ])
    mux.add(dram_ctl, 0x250)

    if 0:
        dram_clk_p = soc_clk_p
        dram_clk_n = soc_clk_n

        mig_inst = mig_with_tb(
            dram_rst, dram_clk_p, dram_clk_n,
            dram_calib_done, dram_error,

            mcb3_dram_ck, mcb3_dram_ck_n,
            mcb3_dram_ras_n, mcb3_dram_cas_n, mcb3_dram_we_n,
            mcb3_dram_ba, mcb3_dram_a, mcb3_dram_odt,
            mcb3_dram_dqs, mcb3_dram_dqs_n, mcb3_dram_udqs, mcb3_dram_udqs_n,
            mcb3_dram_dm, mcb3_dram_udm, mcb3_dram_dq,
            soc_clk, soc_clk_b)
        insts.append(mig_inst)

    else:
        soc_clk_ibuf = Signal(False)
        soc_clk_ibuf_inst = ibufgds('soc_clk_ibuf_inst',
                                    soc_clk_p, soc_clk_n,
                                    soc_clk_ibuf)
        insts.append(soc_clk_ibuf_inst)

        mig = Mig()
        mig.rst = dram_rst
        mig.clkin = soc_clk_ibuf
        mig.soc_clk = soc_clk
        mig.soc_clk_b = soc_clk_b

        mig.calib_done = dram_calib_done

        mig.mcbx_dram_addr = mcb3_dram_a
        mig.mcbx_dram_ba = mcb3_dram_ba
        mig.mcbx_dram_ras_n = mcb3_dram_ras_n
        mig.mcbx_dram_cas_n = mcb3_dram_cas_n
        mig.mcbx_dram_we_n = mcb3_dram_we_n
        mig.mcbx_dram_clk = mcb3_dram_ck
        mig.mcbx_dram_clk_n = mcb3_dram_ck_n
        mig.mcbx_dram_dq = mcb3_dram_dq
        mig.mcbx_dram_dqs = mcb3_dram_dqs
        mig.mcbx_dram_dqs_n = mcb3_dram_dqs_n
        mig.mcbx_dram_udqs = mcb3_dram_udqs
        mig.mcbx_dram_udqs_n = mcb3_dram_udqs_n
        mig.mcbx_dram_udm = mcb3_dram_udm
        mig.mcbx_dram_ldm = mcb3_dram_dm

        mig_inst = mig.gen()
        insts.append(mig_inst)

    ####################################################################
    # A MUX and some test code for it

    soc_system = System(soc_clk, None)

    sm = SimpleMux(soc_system)

    if 1:
        # Some RAM
        sr = SimpleRam(soc_system, 1024, 32)
        sr_inst = sr.gen()
        insts.append(sr_inst)
        sm.add(sr.bus(), addr = 0x8000)

    if 1:
        # A read only area which returns predictable patterns
        sa = SimpleAlgo(soc_system, (1<<16), 32)
        sa_inst = sa.gen()
        insts.append(sa_inst)
        sm.add(sa.bus(), 0x10000)

    ####################################################################
    # Front panel attached to the SoC bus

    frontpanel = FrontPanel(soc_system, fp_rst, fp_clk, fp_din)
    frontpanel_inst = frontpanel.gen()
    insts.append(frontpanel_inst)

    # These need to be spaced a bit apart, otherwise burst will make
    # us read from the data_bus register when we only want to read the
    # ctl_bus register.
    sm.add(frontpanel.ctl_bus, addr = 0x100)
    sm.add(frontpanel.data_bus, addr = 0x104)

    ####################################################################
    # LEDs on the front panel

    led_green_tmp = Signal(False)
    led_white_tmp = Signal(False)

    misc_reg = SimpleReg(soc_system, 'misc', "Miscellaneous", [
        SimpleRwField('green', "Green LED", led_green_tmp),
        SimpleRwField('white', "White LED", led_white_tmp),
        ])

    sm.add(misc_reg.bus(), addr = 0x108)
    insts.append(misc_reg.gen())

    @always_comb
    def led_inst():
        led_green.next = led_green_tmp
        led_white.next = led_white_tmp
    insts.append(led_inst)

    ####################################################################
    # SoC bus

    # First finish the MUX
    sm.addr_depth = 32 * 1024 * 1024
    sm_inst = sm.gen()
    insts.append(sm_inst)
    simple_bus = sm.bus()

    soc_bus = DdrBus(2, 12, 2)

    # And attach the MUX bus to the SoC bus
    soc_ddr = Ddr()
    soc_inst = soc_ddr.gen(soc_system, soc_bus, simple_bus)
    insts.append(soc_inst)

    soc_connect_inst = ddr_connect(
        soc_bus, soc_clk, soc_clk_b, None,
        soc_cs, soc_ras, soc_cas, soc_we, soc_ba, soc_a,
        soc_dqs, soc_dm, soc_dq)
    insts.append(soc_connect_inst)

    if 1:

        soc_capture = Signal(False)
        soc_ctl = RegFile('soc_ctl', "SOC control", [
            RwField(spi_system, 'soc_capture', "Capture samples", soc_capture),
            ])
        mux.add(soc_ctl, 0x231)
        soc_capture_sync = Signal(False)
        soc_capture_sync_inst = syncro(soc_clk, soc_capture, soc_capture_sync)
        insts.append(soc_capture_sync_inst)

        soc_sdr = ConcatSignal(
            soc_a, soc_ba, soc_we, soc_cas, soc_ras, soc_cs)

        soc_sdr_sampler = Sampler(addr_depth = 0x800,
                                  sample_clk = soc_clk,
                                  sample_data = soc_sdr,
                                  sample_enable = soc_capture_sync)
        mux.add(soc_sdr_sampler, 0x2000)

        soc_reg = ConcatSignal(
            soc_bus.A, soc_bus.BA,
            soc_bus.WE_B, soc_bus.CAS_B, soc_bus.RAS_B, soc_bus.CS_B)

        soc_reg_sampler = Sampler(addr_depth = 0x800,
                                   sample_clk = soc_clk,
                                   sample_data = soc_reg,
                                   sample_enable = soc_capture_sync)
        mux.add(soc_reg_sampler, 0x2800)

        soc_ddr_0 = ConcatSignal(soc_bus.DQ1_OE, soc_bus.DQS1_O, soc_bus.DQS1_OE, soc_bus.DQ0_I, soc_bus.DM0_I, soc_bus.DQS0_I)
        soc_ddr_1 = ConcatSignal(soc_bus.DQ0_OE, soc_bus.DQS0_O, soc_bus.DQS0_OE, soc_bus.DQ1_I, soc_bus.DM1_I, soc_bus.DQS1_I)

        soc_ddr_sampler_0 = Sampler(addr_depth = 0x800,
                                    sample_clk = soc_clk,
                                    sample_data = soc_ddr_0,
                                    sample_enable = soc_capture_sync)
        mux.add(soc_ddr_sampler_0, 0x3000)

        soc_ddr_sampler_1 = Sampler(addr_depth = 0x800,
                                    sample_clk = soc_clk,
                                    sample_data = soc_ddr_1,
                                    sample_enable = soc_capture_sync)
        mux.add(soc_ddr_sampler_1, 0x3800)

    ####################################################################
    # ADC bus

    adc_clk_ibuf = Signal(False)
    adc_clk_ibuf_b = Signal(False)
    adc_clk_ibuf_inst = ibufgds_diff_out('ibufgds_diff_out_adc_clk', adc_clk_p, adc_clk_n, adc_clk_ibuf, adc_clk_ibuf_b)
    insts.append(adc_clk_ibuf_inst)

    if 0:
        adc_clk = Signal(False)
        adc_clk_buf_inst = bufg('bufg_adc_clk', adc_clk_ibuf, adc_clk)
        insts.append(adc_clk_buf_inst)

        adc_clk_b = Signal(False)
        adc_clk_b_buf_inst = bufg('bufg_adc_clk_b', adc_clk_ibuf_b, adc_clk_b)
        insts.append(adc_clk_b_buf_inst)
    else:
        adc_clk = adc_clk_ibuf
        adc_clk_b = adc_clk_ibuf_b

    adc_clk._name = 'adc_clk' # Must match name of timing spec in ucf file
    adc_clk_b._name = 'adc_clk_b' # Must match name of timing spec in ucf file

    if 0:
        # For some reason myhdl doesn't recognize these signals
        adc_dat_p._name = 'adc_dat_p'
        adc_dat_n._name = 'adc_dat_n'

    if 0:
        adc_dat_p.read = True
        adc_dat_n.read = True

    print "adc_dat_p", type(adc_dat_p), len(adc_dat_p)
    print "adc_dat_n", type(adc_dat_n), len(adc_dat_n)

    if 0:
        adc_dat_array = [ Signal(False) for _ in range(len(adc_dat_p)) ]
        for i in range(len(adc_dat_p)):
            adc_dat_inst = ibufds('ibufds_adc_dat%d' % i,
                                  adc_dat_p[i], adc_dat_n[i], adc_dat_array[i])
            insts.append(adc_dat_inst)

        print 'adc_dat_array', adc_dat_array

        adc_dat = ConcatSignal(*adc_dat_array)

        print len(adc_dat)

    else:
        adc_dat = Signal(intbv(0)[len(adc_dat_p):])
        if 0:
            adc_dat._name = 'adc_dat'
            adc_dat.read = True
        adc_dat_inst = ibufds_vec('adc_dat_ibufds', adc_dat_p, adc_dat_n, adc_dat)
        insts.append(adc_dat_inst)

    adc_dat_0 = Signal(intbv(0)[len(adc_dat):])
    adc_dat_1 = Signal(intbv(0)[len(adc_dat):])
    adc_dat_ddr_inst = iddr2('adc_dat_iddr2',
                             adc_dat, adc_dat_0, adc_dat_1,
                             c0 = adc_clk, c1 = adc_clk_b,
                             ddr_alignment = 'C0')
    insts.append(adc_dat_ddr_inst)

    adc_ovr = Signal(False)
    adc_ovr_inst = ibufds('ibufds_adc_ovr', adc_ovr_p, adc_ovr_n, adc_ovr)
    insts.append(adc_ovr_inst)

    if 1:
        adc_capture = Signal(False)
        adc_ctl = RegFile('adc_ctl', "ADC control", [
            RwField(spi_system, 'adc_capture', "Capture samples", adc_capture),
            ])
        mux.add(adc_ctl, 0x230)

        adc_capture_sync = Signal(False)
        adc_capture_sync_inst = syncro(adc_clk, adc_capture, adc_capture_sync)
        insts.append(adc_capture_sync_inst)

        adc_sampler_0 = Sampler(addr_depth = 1024,
                                sample_clk = adc_clk,
                                sample_data = adc_dat_0,
                                sample_enable = adc_capture_sync,
                                skip_cnt = 99)
        mux.add(adc_sampler_0, 0x4000)

        adc_sampler_1 = Sampler(addr_depth = 1024,
                                sample_clk = adc_clk,
                                sample_data = adc_dat_1,
                                sample_enable = adc_capture_sync,
                                skip_cnt = 99)
        mux.add(adc_sampler_1, 0x6000)

    ####################################################################
    # Analog frontend

    if 1:
        shifter_bus = ShifterBus(6)

        @always_comb
        def shifter_comb():
            shifter_sck.next = shifter_bus.SCK
            shifter_sdo.next = shifter_bus.SDO

            bu2506_ld.next = shifter_bus.CS[0]
            adf4360_le.next = shifter_bus.CS[1]
            adc08d500_cs.next = not shifter_bus.CS[2]
            lmh6518_cs.next[0] = not shifter_bus.CS[3]
            lmh6518_cs.next[1] = not shifter_bus.CS[4]
            dac8532_sync.next = not shifter_bus.CS[5]
        insts.append(shifter_comb)

        shifter = Shifter(spi_system, shifter_bus, divider = 100)
        addr = 0x210
        for reg in shifter.create_regs():
            mux.add(reg, addr)
            addr += 1
        insts.append(shifter.gen())

    trig = Signal(intbv(0)[len(trig_p):])
    trig_inst = ibufds_vec('ibufds_trig', trig_p, trig_n, trig)
    insts.append(trig_inst)

    ####################################################################
    # Probe compensation output and external trigger output
    # Just toggle them at 1kHz

    probe_comb_div = 25000
    probe_comp_ctr = Signal(intbv(0, 0, probe_comb_div))
    probe_comp_int = Signal(False)
    @always_seq (spi_system.CLK.posedge, spi_system.RST)
    def probe_comp_seq():
        if probe_comp_ctr == probe_comb_div - 1:
            probe_comp_int.next = not probe_comp_int
            probe_comp_ctr.next = 0
        else:
            probe_comp_ctr.next = probe_comp_ctr + 1
    insts.append(probe_comp_seq)
    @always_comb
    def probe_comp_comb():
        probe_comp.next = probe_comp_int
        ext_trig_out.next = probe_comp_int
    insts.append(probe_comp_comb)

    ####################################################################
    # Random stuff

    if 1:
        pins = ConcatSignal(cclk,
                            i2c_sda, i2c_scl,
                            ext_trig_out, probe_comp,
                            ac_trig, ba7406_hd, ba7406_vd, trig,
                            ref_clk,
                            bank2)
        hc = HybridCounter()
        mux.add(hc, 0, pins)

    # I have a bug somewhere in my Mux, unless I add this the adc
    # sample buffer won't show up in the address range.  I should fix
    # it but I haven't managed to figure out what's wrong yet.
    if 1:
        ram3 = Ram(addr_depth = 1024, data_width = 32)
        mux.add(ram3, 0x8000)

    wb_slave = mux

    # Create the wishbone bus
    wb_bus = wb_slave.create_bus()
    wb_bus.CLK_I = clk_buf
    wb_bus.RST_I = None

    # Create the SPI slave
    spi = SpiSlave()
    spi.addr_width = 32
    spi.data_width = 32

    wb_inst = wb_slave.gen(wb_bus)
    insts.append(wb_inst)

    slave_spi_inst = spi.gen(slave_spi_bus, wb_bus)
    insts.append(slave_spi_inst)

    return insts

def impl():
    from rhea.build.boards import get_board

    brd = get_board('sds7102')
    flow = brd.get_flow(top = top)

    if 1:
        flow.add_files([
            '../../../ip/mig/rtl/mcb_controller/iodrp_controller.v',
            '../../../ip/mig/rtl/mcb_controller/iodrp_mcb_controller.v',
            '../../../ip/mig/rtl/mcb_controller/mcb_raw_wrapper.v',
            '../../../ip/mig/rtl/mcb_controller/mcb_soft_calibration.v',
            '../../../ip/mig/rtl/mcb_controller/mcb_soft_calibration_top.v',
            '../../../ip/mig/rtl/mcb_controller/mcb_ui_top.v',
            ])

    if 0:
        flow.add_files([
            '../../../ip/mig/rtl/example_top.v',
            '../../../ip/mig/rtl/infrastructure.v',

            '../../../ip/mig/rtl/memc_wrapper.v',

            '../../../ip/mig/rtl/memc_tb_top.v',
            '../../../ip/mig/rtl/traffic_gen/afifo.v',
            '../../../ip/mig/rtl/traffic_gen/cmd_gen.v',
            '../../../ip/mig/rtl/traffic_gen/cmd_prbs_gen.v',
            '../../../ip/mig/rtl/traffic_gen/data_prbs_gen.v',
            '../../../ip/mig/rtl/traffic_gen/init_mem_pattern_ctr.v',
            '../../../ip/mig/rtl/traffic_gen/mcb_flow_control.v',
            '../../../ip/mig/rtl/traffic_gen/mcb_traffic_gen.v',
            '../../../ip/mig/rtl/traffic_gen/rd_data_gen.v',
            '../../../ip/mig/rtl/traffic_gen/read_data_path.v',
            '../../../ip/mig/rtl/traffic_gen/read_posted_fifo.v',
            '../../../ip/mig/rtl/traffic_gen/sp6_data_gen.v',
            '../../../ip/mig/rtl/traffic_gen/tg_status.v',
            '../../../ip/mig/rtl/traffic_gen/v6_data_gen.v',
            '../../../ip/mig/rtl/traffic_gen/wr_data_gen.v',
            '../../../ip/mig/rtl/traffic_gen/write_data_path.v',
            ])

    flow.run()
    info = flow.get_utilization()
    pprint(info)

if __name__ == '__main__':
    impl()
