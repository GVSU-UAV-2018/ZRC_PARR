#!/usr/bin/env python2
##################################################
# GNU Radio Python Flow Graph
# Title: Ant Rec
# Generated: Sun Nov 27 20:59:05 2016
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import fcdproplus
import sys
import time

class ant_rec(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Ant Rec")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 192000
        self.gain = gain = 20
        self.collar_freq = collar_freq = 150.742e6-3000
        self.SNR = SNR = 5

        ##################################################
        # Blocks
        ##################################################
        self.fcdproplus_fcdproplus_0 = fcdproplus.fcdproplus("",1)
        self.fcdproplus_fcdproplus_0.set_lna(1)
        self.fcdproplus_fcdproplus_0.set_mixer_gain(1)
        self.fcdproplus_fcdproplus_0.set_if_gain(gain)
        self.fcdproplus_fcdproplus_0.set_freq_corr(22)
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
          
        self.blocks_udp_sink_0 = blocks.udp_sink(gr.sizeof_gr_complex*1, "192.168.1.6", 1234, 1472, True)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, "funcube_replacement_no_antenna", False)
        self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.fcdproplus_fcdproplus_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.fcdproplus_fcdproplus_0, 0), (self.blocks_udp_sink_0, 0))    

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.fcdproplus_fcdproplus_0.set_if_gain(self.gain)

    def get_collar_freq(self):
        return self.collar_freq

    def set_collar_freq(self, collar_freq):
        self.collar_freq = collar_freq
        self.fcdproplus_fcdproplus_0.set_freq(self.collar_freq - 3000)

    def get_SNR(self):
        return self.SNR

    def set_SNR(self, SNR):
        self.SNR = SNR


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."
    from distutils.version import StrictVersion
    tb = ant_rec()
    tb.start()

    time.sleep(30)


    def quitting():
        tb.stop()
        tb.wait()
    tb = None  # to clean up Qt widgets
