#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Rdf Detection No Gui
# Generated: Mon Oct 26 23:51:08 2015
##################################################

import math
import numpy
import threading
from gnuradio import blocks
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import osmosdr
import fcdproplus
import sip
import sys
import Serial_CRC
import serial
import time
import threading
import smbus
import time
import math
import collar_detect
import smbus
from gnuradio import analog
from pubsub import pub

import Adafruit_BMP.BMP085 as BMP085
import Serial_CRC

# sensor bus library for i2c for sensor for communication between pi processor and sensor
bus = smbus.SMBus(1)
# Address of BMP devices
address = 0x1e
# sensor is altimeter and compass
sensor = BMP085.BMP085()


def read_byte(adr):
    return bus.read_byte_data(address, adr)


def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr + 1)
    val = (high << 8) + low
    return val


def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val


def write_byte(adr, value):
    bus.write_byte_data(address, adr, value)


# Configuring the sensor
write_byte(0, 0b01110000)  # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000)  # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000)  # Continuous sampling

scale = 0.984

collar_freq = 150704800.0
gain = 20
SNR = 5.0
scanning = 0
bearing = 0.0
i = 0
var_avg = 0.0
var_avg_temp = 0.0
prev_time = 0.0
collar_offset = 3000.0
sample_freq_decim = 16000.0
collar_bandwidth = 1000.0
max_bin = int(((collar_offset + collar_bandwidth / 2) / sample_freq_decim) * 512)
min_bin = int(((collar_offset - collar_bandwidth / 2) / sample_freq_decim) * 512)
v_avg = numpy.array([0.0, 0.0])
detection = numpy.array([0.0, 0.0])
prv_scanning = 0
num_detections = 0.0


