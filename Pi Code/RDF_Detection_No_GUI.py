#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Rdf Detection No Gui
# Generated: Mon Oct 26 23:51:08 2015
##################################################

import math
import threading
import time
import numpy
from gnuradio import blocks
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser

import collar_detect
import osmosdr
import smbus
from pubsub import pub

import Adafruit_BMP.BMP085 as BMP085
import Serial_CRC

#sensor bus library for i2c for sensor for communication between pi processor and sensor
bus = smbus.SMBus(1)
#Address of BMP devices
address = 0x1e
#sensor is altimeter and compass
sensor = BMP085.BMP085()


def read_byte(adr):
    return bus.read_byte_data(address, adr)

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
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

#Configuring the sensor
write_byte(0, 0b01110000) # Set to 8 samples @ 15Hz
write_byte(1, 0b00100000) # 1.3 gain LSb / Gauss 1090 (default)
write_byte(2, 0b00000000) # Continuous sampling

scale = 0.92

collar_freq = 150704800
gain = 20
SNR = 5.0
scanning = False
bearing = 0.0
i = 0
var_avg = 0.0
var_avg_temp = 0.0
prev_time = 0.0
collar_offset = 3000
sample_freq_decim = 16000.0
collar_bandwidth = 1000.0
max_bin = int(((collar_offset+collar_bandwidth/2)/sample_freq_decim) * 512)
min_bin = int(((collar_offset-collar_bandwidth/2)/sample_freq_decim) * 512)
v_avg = numpy.array([0.0,0.0])
detection = numpy.array([0.0,0.0])
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

        pub.subscribe(self.averaging, 'detection')

    def averaging(self, pulse_snr):
        global scanning
        global prv_scanning
        global v_avg
        global bearing
        global num_detections
        global prv_scanning
        global detection
        # if there is a change in state of scanning, and it was not scanning prior
        if (scanning != prv_scanning) and (prv_scanning == 0):
            v_avg = numpy.array([0.0, 0.0])
            num_detections = 0.0
            prv_scanning = scanning
        elif (scanning != prv_scanning) and (prv_scanning == 1):
            v_avg /= num_detections
            detection_mag = numpy.linalg.norm(v_avg)
            detection_ang = numpy.arctan2(v_avg[1], v_avg[0])
            if detection_ang < 0:
                detection_ang += 2 * math.pi
                detection_ang = math.degrees(detection_ang)
                detection = numpy.array([detection_mag, detection_ang])
                print detection
                prv_scanning = scanning
        else:
            prv_scanning = scanning
        if scanning == 1:
            v_avg = v_avg + numpy.array([pulse_snr * math.cos(bearing), pulse_snr * math.sin(bearing)])
            num_detections += 1.0
        print pulse_snr

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
        self.fcdproplus_fcdproplus_0.set_if_gain(self.gain)

    def get_collar_freq(self):
        return self.collar_freq

    def set_collar_freq(self, freq):
        global collar_freq
        collar_freq = freq
        self.rtlsdr_source_0.set_center_freq(self.collar_freq-3000, 0)

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
        collar_freq = rcvd_msg.data[0]
        scanning = rcvd_msg.scanning
        self.collar_detect_collar_detect_0.update_SNR(rcvd_msg.data[2])
        self.collar_detect_collar_detect_0.update_scanning(scanning,bearing)
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
        self.fcdproplus_fcdproplus_0.set_if_gain(rcvd_msg.data[1])

#Sending the status down to the ground (current heading (compass) and system info parameters)
def status_sender(tb):
    global collar_freq
    global gain
    global scanning
    global SNR
    global bearing
    while True:
        time.sleep(.2)
        #reading for memory locations 3,7
        #180 and 709 are currently hardcoded calibrations of compass offsets with Kurt's setup
        y_out = (read_word_2c(3) - 180) * scale #y and x are uav plane
        x_out = (read_word_2c(7) + 709) * scale

        bearing  = math.atan2(y_out, x_out) - .1745329
        if (bearing < 0):
            bearing += 2 * math.pi
        # If not scanning (scanning = 0) it sends most recent detection or sends empty data upon initialization
        if(scanning == False):
            detection = 0.0
            Serial_CRC.send_serial("RPI_to_GS","DETECTION",[collar_freq,detection - 178.0, detection])#swapped i for collar_freq
        #So if math.degrees(bearing) is 2 degrees then the UAV is pointed south
        #This will change if the position of the compass changes orientation
        #Always sends system info
        Serial_CRC.send_serial("RPI_to_GS","SYS_INFO",[collar_freq ,(math.degrees(bearing) - 178.0),sensor.read_altitude()])

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."
    tb = RDF_Detection_No_GUI()
    tb.start()
    receiver = threading.Thread(target = Serial_CRC.receive_serial, args = (tb,))
    receiver.start()
    sender = threading.Thread(target = status_sender, args = (tb,))
    sender.start()
    raw_input('Press Enter to quit: ')
    tb.stop()
    tb.wait()
    Serial_CRC.ser_close()
