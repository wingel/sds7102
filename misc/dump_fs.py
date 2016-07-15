#! /usr/bin/python

"""A script that tries to understand the file system inside a dump of
the SDS7102 NAND flash.  It will write the files from the file
system to a directory called "fs"."""

from __future__ import print_function

import sys
import struct
import os

OUTPUT_DIR = 'fs'

FS_START = 0xa0000
PAGE_SIZE = 2048
EMPTY_PAGE = '\xff' * PAGE_SIZE

HEADER = '\x01\xff\xff\xff\x01\x00\x00\x00\xff\xff'

FN_START = 0xa
FN_END = FN_START + 0x100

SIZE_START = 0x124
SIZE_END = SIZE_START + 4

VERS_START = 0x1fc
VERS_END = VERS_START + 4

META_SIZE = 20
META_START = PAGE_SIZE - META_SIZE
META_EMPTY = '\0' * META_SIZE

def makedirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)

makedirs(OUTPUT_DIR)

numbers = dict()

fn = 'sds7102.bin'
if len(sys.argv) > 1:
    fn = sys.argv[1]

with open(fn, 'rb') as f:
    offset = FS_START
    f.seek(offset)

    data = f.read(PAGE_SIZE)
    while data:
        if data == EMPTY_PAGE:
            offset += PAGE_SIZE
            data = f.read(PAGE_SIZE)
            continue

        print("%08x" % (offset))

        if not data.startswith(HEADER):
            print("%08x: unexpected data %s" % (offset, repr(data[:32])))
            offset += PAGE_SIZE
            data = f.read(PAGE_SIZE)
            continue

        fn = data[FN_START:FN_END].rstrip('\0')
        size, = struct.unpack('<L', data[SIZE_START:SIZE_END])
        hbar, = struct.unpack('<L', data[VERS_START:VERS_END])
        print("%08x: start %s %u 0x%x" % (
            offset, repr(fn), size, hbar))

        assert hbar in [ 0, 1 ]

        header = data

        offset += PAGE_SIZE

        content = ''

        while 1:
            data = f.read(PAGE_SIZE)
            if not data:
                break

            if data == EMPTY_PAGE:
                print("%08x: empty page" % offset)
                offset += PAGE_SIZE
                continue

            if data.startswith(HEADER):
                break

            content += data[:META_START]

            meta = data[META_START:]
            if meta != META_EMPTY:
                print("%08x: meta %s" % meta.encode('hex'))

            offset += PAGE_SIZE

        if size:
            print("%s: %u bytes %u" % (size, len(content), len(content) - size))
        else:
            tfn = data[FN_START:FN_END].rstrip('\0')
            size, = struct.unpack('<L', data[SIZE_START:SIZE_END])
            tbar, = struct.unpack('<L', data[VERS_START:VERS_END])

            print("%08x: end   %s %u 0x%x %u bytes %u" % (
                offset, repr(tfn), size, tbar,
                  len(content), len(content) - size))

            for i in range(len(header)):
                if header[i] != data[i]:
                    print("%04x %02x %02x" % (i, ord(header[i]), ord(data[i])))

            assert tbar == 0
            assert header[:SIZE_START] == data[:SIZE_START]
            assert header[SIZE_END:VERS_START] == data[SIZE_END:VERS_START]
            assert header[VERS_END:] == data[VERS_END:]

            offset += PAGE_SIZE

            data = f.read(PAGE_SIZE)

        if content[size:] == '\0' * (len(content) - size):
            content = content[:size]
        else:
            print("contents padded with nonzero data")

        path = os.path.join(OUTPUT_DIR, fn)
        try:
            num = numbers[fn]
            numbers[fn] = num + 1
            path += '.%u' % num
        except KeyError:
            numbers[fn] = 0

        with open(path, 'w+') as wf:
            wf.write(content)
