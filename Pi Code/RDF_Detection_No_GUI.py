#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Rdf Detection No Gui
# Generated: Mon Oct 26 23:51:08 2015
##################################################

import math
import threading
import time
from gnuradio import blocks
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser

import collar_detect
import fcdproplus
import smbus

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
        self.gain = gain
        self.collar_freq = collar_freq 
        self.SNR = SNR

        ##################################################
        # Blocks
        ##################################################
        self.fft_vxx_0 = fft.fft_vfc(512, True, (window.rectangular(512)), 1)
        self.fcdproplus_fcdproplus_0 = fcdproplus.fcdproplus("",1)
        self.fcdproplus_fcdproplus_0.set_lna(1)
        self.fcdproplus_fcdproplus_0.set_mixer_gain(1)
        self.fcdproplus_fcdproplus_0.set_if_gain(gain)
        self.fcdproplus_fcdproplus_0.set_freq_corr(0)
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
          
        self.collar_detect_Burst_Detection_0 = collar_detect.Burst_Detection(SNR)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_float*1, 512)
        self.blocks_udp_sink_0_0 = blocks.udp_sink(gr.sizeof_gr_complex * 1, "192.168.1.11", 1234, 1472, True)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(512)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(512)
        self.band_pass_filter_0 = filter.fir_filter_ccf(12, firdes.band_pass(
            100, samp_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.fcdproplus_fcdproplus_0, 0), (self.band_pass_filter_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_udp_sink_0_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.collar_detect_Burst_Detection_0, 0))



    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.band_pass_filter_0.set_taps(firdes.band_pass(100, self.samp_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))

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
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)

    def get_SNR(self):
        return self.SNR

    def set_SNR(self, snr):
        global SNR
        SNR = snr
        print SNR

    def update_vars(self, rcvd_msg):
        global bearing_deg
        global collar_freq
        collar_freq = rcvd_msg.data[0]
        self.collar_detect_Burst_Detection_0.update_SNR(rcvd_msg.data[2])
        self.collar_detect_Burst_Detection_0.update_scanning(rcvd_msg.scanning,bearing)
        print rcvd_msg.scanning,bearing
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
        self.fcdproplus_fcdproplus_0.set_if_gain(rcvd_msg.data[1])

#Sending the status down to the ground (current heading (compass) and system info parameters)
def status_sender(tb):
    global collar_freq
    global gain
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
        print "Compass Bearing:"
        print bearing
        if(scanning == 0):
            detection = tb.collar_detect_Burst_Detection_0.get_detection()

            Serial_CRC.send_serial("RPI_to_GS","DETECTION",[collar_freq,detection[1] - 178.0, detection[0]])#swapped i for collar_freq
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
