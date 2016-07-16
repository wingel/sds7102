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
        'ref_clk':       dict(frequency = 10e6, pins = ('C10',), iostandard = 'LVCMOS33'),
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

        'bank0':        dict(pins = ("C4",  "A4",  "B5",  "A5",  "D5",
                                     "C5",  "B6",  "A6",  "F7",  "E6",
                                     "C7",  "A7",  "D6",  "C6", " B8",
                                     "A8",  "C9",  "A9",
                                     "E10", "C10", "D8",
                                     "C8",  "F9",  "D9",
                                     ),
                             iostandard = 'LVCMOS33',
                             clock_dedicated_route = False,
                             pullup = True,
                             # pulldown = True,
                             ),

        'bank1':        dict(pins = ("R12", "T12"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             # pullup = True,
                             # pulldown = True,
                             ),

        'bank2':        dict(pins = ("T11", "M12", "M11", "T10", "N12",
                                     "P12", "N11", "P11", "N9",  "P9",
                                     "L10", "M10", "R9",  "T9",  "M9",
                                     "N8",  "P8",  "T8",  "P7",  "M7",
                                     "R7",  "T7",  "P6",  "T6",  "R5",
                                     "T5",  "N5",  "P5",  "L8",  "L7",
                                     "P4",  "T4",  "M6",  "N6",  "T3"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             # pullup = True,
                             # pulldown = True,
                             ),


        'bank3':        dict(pins = ("M4",  "M3",  "M5",  "N4",  "R2",
                                     "R1",  "P2",  "P1",  "N3",  "N1",
                                     "M2",  "M1",  "L3",  "L1",  "K2",
                                     "K1",  "J3",  "J1",  "H2",  "H1",
                                     "G3",  "G1",  "F2",  "F1",  "K3",
                                     "J4",  "J6",  "H5",  "H4",  "H3",
                                     "L4",  "L5",  "E2",  "E1",  "K5",
                                     "K6",  "C3",  "C2",  "D3",  "D1",
                                     "C1",  "B1",  "G6",  "G5",  "B2",
                                     "A2",  "F4",  "F3",  "E4",  "E3",
                                     "F6",  "F5",  "B3",  "A3"),
                             iostandard = 'LVCMOS18',
                             clock_dedicated_route = False,
                             # pullup = True,
                             # pulldown = True,
                             ),
    }

    for k, v in sorted(default_ports.items()):
        print k, len(v['pins'])

    def get_flow(self, top=None):
        return ISE(brd=self, top=top)

    def get_portmap(self, top=None, **kwargs):
        pp = FPGA.get_portmap(self, top, **kwargs)
        pp['init_b'] = TristateSignal(False)
        print 'hacked pp', pp
        return pp
