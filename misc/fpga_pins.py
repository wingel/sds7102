#! /usr/bin/python

"""
A script that produces the images in my blog post about the FPGA pins at

    http://blog.weinigel.se/2016/06/19/sds7102-more-fpga-pins.html

This script also serves as documentation about what the FPGA pins do.

The output from this script is a couple of .png files that the scripts
runs eom (Eye of MATE, the MATE desktop image viewer) on.

It started out as a quick cut and paste from the Xilinx documentation
into the "raw_pins" string.  This was then parsed to produce the
"my_pins" string that I then pasted back into the code.  It didn't
have any annotations at that time so that's something I've been doing
as I have been discovering more and more about the connections inside
the scope.
"""

my_pins = """
0  C4  IO_L1P_HSWAPEN_0			AT88SC SCL
0  A4  IO_L1N_VREF_0			50Hz - wall power for AC triggering?
0  B5  IO_L2P_0				Panel - data
0  A5  IO_L2N_0				Panel - reset
0  D5  IO_L3P_0				Ch 1 BA7046 Vd output
0  C5  IO_L3N_0				AT88SC SDA ?
0  B6  IO_L4P_0				Ch1 trig_p
0  A6  IO_L4N_0				Ch1 trig_n
0  F7  IO_L5P_0				BU2505 LD
0  E6  IO_L5N_0				Ch 1 BA7046 Hd output
0  C7  IO_L6P_0				ADF4360-7 LE
0  A7  IO_L6N_0				Ch 1 LMH6518 CS
0  D6  IO_L7P_0				Panel - green LED in "Run/Stop" button
0  C6  IO_L7N_0				Panel - clock
0  B8  IO_L33P_0			Panel - white LED in "Single" button
0  A8  IO_L33N_0			DAC8532 CS
0  C9  IO_L34P_GCLK19_0			Ch2 trig_p
0  A9  IO_L34N_GCLK18_0			Ch2 trig_n
0  B10 IO_L35P_GCLK17_0			ADC ? P
0  A10 IO_L35N_GCLK16_0			ADC ? N
0  E7  IO_L36P_GCLK15_0			ADC Sampling clock P
0  E8  IO_L36N_GCLK14_0			ADC Sampling clock N
0  E10 IO_L37P_GCLK13_0			External trig out on the back
0  C10 IO_L37N_GCLK12_0			10MHz reference clock
0  D8  IO_L38P_0			SDO
0  C8  IO_L38N_VREF_0			Ch 2 LMH6518 CS
0  C11 IO_L39P_0			ADC ? P
0  A11 IO_L39N_0			ADC ? N
0  F9  IO_L40P_0			ADC08D500 CS
0  D9  IO_L40N_0			SCK
0  B12 IO_L62P_0			ADC ? P
0  A12 IO_L62N_VREF_0			ADC ? N
0  C13 IO_L63P_SCP7_0			ADC ? P
0  A13 IO_L63N_SCP6_0			ADC ? N
0  F10 IO_L64P_SCP5_0			ADC ? P
0  E11 IO_L64N_SCP4_0			ADC ? N
0  B14 IO_L65P_SCP3_0			ADC ? P
0  A14 IO_L65N_SCP2_0			ADC ? N
0  D11 IO_L66P_SCP1_0			ADC ? P
0  D12 IO_L66N_SCP0_0			ADC ? N
NA C14 TCK
NA C12 TDI
NA A15 TMS
NA E14 TDO
1  E13 IO_L1P_A25_1			ADC ? P
1  E12 IO_L1N_A24_VREF_1		ADC ? N
1  B15 IO_L29P_A23_M1A13_1		ADC ? P
1  B16 IO_L29N_A22_M1A14_1		ADC ? N
1  F12 IO_L30P_A21_M1RESET_1		ADC ? P
1  G11 IO_L30N_A20_M1A11_1		ADC ? N
1  D14 IO_L31P_A19_M1CKE_1		ADC ? P
1  D16 IO_L31N_A18_M1A12_1		ADC ? N
1  F13 IO_L32P_A17_M1A8_1		ADC OVR_P
1  F14 IO_L32N_A16_M1A9_1		ADC OVR_N
1  C15 IO_L33P_A15_M1A10_1		ADC ? P
1  C16 IO_L33N_A14_M1A4_1		ADC ? N
1  E15 IO_L34P_A13_M1WE_1		ADC ? P
1  E16 IO_L34N_A12_M1BA2_1		ADC ? N
1  F15 IO_L35P_A11_M1A7_1		ADC ? P
1  F16 IO_L35N_A10_M1A2_1		ADC ? N
1  G14 IO_L36P_A9_M1BA0_1		ADC ? P
1  G16 IO_L36N_A8_M1BA1_1		ADC ? N
1  H15 IO_L37P_A7_M1A0_1		ADC ? P
1  H16 IO_L37N_A6_M1A1_1		ADC ? N
1  G12 IO_L38P_A5_M1CLK_1		ADC ? P
1  H11 IO_L38N_A4_M1CLKN_1		ADC ? N
1  H13 IO_L39P_M1A3_1			ADC ? P
1  H14 IO_L39N_M1ODT_1			ADC ? N
1  J11 IO_L40P_GCLK11_M1A5_1		ADC ? P
1  J12 IO_L40N_GCLK10_M1A6_1		ADC ? N
1  J13 IO_L41P_GCLK9_IRDY1_M1RASN_1	ADC ? P
1  K14 IO_L41N_GCLK8_M1CASN_1		ADC ? N
1  K12 IO_L42P_GCLK7_M1UDM_1		ADC ? P
1  K11 IO_L42N_GCLK6_TRDY1_M1LDM_1	ADC ? N
1  J14 IO_L43P_GCLK5_M1DQ4_1		ADC ? P
1  J16 IO_L43N_GCLK4_M1DQ5_1		ADC ? N
1  K15 IO_L44P_A3_M1DQ6_1		ADC ? P
1  K16 IO_L44N_A2_M1DQ7_1		ADC ? N
1  N14 IO_L45P_A1_M1LDQS_1		ADC ? P
1  N16 IO_L45N_A0_M1LDQSN_1		ADC ? N
1  M15 IO_L46P_FCS_B_M1DQ2_1		ADC ? P
1  M16 IO_L46N_FOE_B_M1DQ3_1		ADC ? N
1  L14 IO_L47P_FWE_B_M1DQ0_1		ADC ? P
1  L16 IO_L47N_LDC_M1DQ1_1		ADC ? N
1  P15 IO_L48P_HDC_M1DQ8_1		ADC ? P
1  P16 IO_L48N_M1DQ9_1			ADC ? N
1  R15 IO_L49P_M1DQ10_1			ADC ? P
1  R16 IO_L49N_M1DQ11_1			ADC ? N
1  R14 IO_L50P_M1UDQS_1			ADC ? P
1  T15 IO_L50N_M1UDQSN_1		ADC ? N
1  T14 IO_L51P_M1DQ12_1			ADC ? P
1  T13 IO_L51N_M1DQ13_1			ADC ? N
1  R12 IO_L52P_M1DQ14_1			Ch 2 BA7046 Hd output (was Ch 1)
1  T12 IO_L52N_M1DQ15_1			Ch 2 BA7046 Vd output
1  L12 IO_L53P_1			ADC ? P
1  L13 IO_L53N_VREF_1			ADC ? N
1  M13 IO_L74P_AWAKE_1			ADC ? P
1  M14 IO_L74N_DOUT_BUSY_1		ADC ? N
NA P14 SUSPEND				Not used, should be tied to ground
2  L11 CMPCS_B_2			CMPCS_B (not used)
2  P13 DONE_2				CFG DONE
2  R11 IO_L1P_CCLK_2			CFG CCLK
2  T11 IO_L1N_M0_CMPMISO_2		Probe Compensation output (pulled up via R125)
2  M12 IO_L2P_CMPCLK_2			SoC DQ[?]
2  M11 IO_L2N_CMPMOSI_2			SoC DQ[?]
2  P10 IO_L3P_D0_DIN_MISO_MISO1_2	CFG DIN
2  T10 IO_L3N_MOSI_CSI_B_MISO0_2	SoC DM[1]
2  N12 IO_L12P_D1_MISO2_2		SoC BA[1]
2  P12 IO_L12N_D2_MISO3_2		SoC A[5]
2  N11 IO_L13P_M1_2			? Pulled up via R124.  Unknown function, haven't found it anywhere else.  Might not have any other function except for M1
2  P11 IO_L13N_D10_2			SoC DM[0] ?
2  N9  IO_L14P_D11_2			SoC A[3]
2  P9  IO_L14N_D12_2			SoC DQ[?]
2  L10 IO_L16P_2			SoC A[7]
2  M10 IO_L16N_VREF_2			SoC VREF
2  R9  IO_L23P_2			SoC /CAS
2  T9  IO_L23N_2			SoC DQS[0] ?
2  M9  IO_L29P_GCLK3_2			SoC DQ[?]
2  N8  IO_L29N_GCLK2_2			SoC DQ[?]
2  P8  IO_L30P_GCLK1_D13_2		SoC DQ[?]
2  T8  IO_L30N_GCLK0_USERCCLK_2		SoC /RAS
2  P7  IO_L31P_GCLK31_D14_2		SoC clock P
2  M7  IO_L31N_GCLK30_D15_2		SoC clock N
2  R7  IO_L32P_GCLK29_2			SoC A[4]
2  T7  IO_L32N_GCLK28_2			SoC DQ[?]
2  P6  IO_L47P_2			SoC /WE
2  T6  IO_L47N_2			SoC DQ[?]
2  R5  IO_L48P_D7_2			SoC DQ[?]
2  T5  IO_L48N_RDWR_B_VREF_2		SoC VREF
2  N5  IO_L49P_D3_2			SoC DQ[?]
2  P5  IO_L49N_D4_2			SoC DQ[?]
2  L8  IO_L62P_D5_2			SoC A9
2  L7  IO_L62N_D6_2			SoC DQ[?]
2  P4  IO_L63P_2			SoC DQ[?]
2  T4  IO_L63N_2			SoC DQ[?]
2  M6  IO_L64P_D8_2			SoC DQS[1] ?
2  N6  IO_L64N_D9_2			SoC DQ[?]
2  R3  IO_L65P_INIT_B_2			CFG INIT_B
2  T3  IO_L65N_CSO_B_2			SoC DQ[?]
2  T2  PROGRAM_B_2			CFG PROGRAM_B
3  M4  IO_L1P_3				SoC A1
3  M3  IO_L1N_VREF_3			DDR VREF
3  M5  IO_L2P_3				SoC A[10]
3  N4  IO_L2N_3				SoC A[11]
3  R2  IO_L32P_M3DQ14_3			DDR
3  R1  IO_L32N_M3DQ15_3			DDR
3  P2  IO_L33P_M3DQ12_3			DDR
3  P1  IO_L33N_M3DQ13_3			DDR
3  N3  IO_L34P_M3UDQS_3			DDR
3  N1  IO_L34N_M3UDQSN_3		DDR
3  M2  IO_L35P_M3DQ10_3			DDR
3  M1  IO_L35N_M3DQ11_3			DDR
3  L3  IO_L36P_M3DQ8_3			DDR
3  L1  IO_L36N_M3DQ9_3			DDR
3  K2  IO_L37P_M3DQ0_3			DDR
3  K1  IO_L37N_M3DQ1_3			DDR
3  J3  IO_L38P_M3DQ2_3			DDR
3  J1  IO_L38N_M3DQ3_3			DDR
3  H2  IO_L39P_M3LDQS_3			DDR
3  H1  IO_L39N_M3LDQSN_3		DDR
3  G3  IO_L40P_M3DQ6_3			DDR
3  G1  IO_L40N_M3DQ7_3			DDR
3  F2  IO_L41P_GCLK27_M3DQ4_3		DDR
3  F1  IO_L41N_GCLK26_M3DQ5_3		DDR
3  K3  IO_L42P_GCLK25_TRDY2_M3UDM_3	DDR
3  J4  IO_L42N_GCLK24_M3LDM_3		DDR
3  J6  IO_L43P_GCLK23_M3RASN_3		DDR
3  H5  IO_L43N_GCLK22_IRDY2_M3CASN_3	DDR
3  H4  IO_L44P_GCLK21_M3A5_3		DDR
3  H3  IO_L44N_GCLK20_M3A6_3		DDR
3  L4  IO_L45P_M3A3_3			DDR
3  L5  IO_L45N_M3ODT_3			DDR
3  E2  IO_L46P_M3CLK_3			DDR
3  E1  IO_L46N_M3CLKN_3			DDR
3  K5  IO_L47P_M3A0_3			DDR
3  K6  IO_L47N_M3A1_3			DDR
3  C3  IO_L48P_M3BA0_3			DDR
3  C2  IO_L48N_M3BA1_3			DDR
3  D3  IO_L49P_M3A7_3			DDR
3  D1  IO_L49N_M3A2_3			DDR
3  C1  IO_L50P_M3WE_3			DDR
3  B1  IO_L50N_M3BA2_3			SoC /CS
3  G6  IO_L51P_M3A10_3			DDR
3  G5  IO_L51N_M3A4_3			DDR
3  B2  IO_L52P_M3A8_3			DDR
3  A2  IO_L52N_M3A9_3			DDR
3  F4  IO_L53P_M3CKE_3			SoC A[2] (should be DDR CKE, but could be hardwired)
3  F3  IO_L53N_M3A12_3			DDR
3  E4  IO_L54P_M3RESET_3		SoC A[8]
3  E3  IO_L54N_M3A11_3			DDR
3  F6  IO_L55P_M3A13_3			SoC BA[0]
3  F5  IO_L55N_M3A14_3			SoC A[0]
3  B3  IO_L83P_3			SoC A[6]
3  A3  IO_L83N_VREF_3			DDR VREF
NA A1  GND
NA A16 GND
NA B11 GND
NA B7  GND
NA D13 GND
NA D4  GND
NA E9  GND
NA G15 GND
NA G2  GND
NA G8  GND
NA H12 GND
NA H7  GND
NA H9  GND
NA J5  GND
NA J8  GND
NA K7  GND
NA K9  GND
NA L15 GND
NA L2  GND
NA M8  GND
NA N13 GND
NA P3  GND
NA R10 GND
NA R6  GND
NA T1  GND
NA T16 GND
NA E5  VCCAUX
NA F11 VCCAUX
NA F8  VCCAUX
NA G10 VCCAUX
NA H6  VCCAUX
NA J10 VCCAUX
NA L6  VCCAUX
NA L9  VCCAUX
NA G7  VCCINT
NA G9  VCCINT
NA H10 VCCINT
NA H8  VCCINT
NA J7  VCCINT
NA J9  VCCINT
NA K10 VCCINT
NA K8  VCCINT
0  B13 VCCO_0
0  B4  VCCO_0
0  B9  VCCO_0
0  D10 VCCO_0
0  D7  VCCO_0
1  D15 VCCO_1
1  G13 VCCO_1
1  J15 VCCO_1
1  K13 VCCO_1
1  N15 VCCO_1
1  R13 VCCO_1
2  N10 VCCO_2
2  N7  VCCO_2
2  R4  VCCO_2
2  R8  VCCO_2
3  D2  VCCO_3
3  G4  VCCO_3
3  J2  VCCO_3
3  K4  VCCO_3
3  N2  VCCO_3
"""

