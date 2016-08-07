#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('spartan6.py')

from myhdl import Signal, SignalType, instance, always_comb, intbv

use_xilinx = 1

_one = '1\'b1'
_zero = '1\'b0'

def make_params(**kwargs):
    params = []
    for k, v in kwargs.items():
        if isinstance(v, basestring):
            v = '"' + v + '"'
        params.append('.%s(%s)' % (k.upper(), v))
    params = ','.join(params)
    return params

def make_comments(**kwargs):
    params = []
    for k, v in kwargs.items():
        if isinstance(v, basestring):
            v = '"' + v + '"'
        params.append('(*%s = %s*)' % (k.upper(), v))
    params = '\n'.join(params)
    return params

def startup_spartan6(name, cfgclk = None, cfgmclk = None):
    if use_xilinx:
        if cfgclk is None:
            cfgclk = ''
        else:
            cfgclk.driven = 'wire'

        if cfgmclk is None:
            cfmgclk = ''
        else:
            cfgmclk.driven = 'wire'

    lowTime = 100
    highTime = 100

    @instance
    def cfgclkGen():
        while True:
            yield delay(lowTime)
            cfgclk.next = 1
            yield delay(highTime)
            cfgclk.next = 0

    @instance
    def cfgmclkGen():
        while True:
            yield delay(lowTime)
            cfgmclk.next = 1
            yield delay(highTime)
            cfgmclk.next = 0

    return cfgclkGen, cfgmclkGen

if use_xilinx:
    startup_spartan6.verilog_code = r'''

STARTUP_SPARTAN6 $name (
    .CFGCLK($cfgclk),
    .CFGMCLK($cfgmclk),
    .EOS(),
    .CLK(),
    .GSR(),
    .GTS(),
    .KEYCLEARB()
);
'''.strip()

def bufg(name, i, o):
    o.driven = 'wire'

    @always_comb
    def comb():
        o.next = i

    return comb

bufg.verilog_code = r'''
BUFG $name (
    .I  ($i),
    .O  ($o)
);
'''.strip()

def bufgce(name, i, o, ce):
    o.driven = 'wire'

    @always_comb
    def comb():
        if ce:
            o.next = i
        else:
            o.next = 0

    return comb

bufgce.verilog_code = r'''
BUFGCE $name (
    .I  ($i),
    .O  ($o),
    .CE ($ce)
);
'''.strip()

def ibufg(name, i, o):
    o.driven = 'wire'

    @always_comb
    def comb():
        o.next = i

    return comb

if use_xilinx:
    ibufg.verilog_code = r'''
IBUFG $name (
    .I  ($i),
    .O  ($o)
);
'''.strip()

def ibufds(name, i, ib, o):
    print type(i), i, type(ib), ib, type(o), o

    o.driven = 'wire'

    @always_comb
    def comb():
        o.next = i

    return comb

if use_xilinx:
    ibufds.verilog_code = r'''
IBUFDS $name (
    .I  ($i),
    .IB ($ib),
    .O  ($o)
);
'''.strip()

def ibufds_vec(name, i, ib, o):
    print type(i), i, type(ib), ib, type(o), o

    o.driven = 'wire'

    @always_comb
    def comb():
        o.next = i

    assert len(i) == len(ib) == len(o)

    ii = name + '_ii'
    iname = name + '_block'
    n = len(i)

    return comb

ibufds_vec.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IBUFDS $name (
            .I  ($i[$ii]),
            .IB ($ib[$ii]),
            .O  ($o[$ii])
        );
    end
endgenerate
'''.strip()

def ibufgds(name, i, ib, o):
    o.driven = 'wire'

    @always_comb
    def comb():
        o.next = i

    return comb

if use_xilinx:
    ibufgds.verilog_code = r'''
IBUFGDS $name (
    .I  ($i),
    .IB ($ib),
    .O  ($o)
);
'''.strip()

def ibufgds_diff_out(name, i, ib, o, ob):
    o.driven = 'wire'
    ob.driven = 'wire'

    @always_comb
    def comb():
        o.next = i
        ob.next = ib

    return comb

if use_xilinx:
    ibufgds_diff_out.verilog_code = r'''
IBUFGDS_DIFF_OUT $name (
    .I  ($i),
    .IB ($ib),
    .O  ($o),
    .OB ($ob)
);
'''.strip()

def iobuf(name, i, o, t, io):
    if isinstance(i, SignalType):
        assert len(i) == len(io)
        i.read = True

    if isinstance(o, SignalType):
        assert len(o) == len(io)
        o.driven = 'wire'

    if isinstance(t, SignalType):
        assert len(t) == len(io)
        t.read = True
    else:
        t = intbv(~0)[len(io):]

    io.read = True
    io.driven = 'wire'

    ii = name + '_ii'
    iname = name + '_block'
    n = len(io)

    @always_comb
    def i_comb():
            o.next[ii] = io

    @always_comb
    def o_comb():
        for ii in range(len(io)):
            if t[ii]:
                io.next[ii] = i[ii]
            else:
                io.next[ii] = 0

    return i_comb, o_comb

iobuf.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IOBUF $name (
            .I  ($i[$ii]),
            .O  ($o[$ii]),
            .T  ($t[$ii]),
            .IO ($io[$ii])
        );
    end
endgenerate
'''.strip()

def iobuf_oe(name, i, o, oe, io):
    if isinstance(i, SignalType):
        assert len(i) == len(io)
        i.read = True

    if isinstance(o, SignalType):
        assert len(o) == len(io)
        o.driven = 'wire'

    if isinstance(oe, SignalType):
        assert len(oe) == 1
        oe.read = True
    else:
        oe = 0

    io.read = True
    io.driven = 'wire'

    ii = name + '_ii'
    iname = name + '_block'
    n = len(io)

    @always_comb
    def i_comb():
            o.next[ii] = io

    @always_comb
    def o_comb():
        for ii in range(len(io)):
            if t[ii]:
                io.next[ii] = i[ii]
            else:
                io.next[ii] = 0

    return i_comb, o_comb

iobuf_oe.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IOBUF $name (
            .I  ($i[$ii]),
            .O  ($o[$ii]),
            .T  (~$oe),
            .IO ($io[$ii])
        );
    end
endgenerate
'''.strip()

def iddr2(name, d, q0, q1, c0, c1 = None, ce = _one, r = _zero, s = _zero,
               ddr_alignment = 'NONE',
               init_q0 = _zero, init_q1 = _zero,
               srtype = 'SYNC'):
    insts = []

    print "IDDR2 c0", c0
    print "IDDR2 c1", c1

    if c1 is None:
        c1 = Signal(False)
        @always_comb
        def c1_comb():
            c1.next = not c0
        insts.append(c1_comb)

        print "IDDR2 fake c1", c1

    insts.append(iddr2_int(name, d, q0, q1, c0, c1, ce, r, s,
                           ddr_alignment, init_q0, init_q1, srtype))

    return insts

def iddr2_int(name, d, q0, q1, c0, c1, ce = _one, r = _zero, s = _zero,
              ddr_alignment = 'NONE',
              init_q0 = _zero, init_q1 = _zero,
              srtype = 'SYNC'):
    d.read = True
    c0.read = True
    c1.read = True

    if isinstance(ce, SignalType):
        ce.read = True

    if isinstance(r, SignalType):
        r.read = True

    if isinstance(s, SignalType):
        s.read = True

    q0.driven = 'wire'
    q1.driven = 'wire'

    assert len(d) == len(q0) == len(q1)

    ii = name + '_ii'
    iname = name + '_block'
    n = len(d)

    @always_comb
    def comb():
        q0.next = d
        q1.next = d

    return comb

iddr2_int.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IDDR2 #(
        .DDR_ALIGNMENT("$ddr_alignment"),
        .INIT_Q0($init_q0),
        .INIT_Q1($init_q1),
        .SRTYPE("$srtype")
        ) $name (
            .D  ($d[$ii]),
            .Q0 ($q0[$ii]),
            .Q1  ($q1[$ii]),
            .C0 ($c0),
            .C1 ($c1),
            .CE ($ce),
            .R  ($r),
            .S  ($s)
        );
    end
endgenerate
'''.strip()

