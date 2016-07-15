#! /usr/bin/python
from myhdl import SignalType, always_comb

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

