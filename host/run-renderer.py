#! /usr/bin/python
import sds
import numpy
import sys
import time
import os

from scipy.misc import toimage

from sds import SDS, hd

def main():
    sds = SDS(sys.argv[1])

    assert sds.read_soc_reg(0x240) & 2

    screen = []

    width = 400


    # This takes about 220 ms to render, the FPGA starts to limit
    start = 30 * 512; scale = 16384

    # This takes about 190 ms to render and is not limited by the FPGA
    start = 30 * 512; scale = 8000

    start = 115 * 512; scale = 16
    start = 100 * 512; scale = 64
    start = 30 * 512; scale = 550

    start = 30 * 512; scale = 2000

    # 16384 is maximum scale.  why?  16384 * 400 * 4 -> ~26MByte that's not it

    # sds.do_mig_capture()

    if 1:
        data = sds.render(start, width, scale)

        hd(data[:64])

    else:
        data = []
        for x in range(width):
            print x

            for i in range(4):
                sds.write_soc_regs(0x400 + i * 0x100, [ 0 ] * 256)

            sds.read_soc_reg(0x240)

            src_addr = start + x * scale
            count = scale

            sds.write_soc_reg(0x130, src_addr)
            sds.write_soc_reg(0x131, count)

            for d in range(1000):
                if sds.read_soc_reg(0x240) & 2:
                    break
            else:
                raise os.TimeoutError()

            data.append(sds.read_soc_regs(0x400, 0x100))

    data = numpy.array(data).reshape((width, 0x100))

    z = numpy.zeros(256, dtype = numpy.uint8)

    for aa in data:
        aa = [ aa & 0xffff, (aa >> 16) & 0xffff ]

        for i in range(len(aa)):
            a = aa[i][::-1]
            min_val = 64
            max_val = 500
            a = a * (max_val-min_val) / scale + a.clip(0, 1) * min_val
            a[0] = 0
            a[255] = 0
            a = a.clip(0, 255)
            aa[i] = a
            # print min(a), max(a)

        screen.append(numpy.dstack((aa[0], aa[1], z))[0])

    screen = numpy.array(screen, dtype = numpy.uint8).transpose()

    img = toimage(screen)
    img.show()
    img.save('screen.png')

if __name__ == '__main__':
    if not sys.argv[0]:
        sys.argv = [ '', 'sds' ]

    main()
