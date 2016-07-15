#! /usr/bin/python

class System(object):
    def __init__(self, clk, rst = None):
        self.CLK = clk
        self.RST = rst

