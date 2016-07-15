#! /usr/bin/python
from myhdl import Signal, SignalType, instance, delay
from timebase import sec

def clkgen(clk, freq):
    halfperiod = sec / float(freq) / 2

    # print "clk", freq, halfperiod

    @instance
    def inst():
        acc = 0

        while 1:
            acc += halfperiod
            d = int(acc)
            acc -= d
            yield delay(d)
            clk.next = not clk

    return inst

class Clk(SignalType):
    def __init__(self, freq, value = False):
        super(Clk, self).__init__(value)
        self.freq = freq

    def gen(self):
        clk_inst = clkgen(self, self.freq)
        return clk_inst
