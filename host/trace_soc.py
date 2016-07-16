#! /usr/bin/python

"""Application that gets a trace from the SOC bus and converts it to a
"soc.vcd" file which can be visualised by gtkwave.  """

import sds
import numpy
import sys
import time
import os
import string

from sds import SDS

name_sdr = (
    'CS',  'RAS', 'CAS', 'WE',
    'BA[0]', 'BA[1]',
    'A[0]',  'A[1]',  'A[2]',  'A[3]',
    'A[4]',  'A[5]', 'A[6]',  'A[7]',
    'A[8]',  'A[9]',  'A[10]', 'A[11]',
    )

name_ddr = ('DQS[0]', 'DQS[1]',
            'DM[0]',  'DM[1]',
            'DQ[0]',  'DQ[1]',  'DQ[2]',  'DQ[3]',
            'DQ[4]',  'DQ[5]',  'DQ[6]',  'DQ[7]',
            'DQ[8]',  'DQ[9]',  'DQ[10]', 'DQ[11]',
            'DQ[12]', 'DQ[13]', 'DQ[14]', 'DQ[15]',
            )

print len(name_sdr)
print len(name_ddr)

sym_sdr = string.lowercase
sym_ddr = string.digits + string.punctuation

def out(f, v, n, sym):
    for i in range(n):
        f.write('%u%s\n' % ((v >> i) & 1, sym[i]))

def main():
    sds = SDS(sys.argv[1])

    sdr, ddr = sds.trace_soc(2048)

    f = open('soc.vcd', 'w')

    f.write('$date November 11, 2009 $end\n')
    f.write('$version blah $end\n')
    f.write('$timescale 1ns $end\n')
    f.write('$scope module logic $end\n')
    for i in range(len(name_sdr)):
        f.write('$var wire 1 %s %s $end\n' % (sym_sdr[i], name_sdr[i]))
    for i in range(len(name_ddr)):
        f.write('$var wire 1 %s %s $end\n' % (sym_ddr[i], name_ddr[i]))
    f.write('$upscope $end\n')
    f.write('$enddefinitions $end\n')
    f.write('$dumpvars\n')

    print 'sdr', sdr
    print 'ddr', ddr

    last_sdr = 0
    last_ddr = 0
    for i in range(len(ddr)):
        v_sdr = sdr[i]
        v_ddr = ddr[i]
        if last_sdr != v_sdr or last_ddr != v_ddr:
            f.write('#%u\n' % i)
            out(f, v_sdr, len(name_sdr), sym_sdr)
            out(f, v_ddr, len(name_ddr), sym_ddr)
            last_sdr = v_sdr
            last_ddr = v_ddr

    f.write('$dumpoff\n')
    f.write('$end\n')
    f.close()

if __name__ == '__main__':
    if not sys.argv[0]:
        sys.argv = [ '', 'sds' ]

    main()
