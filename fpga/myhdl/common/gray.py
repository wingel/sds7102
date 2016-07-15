#! /usr/bin/python
import hacking
if __name__ == '__main__':
    hacking.reexec_if_needed('gray.py')

from myhdl import Signal, intbv, always, always_comb

def gray_encoder(bin_value, gray_value):
    assert len(bin_value) == len(gray_value)
    @always_comb
    def comb():
        gray_value.next = bin_value ^ (bin_value >> 1)
    return comb

def gray_decoder(gray_value, bin_value):
    assert len(gray_value) == len(bin_value)
    @always_comb
    def comb():
        t = 0
        for i in range(len(bin_value)):
            n = len(bin_value) - i - 1
            t ^= gray_value[n]
            bin_value.next[n] = t
    return comb

def gray_counter(clk, gray_value):
    cur_gray = Signal(intbv(0)[len(gray_value):0])
    cur_bin = Signal(intbv(0)[len(gray_value):0])

    next_bin = Signal(intbv(0)[len(gray_value):0])
    next_gray = Signal(intbv(0)[len(gray_value):0])

    decoder = gray_decoder(cur_gray, cur_bin)
    encoder = gray_encoder(next_bin, next_gray)

    @always_comb
    def comb():
        next_bin.next = cur_bin + 1
        gray_value.next = cur_gray

    @always (clk.posedge)
    def seq():
        cur_gray.next = next_gray

    return seq, comb, decoder, encoder

def test():
    from myhdl import Simulation, intbv, delay, bin, instance

    bits = 4
    bin_value = Signal(intbv(0)[bits:0])
    gray_value = Signal(intbv(0)[bits:0])
    bin_value_2 = Signal(intbv(0)[bits:0])

    gray_encoder_instance = gray_encoder(bin_value, gray_value)
    gray_decoder_instance = gray_decoder(gray_value, bin_value_2)

    @instance
    def logic():
        for i in range(1<<bits):
            bin_value.next = i
            yield delay(1)
            print bin(bin_value, bits), bin(gray_value, bits), bin(bin_value_2, bits)
            assert bin_value == bin_value_2

    print
    sim = Simulation(gray_encoder_instance, gray_decoder_instance, logic)
    sim.run(17)

def emit():
    from myhdl import toVerilog, intbv

    bits = 10

    bin_value = Signal(intbv(0)[bits:0])
    gray_value = Signal(intbv(0)[bits:0])
    bin_value_2 = Signal(intbv(0)[bits:0])

    toVerilog(gray_encoder, bin_value, gray_value)
    toVerilog(gray_decoder, gray_value, bin_value)

    pin = Signal(False)

    toVerilog(gray_counter, pin, gray_value)

    print
    print open('gray_encoder.v', 'r').read()
    print open('gray_decoder.v', 'r').read()
    print open('gray_counter.v', 'r').read()

if __name__ == '__main__':
    test()
    emit()
