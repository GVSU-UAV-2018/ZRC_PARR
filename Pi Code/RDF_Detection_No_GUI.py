#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Rdf Detection No Gui
# Generated: Sun Jul 24 03:29:53 2016
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import collar_detect
import osmosdr

class RDF_Detection_No_GUI(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Rdf Detection No Gui")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 192000
        self.gain = gain = 20
        self.collar_freq = collar_freq = 150.742800e6
        self.SNR = SNR = 5

        ##################################################
        # Blocks
        ##################################################
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(collar_freq-3000, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(2, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(2, 0)
        self.rtlsdr_source_0.set_gain_mode(True, 0)
        self.rtlsdr_source_0.set_gain(10, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)

        self.fft_vxx_0 = fft.fft_vfc(512, True, (window.rectangular(512)), 1)
        self.collar_detect_collar_detect_0 = collar_detect.collar_detect()
        self.blocks_udp_sink_0_0 = blocks.udp_sink(gr.sizeof_gr_complex*1, "192.168.1.11", 1234, 1472, True)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_float*1, 512)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(512)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(512)
        self.band_pass_filter_0 = filter.fir_filter_ccf(6, firdes.band_pass(
        	100, samp_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.band_pass_filter_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_udp_sink_0_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.band_pass_filter_0, 0))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.collar_detect_collar_detect_0, 0))



    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_pass_filter_0.set_taps(firdes.band_pass(100, self.samp_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

    def get_collar_freq(self):
        return self.collar_freq

    def set_collar_freq(self, collar_freq):
        self.collar_freq = collar_freq
        self.rtlsdr_source_0.set_center_freq(self.collar_freq-3000, 0)

    def get_SNR(self):
        return self.SNR

    def set_SNR(self, SNR):
        self.SNR = SNR

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."
    tb = RDF_Detection_No_GUI()
    tb.start()
    raw_input('Press Enter to quit: ')
    tb.stop()
    tb.wait()