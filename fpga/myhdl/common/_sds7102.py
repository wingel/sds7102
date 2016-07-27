#
# Copyright (c) 2016 Christer Weinigel <christer@weinigel.se>
#

from myhdl import TristateSignal, intbv

from rhea.build import FPGA
from rhea.build.extintf import Port
from rhea.build.toolflow import ISE

class SDS7102(FPGA):
    vendor = 'xilinx'
    family = 'spartan6'
    device = 'XC6SLX9'
    package = 'FTG256'
    speed = '-3'
    version = 3
    _name = 'sds7102'
    no_startup_jtag_clock = True

    default_clocks = {
        #'ref_clk':       dict(frequency = 10e6, pins = ('C10',), iostandard = 'LVCMOS33'),
    }

    default_resets = {
        # rst_n in documentation
        #'reset': dict(active=0, async=True, pins=(38,),
        #              iostandard='LVTTL')
    }

    default_ports = {
        'init_b':	dict(pins = ('R3',),  iostandard = 'LVCMOS18'),
        'cclk':		dict(pins = ('R11',),
                             clock_dedicated_route = False,
                             iostandard = 'LVCMOS18',
                             ),
        'din':		dict(pins = ('P10',), iostandard = 'LVCMOS18'),

        'ref_clk':	dict(pins = ('C10',), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False),

        'soc_clk_p':	dict(pins = ('P7',), iostandard = 'DIFF_SSTL18_II'),
        'soc_clk_n':	dict(pins = ('M7',), iostandard = 'DIFF_SSTL18_II'),

        'soc_cs':       dict(pins = ('B1'), iostandard = 'SSTL18_II'),
        'soc_ras':      dict(pins = ('T8'), iostandard = 'SSTL18_II'),
        'soc_cas':      dict(pins = ('R9'), iostandard = 'SSTL18_II'),
        'soc_we':       dict(pins = ('P6'), iostandard = 'SSTL18_II'),
        'soc_ba':       dict(pins = ('F6',  'N12'), iostandard = 'SSTL18_II'),
        'soc_a':        dict(pins = ('F5',  'M4',  'F4',  'N9',
                                     'R7',  'P12', 'B3',  'L10',
                                     'E4',  'L8',  'M5',  'N4'),
                             iostandard = 'SSTL18_II'),

        # All SOC signals should use the SSTL18_II IO standard but
        # that standard isn't supported for output on bank 2.  At
        # first Xilinx said that it was a bug in ISE that SSTL18_II
        # couldn't be used on bank 2:
        #
        #     http://www.xilinx.com/support/answers/33757.html
        #
        # Later they said that SSTL18_II is just not supported on bank 2:
        #
        #     http://www.xilinx.com/support/answers/34313.html
        #
        # SSTL18_I is supported though.  The differences between
        # SSTL18_I and SSTL18_II as far as I can tell from Xilinx
        # DS162 "Spartan-6 FPGA Data Sheet: DC and Switching
        # Characteristics" is that SSTL18_I has tighter acceptable
        # input range VTT +/- 0.47V instead of VTT +/- 0.60V and that
        # SSTL1_I has a weaker drive strength of 6.7mA instead of
        # 13.4mA for SSTL18_II.  And using SSTL18_I seems to work.

        'soc_dqs':      dict(pins = ('T9', 'M6'), iostandard = 'SSTL18_I'),
        'soc_dm':       dict(pins = ('P11', 'T10'), iostandard = 'SSTL18_I'),
        'soc_dq':       dict(pins = ('T7',  'L7',  'P9',  'N5',
                                     'M11', 'T3',  'M9',  'T4',
                                     'T6',  'M12', 'P4',  'N6',
                                     'N8',  'P5',  'P8',  'R5'),
                             iostandard = 'SSTL18_I'),

        'adc_clk_p':	dict(pins = ('E7',), iostandard = 'LVDS_25'),
        'adc_clk_n':	dict(pins = ('E8',), iostandard = 'LVDS_25'),

        'adc_dat_p':	dict(pins = ('B10', 'C11', 'B12', 'C13', 'F10', 'B14', 'D11', 'E13',
                                     'B15', 'F12', 'D14', 'C15', 'E15', 'F15', 'G14', 'H15',
                                     'G12', 'H13', 'J11', 'J13', 'K12', 'J14', 'K15', 'N14',
                                     'M15', 'L14', 'P15', 'R15', 'R14', 'T14', 'L12', 'M13',
            ), iostandard = 'LVDS_25'),
        'adc_dat_n':	dict(pins = ('A10', 'A11', 'A12', 'A13', 'E11', 'A14', 'D12', 'E12',
                                     'B16', 'G11', 'D16', 'C16', 'E16', 'F16', 'G16', 'H16',
                                     'H11', 'H14', 'J12', 'K14', 'K11', 'J16', 'K16', 'N16',
                                     'M16', 'L16', 'P16', 'R16', 'T15', 'T13', 'L13', 'M14',
                                     ), iostandard = 'LVDS_25'),

        'adc_ovr_p':    dict(pins = ('F13',), iostandard = 'LVDS_25'),
        'adc_ovr_n':    dict(pins = ('F14',), iostandard = 'LVDS_25'),

        'shifter_sck':  dict(pins = ('D9'), iostandard = 'LVCMOS33'),
        'shifter_sdo':  dict(pins = ('D8'), iostandard = 'LVCMOS33'),
        'bu2506_ld':    dict(pins = ('F7'), iostandard = 'LVCMOS33'),
        'adc08d500_cs': dict(pins = ('F9'), iostandard = 'LVCMOS33'),
        'adf4360_le':   dict(pins = ('C7'), iostandard = 'LVCMOS33'),
        'lmh6518_cs':   dict(pins = ('A7', 'C8'), iostandard = 'LVCMOS33'),
        'dac8532_sync': dict(pins = ('A8'), iostandard = 'LVCMOS33'),

        'trig_p':	dict(pins = ('B6', 'C9',),
                             clock_dedicated_route = False,
                             iostandard = 'LVPECL_33',
                             ),
        'trig_n':	dict(pins = ('A6', 'A9',),
                             clock_dedicated_route = False,
                             iostandard = 'LVPECL_33',
                             ),

        'ba7406_vd':    dict(pins = ('D5', 'T12'), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False),
        'ba7406_hd':    dict(pins = ('E6', 'R12'), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False),

        'ac_trig':	dict(pins = ('A4'), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             ),

        'probe_comp':   dict(pins = ('T11',), iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             ),

        'ext_trig_out': dict(pins = ('E10',), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             ),

        'i2c_scl':      dict(pins = ('C4'), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             ),

        'i2c_sda':      dict(pins = ('C5'), iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             ),

        'fp_rst':       dict(pins = ('A5'), iostandard = 'LVCMOS33'),
        'fp_clk':       dict(pins = ('C6'), iostandard = 'LVCMOS33'),
        'fp_din':       dict(pins = ('B5'), iostandard = 'LVCMOS33'),
        'fp_red':       dict(pins = ('D6'), iostandard = 'LVCMOS33'),
        'fp_white':     dict(pins = ('B8'), iostandard = 'LVCMOS33'),

        'mcb3_dram_ck':	    dict(pins = ('E2'),iostandard = 'DIFF_SSTL18_II'),
        'mcb3_dram_ck_n':   dict(pins = ('E1'), iostandard = 'DIFF_SSTL18_II'),

        'mcb3_dram_ras_n':  dict(pins = ('J6'), iostandard = 'SSTL18_II'),
        'mcb3_dram_cas_n':  dict(pins = ('H5'), iostandard = 'SSTL18_II'),
        'mcb3_dram_we_n':   dict(pins = ('C1'), iostandard = 'SSTL18_II'),

        'mcb3_dram_ba':     dict(pins = ("C3",  "C2"),
                                 iostandard = 'SSTL18_II'),

        'mcb3_dram_a':      dict(pins = ('K5', 'K6', 'D1', 'L4',
                                         'G5', 'H4', 'H3', 'D3',
                                         'B2', 'A2', 'G6', 'E3',
                                         'F3'),
                                 iostandard = 'SSTL18_II'),

        'mcb3_dram_odt':    dict(pins = ('L5'), iostandard = 'SSTL18_II'),

        'mcb3_dram_dqs':    dict(pins = ('H2'),
                                 iostandard = 'DIFF_SSTL18_II',
                                 in_term = 'UNTUNED_SPLIT_25'),
        'mcb3_dram_dqs_n':  dict(pins = ('H1'),
                                 iostandard = 'DIFF_SSTL18_II',
                                 in_term = 'UNTUNED_SPLIT_25'),
        'mcb3_dram_udqs':   dict(pins = ('N3'),
                                 iostandard = 'DIFF_SSTL18_II',
                                 in_term = 'UNTUNED_SPLIT_25'),
        'mcb3_dram_udqs_n': dict(pins = ('N1'),
                                 iostandard = 'DIFF_SSTL18_II',
                                 in_term = 'UNTUNED_SPLIT_25'),

        'mcb3_dram_dm':     dict(pins = ('J4'), iostandard = 'SSTL18_II'),
        'mcb3_dram_udm':    dict(pins = ('K3'), iostandard = 'SSTL18_II'),

        'mcb3_dram_dq':     dict(pins = ('K2', 'K1', 'J3', 'J1',
                                         'F2', 'F1', 'G3', 'G1',
                                         'L3', 'L1', 'M2', 'M1',
                                         'P2', 'P1', 'R2', 'R1'),
                                 iostandard = 'SSTL18_II',
                                 in_term = 'UNTUNED_SPLIT_25'),

        'bank2':        dict(pins = ("N11"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             ),

    }

    extra_ucf = '''
CONFIG VCCAUX = "3.3";

# VREF bank 2
CONFIG PROHIBIT = M10;
CONFIG PROHIBIT = T5;

# VREF Bank 3
CONFIG PROHIBIT = A3;
CONFIG PROHIBIT = M3;

CONFIG MCB_PERFORMANCE= STANDARD;

# NET "memc?_wrapper_inst/mcb_ui_top_inst/mcb_raw_wrapper_inst/selfrefresh_mcb_mode" TIG;
# NET "c?_pll_lock" TIG;
# INST "memc?_wrapper_inst/mcb_ui_top_inst/mcb_raw_wrapper_inst/gen_term_calib.mcb_soft_calibration_top_inst/mcb_soft_calibration_inst/DONE_SOFTANDHARD_CAL*" TIG;
# NET "memc?_wrapper_inst/mcb_ui_top_inst/mcb_raw_wrapper_inst/gen_term_calib.mcb_soft_calibration_top_inst/mcb_soft_calibration_inst/CKE_Train" TIG; ##This path exists for DDR2 only

# NET "memc3_infrastructure_inst/sys_clk_ibufg" TNM_NET = "SYS_CLK3";
# TIMESPEC "TS_SYS_CLK3" = PERIOD "SYS_CLK3"  3.0  ns HIGH 50 %;

NET "soc_clk_p" TNM_NET = "SOC_CLK";
TIMESPEC "TS_SOC_CLK" = PERIOD "SOC_CLK"  7.5  ns HIGH 50 %;

# NET "soc_clk" TNM_NET = "SOC_CLK_INT";
# TIMESPEC "TS_SOC_CLK_INT" = PERIOD "SOC_CLK_INT"  6  ns HIGH 50 %;
'''

    for k, v in sorted(default_ports.items()):
        print k, len(v['pins'])

    def get_flow(self, top=None):
        return ISE(brd=self, top=top)

    def get_portmap(self, top=None, **kwargs):
        pp = FPGA.get_portmap(self, top, **kwargs)
        pp['init_b'] = TristateSignal(False)
        print 'hacked pp', pp
        return pp
