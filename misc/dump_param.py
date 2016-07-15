#! /usr/bin/python

"""A script that parses the contents of the param file from the
SDS7102 file system."""

from __future__ import print_function

import struct
import os

data = open('fs/param.6', 'rb').read()

if 0:
    def crc32(data):
        s = 0
        for c in data:
            s ^= ord(c) << 8
            for i in range(8):
                s <<= 1
                if s & 0x10000:
                    s ^= 0x1021
            s &= 0xffffffff

        return s

else:
    def gen_crc32_table():
        poly = 0x1021
        table = [0] * 256
        for i in range(256):
            crc = (i << 8)
            for j in range(8):
                crc <<= 1
                if crc & 0x10000:
                    crc ^= poly
                crc &= 0xffffffff
            table[i] = crc
        return table

    crc32_table = gen_crc32_table()

    def crc32(data):
        s = 0
        for c in data:
            s = ((s << 8) & 0xff00ff00) ^ crc32_table[((s >> 8) ^ ord(c)) & 0xff]

        return s

assert len(data) == 0x1cc

checksum, = struct.unpack('<L', data[0x1c8:0x1cc])
s = crc32(data[:0x1c4])
assert s == checksum

def process(offset, flag, addr, size, checksum, name):
    print("0x%04x 0x%08x 0x%08x 0x%08x (%7d) 0x%08x %s" % (
        (offset, flag, addr, size, size, checksum, name)))

    if 1 or name in [ 'tx' ]:
        data = open(os.path.join('fs', name), 'rb').read()
        s = crc32(data)
        assert s == checksum

v = ( 0x124, 'os' ),
offset = 0x124
name = 'os'
flag, addr, entry, size, checksum = struct.unpack('<LLLLL',
                                                  data[offset:offset + 20])
process(offset, flag, addr, size, checksum, name)
print("extra value %08x" % entry)

for offset, name in [
    ( 0x144, 'hz' ),
    ( 0x154, 'tx' ),
    ( 0x170, 'me' ),
    ( 0x184, 'hlp' ),
    ( 0x198, 'fp' ),
    ( 0x1a8, 'bmp' ),
    ]:
    flag, addr, size, checksum = struct.unpack('<LLLL',
                                               data[offset:offset + 16])
    process(offset, flag, addr, size, checksum, name)