class RDF_Detection_No_GUI(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Rdf Detection No Gui")

        ##################################################
        # Variables
        ##################################################
        global collar_freq
        global gain
        global SNR
        self.samp_rate = samp_rate = 32000
        self.gain = gain = 20
        self.collar_freq = collar_freq = 150.742800e6
        self.SNR = SNR

        ##################################################
        # Blocks
        ##################################################

        self.rtlsdr_source_0 = osmosdr.source(args="numchan=" + str(1) + " " + "")
        self.rtlsdr_source_0.set_sample_rate(192000)
        self.rtlsdr_source_0.set_center_freq(collar_freq - collar_offset, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(10, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)

        self.fft_vxx_0 = fft.fft_vcc(512, True, (window.blackmanharris(512)), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex * 1, 512)
        self.blocks_udp_sink_0 = blocks.udp_sink(gr.sizeof_gr_complex * 1, "192.168.1.21", 1234, 1472, True)
        self.blocks_stream_to_vector_1 = blocks.stream_to_vector(gr.sizeof_float * 1, 512)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex * 1, 512)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_float * 1)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(512)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.band_pass_filter_0 = filter.fir_filter_ccf(4, firdes.band_pass(
            1, 192000, 2500, 3500, 600, firdes.WIN_HAMMING, 6.76))
        #self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(-150, 1, 0, False)
        self.collar_detect_collar_detect_0 = collar_detect.collar_detect()

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_stream_to_vector_1, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_udp_sink_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_1, 0), (self.collar_detect_collar_detect_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        #self.connect((self.blocks_vector_to_stream_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 2))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 3))
        self.connect((self.rtlsdr_source_0, 0), (self.band_pass_filter_0, 0))

        pub.subscribe(self.averaging, 'detection')

    def averaging(self, arg1):
        global scanning
        global prv_scanning
        global v_avg
        global bearing
        global num_detections
        global prv_scanning
        global detection

        print "Pulse Detection:"
        print arg1

        if scanning != prv_scanning:
            if prv_scanning is 1:
                print "Averaging..."
                v_avg /= num_detections
                detection_mag = numpy.linalg.norm(v_avg)
                detection_ang = numpy.arctan2(v_avg[1], v_avg[0])

                if detection_ang < 0.0:
                    detection_ang += 2.0 * math.pi

                detection_ang = math.degrees(detection_ang)
                detection = numpy.array([detection_mag, detection_ang])
                print "Avg Detection:"
                print detection
                prv_scanning = 0
            else:
                prv_scanning = scanning
                print "Scanning"
        else:
            prv_scanning = scanning
        if scanning is 1:
            # reading for memory locations 3,7
            # 180 and 709 are currently hardcoded calibrations of compass offsets with Kurt's setup
            y_out = (read_word_2c(7) + 956.0) * scale  # y and x are uav plane
            x_out = (read_word_2c(3) - 680.0) * scale * -1.0
            z_out = read_word_2c(5)

            bearing = math.atan2(y_out, x_out) + math.radians(95.0)
            v_avg = v_avg + numpy.array([arg1 * math.cos(bearing), arg1 * math.sin(bearing)])
            num_detections += 1.0

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)
        self.band_pass_filter_0.set_taps(
            firdes.band_pass(100, self.samp_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.rtlsdr_source_0.set_center_freq(self.gain)

    def get_collar_freq(self):
        return self.collar_freq

    def set_collar_freq(self, freq):
        global collar_freq
        collar_freq = freq
        self.rtlsdr_source_0.set_center_freq(self.collar_freq - 3000, 0)

    def get_SNR(self):
        return self.SNR

    def set_SNR(self, snr):
        global SNR
        SNR = snr
        print SNR

    def update_vars(self, rcvd_msg):
        global bearing
        global collar_freq
        global scanning
        global prv_scanning
        global num_detections
        global v_avg

        # if there is a change in state of scanning, and it was not scanning prior,
        # clear the averaging values
        if (scanning != prv_scanning) and (prv_scanning is 0):
            v_avg = numpy.array([0.0, 0.0])
            num_detections = 0.0
            prv_scanning = scanning
            print "Scan Started"
        elif (scanning != prv_scanning) and (prv_scanning is 1):
            print "Finished Scanning"
            pub.sendMessage('detection', arg1=0.0)
        else:
            prv_scanning = scanning

        collar_freq = rcvd_msg.data[0]
        scanning = rcvd_msg.scanning
        self.collar_detect_collar_detect_0.update_SNR(rcvd_msg.data[2])
        self.collar_detect_collar_detect_0.update_scanning(scanning, bearing)
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
        self.fcdproplus_fcdproplus_0.set_if_gain(rcvd_msg.data[1])


# Sending the status down to the ground (current heading (compass) and system info parameters)
def status_sender(tb):
    global collar_freq
    global gain
    global scanning
    global SNR
    global bearing
    global detection
    global scale

    while True:
        time.sleep(.3)
        # reading for memory locations 3,7
        # 180 and 709 are currently hardcoded calibrations of compass offsets with Kurt's setup
        y_out = (read_word_2c(7) + 956.0) * scale  # y and x are uav plane
        x_out = (read_word_2c(3) - 680.0) * scale * -1.0
        z_out = read_word_2c(5)

        bearing = math.atan2(y_out, x_out) + math.radians(95.0)
        if bearing < 0.0:
            bearing += 2.0*math.pi

        # If not scanning (scanning = 0) it sends most recent detection or sends empty data upon initialization
        if scanning is 0:
            Serial_CRC.send_serial("RPI_to_GS", "DETECTION",
                                   [detection[1], detection[0], collar_freq])  # swapped i for collar_freq

        # So if math.degrees(bearing) is 2 degrees then the UAV is pointed south
        # This will change if the position of the compass changes orientation
        # Always sends system info
        Serial_CRC.send_serial("RPI_to_GS", "SYS_INFO",
                               [collar_freq, (math.degrees(bearing)), sensor.read_altitude()])


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."
    tb = RDF_Detection_No_GUI()
    tb.start()
    receiver = threading.Thread(target=Serial_CRC.receive_serial, args=(tb,))
    receiver.start()
    sender = threading.Thread(target=status_sender, args=(tb,))
    sender.start()
    raw_input('Press Enter to quit: ')
    tb.stop()
    tb.wait()
    Serial_CRC.ser_close()
