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
        # Use LVCMOS18 with the highest drive strength instead.

        'soc_dqs':      dict(pins = ('T9', 'M6'), iostandard = 'LVCMOS18',
                             drive = '16'),
        'soc_dm':       dict(pins = ('P11', 'T10'), iostandard = 'LVCMOS18',
                             drive = '16'),
        'soc_dq':       dict(pins = ('T7',  'L7',  'P9',  'N5',
                                     'M11', 'T3',  'M9',  'T4',
                                     'T6',  'M12', 'P4',  'N6',
                                     'N8',  'P5',  'P8',  'R5'),
                             iostandard = 'LVCMOS18',
                             drive = '16'),

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

        'bank0':        dict(pins = ("B5",  "A5",
                                     "D6",  "C6", " B8",
                                     ),
                             iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             pullup = True,
                             # pulldown = True,
                             ),

        'bank2':        dict(pins = ("N11"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             ),

        'bank3':        dict(pins = ("R2",
                                     "R1",  "P2",  "P1",  "N3",  "N1",
                                     "M2",  "M1",  "L3",  "L1",  "K2",
                                     "K1",  "J3",  "J1",  "H2",  "H1",
                                     "G3",  "G1",  "F2",  "F1",  "K3",
                                     "J4",  "J6",  "H5",  "H4",  "H3",
                                     "L4",  "L5",  "E2",  "E1",  "K5",
                                     "K6",  "C3",  "C2",  "D3",  "D1",
                                     "C1",  "G6",  "G5",  "B2",
                                     "A2",  "F3",  "E3"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             # pullup = True,
                             # pulldown = True,
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