headers = [ "Bank" "Description", "Pin Name",  "Region" ]

raw_pins = """
0 IO_L1P_HSWAPEN_0 C4 TL
0 IO_L1N_VREF_0 A4 TL
0 IO_L2P_0 B5 TL
0 IO_L2N_0 A5 TL
0 IO_L3P_0 D5 TL
0 IO_L3N_0 C5 TL
0 IO_L4P_0 B6 TL
0 IO_L4N_0 A6 TL
0 IO_L5P_0 F7 TL
0 IO_L5N_0 E6 TL
0 IO_L6P_0 C7 TL
0 IO_L6N_0 A7 TL
0 IO_L7P_0 D6 TL
0 IO_L7N_0 C6 TL
0 IO_L33P_0 B8 TL
0 IO_L33N_0 A8 TL
0 IO_L34P_GCLK19_0 C9 TL
0 IO_L34N_GCLK18_0 A9 TL
0 IO_L35P_GCLK17_0 B10 TL
0 IO_L35N_GCLK16_0 A10 TL
0 IO_L36P_GCLK15_0 E7 TR
0 IO_L36N_GCLK14_0 E8 TR
0 IO_L37P_GCLK13_0 E10 TR
0 IO_L37N_GCLK12_0 C10 TR
0 IO_L38P_0 D8 TR
0 IO_L38N_VREF_0 C8 TR
0 IO_L39P_0 C11 TR
0 IO_L39N_0 A11 TR
0 IO_L40P_0 F9 TR
0 IO_L40N_0 D9 TR
0 IO_L62P_0 B12 TR
0 IO_L62N_VREF_0 A12 TR
0 IO_L63P_SCP7_0 C13 TR
0 IO_L63N_SCP6_0 A13 TR
0 IO_L64P_SCP5_0 F10 TR
0 IO_L64N_SCP4_0 E11 TR
0 IO_L65P_SCP3_0 B14 TR
0 IO_L65N_SCP2_0 A14 TR
0 IO_L66P_SCP1_0 D11 TR
0 IO_L66N_SCP0_0 D12 TR
NA TCK C14 NA
NA TDI C12 NA
NA TMS A15 NA
NA TDO E14 NA
1 IO_L1P_A25_1 E13 RT
1 IO_L1N_A24_VREF_1 E12 RT
1 IO_L29P_A23_M1A13_1 B15 RT
1 IO_L29N_A22_M1A14_1 B16 RT
1 IO_L30P_A21_M1RESET_1 F12 RT
1 IO_L30N_A20_M1A11_1 G11 RT
1 IO_L31P_A19_M1CKE_1 D14 RT
1 IO_L31N_A18_M1A12_1 D16 RT
1 IO_L32P_A17_M1A8_1 F13 RT
1 IO_L32N_A16_M1A9_1 F14 RT
1 IO_L33P_A15_M1A10_1 C15 RT
1 IO_L33N_A14_M1A4_1 C16 RT
1 IO_L34P_A13_M1WE_1 E15 RT
1 IO_L34N_A12_M1BA2_1 E16 RT
1 IO_L35P_A11_M1A7_1 F15 RT
1 IO_L35N_A10_M1A2_1 F16 RT
1 IO_L36P_A9_M1BA0_1 G14 RT
1 IO_L36N_A8_M1BA1_1 G16 RT
1 IO_L37P_A7_M1A0_1 H15 RT
1 IO_L37N_A6_M1A1_1 H16 RT
1 IO_L38P_A5_M1CLK_1 G12 RT
1 IO_L38N_A4_M1CLKN_1 H11 RT
1 IO_L39P_M1A3_1 H13 RT
1 IO_L39N_M1ODT_1 H14 RT
1 IO_L40P_GCLK11_M1A5_1 J11 RT
1 IO_L40N_GCLK10_M1A6_1 J12 RT
1 IO_L41P_GCLK9_IRDY1_M1RASN_1 J13 RT
1 IO_L41N_GCLK8_M1CASN_1 K14 RT
1 IO_L42P_GCLK7_M1UDM_1 K12 RB
1 IO_L42N_GCLK6_TRDY1_M1LDM_1 K11 RB
1 IO_L43P_GCLK5_M1DQ4_1 J14 RB
1 IO_L43N_GCLK4_M1DQ5_1 J16 RB
1 IO_L44P_A3_M1DQ6_1 K15 RB
1 IO_L44N_A2_M1DQ7_1 K16 RB
1 IO_L45P_A1_M1LDQS_1 N14 RB
1 IO_L45N_A0_M1LDQSN_1 N16 RB
1 IO_L46P_FCS_B_M1DQ2_1 M15 RB
1 IO_L46N_FOE_B_M1DQ3_1 M16 RB
1 IO_L47P_FWE_B_M1DQ0_1 L14 RB
1 IO_L47N_LDC_M1DQ1_1 L16 RB
1 IO_L48P_HDC_M1DQ8_1 P15 RB
1 IO_L48N_M1DQ9_1 P16 RB
1 IO_L49P_M1DQ10_1 R15 RB
1 IO_L49N_M1DQ11_1 R16 RB
1 IO_L50P_M1UDQS_1 R14 RB
1 IO_L50N_M1UDQSN_1 T15 RB
1 IO_L51P_M1DQ12_1 T14 RB
1 IO_L51N_M1DQ13_1 T13 RB
1 IO_L52P_M1DQ14_1 R12 RB
1 IO_L52N_M1DQ15_1 T12 RB
1 IO_L53P_1 L12 RB
1 IO_L53N_VREF_1 L13 RB
1 IO_L74P_AWAKE_1 M13 RB
1 IO_L74N_DOUT_BUSY_1 M14 RB
NA SUSPEND P14 NA
2 CMPCS_B_2 L11 NA
2 DONE_2 P13 NA
2 IO_L1P_CCLK_2 R11 BR
2 IO_L1N_M0_CMPMISO_2 T11 BR
2 IO_L2P_CMPCLK_2 M12 BR
2 IO_L2N_CMPMOSI_2 M11 BR
2 IO_L3P_D0_DIN_MISO_MISO1_2 P10 BR
2 IO_L3N_MOSI_CSI_B_MISO0_2 T10 BR
2 IO_L12P_D1_MISO2_2 N12 BR
2 IO_L12N_D2_MISO3_2 P12 BR
2 IO_L13P_M1_2 N11 BR
2 IO_L13N_D10_2 P11 BR
2 IO_L14P_D11_2 N9 BR
2 IO_L14N_D12_2 P9 BR
2 IO_L16P_2 L10 BR
2 IO_L16N_VREF_2 M10 BR
2 IO_L23P_2 R9 BR
2 IO_L23N_2 T9 BR
2 IO_L29P_GCLK3_2 M9 BR
2 IO_L29N_GCLK2_2 N8 BR
2 IO_L30P_GCLK1_D13_2 P8 BR
2 IO_L30N_GCLK0_USERCCLK_2 T8 BR
2 IO_L31P_GCLK31_D14_2 P7 BL
2 IO_L31N_GCLK30_D15_2 M7 BL
2 IO_L32P_GCLK29_2 R7 BL
2 IO_L32N_GCLK28_2 T7 BL
2 IO_L47P_2 P6 BL
2 IO_L47N_2 T6 BL
2 IO_L48P_D7_2 R5 BL
2 IO_L48N_RDWR_B_VREF_2 T5 BL
2 IO_L49P_D3_2 N5 BL
2 IO_L49N_D4_2 P5 BL
2 IO_L62P_D5_2 L8 BL
2 IO_L62N_D6_2 L7 BL
2 IO_L63P_2 P4 BL
2 IO_L63N_2 T4 BL
2 IO_L64P_D8_2 M6 BL
2 IO_L64N_D9_2 N6 BL
2 IO_L65P_INIT_B_2 R3 BL
2 IO_L65N_CSO_B_2 T3 BL
2 PROGRAM_B_2 T2 NA
3 IO_L1P_3 M4 LB
3 IO_L1N_VREF_3 M3 LB
3 IO_L2P_3 M5 LB
3 IO_L2N_3 N4 LB
3 IO_L32P_M3DQ14_3 R2 LB
3 IO_L32N_M3DQ15_3 R1 LB
3 IO_L33P_M3DQ12_3 P2 LB
3 IO_L33N_M3DQ13_3 P1 LB
3 IO_L34P_M3UDQS_3 N3 LB
3 IO_L34N_M3UDQSN_3 N1 LB
3 IO_L35P_M3DQ10_3 M2 LB
3 IO_L35N_M3DQ11_3 M1 LB
3 IO_L36P_M3DQ8_3 L3 LB
3 IO_L36N_M3DQ9_3 L1 LB
3 IO_L37P_M3DQ0_3 K2 LB
3 IO_L37N_M3DQ1_3 K1 LB
3 IO_L38P_M3DQ2_3 J3 LB
3 IO_L38N_M3DQ3_3 J1 LB
3 IO_L39P_M3LDQS_3 H2 LB
3 IO_L39N_M3LDQSN_3 H1 LB
3 IO_L40P_M3DQ6_3 G3 LB
3 IO_L40N_M3DQ7_3 G1 LB
3 IO_L41P_GCLK27_M3DQ4_3 F2 LB
3 IO_L41N_GCLK26_M3DQ5_3 F1 LB
3 IO_L42P_GCLK25_TRDY2_M3UDM_3 K3 LB
3 IO_L42N_GCLK24_M3LDM_3 J4 LB
3 IO_L43P_GCLK23_M3RASN_3 J6 LT
3 IO_L43N_GCLK22_IRDY2_M3CASN_3 H5 LT
3 IO_L44P_GCLK21_M3A5_3 H4 LT
3 IO_L44N_GCLK20_M3A6_3 H3 LT
3 IO_L45P_M3A3_3 L4 LT
3 IO_L45N_M3ODT_3 L5 LT
3 IO_L46P_M3CLK_3 E2 LT
3 IO_L46N_M3CLKN_3 E1 LT
3 IO_L47P_M3A0_3 K5 LT
3 IO_L47N_M3A1_3 K6 LT
3 IO_L48P_M3BA0_3 C3 LT
3 IO_L48N_M3BA1_3 C2 LT
3 IO_L49P_M3A7_3 D3 LT
3 IO_L49N_M3A2_3 D1 LT
3 IO_L50P_M3WE_3 C1 LT
3 IO_L50N_M3BA2_3 B1 LT
3 IO_L51P_M3A10_3 G6 LT
3 IO_L51N_M3A4_3 G5 LT
3 IO_L52P_M3A8_3 B2 LT
3 IO_L52N_M3A9_3 A2 LT
3 IO_L53P_M3CKE_3 F4 LT
3 IO_L53N_M3A12_3 F3 LT
3 IO_L54P_M3RESET_3 E4 LT
3 IO_L54N_M3A11_3 E3 LT
3 IO_L55P_M3A13_3 F6 LT
3 IO_L55N_M3A14_3 F5 LT
3 IO_L83P_3 B3 LT
3 IO_L83N_VREF_3 A3 LT
NA GND A1 NA
NA GND A16 NA
NA GND B11 NA
NA GND B7 NA
NA GND D13 NA
NA GND D4 NA
NA GND E9 NA
NA GND G15 NA
NA GND G2 NA
NA GND G8 NA
NA GND H12 NA
NA GND H7 NA
NA GND H9 NA
NA GND J5 NA
NA GND J8 NA
NA GND K7 NA
NA GND K9 NA
NA GND L15 NA
NA GND L2 NA
NA GND M8 NA
NA GND N13 NA
NA GND P3 NA
NA GND R10 NA
NA GND R6 NA
NA GND T1 NA
NA GND T16 NA
NA VCCAUX E5 NA
NA VCCAUX F11 NA
NA VCCAUX F8 NA
NA VCCAUX G10 NA
NA VCCAUX H6 NA
NA VCCAUX J10 NA
NA VCCAUX L6 NA
NA VCCAUX L9 NA
NA VCCINT G7 NA
NA VCCINT G9 NA
NA VCCINT H10 NA
NA VCCINT H8 NA
NA VCCINT J7 NA
NA VCCINT J9 NA
NA VCCINT K10 NA
NA VCCINT K8 NA
0 VCCO_0 B13 NA
0 VCCO_0 B4 NA
0 VCCO_0 B9 NA
0 VCCO_0 D10 NA
0 VCCO_0 D7 NA
1 VCCO_1 D15 NA
1 VCCO_1 G13 NA
1 VCCO_1 J15 NA
1 VCCO_1 K13 NA
1 VCCO_1 N15 NA
1 VCCO_1 R13 NA
2 VCCO_2 N10 NA
2 VCCO_2 N7 NA
2 VCCO_2 R4 NA
2 VCCO_2 R8 NA
3 VCCO_3 D2 NA
3 VCCO_3 G4 NA
3 VCCO_3 J2 NA
3 VCCO_3 K4 NA
3 VCCO_3 N2 NA
"""

