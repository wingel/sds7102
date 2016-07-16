#! /usr/bin/python
import sds
import numpy
import sys
import time
import os

from sds import SDS
from convert import convert, save, display

def main():
    sds = SDS(sys.argv[1])

    data = sds.capture(1024)
    numpy.savetxt('data.txt', data, fmt = '%u', delimiter = ' ')
    samples = convert(data)

    if 'DISPLAY' in os.environ:
        display(samples)
    else:
        save('plot.png', samples)

if __name__ == '__main__':
    if not sys.argv[0]:
        sys.argv = [ '', 'sds' ]

    main()
