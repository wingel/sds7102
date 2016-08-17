#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('spi_slave.py')

from myhdl import Signal, intbv, always_seq, always_comb

from wb import WbSlave

# CPHA=1 is needed for bidirectional communications to work properly.
# The host writes the address and then has to turn off its sdio driver
# before the device can be allowed to turn on its sdio driver.  To
# indicate to the driver that it can turn on its driver it needs to
# see a an initial clock edge, the host then latches the data on the
# second edge.
#
# Actually that's not true, I could use CPHA=0 and just turn off the
# drivers just before the falling trailing edge of the last bit.  Oh
# well, lets go with CPHA=1 right now.

class SpiInterface(object):
    def __init__(self):
        self.CS = Signal(False)
        self.SCK = Signal(False)
        self.SD_I = Signal(False)
        self.SD_O = Signal(False)
        self.SD_OE = Signal(False)

class SpiSlave(object):
    def __init__(self):
        self.addr_width = None
        self.data_width = None

    def gen(self, spi, slave):
        if self.addr_width is None:
            self.addr_width = len(slave.ADR_I)
            # one extra bit for the direction bit
            self.addr_width += 1
            # round up to a byte
            self.addr_width = (self.addr_width + 7) & ~7

        if self.data_width is None:
            self.data_width = max(len(slave.DAT_I), len(slave.DAT_O))
            # round up to a byte
            self.data_width = (self.data_width + 7) & ~7

        width = max(self.addr_width, self.data_width)

        print "SpiSlave", self.addr_width, self.data_width, width

        addr = Signal(intbv(0)[len(slave.ADR_I):])

        bit = Signal(intbv(0, 0, width))
        data = Signal(intbv(0)[width:])

        rd = Signal(False)
        wr = Signal(False)

        addr_mode = Signal(False)
        r_w = Signal(False)

        last_sck = Signal(False)

        oe = Signal(False)

        @always_comb
        def comb():
            slave.CYC_I.next = 0
            slave.STB_I.next = 0
            slave.WE_I.next = 0
            slave.ADR_I.next = 0
            slave.DAT_I.next = 0
            slave.SEL_I.next = intbv(~0)[len(slave.SEL_I):]

            if rd or wr:
                slave.CYC_I.next = 1
                slave.STB_I.next = 1
                slave.ADR_I.next = addr

                if wr:
                    slave.WE_I.next = 1
                    slave.DAT_I.next = data

            spi.SD_OE.next = oe and spi.CS


        @always_seq(slave.CLK_I.posedge, slave.RST_I)
        def shifter():
            if slave.ACK_O or slave.ERR_O:
                if rd:
                    data.next = slave.DAT_O
                addr.next = addr + 1

                rd.next = 0
                wr.next = 0

            elif slave.RTY_O:
                # Leave rd/wr as is and retry
                pass

            if not spi.CS:
                addr_mode.next = 1
                r_w.next = 0
                bit.next = 0
                oe.next = 0

            else:
                if spi.SCK and not last_sck:
                    if r_w:
                        spi.SD_O.next = data[self.data_width - bit - 1]
                        oe.next = 1

                        if bit == self.data_width - 1:
                            bit.next = 0
                            rd.next = 1

                        else:
                            bit.next = bit + 1

                elif not spi.SCK and last_sck:
                    if addr_mode:
                        data.next[self.addr_width - bit - 1] = spi.SD_I

                        if bit == self.addr_width - 1:
                            bit.next = 0

                            addr_mode.next = 0
                            addr.next = data[len(addr):1]

                            if spi.SD_I:
                                rd.next = 1
                                r_w.next = 1
                                data.next = intbv(~0)[len(data):]
                            else:
                                r_w.next = 0

                        else:
                            bit.next = bit + 1

                    elif not r_w:
                        data.next[self.data_width - bit - 1] = spi.SD_I

                        if bit == self.data_width - 1:
                            bit.next = 0
                            wr.next = 1

                        else:
                            bit.next = bit + 1

            last_sck.next = spi.SCK

        return (comb, shifter)

if __name__ == '__main__':
    from test_spi_slave import sim, emit
    sim()
    emit()
