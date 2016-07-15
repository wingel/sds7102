#! /usr/bin/python
from myhdl import toVerilog, traceSignals

# Multiplier for all time scales
timescale = '100ps'

nsec = 10
usec = 1000 * nsec
msec = 1000 * usec
sec = 1000 * msec

toVerilog.timescale = timescale + '/10ps'
traceSignals.timescale = timescale
