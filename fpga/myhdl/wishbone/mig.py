#! /usr/bin/python
from myhdl import Signal, SignalType, instance, always_comb, intbv, always

def mig(sys_rst_i, sys_clk_p, sys_clk_n,
        calib_done, error,
        mcb3_dram_ck, mcb3_dram_ck_n,
        mcb3_dram_ras_n, mcb3_dram_cas_n, mcb3_dram_we_n,
        mcb3_dram_ba, mcb3_dram_a, mcb3_dram_odt,
        mcb3_dram_dqs, mcb3_dram_dqs_n, mcb3_dram_udqs, mcb3_dram_udqs_n, mcb3_dram_dm, mcb3_dram_udm,
        mcb3_dram_dq):

    sys_rst_i.read = True
    sys_clk_p.read = True
    sys_clk_n.read = True

    calib_done.driven = True
    error.driven = True

    mcb3_dram_ck.driven = True
    mcb3_dram_ck_n.driven = True

    mcb3_dram_ras_n.driven = True
    mcb3_dram_cas_n.driven = True
    mcb3_dram_we_n.driven = True

    mcb3_dram_ba.driven = True
    mcb3_dram_a.driven = True
    mcb3_dram_odt.driven = True

    mcb3_dram_dqs.read = True
    mcb3_dram_dqs.driven = True
    mcb3_dram_dqs_n.read = True
    mcb3_dram_dqs_n.driven = True

    mcb3_dram_udqs.read = True
    mcb3_dram_udqs.driven = True
    mcb3_dram_udqs_n.read = True
    mcb3_dram_udqs_n.driven = True

    mcb3_dram_dm.read = True
    mcb3_dram_dm.driven = True

    mcb3_dram_udm.read = True
    mcb3_dram_udm.driven = True

    mcb3_dram_dq.read = True
    mcb3_dram_dq.driven = True

    @always_comb
    def comb():
        error = None
        if sys_rst_i:
            calib_done.next = 0
        else:
            calib_done.next = 1

    return comb

mig.verilog_code = r'''
example_top #(
	.C3_CALIB_SOFT_IP("FALSE")
) mig_inst_internal (
         .c3_sys_rst_i                      ($sys_rst_i),

         .c3_sys_clk_p                      ($sys_clk_p),  // [input] differential p type clock from board
         .c3_sys_clk_n                      ($sys_clk_n),  // [input] differential n type clock from board

         .calib_done                     ($calib_done),
         .error                          ($error),

         .mcb3_dram_a                    ($mcb3_dram_a),
         .mcb3_dram_ba                   ($mcb3_dram_ba),
         .mcb3_dram_ras_n                ($mcb3_dram_ras_n),
         .mcb3_dram_cas_n                ($mcb3_dram_cas_n),
         .mcb3_dram_we_n                 ($mcb3_dram_we_n),
         .mcb3_dram_ck                   ($mcb3_dram_ck),
         .mcb3_dram_ck_n                 ($mcb3_dram_ck_n),
         .mcb3_dram_dq                   ($mcb3_dram_dq),
         .mcb3_dram_dqs                  ($mcb3_dram_dqs),
         .mcb3_dram_dqs_n                ($mcb3_dram_dqs_n),
         .mcb3_dram_udqs                 ($mcb3_dram_udqs),
         .mcb3_dram_udqs_n               ($mcb3_dram_udqs_n),
         .mcb3_dram_udm                  ($mcb3_dram_udm),
         .mcb3_dram_dm                   ($mcb3_dram_dm),
         .mcb3_dram_odt                  ($mcb3_dram_odt),
         .mcb3_dram_cke                  (),
         .mcb3_rzq			 ()
);
'''
