#! /usr/bin/python
import string

class VCDOutput(object):
    def __init__(self, f, names):
        self.f = f

        symbols = (string.lowercase + string.uppercase +
                   string.digits + string.punctuation)

        self.symbols = {}
        for i, name in enumerate(names):
            self.symbols[name] = symbols[i]

        self.write_header(names)

    def write_header(self, names):
        self.f.write('$date November 11, 2009 $end\n')
        self.f.write('$version blah $end\n')
        self.f.write('$timescale 1ns $end\n')
        self.f.write('$scope module logic $end\n')
        for name in names:
            self.f.write('$var wire 1 %s %s $end\n' % (
                self.symbols[name], name))
        self.f.write('$upscope $end\n')
        self.f.write('$enddefinitions $end\n')
        self.f.write('$dumpvars\n')

    def write_timestamp(self, t):
        self.f.write('#%u\n' % t)

    def write_bit(self, name, value):
        self.f.write('%u%s\n' % (value, self.symbols[name]))
