#! /usr/bin/python
if __name__ == '__main__':
    import hacking
    hacking.reexec('test_hybrid_counter.py')

from myhdl import Signal, intbv, always_comb, always_seq

from common.gray import gray_decoder, gray_counter

from wb import WbSlave

class HybridCounter(WbSlave):
    """A hybrid asynchronous/synchronous counter which can count
    higher frequencies than sysclk on a number of pins.

    An asynchronous gray counter which counts the number of positive
    edges on a set of pins.  Each counter is split into an
    asynchronous part that can run faster than sysclk and a
    synchronous part that is updated periodically.

    The purpose of this counter is to save on the number of ripple
    carry resources used in an FPGA and to let the asynchronous
    counters run faster than they could have done otherwise.  It's
    only possible to fit about 80 asynchronous 32 bit counters into a
    Xilinx XC6SLX9 FPGA before the it runs out of space.  With the
    hybrid approach where only the lower 12 bits are updated
    asynchronously should be able to fit two or three times as many
    counters into the same FPGA.

    An asynchronous gray counter increments the lower async_width of
    the counter on every positive edge of the pin.

    A task which is synchronous with sysclk will sample the
    asynchronous counter, convert it from gray to binary and use it to
    update bothe the lowest aync_width of the synchronous counter and
    increment the high bits of the synchronous counter if the
    asynchronous counter has wrapped around.

    The task loops through and updates the counter for one pin each
    tick of sysclk.  To calculate the number of edges the asynchronous
    counters must be able to count so to not overflow, use the
    following forumla:

        Maximum counter value = Fasync / Fsysclk * len(pins) + 1

    For example, if your sysclk is 50MHz, you want to frequencies up
    to 250MHz on 200 pins the counter must be able to count up to
    1001.  Use a 10 bit counter and you should be on the safe side.
    """

    def __init__(self, addr_depth = None, data_width = 32, async_width = 10):
        super(HybridCounter, self).__init__(
            addr_depth = addr_depth, data_width = data_width)
        self.async_width = async_width

    def check_args(self, pins):
        if self.addr_depth is None:
            self.addr_depth = len(pins)

    def gen(self, bus, pins):
        async_width = self.async_width
        data_width = self.data_width

        assert data_width >= async_width

        pin_array = [ Signal(False) for _ in range(len(pins)) ]

        ctrs = [ Signal(intbv(0)[self.data_width-1:]) for _ in range(len(pin_array)) ]

        idle_idx = Signal(intbv(0, 0, len(pin_array)))
        act_idx = Signal(intbv(0, 0, len(pin_array)))

        gray_ctrs = [ Signal(intbv(0)[self.async_width:]) for _ in range(len(pin_array)) ]
        gray_insts = []
        for i in range(len(pin_array)):
            gray_insts.append(gray_counter(pin_array[i], gray_ctrs[i]))

        act_encoded = Signal(intbv(0)[self.async_width:])
        act_decoded = Signal(intbv(0)[self.async_width:])
        decoder_inst = gray_decoder(act_encoded, act_decoded)

        act_ctr = Signal(intbv(0)[self.data_width-1:])
        act_state = Signal(False)

        processing = Signal(False)
        internal_rd_ack = Signal(False)

        @always_comb
        def comb():
            for i in range(len(pins)):
                pin_array[i].next = pins[i]

        @always_seq (bus.CLK_I.posedge, bus.RST_I)
        def seq():
            bus.ACK_O.next = 0
            bus.ERR_O.next = 0
            bus.RTY_O.next = 0

            # Handle data that was retrieved last time
            ctr = (act_ctr[:async_width] << async_width) | act_decoded
            if act_ctr[async_width:] > act_decoded:
                ctr = (ctr + (1<<async_width)) & ((1<<(data_width-1))-1)
            ctrs[act_idx].next = ctr

            bus.DAT_O.next[data_width-1] = act_state
            bus.DAT_O.next[data_width-1:] = ctr

            if processing:
                bus.ACK_O.next = 1
                processing.next = 0

            next_idx = idle_idx

            if (not processing and bus.CYC_I and bus.STB_I and
                not bus.ACK_O and not bus.ERR_O and not bus.RTY_O):
                # New request

                if not bus.WE_I and bus.ADR_I < len(pin_array):
                    # Valid request

                    if bus.ADR_I == act_idx:
                        # Already at the right index, return data immedately
                        bus.ACK_O.next = 1

                    else:
                        # Otherwise schedule a read for the next cycle
                        processing.next = 1
                        next_idx = bus.ADR_I

                else:
                    # Out of range or a write, return an error
                    bus.ERR_O.next = 1

            if idle_idx == next_idx:
                idle_idx.next = 0
                if idle_idx != len(pin_array) - 1:
                    idle_idx.next = idle_idx + 1

            act_idx.next = next_idx
            act_encoded.next = gray_ctrs[next_idx]
            act_ctr.next = ctrs[next_idx]
            act_state.next = pin_array[next_idx]

        return comb, seq, gray_insts, decoder_inst
