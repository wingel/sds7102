#! /usr/bin/python

import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_util.py')

from myhdl import ConcatSignal, SignalType, always_comb

def rename_interface(self, prefix):
    for k, v in vars(self).items():
        if isinstance(v, SignalType):
            if prefix is None:
                v._name = k
            else:
                v._name = prefix + '_' + k

def tristate(pin, i, o, oe):
    driver = pin.driver()

    @always_comb
    def logic():
        i.next = pin
        if oe:
            driver.next = o
        else:
            driver.next = None

    return logic

def mask(signal):
    return (1<<len(signal)) - 1

def lsh(signal):
    for i in range(len(signal)-1):
        signal[i+1].next = signal[i]
    signal[0].next = 0

class Packer(object):
    def __init__(self, constructor, *args, **kwargs):
        self._constructor = constructor
        self._args = args
        self._kwargs = kwargs

        self._width = 0
        self._items = []

        obj = self.create()

        for k, v in vars(obj).items():
            if isinstance(v, SignalType):
                width = len(v)
                self._items.append((k, self._width, width))
                self._width += width

        print self._constructor.__name__, self._items

    def __len__(self):
        return self._width

    def create(self):
        return self._constructor(*self._args, **self._kwargs)

    def pack(self, obj):
        signals = []
        for k, lo, hi in self._items:
            signals.append(getattr(obj, k))
        return ConcatSignal(*reversed(signals))

    # This does not work, MyHDL gets confused
    def unpack_to_obj(self, packed):
        assert isinstance(packed, SignalType)
        assert len(packed) == self._width

        obj = self.create()

        for k, offset, width in self._items:
            setattr(obj, k, packed[offset+width:offset])

        return obj

    # So do it this way instead
    def unpack(self, packed, unpacked):
        assert isinstance(packed, SignalType)
        assert isinstance(unpacked, self._constructor)

        insts = [ ]
        # reversed isn't needed here, it's just to make the verilog
        # code order match the ConcatSignal order above
        for k, offset, width in reversed(self._items):
            signal = getattr(unpacked, k)
            lo = offset
            hi = offset + width
            # MyHDL gets confused if the function is inline
            if 1:
                inst = self.extractor(signal, packed, lo, hi)
            else:
                @always_comb
                def inst():
                    signal.next = packed[hi:lo]
            insts.append(inst)

        return insts

    @staticmethod
    def extractor(signal, packed, lo, hi):
        @always_comb
        def inst():
            signal.next = packed[hi:lo]
        return inst