def oddr2(name, d0, d1, q, c0, c1 = None, ce = _one, r = _zero, s = _zero,
          ddr_alignment = 'NONE',
          init = 0,
          srtype = 'SYNC'):
    insts = []

    if c1 is None:
        c1 = Signal(False)
        @always_comb
        def c1_comb():
            c1.next = not c0
        insts.append(c1_comb)

    d0.read = True
    d1.read = True
    c0.read = True
    c1.read = True
    q.driven = 'wire'

    insts.append(oddr2_int(name, d0, d1, q, c0, c1, ce, r, s,
                           ddr_alignment, init, srtype))

    return insts

def oddr2_int(name, d0, d1, q, c0, c1, ce = _one, r = _zero, s = _zero,
              ddr_alignment = 'NONE',
              init = 0,
              srtype = 'SYNC'):
    d0.read = True
    d1.read = True
    c0.read = True
    c1.read = True

    if isinstance(ce, SignalType):
        ce.read = True

    if isinstance(r, SignalType):
        r.read = True

    if isinstance(s, SignalType):
        s.read = True

    q.driven = 'wire'

    assert len(d0) == len(d1) == len(q)

    ii = name + '_ii'
    iname = name + '_block'
    n = len(q)

    @always_comb
    def comb():
        q.next = d0 or d1

    return comb

oddr2_int.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        ODDR2 #(
        .DDR_ALIGNMENT("$ddr_alignment"),
        .INIT($init),
        .SRTYPE("$srtype")
        ) $name (
            .D0 ($d0[$ii]),
            .D1 ($d1[$ii]),
            .Q  ($q[$ii]),
            .C0 ($c0),
            .C1 ($c1),
            .CE ($ce),
            .R  ($r),
            .S  ($s)
        );
    end
endgenerate
'''.strip()

def iodelay2_se(
    name,
    busy = '',
    dataout = '',
    dataout2 = '',
    dout = '',
    tout = '',
    cal = '',
    ce = '',
    clk = '',
    idatain = '',
    inc = '',
    ioclk = '',
    odatain = '',
    rst = '',
    t = '',

    counter_wraparound = 'WRAPAROUND',
    data_rate = 'SDR',
    delay_src = 'IDATAIN',
    idelay_type = 'DEFAULT',
    idelay_value = 0,
    idelay2_value = 0,
    odelay_value = 0,
    serdes_mode = 'NONE'):

    odatain.read = True
    idatain.read = True
    t.read = True

    dataout.driven = 'wire'
    dout.driven = 'wire'
    tout.driven = 'wire'

    ii = name + '_ii'
    iname = name + '_block'
    n = len(dout)

    @always_comb
    def comb():
        q.next = d0

    return comb

iodelay2_se.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IODELAY2 #(
            .COUNTER_WRAPAROUND("$counter_wraparound"),
            .DATA_RATE("$data_rate"),
            .DELAY_SRC("$delay_src"),
            .IDELAY2_VALUE($idelay2_value),
            .IDELAY_TYPE("$idelay_type"),
            .IDELAY_VALUE($idelay_value),
            .ODELAY_VALUE($odelay_value),
            .SERDES_MODE("$serdes_mode")
        )
        IODELAY2_inst (
            .BUSY($busy),
            .DATAOUT($dataout[$ii]),
            .DATAOUT2($dataout2),
            .DOUT($dout[$ii]),
            .TOUT($tout[$ii]),
            .CAL($cal),
            .CE($ce),
            .CLK($clk),
            .IDATAIN($idatain[$ii]),
            .INC($inc),
            .IOCLK0($ioclk),
            .IOCLK1(~$ioclk),
            .ODATAIN($odatain[$ii]),
            .RST($rst),
            .T($t[$ii])
        );
    end
endgenerate
'''.strip()

def iodelay2_fixed(
    name,
    busy = '',
    dataout = '',
    dataout2 = '',
    dout = '',
    tout = '',
    idatain = '',
    odatain = '',
    rst = '',
    cal = '',
    t = '',

    counter_wraparound = 'WRAPAROUND',
    data_rate = 'SDR',
    delay_src = 'IDATAIN',
    idelay_value = 0,
    idelay2_value = 0,
    odelay_value = 0,
    serdes_mode = 'NONE'):

    idelay_type = 'FIXED'

    odatain.read = True
    idatain.read = True
    t.read = True

    dataout.driven = 'wire'
    dout.driven = 'wire'
    tout.driven = 'wire'

    ii = name + '_ii'
    iname = name + '_block'
    n = len(dout)

    @always_comb
    def comb():
        q.next = d0

    return comb

iodelay2_fixed.verilog_code = r'''
genvar $ii;
generate
    for ($ii = 0; $ii < $n; $ii = $ii + 1) begin : $iname
        IODELAY2 #(
            .COUNTER_WRAPAROUND("$counter_wraparound"),
            .DATA_RATE("$data_rate"),
            .DELAY_SRC("$delay_src"),
            .IDELAY2_VALUE($idelay2_value),
            .IDELAY_TYPE("$idelay_type"),
            .IDELAY_VALUE($idelay_value),
            .ODELAY_VALUE($odelay_value),
            .SERDES_MODE("$serdes_mode")
        )
        IODELAY2_inst (
            .BUSY($busy),
            .DATAOUT($dataout[$ii]),
            .DATAOUT2($dataout2),
            .DOUT($dout[$ii]),
            .TOUT($tout[$ii]),
            .IDATAIN($idatain[$ii]),
            .ODATAIN($odatain[$ii]),
            .RST($rst),
            .CAL($cal),
            .T($t[$ii])
        );
    end
endgenerate
'''.strip()