pins = []
pin_map = {}
for s in raw_pins.strip().split('\n'):
    parts = s.split()
    assert len(parts) == 4
    # print "%-2s %-3s %-32s" % (parts[0], parts[2], parts[1])
    pins.append(tuple(parts))
    pin_map[parts[2]] = parts

usage_map = {}
for s in my_pins.strip().split('\n'):
    parts = s.split()
    usage_map[parts[1]] = ' '.join(parts[3:])

rows = 'ABCDEFGHJKLMNPRT'

assert(len(pins)) == 256
for row in range(0, 16):
    for col in range(0, 16):
        name = '%s%s' % (rows[row], col + 1)
        assert name in pin_map

import os
import sys

os.environ['DISPLAY'] = ':0'

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

points = np.ones(5)  # Draw 3 points for each line
text_style = dict(horizontalalignment='right', verticalalignment='center',
                  fontsize=12, fontdict={'family': 'monospace'})
marker_style = dict(color='cornflowerblue', linestyle=':', marker='o',
                    markersize=15, markerfacecoloralt='gray')

def nice_repr(text):
    return repr(text).lstrip('u')

a = [
    [ ( 'Type', None ),
      ( 'I/O', dict(
        marker = 'o', markersize = 12, fillstyle = 'none', c = '#000000') ),
      ( 'I/O or clock', dict(
        marker = 'h', markersize = 12, fillstyle = 'none', c = '#000000') ),
      ( 'I/O or VREF', dict(
        marker = 'D', markersize = 9, fillstyle = 'none', c = '#000000') ),
      ( 'VCC', dict(
        marker = '^', markersize = 12, fillstyle = 'none', c = '#000000') ),
      ( 'GND', dict(
        marker = 'v', markersize = 12, fillstyle = 'none', c = '#000000') ),
      ( 'Config', dict(
        marker = '*', markersize = 12, fillstyle = 'none', c = '#000000') ),
      ],
    [ ( 'Bank', None ),
      ( 'Bank 0', dict(
        marker = 'o', markersize = 12, c = '#ff8888') ),
      ( 'Bank 1', dict(
        marker = 'o', markersize = 12, c = '#88ff88') ),
      ( 'Bank 2', dict(
        marker = 'o', markersize = 12, c = '#8888ff') ),
      ( 'Bank 3', dict(
        marker = 'o', markersize = 12, c = '#88ffff') ),
      ( 'N/A', dict(
        marker = 'o', markersize = 12, c = '#cccccc') ),
      ],
    [ ( 'Usage', None ),
      ( 'Miscellaneous', dict(
        marker = 's', markersize = 16, c = '#ff8888') ),
      ( 'ADC', dict(
        marker = 's', markersize = 16, c = '#88ff88') ),
      ( 'SoC bus', dict(
        marker = 's', markersize = 16, c = '#8888ff') ),
      ( 'DDR', dict(
        marker = 's', markersize = 16, c = '#88ffff') ),
      ( 'Fixed function', dict(
        marker = 's', markersize = 16, c = '#cccccc') ),
      ( 'Configuration', dict(
        marker = 's', markersize = 16, c = '#ffff88') ),
      ],

   ]

