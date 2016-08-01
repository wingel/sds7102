#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('test_ram.py')

from myhdl import Signal, intbv, always_comb

class SimpleBus(object):
    """Simple bus.

    A simple bus port.  A master presents the ADDR and WR, WR_DATA and
    RD on the first positive edge of the clock.  On a read the slave
    must output RD_DATA with enough setup time to be sampled on the
    second edge.  Since there can be no wait states, there is no ACK
    nor WAIT signal.

    The clock and reset is provided separately from the rest of the
    bus since a device, such as a dual port RAM, can have multiple
    port.  Use the system.System class for providing clock and reset.

    A slave must drive zeroes on RD_DATA when it is not selected.
    This simplifies the address decoder/mux since it can just use an
    OR of all the slave RD_DATAs to combine all the buses.

    A write cycle:
                        1   2
                 _   _  |_  |_   _
        CLK     / \_/ \_/ \_/ \_/ \_
                     ___|   |
        ADDR    XXXX<___>XXXXXXXXXXX
                     ___|   |
        WR      ____/   \___________
                     ___|   |
        WR_DATA XXXX<___>XXXXXXXXXXX
                        |   |
        RD      ____________________
                        |   |
        RD_DATA ____________________

    A read cycle:
                        1   2
                 _   _  |_  |_   _
        CLK     / \_/ \_/ \_/ \_/ \_
                     ___|   |
        ADDR    XXXX<___>XXXXXXXXXXX
                        |   |
        WR      ____________________
                        |   |
        WR_DATA XXXXXXXXXXXXXXXXXXXX
                     ___|   |
        RD      ____/   \___________
                        |___|
        RD_DATA ________/___\_______

    I could have reused the wishbone signals but there are multiple
    reasons why I didn't.

    If prefer RD and WR rather than STB and WE just because I think
    it's easier to read.  It also makes it theoretically possible to
    perform both a read and a write at the same time, but that's maybe
    something that shouldn't be used.

    Also I don't like the _I and _O naming in wishbone, it gets really
    confusing when you have an interface as you can in MyHDL: "_I is
    an input excepth that it becomes an output in the master".

    RD_DATA and WR_DATA is unambigous, RD_DATA is associated with an
    RD operation, WR_DATA is associated with a WR operation."""

    def __init__(self, addr_depth, data_width, align = None):
        self.addr_depth = addr_depth
        self.data_width = data_width
        self.align = align

        addr_width = len(intbv(0, 0, addr_depth))

        self.ADDR = Signal(intbv(0)[addr_width:])

        self.WR = Signal(False)
        self.WR_DATA = Signal(intbv(0)[data_width:])

        self.RD = Signal(False)
        self.RD_DATA = Signal(intbv(0)[data_width:])

    def connect(self, other):
        @always_comb
        def comb():
            self.ADDR.next = other.ADDR
            self.WR.next = other.WR.next
            self.WR_DATA.next = other.WR_DATA
            self.RD.next = other.RD
            other.RD_DATA.next = self.RD_DATA
        return comb