def iobuf_ddr2(name, i0, i1, ic0, ic1, o0, o1, oe0, oe1, oc0, oc1, io,
               ddr_alignment = 'NONE',
               srtype = 'SYNC'):
    i = Signal(intbv(0)[len(io):])
    o = Signal(intbv(0)[len(io):])
    t = Signal(intbv(0)[len(io):])
    t0 = Signal(intbv(0)[len(io):])
    t1 = Signal(intbv(0)[len(io):])

    insts = []

    iobuf_inst = iobuf(name + '_iobuf', i, o, t, io)
    insts.append(iobuf_inst)

    iddr2_inst = iddr2(name + '_iddr2', o, i0, i1, ic0, ic1,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(iddr2_inst)

    oddr2_inst = oddr2(name + '_oddr2', o0, o1, i, oc0, oc1,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(oddr2_inst)

    tddr2_inst = oddr2(name + '_tddr2', t0, t1, t, oc0, oc1,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(tddr2_inst)

    @always_comb
    def comb():
        if oe0:
            t0.next = 0
        else:
            t0.next = (1<<len(t0))-1
        if oe1:
            t1.next = 0
        else:
            t1.next = (1<<len(t1))-1
    insts.append(comb)

    return insts

def iobuf_ddr2_se(name, i0, i1, o0, o1, oe0, oe1, io, c,
                  ddr_alignment = 'NONE',
                  srtype = 'SYNC'):
    i = Signal(intbv(0)[len(io):])
    o = Signal(intbv(0)[len(io):])
    t = Signal(intbv(0)[len(io):])
    t0 = Signal(intbv(0)[len(io):])
    t1 = Signal(intbv(0)[len(io):])

    insts = []

    iobuf_inst = iobuf(name + '_iobuf', i, o, t, io)
    insts.append(iobuf_inst)

    iddr2_inst = iddr2_se(name + '_iddr2', o, i0, i1, c,
                          ddr_alignment = ddr_alignment,
                          srtype = srtype)
    insts.append(iddr2_inst)

    oddr2_inst = oddr2_se(name + '_oddr2', o0, o1, i, c,
                          ddr_alignment = ddr_alignment,
                          srtype = srtype)
    insts.append(oddr2_inst)

    tddr2_inst = oddr2_se(name + '_tddr2', t0, t1, t, c,
                          ddr_alignment = ddr_alignment,
                          srtype = srtype)
    insts.append(tddr2_inst)

    @always_comb
    def comb():
        if oe0:
            t0.next = 0
        else:
            t0.next = (1<<len(t0))-1
        if oe1:
            t1.next = 0
        else:
            t1.next = (1<<len(t1))-1
    insts.append(comb)

    return insts

def iobuf_delay_ddr2_fixed(name, i0, i1, o0, o1, oe0, oe1, io, clk, clk_b = None,
                           ddr_alignment = 'NONE',
                           srtype = 'SYNC',
                           idelay_value = 0,
                           odelay_value = 0):
    insts = []

    i0.driven = 'wire'
    i1.driven = 'wire'
    o0.read = True
    o1.read = True
    oe0.read = True
    oe1.read = True
    io.driven = 'wire'
    clk.read = True

    if clk_b is not None:
        clk_b.read = True

    i = Signal(intbv(0)[len(io):])
    o = Signal(intbv(0)[len(io):])
    t = Signal(intbv(0)[len(io):])

    iobuf_inst = iobuf(name + '_iobuf', i, o, t, io)
    insts.append(iobuf_inst)

    i2 = Signal(intbv(0)[len(io):])
    o2 = Signal(intbv(0)[len(io):])
    t2 = Signal(intbv(0)[len(io):])

    iodelay_inst = iodelay2_fixed(name + '_iodelay',
                               dout = i, odatain = i2,
                               dataout = o2, idatain = o,
                               t = t2, tout = t,

                               data_rate = 'DDR',
                               idelay_value = idelay_value,
                               odelay_value = odelay_value,
                               delay_src = 'IO',
                               )
    insts.append(iodelay_inst)

    iddr2_inst = iddr2(name + '_iddr2', o2, i0, i1, clk, clk_b,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(iddr2_inst)

    oddr2_inst = oddr2(name + '_oddr2', o0, o1, i2, clk, clk_b,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(oddr2_inst)

    t0 = Signal(intbv(0)[len(io):])
    t1 = Signal(intbv(0)[len(io):])

    tddr2_inst = oddr2(name + '_tddr2', t0, t1, t2, clk, clk_b,
                       ddr_alignment = ddr_alignment,
                       srtype = srtype)
    insts.append(tddr2_inst)

    @always_comb
    def comb():
        if oe0:
            t0.next = 0
        else:
            t0.next = (1<<len(t0))-1
        if oe1:
            t1.next = 0
        else:
            t1.next = (1<<len(t1))-1
    insts.append(comb)

    return insts

def pll_adv(
    name,

    rst = 0,
    clkinsel = 1,                       # default to clkin1
    clkin1 = 0,
    clkin2 = 0,

    clkfbin = 0,
    clkfbdcm = '',
    clkfbout = '',

    clkoutdcm0 = '',
    clkoutdcm1 = '',
    clkoutdcm2 = '',
    clkoutdcm3 = '',
    clkoutdcm4 = '',
    clkoutdcm5 = '',

    clkout0 = '',
    clkout1 = '',
    clkout2 = '',
    clkout3 = '',
    clkout4 = '',
    clkout5 = '',

    locked = '',

    BANDWIDTH          = "OPTIMIZED",

    CLKIN1_PERIOD      = 1000,          # (ps)
    CLKIN2_PERIOD      = 1000,          # (ps)

    DIVCLK_DIVIDE      = 1,
    CLKFBOUT_MULT      = 1,

    CLKOUT0_DIVIDE     = 1,
    CLKOUT1_DIVIDE     = 1,
    CLKOUT2_DIVIDE     = 1,
    CLKOUT3_DIVIDE     = 1,
    CLKOUT4_DIVIDE     = 1,
    CLKOUT5_DIVIDE     = 1,

    CLKOUT0_PHASE      = 0.000,
    CLKOUT1_PHASE      = 0.000,
    CLKOUT2_PHASE      = 0.000,
    CLKOUT3_PHASE      = 0.000,
    CLKOUT4_PHASE      = 0.000,
    CLKOUT5_PHASE      = 0.000,

    CLKOUT0_DUTY_CYCLE = 0.500,
    CLKOUT1_DUTY_CYCLE = 0.500,
    CLKOUT2_DUTY_CYCLE = 0.500,
    CLKOUT3_DUTY_CYCLE = 0.500,
    CLKOUT4_DUTY_CYCLE = 0.500,
    CLKOUT5_DUTY_CYCLE = 0.500,

    SIM_DEVICE         = "SPARTAN6",
    COMPENSATION       = "INTERNAL",

    CLKFBOUT_PHASE     = 0.000,
    REF_JITTER         = 0.005
    ):

    insts = []

    if isinstance(rst, SignalType):
        rst.read = True

    if isinstance(clkinsel, SignalType):
        clkinsel.read = True

    if isinstance(clkin1, SignalType):
        clkin1.read = True

    if isinstance(clkin2, SignalType):
        clkin2.read = True

    if isinstance(clkfbin, SignalType):
        clkfbin.read = True

    if isinstance(clkfbdcm, SignalType):
        clkfbdcm.driven = 'wire'
        @always_comb
        def clkfbdcm_inst():
            clkfbdcm.next = clkin1
        insts.append(clkfbdcm_inst)

    if isinstance(clkfbout, SignalType):
        clkfbout.driven = 'wire'
        @always_comb
        def clkfbout_inst():
            clkfbout.next = clkin1
        insts.append(clkfbout_inst)

    if isinstance(clkout0, SignalType):
        clkout0.driven = 'wire'
        @always_comb
        def clkout0_inst():
            clkout0.next = clkin1
        insts.append(clkout0_inst)

    if isinstance(clkout1, SignalType):
        clkout1.driven = 'wire'
        @always_comb
        def clkout1_inst():
            clkout1.next = clkin1
        insts.append(clkout1_inst)

    if isinstance(clkout2, SignalType):
        clkout2.driven = 'wire'
        @always_comb
        def clkout2_inst():
            clkout2.next = clkin1
        insts.append(clkout2_inst)

    if isinstance(clkout3, SignalType):
        clkout3.driven = 'wire'
        @always_comb
        def clkout3_inst():
            clkout3.next = clkin1
        insts.append(clkout3_inst)

    if isinstance(clkout4, SignalType):
        clkout4.driven = 'wire'
        @always_comb
        def clkout4_inst():
            clkout4.next = clkin1
        insts.append(clkout4_inst)

    if isinstance(clkout5, SignalType):
        clkout5.driven = 'wire'
        @always_comb
        def clkout5_inst():
            clkout5.next = clkin1
        insts.append(clkout5_inst)

    return insts

pll_adv.verilog_code = '''
PLL_ADV #(
    .BANDWIDTH          ("$BANDWIDTH"),
    .CLKIN1_PERIOD      ($CLKIN1_PERIOD),
    .CLKIN2_PERIOD      ($CLKIN2_PERIOD),
    .DIVCLK_DIVIDE      ($DIVCLK_DIVIDE),
    .CLKFBOUT_MULT      ($CLKFBOUT_MULT),
    .CLKFBOUT_PHASE     ($CLKFBOUT_PHASE),
    .CLKOUT0_DIVIDE     ($CLKOUT0_DIVIDE),
    .CLKOUT1_DIVIDE     ($CLKOUT1_DIVIDE),
    .CLKOUT2_DIVIDE     ($CLKOUT2_DIVIDE),
    .CLKOUT3_DIVIDE     ($CLKOUT3_DIVIDE),
    .CLKOUT4_DIVIDE     ($CLKOUT4_DIVIDE),
    .CLKOUT5_DIVIDE     ($CLKOUT5_DIVIDE),
    .CLKOUT0_PHASE      ($CLKOUT0_PHASE),
    .CLKOUT1_PHASE      ($CLKOUT1_PHASE),
    .CLKOUT2_PHASE      ($CLKOUT2_PHASE),
    .CLKOUT3_PHASE      ($CLKOUT3_PHASE),
    .CLKOUT4_PHASE      ($CLKOUT4_PHASE),
    .CLKOUT5_PHASE      ($CLKOUT5_PHASE),
    .CLKOUT0_DUTY_CYCLE ($CLKOUT0_DUTY_CYCLE),
    .CLKOUT1_DUTY_CYCLE ($CLKOUT1_DUTY_CYCLE),
    .CLKOUT2_DUTY_CYCLE ($CLKOUT2_DUTY_CYCLE),
    .CLKOUT3_DUTY_CYCLE ($CLKOUT3_DUTY_CYCLE),
    .CLKOUT4_DUTY_CYCLE ($CLKOUT4_DUTY_CYCLE),
    .CLKOUT5_DUTY_CYCLE ($CLKOUT5_DUTY_CYCLE),
    .SIM_DEVICE         ("SPARTAN6"),
    .COMPENSATION       ("INTERNAL"),
    .REF_JITTER         ($REF_JITTER)
)
$name
(
    .RST         ($rst),

    .CLKFBIN     ($clkfbin),
    .CLKINSEL    ($clkinsel),
    .CLKIN1      ($clkin1),
    .CLKIN2      ($clkin2),
    .CLKFBDCM    ($clkfbdcm),
    .CLKFBOUT    ($clkfbout),

    .CLKOUTDCM0  ($clkoutdcm0),
    .CLKOUTDCM1  ($clkoutdcm1),
    .CLKOUTDCM2  ($clkoutdcm2),
    .CLKOUTDCM3  ($clkoutdcm3),
    .CLKOUTDCM4  ($clkoutdcm4),
    .CLKOUTDCM5  ($clkoutdcm5),

    .CLKOUT0     ($clkout0),
    .CLKOUT1     ($clkout1),
    .CLKOUT2     ($clkout2),
    .CLKOUT3     ($clkout3),
    .CLKOUT4     ($clkout4),
    .CLKOUT5     ($clkout5),

    .REL         (1'b0),
    .LOCKED      ($locked),

    .DADDR       (5'b0),
    .DCLK        (1'b0),
    .DEN         (1'b0),
    .DI          (16'b0),
    .DWE         (1'b0),
    .DO          (),
    .DRDY        ()
);
'''

def bufpll_mcb(
        name,

        gclk,
        pllin0,
        pllin1,
        locked,

        ioclk0,
        ioclk1,
        serdesstrobe0,
        serdesstrobe1,
        lock,
        ):

    gclk.read = True
    pllin0.read = True
    pllin1.read = True
    lock.read = True

    ioclk0.driven = 'wire'
    ioclk1.driven = 'wire'
    serdesstrobe0.driven = 'wire'
    serdesstrobe1.driven = 'wire'
    lock.driven = 'wire'

    @always_comb
    def comb():
        serdesstrobe0.next = pllin0
        serdesstrobe1.next = pllin1
    return comb

bufpll_mcb.verilog_code = '''
BUFPLL_MCB $name
(
    .GCLK           ($gclk),
    .PLLIN0         ($pllin0),
    .PLLIN1         ($pllin1),
    .LOCKED         ($locked),

    .IOCLK0         ($ioclk0),
    .IOCLK1         ($ioclk1),
    .SERDESSTROBE0  ($serdesstrobe0),
    .SERDESSTROBE1  ($serdesstrobe1),
    .LOCK           ($lock)
);
'''

def mcb_ui_top(
    name,

    mcbx_dram_clk,
    mcbx_dram_clk_n,
    mcbx_dram_cke,
    mcbx_dram_ras_n,
    mcbx_dram_cas_n,
    mcbx_dram_we_n,
    mcbx_dram_ba,
    mcbx_dram_addr,
    mcbx_dram_dqs,
    mcbx_dram_dqs_n,
    mcbx_dram_udqs,
    mcbx_dram_udqs_n,
    mcbx_dram_ldm,
    mcbx_dram_udm,
    mcbx_dram_dq,
    mcbx_dram_odt,
    mcbx_dram_ddr3_rst,
    mcbx_rzq,
    mcbx_zio,

    sys_rst,

    ui_clk,

    sysclk_2x,
    sysclk_2x_180,

    pll_ce_0,
    pll_ce_90,
    pll_lock,

    sysclk_2x_bufpll_o = '',
    sysclk_2x_180_bufpll_o = '',

    pll_ce_0_bufpll_o = '',
    pll_ce_90_bufpll_o = '',
    pll_lock_bufpll_o = '',

    p0_arb_en = 1,

    p0_cmd_clk = 0,
    p0_cmd_en = 0,
    p0_cmd_instr = 0,
    p0_cmd_bl = 0,
    p0_cmd_byte_addr = 0,
    p0_cmd_empty = '',
    p0_cmd_full = '',

    p0_wr_clk = 0,
    p0_wr_en = 0,
    p0_wr_mask = 0,
    p0_wr_data = 0,
    p0_wr_full = '',
    p0_wr_empty = '',
    p0_wr_count = '',
    p0_wr_underrun = '',
    p0_wr_error = '',

    p0_rd_clk = 0,
    p0_rd_en = 0,
    p0_rd_data = '',
    p0_rd_full = '',
    p0_rd_empty = '',
    p0_rd_count = '',
    p0_rd_overflow = '',
    p0_rd_error = '',

    p1_arb_en = 1,

    p1_cmd_clk = 0,
    p1_cmd_en = 0,
    p1_cmd_instr = 0,
    p1_cmd_bl = 0,
    p1_cmd_byte_addr = 0,
    p1_cmd_empty = '',
    p1_cmd_full = '',

    p1_wr_clk = 0,
    p1_wr_en = 0,
    p1_wr_mask = 0,
    p1_wr_data = 0,
    p1_wr_full = '',
    p1_wr_empty = '',
    p1_wr_count = '',
    p1_wr_underrun = '',
    p1_wr_error = '',

    p1_rd_clk = 0,
    p1_rd_en = 0,
    p1_rd_data = '',
    p1_rd_full = '',
    p1_rd_empty = '',
    p1_rd_count = '',
    p1_rd_overflow = '',
    p1_rd_error = '',

    p2_arb_en = 1,

    p2_cmd_clk = 0,
    p2_cmd_en = 0,
    p2_cmd_instr = 0,
    p2_cmd_bl = 0,
    p2_cmd_byte_addr = 0,
    p2_cmd_empty = '',
    p2_cmd_full = '',

    p2_wr_clk = 0,
    p2_wr_en = 0,
    p2_wr_mask = 0,
    p2_wr_data = 0,
    p2_wr_full = '',
    p2_wr_empty = '',
    p2_wr_count = '',
    p2_wr_underrun = '',
    p2_wr_error = '',

    p2_rd_clk = 0,
    p2_rd_en = 0,
    p2_rd_data = '',
    p2_rd_full = '',
    p2_rd_empty = '',
    p2_rd_count = '',
    p2_rd_overflow = '',
    p2_rd_error = '',

    p3_arb_en = 1,

    p3_cmd_clk = 0,
    p3_cmd_en = 0,
    p3_cmd_instr = 0,
    p3_cmd_bl = 0,
    p3_cmd_byte_addr = 0,
    p3_cmd_empty = '',
    p3_cmd_full = '',

    p3_wr_clk = 0,
    p3_wr_en = 0,
    p3_wr_mask = 0,
    p3_wr_data = 0,
    p3_wr_full = '',
    p3_wr_empty = '',
    p3_wr_count = '',
    p3_wr_underrun = '',
    p3_wr_error = '',

    p3_rd_clk = 0,
    p3_rd_en = 0,
    p3_rd_data = '',
    p3_rd_full = '',
    p3_rd_empty = '',
    p3_rd_count = '',
    p3_rd_overflow = '',
    p3_rd_error = '',

    p4_arb_en = 1,

    p4_cmd_clk = 0,
    p4_cmd_en = 0,
    p4_cmd_instr = 0,
    p4_cmd_bl = 0,
    p4_cmd_byte_addr = 0,
    p4_cmd_empty = '',
    p4_cmd_full = '',

    p4_wr_clk = 0,
    p4_wr_en = 0,
    p4_wr_mask = 0,
    p4_wr_data = 0,
    p4_wr_full = '',
    p4_wr_empty = '',
    p4_wr_count = '',
    p4_wr_underrun = '',
    p4_wr_error = '',

    p4_rd_clk = 0,
    p4_rd_en = 0,
    p4_rd_data = '',
    p4_rd_full = '',
    p4_rd_empty = '',
    p4_rd_count = '',
    p4_rd_overflow = '',
    p4_rd_error = '',

    p5_arb_en = 1,

    p5_cmd_clk = 0,
    p5_cmd_en = 0,
    p5_cmd_instr = 0,
    p5_cmd_bl = 0,
    p5_cmd_byte_addr = 0,
    p5_cmd_empty = '',
    p5_cmd_full = '',

    p5_wr_clk = 0,
    p5_wr_en = 0,
    p5_wr_mask = 0,
    p5_wr_data = 0,
    p5_wr_full = '',
    p5_wr_empty = '',
    p5_wr_count = '',
    p5_wr_underrun = '',
    p5_wr_error = '',

    p5_rd_clk = 0,
    p5_rd_en = 0,
    p5_rd_data = '',
    p5_rd_full = '',
    p5_rd_empty = '',
    p5_rd_count = '',
    p5_rd_overflow = '',
    p5_rd_error = '',

    status = '',
    selfrefresh_enter = 0,
    selfrefresh_mode = '',

    uo_done_cal = '',

    C_MEMCLK_PERIOD           = 2500,

    C_P0_MASK_SIZE            = 4,
    C_P0_DATA_PORT_SIZE       = 32,
    C_P1_MASK_SIZE            = 4,
    C_P1_DATA_PORT_SIZE       = 32,

    C_PORT_ENABLE             = 0x2f, # 6'b111111
    C_PORT_CONFIG             = "B128",
    C_MEM_ADDR_ORDER          = "BANK_ROW_COLUMN",

    # The following parameter reflects the GUI selection of the
    # Arbitration algorithm.  Zero value corresponds to round robin
    # algorithm and one to custom selection.  The parameter is used to
    # calculate the arbitration time slot parameters.
    C_ARB_ALGORITHM           = 0,
    C_ARB_NUM_TIME_SLOTS      = 12,
    C_ARB_TIME_SLOT_0         = "18'o012345",
    C_ARB_TIME_SLOT_1         = "18'o123450",
    C_ARB_TIME_SLOT_2         = "18'o234501",
    C_ARB_TIME_SLOT_3         = "18'o345012",
    C_ARB_TIME_SLOT_4         = "18'o450123",
    C_ARB_TIME_SLOT_5         = "18'o501234",
    C_ARB_TIME_SLOT_6         = "18'o012345",
    C_ARB_TIME_SLOT_7         = "18'o123450",
    C_ARB_TIME_SLOT_8         = "18'o234501",
    C_ARB_TIME_SLOT_9         = "18'o345012",
    C_ARB_TIME_SLOT_10        = "18'o450123",
    C_ARB_TIME_SLOT_11        = "18'o501234",

    C_MEM_TRAS                = 45000,
    C_MEM_TRCD                = 12500,
    C_MEM_TREFI               = 7800000,
    C_MEM_TRFC                = 105000, # 127500
    C_MEM_TRP                 = 15000,  # 12500
    C_MEM_TWR                 = 15000,
    C_MEM_TRTP                = 7500,
    C_MEM_TWTR                = 7500,
    C_NUM_DQ_PINS             = 8,
    C_MEM_TYPE                = "DDR3",
    C_MEM_DENSITY             = "512M",
    C_MEM_BURST_LEN           = 8,
    C_MEM_CAS_LATENCY         = 4,
    C_MEM_ADDR_WIDTH          = 13,
    C_MEM_BANKADDR_WIDTH      = 3,
    C_MEM_NUM_COL_BITS        = 11,
    C_MEM_DDR3_CAS_LATENCY    = 7,
    C_MEM_MOBILE_PA_SR        = "FULL",
    C_MEM_DDR1_2_ODS          = "FULL",
    C_MEM_DDR3_ODS            = "DIV6",
    C_MEM_DDR2_RTT            = "50OHMS",
    C_MEM_DDR3_RTT            = "DIV2",
    C_MEM_MDDR_ODS            = "FULL",
    C_MEM_DDR2_DIFF_DQS_EN    = "YES",
    C_MEM_DDR2_3_PA_SR        = "OFF",
    C_MEM_DDR3_CAS_WR_LATENCY = 5,
    C_MEM_DDR3_AUTO_SR        = "ENABLED",
    C_MEM_DDR2_3_HIGH_TEMP_SR = "NORMAL",
    C_MEM_DDR3_DYN_WRT_ODT    = "OFF",
    C_MC_CALIB_BYPASS         = "NO",
    C_MC_CALIBRATION_MODE     = "CALIBRATION",
    C_MC_CALIBRATION_DELAY    = "HALF",
    C_SKIP_IN_TERM_CAL        = 0,
    C_SKIP_DYNAMIC_CAL        = 0,

    LDQSP_TAP_DELAY_VAL       = 0,
    UDQSP_TAP_DELAY_VAL       = 0,
    LDQSN_TAP_DELAY_VAL       = 0,
    UDQSN_TAP_DELAY_VAL       = 0,
    DQ0_TAP_DELAY_VAL         = 0,
    DQ1_TAP_DELAY_VAL         = 0,
    DQ2_TAP_DELAY_VAL         = 0,
    DQ3_TAP_DELAY_VAL         = 0,
    DQ4_TAP_DELAY_VAL         = 0,
    DQ5_TAP_DELAY_VAL         = 0,
    DQ6_TAP_DELAY_VAL         = 0,
    DQ7_TAP_DELAY_VAL         = 0,
    DQ8_TAP_DELAY_VAL         = 0,
    DQ9_TAP_DELAY_VAL         = 0,
    DQ10_TAP_DELAY_VAL        = 0,
    DQ11_TAP_DELAY_VAL        = 0,
    DQ12_TAP_DELAY_VAL        = 0,
    DQ13_TAP_DELAY_VAL        = 0,
    DQ14_TAP_DELAY_VAL        = 0,
    DQ15_TAP_DELAY_VAL        = 0,

    C_CALIB_SOFT_IP           = "TRUE",
    C_SIMULATION              = "FALSE",

    ):

    mcbx_dram_clk.driven = 'wire'
    mcbx_dram_clk_n.driven = 'wire'
    if isinstance(mcbx_dram_cke, SignalType):
        mcbx_dram_cke.driven = 'wire'
    mcbx_dram_ras_n.driven = 'wire'
    mcbx_dram_cas_n.driven = 'wire'
    mcbx_dram_we_n.driven = 'wire'
    mcbx_dram_ba.driven = 'wire'
    mcbx_dram_addr.driven = 'wire'
    mcbx_dram_dqs.read = True
    mcbx_dram_dqs.driven = 'wire'
    mcbx_dram_dqs_n.read = True
    mcbx_dram_dqs_n.driven = 'wire'
    mcbx_dram_udqs.read = True
    mcbx_dram_udqs.driven = 'wire'
    mcbx_dram_udqs_n.read = True
    mcbx_dram_udqs_n.driven = 'wire'
    mcbx_dram_ldm.driven = 'wire'
    mcbx_dram_udm.driven = 'wire'
    mcbx_dram_dq.read = True
    mcbx_dram_dq.driven = 'wire'

    if isinstance(sys_rst, SignalType):
        sys_rst.read = True
    elif sys_rst is None:
        sys_rst = 0

    ui_clk.read = True
    sysclk_2x.read = True
    sysclk_2x_180.read = True
    pll_ce_0.read = True
    pll_ce_90.read = True
    pll_lock.read = True

    if isinstance(uo_done_cal, SignalType):
        uo_done_cal.driven = 'wire'

    C_MC_CALIBRATION_CLK_DIV  = 1

    # 16 clock cycles are added to avoid trfc violations
    C_MEM_TZQINIT_MAXCNT      = 512 + 16
    C_SKIP_DYN_IN_TERM        = 1

    C_MC_CALIBRATION_RA       = intbv(0)[16:]
    C_MC_CALIBRATION_BA       = intbv(0)[3:]
    C_MC_CALIBRATION_CA       = intbv(0)[12:]

    C_MCB_USE_EXTERNAL_BUFPLL = 1

    @always_comb
    def comb():
        status.next = not sys_rst

    return comb

mcb_ui_top.verilog_code = '''
mcb_ui_top #(
    // Raw Wrapper Parameters
    .C_MEMCLK_PERIOD               ($C_MEMCLK_PERIOD),

    .C_P0_MASK_SIZE                ($C_P0_MASK_SIZE),
    .C_P0_DATA_PORT_SIZE           ($C_P0_DATA_PORT_SIZE),
    .C_P1_MASK_SIZE                ($C_P1_MASK_SIZE),
    .C_P1_DATA_PORT_SIZE           ($C_P1_DATA_PORT_SIZE),

    .C_PORT_ENABLE                 ($C_PORT_ENABLE),
    .C_PORT_CONFIG                 ("$C_PORT_CONFIG"),
    .C_MEM_ADDR_ORDER              ("$C_MEM_ADDR_ORDER"),

    .C_ARB_ALGORITHM               ($C_ARB_ALGORITHM),
    .C_ARB_NUM_TIME_SLOTS          ($C_ARB_NUM_TIME_SLOTS),
    .C_ARB_TIME_SLOT_0             ($C_ARB_TIME_SLOT_0),
    .C_ARB_TIME_SLOT_1             ($C_ARB_TIME_SLOT_1),
    .C_ARB_TIME_SLOT_2             ($C_ARB_TIME_SLOT_2),
    .C_ARB_TIME_SLOT_3             ($C_ARB_TIME_SLOT_3),
    .C_ARB_TIME_SLOT_4             ($C_ARB_TIME_SLOT_4),
    .C_ARB_TIME_SLOT_5             ($C_ARB_TIME_SLOT_5),
    .C_ARB_TIME_SLOT_6             ($C_ARB_TIME_SLOT_6),
    .C_ARB_TIME_SLOT_7             ($C_ARB_TIME_SLOT_7),
    .C_ARB_TIME_SLOT_8             ($C_ARB_TIME_SLOT_8),
    .C_ARB_TIME_SLOT_9             ($C_ARB_TIME_SLOT_9),
    .C_ARB_TIME_SLOT_10            ($C_ARB_TIME_SLOT_10),
    .C_ARB_TIME_SLOT_11            ($C_ARB_TIME_SLOT_11),

    .C_MEM_TRAS                    ($C_MEM_TRAS),
    .C_MEM_TRCD                    ($C_MEM_TRCD),
    .C_MEM_TREFI                   ($C_MEM_TREFI),
    .C_MEM_TRFC                    ($C_MEM_TRFC),
    .C_MEM_TRP                     ($C_MEM_TRP),
    .C_MEM_TWR                     ($C_MEM_TWR),
    .C_MEM_TRTP                    ($C_MEM_TRTP),
    .C_MEM_TWTR                    ($C_MEM_TWTR),
    .C_NUM_DQ_PINS                 ($C_NUM_DQ_PINS),
    .C_MEM_TYPE                    ("$C_MEM_TYPE"),
    .C_MEM_DENSITY                 ("$C_MEM_DENSITY"),
    .C_MEM_BURST_LEN               ($C_MEM_BURST_LEN),
    .C_MEM_CAS_LATENCY             ($C_MEM_CAS_LATENCY),
    .C_MEM_ADDR_WIDTH              ($C_MEM_ADDR_WIDTH),
    .C_MEM_BANKADDR_WIDTH          ($C_MEM_BANKADDR_WIDTH),
    .C_MEM_NUM_COL_BITS            ($C_MEM_NUM_COL_BITS),
    .C_MEM_DDR3_CAS_LATENCY        ($C_MEM_DDR3_CAS_LATENCY),
    .C_MEM_MOBILE_PA_SR            ("$C_MEM_MOBILE_PA_SR"),
    .C_MEM_DDR1_2_ODS              ("$C_MEM_DDR1_2_ODS"),
    .C_MEM_DDR3_ODS                ("$C_MEM_DDR3_ODS"),
    .C_MEM_DDR2_RTT                ("$C_MEM_DDR2_RTT"),
    .C_MEM_DDR3_RTT                ("$C_MEM_DDR3_RTT"),
    .C_MEM_MDDR_ODS                ("$C_MEM_MDDR_ODS"),
    .C_MEM_DDR2_DIFF_DQS_EN        ("$C_MEM_DDR2_DIFF_DQS_EN"),
    .C_MEM_DDR2_3_PA_SR            ("$C_MEM_DDR2_3_PA_SR"),
    .C_MEM_DDR3_CAS_WR_LATENCY     ($C_MEM_DDR3_CAS_WR_LATENCY),
    .C_MEM_DDR3_AUTO_SR            ("$C_MEM_DDR3_AUTO_SR"),
    .C_MEM_DDR2_3_HIGH_TEMP_SR     ("$C_MEM_DDR2_3_HIGH_TEMP_SR"),
    .C_MEM_DDR3_DYN_WRT_ODT        ("$C_MEM_DDR3_DYN_WRT_ODT"),
    .C_MEM_TZQINIT_MAXCNT          ($C_MEM_TZQINIT_MAXCNT),
    .C_MC_CALIB_BYPASS             ("$C_MC_CALIB_BYPASS"),
    .C_MC_CALIBRATION_RA           ($C_MC_CALIBRATION_RA),
    .C_MC_CALIBRATION_BA           ($C_MC_CALIBRATION_BA),
    .C_MC_CALIBRATION_CA           ($C_MC_CALIBRATION_CA),
    .C_CALIB_SOFT_IP               ("$C_CALIB_SOFT_IP"),
    .C_SKIP_IN_TERM_CAL            ($C_SKIP_IN_TERM_CAL),
    .C_SKIP_DYNAMIC_CAL            ($C_SKIP_DYNAMIC_CAL),
    .C_SKIP_DYN_IN_TERM            ($C_SKIP_DYN_IN_TERM),
    .LDQSP_TAP_DELAY_VAL           ($LDQSP_TAP_DELAY_VAL),
    .UDQSP_TAP_DELAY_VAL           ($UDQSP_TAP_DELAY_VAL),
    .LDQSN_TAP_DELAY_VAL           ($LDQSN_TAP_DELAY_VAL),
    .UDQSN_TAP_DELAY_VAL           ($UDQSN_TAP_DELAY_VAL),
    .DQ0_TAP_DELAY_VAL             ($DQ0_TAP_DELAY_VAL),
    .DQ1_TAP_DELAY_VAL             ($DQ1_TAP_DELAY_VAL),
    .DQ2_TAP_DELAY_VAL             ($DQ2_TAP_DELAY_VAL),
    .DQ3_TAP_DELAY_VAL             ($DQ3_TAP_DELAY_VAL),
    .DQ4_TAP_DELAY_VAL             ($DQ4_TAP_DELAY_VAL),
    .DQ5_TAP_DELAY_VAL             ($DQ5_TAP_DELAY_VAL),
    .DQ6_TAP_DELAY_VAL             ($DQ6_TAP_DELAY_VAL),
    .DQ7_TAP_DELAY_VAL             ($DQ7_TAP_DELAY_VAL),
    .DQ8_TAP_DELAY_VAL             ($DQ8_TAP_DELAY_VAL),
    .DQ9_TAP_DELAY_VAL             ($DQ9_TAP_DELAY_VAL),
    .DQ10_TAP_DELAY_VAL            ($DQ10_TAP_DELAY_VAL),
    .DQ11_TAP_DELAY_VAL            ($DQ11_TAP_DELAY_VAL),
    .DQ12_TAP_DELAY_VAL            ($DQ12_TAP_DELAY_VAL),
    .DQ13_TAP_DELAY_VAL            ($DQ13_TAP_DELAY_VAL),
    .DQ14_TAP_DELAY_VAL            ($DQ14_TAP_DELAY_VAL),
    .DQ15_TAP_DELAY_VAL            ($DQ15_TAP_DELAY_VAL),
    .C_MC_CALIBRATION_CLK_DIV      ($C_MC_CALIBRATION_CLK_DIV),
    .C_MC_CALIBRATION_MODE         ("$C_MC_CALIBRATION_MODE"),
    .C_MC_CALIBRATION_DELAY        ("$C_MC_CALIBRATION_DELAY"),
    .C_SIMULATION                  ("$C_SIMULATION"),
    .C_MCB_USE_EXTERNAL_BUFPLL     ($C_MCB_USE_EXTERNAL_BUFPLL)
)
$name
(
    // Raw Wrapper Signals
    .sysclk_2x                     ($sysclk_2x),
    .sysclk_2x_180                 ($sysclk_2x_180),
    .pll_ce_0                      ($pll_ce_0),
    .pll_ce_90                     ($pll_ce_90),
    .pll_lock                      ($pll_lock),
    .sysclk_2x_bufpll_o            ($sysclk_2x_bufpll_o),
    .sysclk_2x_180_bufpll_o        ($sysclk_2x_180_bufpll_o),
    .pll_ce_0_bufpll_o             ($pll_ce_0_bufpll_o),
    .pll_ce_90_bufpll_o            ($pll_ce_90_bufpll_o),
    .pll_lock_bufpll_o             ($pll_lock_bufpll_o),
    .sys_rst                       ($sys_rst),
    .p0_arb_en                     ($p0_arb_en),
    .p0_cmd_clk                    ($p0_cmd_clk),
    .p0_cmd_en                     ($p0_cmd_en),
    .p0_cmd_instr                  ($p0_cmd_instr),
    .p0_cmd_bl                     ($p0_cmd_bl),
    .p0_cmd_byte_addr              ($p0_cmd_byte_addr),
    .p0_cmd_empty                  ($p0_cmd_empty),
    .p0_cmd_full                   ($p0_cmd_full),
    .p0_wr_clk                     ($p0_wr_clk),
    .p0_wr_en                      ($p0_wr_en),
    .p0_wr_mask                    ($p0_wr_mask),
    .p0_wr_data                    ($p0_wr_data),
    .p0_wr_full                    ($p0_wr_full),
    .p0_wr_empty                   ($p0_wr_empty),
    .p0_wr_count                   ($p0_wr_count),
    .p0_wr_underrun                ($p0_wr_underrun),
    .p0_wr_error                   ($p0_wr_error),
    .p0_rd_clk                     ($p0_rd_clk),
    .p0_rd_en                      ($p0_rd_en),
    .p0_rd_data                    ($p0_rd_data),
    .p0_rd_full                    ($p0_rd_full),
    .p0_rd_empty                   ($p0_rd_empty),
    .p0_rd_count                   ($p0_rd_count),
    .p0_rd_overflow                ($p0_rd_overflow),
    .p0_rd_error                   ($p0_rd_error),
    .p1_arb_en                     ($p1_arb_en),
    .p1_cmd_clk                    ($p1_cmd_clk),
    .p1_cmd_en                     ($p1_cmd_en),
    .p1_cmd_instr                  ($p1_cmd_instr),
    .p1_cmd_bl                     ($p1_cmd_bl),
    .p1_cmd_byte_addr              ($p1_cmd_byte_addr),
    .p1_cmd_empty                  ($p1_cmd_empty),
    .p1_cmd_full                   ($p1_cmd_full),
    .p1_wr_clk                     ($p1_wr_clk),
    .p1_wr_en                      ($p1_wr_en),
    .p1_wr_mask                    ($p1_wr_mask),
    .p1_wr_data                    ($p1_wr_data),
    .p1_wr_full                    ($p1_wr_full),
    .p1_wr_empty                   ($p1_wr_empty),
    .p1_wr_count                   ($p1_wr_count),
    .p1_wr_underrun                ($p1_wr_underrun),
    .p1_wr_error                   ($p1_wr_error),
    .p1_rd_clk                     ($p1_rd_clk),
    .p1_rd_en                      ($p1_rd_en),
    .p1_rd_data                    ($p1_rd_data),
    .p1_rd_full                    ($p1_rd_full),
    .p1_rd_empty                   ($p1_rd_empty),
    .p1_rd_count                   ($p1_rd_count),
    .p1_rd_overflow                ($p1_rd_overflow),
    .p1_rd_error                   ($p1_rd_error),
    .p2_arb_en                     ($p2_arb_en),
    .p2_cmd_clk                    ($p2_cmd_clk),
    .p2_cmd_en                     ($p2_cmd_en),
    .p2_cmd_instr                  ($p2_cmd_instr),
    .p2_cmd_bl                     ($p2_cmd_bl),
    .p2_cmd_byte_addr              ($p2_cmd_byte_addr),
    .p2_cmd_empty                  ($p2_cmd_empty),
    .p2_cmd_full                   ($p2_cmd_full),
    .p2_wr_clk                     ($p2_wr_clk),
    .p2_wr_en                      ($p2_wr_en),
    .p2_wr_mask                    ($p2_wr_mask),
    .p2_wr_data                    ($p2_wr_data),
    .p2_wr_full                    ($p2_wr_full),
    .p2_wr_empty                   ($p2_wr_empty),
    .p2_wr_count                   ($p2_wr_count),
    .p2_wr_underrun                ($p2_wr_underrun),
    .p2_wr_error                   ($p2_wr_error),
    .p2_rd_clk                     ($p2_rd_clk),
    .p2_rd_en                      ($p2_rd_en),
    .p2_rd_data                    ($p2_rd_data),
    .p2_rd_full                    ($p2_rd_full),
    .p2_rd_empty                   ($p2_rd_empty),
    .p2_rd_count                   ($p2_rd_count),
    .p2_rd_overflow                ($p2_rd_overflow),
    .p2_rd_error                   ($p2_rd_error),
    .p3_arb_en                     ($p3_arb_en),
    .p3_cmd_clk                    ($p3_cmd_clk),
    .p3_cmd_en                     ($p3_cmd_en),
    .p3_cmd_instr                  ($p3_cmd_instr),
    .p3_cmd_bl                     ($p3_cmd_bl),
    .p3_cmd_byte_addr              ($p3_cmd_byte_addr),
    .p3_cmd_empty                  ($p3_cmd_empty),
    .p3_cmd_full                   ($p3_cmd_full),
    .p3_wr_clk                     ($p3_wr_clk),
    .p3_wr_en                      ($p3_wr_en),
    .p3_wr_mask                    ($p3_wr_mask),
    .p3_wr_data                    ($p3_wr_data),
    .p3_wr_full                    ($p3_wr_full),
    .p3_wr_empty                   ($p3_wr_empty),
    .p3_wr_count                   ($p3_wr_count),
    .p3_wr_underrun                ($p3_wr_underrun),
    .p3_wr_error                   ($p3_wr_error),
    .p3_rd_clk                     ($p3_rd_clk),
    .p3_rd_en                      ($p3_rd_en),
    .p3_rd_data                    ($p3_rd_data),
    .p3_rd_full                    ($p3_rd_full),
    .p3_rd_empty                   ($p3_rd_empty),
    .p3_rd_count                   ($p3_rd_count),
    .p3_rd_overflow                ($p3_rd_overflow),
    .p3_rd_error                   ($p3_rd_error),
    .p4_arb_en                     ($p4_arb_en),
    .p4_cmd_clk                    ($p4_cmd_clk),
    .p4_cmd_en                     ($p4_cmd_en),
    .p4_cmd_instr                  ($p4_cmd_instr),
    .p4_cmd_bl                     ($p4_cmd_bl),
    .p4_cmd_byte_addr              ($p4_cmd_byte_addr),
    .p4_cmd_empty                  ($p4_cmd_empty),
    .p4_cmd_full                   ($p4_cmd_full),
    .p4_wr_clk                     ($p4_wr_clk),
    .p4_wr_en                      ($p4_wr_en),
    .p4_wr_mask                    ($p4_wr_mask),
    .p4_wr_data                    ($p4_wr_data),
    .p4_wr_full                    ($p4_wr_full),
    .p4_wr_empty                   ($p4_wr_empty),
    .p4_wr_count                   ($p4_wr_count),
    .p4_wr_underrun                ($p4_wr_underrun),
    .p4_wr_error                   ($p4_wr_error),
    .p4_rd_clk                     ($p4_rd_clk),
    .p4_rd_en                      ($p4_rd_en),
    .p4_rd_data                    ($p4_rd_data),
    .p4_rd_full                    ($p4_rd_full),
    .p4_rd_empty                   ($p4_rd_empty),
    .p4_rd_count                   ($p4_rd_count),
    .p4_rd_overflow                ($p4_rd_overflow),
    .p4_rd_error                   ($p4_rd_error),
    .p5_arb_en                     ($p5_arb_en),
    .p5_cmd_clk                    ($p5_cmd_clk),
    .p5_cmd_en                     ($p5_cmd_en),
    .p5_cmd_instr                  ($p5_cmd_instr),
    .p5_cmd_bl                     ($p5_cmd_bl),
    .p5_cmd_byte_addr              ($p5_cmd_byte_addr),
    .p5_cmd_empty                  ($p5_cmd_empty),
    .p5_cmd_full                   ($p5_cmd_full),
    .p5_wr_clk                     ($p5_wr_clk),
    .p5_wr_en                      ($p5_wr_en),
    .p5_wr_mask                    ($p5_wr_mask),
    .p5_wr_data                    ($p5_wr_data),
    .p5_wr_full                    ($p5_wr_full),
    .p5_wr_empty                   ($p5_wr_empty),
    .p5_wr_count                   ($p5_wr_count),
    .p5_wr_underrun                ($p5_wr_underrun),
    .p5_wr_error                   ($p5_wr_error),
    .p5_rd_clk                     ($p5_rd_clk),
    .p5_rd_en                      ($p5_rd_en),
    .p5_rd_data                    ($p5_rd_data),
    .p5_rd_full                    ($p5_rd_full),
    .p5_rd_empty                   ($p5_rd_empty),
    .p5_rd_count                   ($p5_rd_count),
    .p5_rd_overflow                ($p5_rd_overflow),
    .p5_rd_error                   ($p5_rd_error),

    .ui_read                       (1'b0),
    .ui_add                        (1'b0),
    .ui_cs                         (1'b0),
    .ui_clk                        ($ui_clk),
    .ui_sdi                        (1'b0),
    .ui_addr                       (5'b0),
    .ui_broadcast                  (1'b0),
    .ui_drp_update                 (1'b0),
    .ui_done_cal                   (1'b1),
    .ui_cmd                        (1'b0),
    .ui_cmd_in                     (1'b0),
    .ui_cmd_en                     (1'b0),
    .ui_dqcount                    (4'b0),
    .ui_dq_lower_dec               (1'b0),
    .ui_dq_lower_inc               (1'b0),
    .ui_dq_upper_dec               (1'b0),
    .ui_dq_upper_inc               (1'b0),
    .ui_udqs_inc                   (1'b0),
    .ui_udqs_dec                   (1'b0),
    .ui_ldqs_inc                   (1'b0),
    .ui_ldqs_dec                   (1'b0),
    .uo_data                       (),
    .uo_data_valid                 (),
    .uo_done_cal                   ($uo_done_cal),
    .uo_cmd_ready_in               (),
    .uo_refrsh_flag                (),
    .uo_cal_start                  (),
    .uo_sdo                        (),

    .mcbx_dram_addr                ($mcbx_dram_addr),
    .mcbx_dram_ba                  ($mcbx_dram_ba),
    .mcbx_dram_ras_n               ($mcbx_dram_ras_n),
    .mcbx_dram_cas_n               ($mcbx_dram_cas_n),
    .mcbx_dram_we_n                ($mcbx_dram_we_n),
    .mcbx_dram_cke                 ($mcbx_dram_cke),
    .mcbx_dram_clk                 ($mcbx_dram_clk),
    .mcbx_dram_clk_n               ($mcbx_dram_clk_n),
    .mcbx_dram_dq                  ($mcbx_dram_dq),
    .mcbx_dram_dqs                 ($mcbx_dram_dqs),
    .mcbx_dram_dqs_n               ($mcbx_dram_dqs_n),
    .mcbx_dram_udqs                ($mcbx_dram_udqs),
    .mcbx_dram_udqs_n              ($mcbx_dram_udqs_n),
    .mcbx_dram_udm                 ($mcbx_dram_udm),
    .mcbx_dram_ldm                 ($mcbx_dram_ldm),
    .mcbx_dram_odt                 ($mcbx_dram_odt),
    .mcbx_dram_ddr3_rst            ($mcbx_dram_ddr3_rst),
    .rzq                           ($mcbx_rzq),
    .zio                           ($mcbx_zio),

    .calib_recal                   (1'b0),

    .status                        ($status),
    .selfrefresh_enter             ($selfrefresh_enter),
    .selfrefresh_mode              ($selfrefresh_mode)
);
'''

def main():
    from myhdl import toVerilog

    if 0:
        clkout0 = Signal(False)
        toVerilog(pll_adv, 'pll_adv_inst', clkout0 = clkout0)
        print
        print open('pll_adv.v', 'r').read()

    if 1:
        mcbx_dram_addr = Signal(intbv(0)[12:])
        mcbx_dram_ba = Signal(intbv(0)[2:])
        mcbx_dram_ras_n = Signal(False)
        mcbx_dram_cas_n = Signal(False)
        mcbx_dram_we_n = Signal(False)
        mcbx_dram_cke = Signal(False)
        mcbx_dram_clk = Signal(False)
        mcbx_dram_clk_n = Signal(False)
        mcbx_dram_dq = Signal(intbv(0)[16:])
        mcbx_dram_dqs = Signal(False)
        mcbx_dram_dqs_n = Signal(False)
        mcbx_dram_udqs = Signal(False)
        mcbx_dram_udqs_n = Signal(False)
        mcbx_dram_udm = Signal(False)
        mcbx_dram_ldm = Signal(False)
        mcbx_dram_odt = Signal(False)
        mcbx_dram_ddr3_rst = Signal(False)

        mcbx_rzq = Signal(False)
        mcbx_zio = Signal(False)

        sys_rst = Signal(False)

        sysclk_2x = Signal(False)
        sysclk_2x_180 = Signal(False)

        pll_ce_0 = Signal(False)
        pll_ce_90 = Signal(False)
        pll_lock = Signal(False)

        ui_clk = Signal(False)

        toVerilog(mcb_ui_top,
                  'mcb_ui_inst',

                  mcbx_dram_clk,
                  mcbx_dram_clk_n,
                  mcbx_dram_cke,

                  mcbx_dram_ras_n,
                  mcbx_dram_cas_n,
                  mcbx_dram_we_n,

                  mcbx_dram_ba,
                  mcbx_dram_addr,

                  mcbx_dram_dqs,
                  mcbx_dram_dqs_n,
                  mcbx_dram_udqs,
                  mcbx_dram_udqs_n,
                  mcbx_dram_udm,
                  mcbx_dram_ldm,

                  mcbx_dram_dq,

                  mcbx_dram_odt,
                  mcbx_dram_ddr3_rst,
                  mcbx_rzq,
                  mcbx_zio,

                  sys_rst,

                  ui_clk,

                  sysclk_2x,
                  sysclk_2x_180,

                  pll_ce_0,
                  pll_ce_90,
                  pll_lock,
                  )

        print
        print open('mcb_ui_top.v', 'r').read()

if __name__ == '__main__':
    main()
