#! /usr/bin/python
from myhdl import Signal, instance, delay
from timebase import sec

def rstgen(rst, t, clk = None, value = True):
    """Reset generator

    The reset is asserted immediately.  If clk is not None the reset
    will be deasserted on the positive edge of clk.  Value is the
    asserted value for the reset signal and defaults to True.
    """

    @instance
    def inst():
        rst.next = value
        yield delay(t)
        if clk:
            yield clk.posedge
        rst.next = not value

    return inst
