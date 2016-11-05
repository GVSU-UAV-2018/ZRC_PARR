#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2016 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy
from gnuradio import gr
from pubsub import pub

i = 0
var_avg = 0.0
vag_avg_temp = []
prev_time = 0.0
collar_offset = 3000
sample_freq_decim = 16000.0
collar_bandwidth = 1000.0

class cw_pulse_detect(gr.sync_block):
    """
    docstring for block cw_pulse_detect
    """
    def __init__(self, snr, floor_samples):
        gr.sync_block.__init__(self,
            name="cw_pulse_detect",
            in_sig=[(numpy.float32, 512)],
            out_sig=None)
        self.snr_threshold = snr or 6.0

    def work(self, input_items, output_items):
        global var_arg
        global i
        global var_avg_temp
        in0 = input_items[0]

        noise_mean = numpy.mean(in0[0])

        noise_var = numpy.var(in0[0])

	if i < 310:
            var_avg_temp.append(noise_mean)
            i += 1
        else:
            var_avg_temp.remove(max(var_avg_temp))
	    var_avg_temp.remove(max(var_avg_temp))
	    var_avg = numpy.mean(var_avg_temp)
    	    i = 0

	if noise_mean > self.snr_threshold * var_avg:
            detected_pulse = noise_mean / var_avg
            pub.sendMessage('detection', magnitude=detected_pulse)

	return len(input_items[0])

