#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2015 <+YOU OR YOUR COMPANY+>.
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
var_avg_temp = []
prev_time = 0.0
collar_offset = 3000
sample_freq_decim = 16000.0
collar_bandwidth = 1000.0
#max_bin = int(((collar_offset + collar_bandwidth / 2.0) / sample_freq_decim) * 512.0)
#min_bin = int(((collar_offset - collar_bandwidth / 2.0) / sample_freq_decim) * 512.0)


class collar_detect(gr.sync_block):
    """
    docstring for block collar_detect
    """

    def __init__(self):
        gr.sync_block.__init__(self,
                               name="collar_detect",
                               in_sig=[(numpy.float32, 512)],
                               out_sig=None)

    def work(self, input_items, output_items):
        global var_avg
        #global min_bin
        #global max_bin
        global i
        global var_avg_temp
        in0 = input_items[0]

        noise_mean = numpy.mean(in0[0])
        #noise_norm = numpy.asarray(in0[0][min_bin:max_bin]) - noise_mean
        #noise_var = numpy.var(noise_norm)

        noise_var = numpy.var(in0[0])

        # at 16kHz and 512 samples, 31 windows is approximately .992 seconds. The pulse is approximately 1.2s.
        # because the pulse will be included in the "noise floor" calculation the majority of the time
        # and the pulse is approximately 2ms, and each window of 512 samples is 3.2ms, and the pulse may
        # overlap two windows, the two largest var_avg_temp values should be destroyed because they likely
        # are contributed from the pulse and do not truly represent the noise floor.

        if i < 31:
            var_avg_temp.append(noise_mean)
            i += 1
        else:
            # remove largest two values from var_avg_temp before averaging
            var_avg_temp.remove(max(var_avg_temp))
            var_avg_temp.remove(max(var_avg_temp))
            var_avg = numpy.mean(var_avg_temp)
            var_avg_temp = []
            i = 0

        if noise_mean > 100.0 * var_avg:
            detected_pulse = noise_mean / var_avg
            pub.sendMessage('detection', arg1=detected_pulse)
            # print numpy.max(noise_norm)

        return len(input_items[0])