if 1:
    fig, ax = plt.subplots(figsize = (4.8, 2.4), dpi = 100)

    plt.axis('off')
    plt.margins(0, 0)

    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())

    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0,
                        hspace = 0, wspace = 0)

    plt.xlim(-0.5, 8)
    plt.ylim(-7, 1)

    x = 0
    for aa in a:
        y = 0
        for name, d in aa:
            if d:
                ax.plot(x, y, **d)
                ax.text(x + 0.4, y, name, verticalalignment = 'center')
            else:
                ax.text(x - 0.2, y, name, verticalalignment = 'center',
                        fontweight = 'bold')
            y -= 1
        x += 2.5

    fig.savefig('legend.png', bbox_inches = 'tight', pad_inches = 0.0)

    os.system('eom -n legend.png </dev/null >/dev/null 2>&1 &')

if 1:
    for i in range(6):
        fig, ax = plt.subplots(figsize = (4.8, 4.8), dpi = 100)

        plt.xlim(-1, 18)
        plt.ylim(-1, 18)

        if 0:
            axes = plt.gca()
            axes.axes.get_xaxis().set_visible(False)
            axes.axes.get_yaxis().set_visible(False)

        plt.axis('off')
        plt.margins(0, 0)

        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())

        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0,
                            hspace = 0, wspace = 0)

        show_soc = 0
        show_ddr = 0
        show_adc = 0
        show_other = 0
        show_unknown = 0

        if i == 0:
            name = 'soc'
            show_soc = 1
        elif i == 1:
            name = 'ddr'
            show_ddr = 1
        elif i == 2:
            name = 'adc'
            show_adc = 1
        elif i == 3:
            name = 'other'
            show_soc = 1
            show_ddr = 1
            show_adc = 1
            show_other = 1
            show_other = 1
        elif i == 4:
            name = 'unknown'
            show_unknown = 1
        elif i == 5:
            name = 'start'

        fn = '%s.png' % name

        ta = dict(fontsize = 10, rotation = 270,
                  horizontalalignment = 'center', verticalalignment = 'center')

        for row in range(0, 16):
            ax.text(16 - row, 0, rows[row], **ta)
            ax.text(16 - row, 17, rows[row], **ta)

        for col in range(0, 16):
            ax.text(0, 16 - col, str(col + 1), **ta)
            ax.text(17, 16 - col, str(col + 1), **ta)

        for row in range(0, 16):
            for col in range(0, 16):
                name = '%s%s' % (rows[row], col + 1)
                parts = pin_map[name]
                usage = usage_map[name]

                x = 16 - row
                y = 16 - col

                c = None

                if parts[1].startswith('VCC'):
                    c = '#cccccc'
                elif parts[1] == 'GND':
                    c = '#cccccc'
                elif usage.startswith('CFG'):
                    c = '#ffff88'
                elif parts[1] in [ 'TCK', 'TDI', 'TMS', 'TDO',
                                   'PROGRAM_B_2', 'DONE_2', 'CMPCS_B_2', 'SUSPEND' ]:
                    c = '#cccccc'
                elif usage.startswith('DDR'):
                    if show_ddr:
                        c = '#88ffff'
                elif usage.startswith('SoC'):
                    if show_soc:
                        c = '#8888ff'
                elif usage.startswith('ADC'):
                    if show_adc:
                        c = '#88ff88'
                elif usage.startswith('?'):
                    if show_unknown:
                        c = '#444444'
                elif usage:
                    if show_other:
                        c = '#ff8888'
                else:
                    print "Unused:", name, usage
                    if show_unknown:
                        c = '#000000'

                if c:
                    ax.plot(x, y, marker = 's', markersize = 16, c = c)

                ms = 12

                if parts[1].startswith('VCC'):
                    m = '^'
                elif parts[1] == 'GND':
                    m = 'v'
                elif parts[1] in [ 'TCK', 'TDI', 'TMS', 'TDO',
                                   'PROGRAM_B_2', 'DONE_2', 'CMPCS_B_2', 'SUSPEND' ]:
                    m = '*'
                elif 'GCLK' in parts[1]:
                    m = 'h'
                elif 'VREF' in parts[1]:
                    m = 'D'
                    ms = 9
                else:
                    m = 'o'

                if parts[0] == '0':
                    c = '#ff8888'
                elif parts[0] == '1':
                    c = '#88ff88'
                elif parts[0] == '2':
                    c = '#8888ff'
                elif parts[0] == '3':
                    c = '#88ffff'
                else:
                    c = '#cccccc'

                ax.plot(x, y, marker = m, markersize = ms, c = c)

        fig.savefig(fn, bbox_inches = 'tight', pad_inches = 0.0)

        os.system('eom -n %s </dev/null >/dev/null 2>&1 &' % fn)
