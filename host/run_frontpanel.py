#! /usr/bin/python

import sds
import numpy
import sys
import time
import os
import string

from sds import SDS
from vcd import VCDOutput

def main():
    sds = SDS(sys.argv[1])

    if 0:
        sds.set_red_led(0)
        sds.set_green_led(0)
        sds.set_white_led(0)

        sds.set_red_led(1)
        time.sleep(0.3)
        sds.set_red_led(0)

        sds.set_green_led(1)
        time.sleep(0.3)
        sds.set_green_led(0)

        sds.set_white_led(1)
        time.sleep(0.3)
        sds.set_white_led(0)

    if 1:
        names = [ 'd[%u]' % i for i in range(64) ]

        if 1:
            names[39] = 'F1'
            names[36] = 'F2'
            names[47] = 'F3'
            names[55] = 'F4'
            names[31] = 'F5'

            names[29] = 'H1'
            names[61] = 'H2'
            names[53] = 'H3'
            names[45] = 'H4'
            names[37] = 'H5'

            names[26] = 'Copy'
            names[48] = 'RunStop'
            names[32] = 'Single'

            names[51] = 'Measure'
            names[50] = 'Acquire'
            names[49] = 'Autoset'
            names[35] = 'Utility'
            names[34] = 'Cursor'
            names[33] = 'Autoscale'
            names[43] = 'Save'
            names[42] = 'Display'
            names[41] = 'Help'

            names[59] = 'Ch1Menu'
            names[58] = 'Ch2Menu'
            names[57] = 'HorizMenu'
            names[25] = 'MathMenu'

            names[40] = 'TrigMenu'
            names[24] = 'Trig50'
            names[56] = 'TrigForce'

            names[13] = 'Multi_0'
            names[ 5] = 'Multi_1'
            names[21] = 'Multi_p'

            names[11] = 'Vert1_0'
            names[ 3] = 'Vert1_1'
            names[19] = 'Vert1_p'

            names[10] = 'Vert2_0'
            names[ 2] = 'Vert2_1'
            names[18] = 'Vert2_p'

            names[ 9] = 'Horiz_0'
            names[ 1] = 'Horiz_1'
            names[17] = 'Horiz_p'

            names[ 8] = 'Trig_0'
            names[ 0] = 'Trig_1'
            names[16] = 'Trig_p'

            names[15] = 'Volts1_0'
            names[ 7] = 'Volts1_1'
            names[23] = 'Volts1_p'

            names[12] = 'Volts2_0'
            names[ 4] = 'Volts2_1'
            names[20] = 'Volts2_p'

            names[14] = 'Sec_0'
            names[ 6] = 'Sec_1'
            names[22] = 'Sec_p'

            names[63] = 'MenuOff'

        if 1:
            sds.fp_init()
            time.sleep(0.1)

        with open('frontpanel.vcd', 'w') as f:
            vcd = VCDOutput(f)
            vcd.write_header(names)
            t = 0
            last_ts = 0
            last = 0

            while 1:
                v = sds.read_soc_reg(0x110)

                ts = (v >> 16) & 0xffff
                active = (v >> 9) & 1
                pressed = (v >> 8) & 1
                key = v & 0xff

                t += (ts - last_ts) & 0xffff
                last_ts = ts

                if key >= len(names):
                    print "invalid key", key
                    continue

                vcd.write_timestamp(t)
                if active:
                    print "0x%08x" % v, names[key]
                    vcd.write_value(names[key], pressed)
                    vcd.f.flush()

                else:
                    if not sys.argv[0]:
                        break

                    time.sleep(0.1)


        if 0:
            sds.fp_init()

if __name__ == '__main__':
    if not sys.argv[0]:
        sys.argv = [ '', 'sds' ]

    main()

