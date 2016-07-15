#! /usr/bin/python
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

if use_xilinx:
    bufg.verilog_code = r'''
BUFG $name (
    .I  ($i),
    .O  ($o)
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
        o.driven = True

    if isinstance(t, SignalType):
        assert len(t) == len(io)
        t.read = True
    else:
        t = intbv(~0)[len(io):]

    io.read = True
    io.driven = True

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
        o.driven = True

    if isinstance(oe, SignalType):
        assert len(oe) == 1
        oe.read = True
    else:
        oe = 0

    io.read = True
    io.driven = True

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

def iddr2(name, d, q0, q1, c0, c1, ce = _one, r = _zero, s = _zero,
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

iddr2.verilog_code = r'''
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

def iddr2_se(name, d, q0, q1, c0, ce = _one, r = _zero, s = _zero,
             ddr_alignment = 'NONE',
             init_q0 = _zero, init_q1 = _zero,
             srtype = 'SYNC'):
    d.read = True
    c0.read = True

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

iddr2_se.verilog_code = r'''
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
            .C1 (~$c0),
            .CE ($ce),
            .R  ($r),
            .S  ($s)
        );
    end
endgenerate
'''.strip()

def oddr2(name, d0, d1, q, c0, c1, ce = _one, r = _zero, s = _zero,
              ddr_alignment = 'NONE', init = 0, srtype = 'SYNC'):
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
        q.next = d0

    return comb

oddr2.verilog_code = r'''
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

def oddr2_se(name, d0, d1, q, c0, ce = _one, r = _zero, s = _zero,
             ddr_alignment = 'NONE', init = 0, srtype = 'SYNC'):
    d0.read = True
    d1.read = True
    c0.read = True

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
        q.next = d0

    return comb

oddr2_se.verilog_code = r'''
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
            .C1 (~$c0),
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

    dataout.driven = True
    dout.driven = True
    tout.driven = True

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

def iobuf_delay_ddr2_se(name, i0, i1, o0, o1, oe0, oe1, io, c,
                        ddr_alignment = 'NONE',
                        srtype = 'SYNC',
                        odelay_value = 0):
    i = Signal(intbv(0)[len(io):])
    o = Signal(intbv(0)[len(io):])
    t = Signal(intbv(0)[len(io):])

    insts = []

    iobuf_inst = iobuf(name + '_iobuf', i, o, t, io)
    insts.append(iobuf_inst)

    i2 = Signal(intbv(0)[len(io):])
    o2 = Signal(intbv(0)[len(io):])
    t2 = Signal(intbv(0)[len(io):])

    iodelay_inst = iodelay2_se(name + '_iodelay',
                               dout = i, odatain = i2,
                               dataout = o2, idatain = o,
                               t = t2, tout = t,
                               ioclk = c,

                               data_rate = 'DDR',
                               idelay_value = 0,
                               idelay_type = 'FIXED',
                               odelay_value = odelay_value,
                               delay_src = 'IO',
                               )
    insts.append(iodelay_inst)

    iddr2_inst = iddr2_se(name + '_iddr2', o2, i0, i1, c,
                          ddr_alignment = ddr_alignment,
                          srtype = srtype)
    insts.append(iddr2_inst)

    oddr2_inst = oddr2_se(name + '_oddr2', o0, o1, i2, c,
                          ddr_alignment = ddr_alignment,
                          srtype = srtype)
    insts.append(oddr2_inst)

    t0 = Signal(intbv(0)[len(io):])
    t1 = Signal(intbv(0)[len(io):])

    tddr2_inst = oddr2_se(name + '_tddr2', t0, t1, t2, c,
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
