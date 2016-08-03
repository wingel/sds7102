#! /usr/bin/python
import string

class VCDOutput(object):
    ALPHABET = (string.lowercase + string.uppercase +
               string.digits + string.punctuation)

    def __init__(self, f):
        self.f = f

    def write_header(self, names, widths = {}):
        self.widths = widths
        self.symbols = {}
        for i, name in enumerate(names):
            self.symbols[name] = self.ALPHABET[i]

        self.f.write('$date November 11, 2009 $end\n')
        self.f.write('$version blah $end\n')
        self.f.write('$timescale 1ns $end\n')
        self.f.write('$scope module logic $end\n')
        for name in names:
            self.f.write('$var wire %u %s %s $end\n' % (
                widths.get(name, 1), self.symbols[name], name))
        self.f.write('$upscope $end\n')
        self.f.write('$enddefinitions $end\n')
        self.f.write('$dumpvars\n')

    def write_timestamp(self, t):
        self.f.write('#%u\n' % t)

    def write_value(self, name, value):
        width = self.widths.get(name, 1)
        if width != 1:
            self.f.write('b%s %s\n' % (format(value, "08b"), self.symbols[name]))
        else:
            self.f.write('%u%s\n' % (value, self.symbols[name]))
