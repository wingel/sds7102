#! /usr/bin/python
from myhdl import (Signal, ResetSignal,
                   instance, delay, always, always_comb,
                   instances)
from timebase import nsec

def rstgen(rst, t, clk = None):
    """Reset generator

    The reset is asserted immediately.  If clk is not None the reset
    will be deasserted on the positive edge of clk.  Value is the
    asserted value for the reset signal and defaults to True.
    """

    internal_rst = Signal(False)

    @instance
    def rst_inst():
        internal_rst.next = 1
        yield delay(t)
        internal_rst.next = 0

    if clk is None:
        if isinstance(rst, ResetSignal):
            active = rst.active
        else:
            active = 1

        @always_comb
        def rst_comb():
            if internal_rst:
                rst.next = active
            else:
                rst.next = not active

    else:
        sync_inst = rst_sync(clk, internal_rst, rst)

    return instances()

def rst_sync(clk, rst_in, rst_out, n = 2):
    taps = [ Signal(False) for _ in range(n) ]

    @always(clk.posedge, rst_in.posedge)
    def rst_seq():
        if rst_in:
            for i in range(0, len(taps)):
                taps[i].next = 0
        else:
            for i in range(1, len(taps)):
                taps[i].next = taps[i-1]
            taps[0].next = 1

    if isinstance(rst_out, ResetSignal):
        active = rst_out.active
    else:
        active = 1

    @always_comb
    def rst_comb():
        if taps[len(taps)-1]:
            rst_out.next = not active
        else:
            rst_out.next = active

    return instances()
