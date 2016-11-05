from gnuradio import blocks
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import Queue
import time
import autoSNR
import smbus
import osmosdr
import numpy
import math
import Adafruit_BMP.BMP085 as BMP085
from zrc_core import SerialInterface, MessageString, MessageType
import threading
from pubsub import pub

import logging
logger = logging.getLogger(__name__)


class UAVRadioFinder(gr.top_block):
    """
    Represents a radio finder located on a UAV. Detection is accomplished
    using gnuradio and a software defined radio.
    Arguments:
        gain - the gain of the SDR receiver
        scan_frequency - the center frequency of the SDR receiver in Hz
        snr_threshold - the snr value above the noise floor at which point the signal of interest is deemed detected
        freq_offset - the frequency offset from the center frequency in Hz
        sample_rate - the sample rate of 75the SDR
        altimeter - sensor device used to get current altitude of UAV
    """
    def __init__(self, serial, **kwargs):
        gr.top_block.__init__(self, "UAV Radio Finder")
        # kwargs.get(<named variable name>, <default value if None>)
        self._gain = kwargs.get('gain', 10)
        self._scan_frequency = kwargs.get('scan_frequency', 150.742e6)
        self._snr_threshold = kwargs.get('snr_threshold', 1.0)

        self._prev_scanning = False
        self._scanning = False
        self._freq_offset = kwargs.get('freq_offset', 3000)
        self._attitude = {'heading': 0.0, 'altitude': 0.0}

        self.altimeter = BarometerSensor()
        self.compass = Compass()
        self._send_attitude_flag = threading.Event()
        self._send_attitude_flag.set()
        self._attitude_thread = threading.Thread(target=self._send_attitude)
        self._attitude_thread.daemon = True

        pub.subscribe(self._on_detection, 'detection')
        self.serial = serial
        if self.serial is not None:
            self.serial.subscribe(MessageString[MessageType.scanning], self._on_scanning)
            self.serial.subscribe(MessageString[MessageType.scan_settings], self._on_scan_settings)

        self._direction_finder = DirectionFinder()
        self._create_gr_blocks(kwargs.get('sample_rate', 192000))
        self._connect_gr_blocks()

    def _create_gr_blocks(self, sample_rate):
        self.rtlsdr_source_0 = osmosdr.source(args="numchan=" + str(1) + " " + "")
        self.rtlsdr_source_0.set_sample_rate(sample_rate)
        self.rtlsdr_source_0.set_center_freq(self._scan_frequency - self._freq_offset, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(self._gain, 0)
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
            1, self._scan_frequency, 2500, 3500, 600, firdes.WIN_HAMMING, 6.76))
        #self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(-150, 1, 0, False)
        self.autoSNR_cw_pulse_detect = autoSNR.cw_pulse_detect(snr=6.0, floor_samples=310)

    def _connect_gr_blocks(self):
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_stream_to_vector_1, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_udp_sink_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_1, 0), (self.autoSNR_cw_pulse_detect, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        #self.connect((self.blocks_vector_to_stream_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 2))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 3))
        self.connect((self.rtlsdr_source_0, 0), (self.band_pass_filter_0, 0))

    def _on_scanning(self, msg):
        if msg is None:
            return

        self._prev_scanning = self._scanning
        self._scanning = msg.scanning

        # Detect falling edge of scanning which means a scan has finished
        if self._prev_scanning is True and self._scanning is False:
            result = self._direction_finder.FindDirection()
            if result is None:
                print 'No detections, not sending detection packet'
                return

            magnitude = result[0]
            angle = result[1]
            print 'Angle: ' + str(angle)
            print 'Magnitude: ' + str(magnitude)
            self.serial.send_detection(magnitude, angle)

    def _on_scan_settings(self, msg):
        if msg is None:
            return

        self.gain = msg.gain
        self.scan_frequency = msg.scan_frequency
        self.snr_threshold = msg.snr_threshold

    def _on_detection(self, magnitude):
        # Detect rising edge of scanning which means a scan has started
        if self._prev_scanning is False and self._scan_frequency is True:
            self._direction_finder.Reset()

        # Accumulate any detections while scan is active
        elif self._scanning is True:
            self._direction_finder.AddDetection(magnitude)

    def _send_attitude(self):
        while self._send_attitude_flag.isSet():
            altitude = self.get_altitude()
            heading = self.get_heading()
            if self.serial is not None:
                self.serial.send_attitude(altitude, heading)
                time.sleep(0.1)

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, val):
        self._gain = val
        self.rtlsdr_source_0.set_if_gain(self._gain)

    @property
    def scan_frequency(self):
        return self._scan_frequency

    @scan_frequency.setter
    def scan_frequency(self, val):
        self._scan_frequency = val
        self.rtlsdr_source_0.set_freq(self._scan_frequency - self._freq_offset)

    @property
    def snr_threshold(self):
        return self._snr_threshold

    @snr_threshold.setter
    def snr_threshold(self, val):
        self._snr_threshold = val
        self.autoSNR_cw_pulse_detect.snr_threshold = self._snr_threshold

    def start(self, max_noutput_items=10000000):
        super(UAVRadioFinder, self).start(max_noutput_items)
        self.serial.start()
        self._attitude_thread.start()

    def get_heading(self):
        if self.compass is None:
            raise TypeError('No compass sensor found')

        return self.compass.get_heading()

    def get_altitude(self):
        if self.altimeter is None:
            raise TypeError('No altimeter sensor found')

        return self.altimeter.get_altitude()

    def close(self):
        self._send_attitude_flag.clear()
        if self.serial is not None:
            self.serial.Dispose()

        self._attitude_thread.join(timeout=0.1)


class DirectionFinder(object):
    """
        Accumulates detections and determines final magnitude
        and direction of a scan
    """
    def __init__(self):
        super(DirectionFinder, self).__init__()
        self._num_detections = 0
        self._sum = numpy.array([0.0, 0.0])

    def Reset(self):
        self._num_detections = 0
        self._sum = numpy.array([0.0, 0.0])

    def AddDetection(self, magnitude, heading):
        self._sum += numpy.array(magnitude * math.cos(heading), magnitude * math.sin(heading))
        self._num_detections += 1

    def FindDirection(self):
        if self._num_detections <= 0:
            return
        average = self._sum / self._num_detections
        found_magnitude = numpy.linalg.norm(average)
        found_angle = numpy.arctan2(average[1], average[0])

        if found_angle < 0:
            found_angle += 2 * math.pi

        found_angle = math.degrees(found_angle)
        return found_magnitude, found_angle


class Compass(object):
    def __init__(self, *args, **kwargs):
        self.sensor = HMC5883L(args, kwargs)
        self.x_offset = 956
        self.y_offset = -680
        self.z_offset = 0
        self.scale = 0.92

    def set_offsets(self, x, y, z, scale):
        self.x_offset = x
        self.y_offset = y
        self.z_offset = z
        self.scale = scale

    def get_heading(self):
        x = self.sensor.get_x()
        y = self.sensor.get_y()
        z = self.sensor.get_z()
        # TODO Revisit this and figure out what is going on here
        x = (x + self.x_offset) * self.scale
        y = (y + self.y_offset) * self.scale
        heading = math.atan2(y, x) - 0.1745329

        if heading < 0:
            heading += 2 * math.pi

        return heading


class HMC5883L(object):
    """
    Represents HMC5883 magnetometer
    Arguments:
        port - The I2C port number on which the device resides
        address - Address location of device
        byte_sample_rate - byte that sets sample rate for device
        byte_gain - byte that sets gain of device
    """
    CONFIG_A_REGISTER = 0
    CONFIG_B_REGISTER = 1
    MODE_REGISTER = 2
    X_REGISTER = 3
    Z_REGISTER = 5
    Y_REGISTER = 7

    def __init__(self, *args, **kwargs):
        self.bus = smbus.SMBus(kwargs.get('port', 1))
        self.address = kwargs.get('bus_address', 0x1e)

        # Set initial sample rate to 8 samples at 15Hz
        self.set_config_a(kwargs.get('config_a', 0b01110000))
        # 1.3 gain LSb / Gauss 1090 (default)
        self.set_config_b(kwargs.get('config_b', 0b00100000))
        self.set_op_mode(kwargs.get('op_mode', 0b00000000))

    def set_config_a(self, config_byte):
        self.write_byte(HMC5883L.CONFIG_A_REGISTER, config_byte)

    def set_config_b(self, config_byte):
        self.write_byte(HMC5883L.CONFIG_B_REGISTER, config_byte)

    def set_op_mode(self, op_mode):
        self.write_byte(HMC5883L.MODE_REGISTER, op_mode)

    def read_byte(self, location):
        return self.bus.read_byte_data(self.address, location)

    def read_word(self, location):
        high_byte = self.bus.read_byte_data(self.address, location)
        low_byte = self.bus.read_byte_data(self.address, location + 1)
        # Construct the word in big endian format
        word = (high_byte << 8) + low_byte
        return word

    def get_x(self):
        return self.read_word_2c(HMC5883L.X_REGISTER)

    def get_z(self):
        return self.read_word_2c(HMC5883L.Z_REGISTER)

    def get_y(self):
        return self.read_word_2c(HMC5883L.Y_REGISTER)

    def read_word_2c(self, location):
        """
        Read a word from the specified address location and perform
        twos complement operation as necessary (eg. word is negative -- 1 as MSB)
        """
        word = self.read_word(location)
        # Check for a negative number (two's complement) and convert to correct representation
        if word >= 0x8000:
            return -((65535 - word) + 1)
        else:
            return word

    def write_byte(self, location, value):
        self.bus.write_byte_data(self.address, location, value)


class BarometerSensor(object):
    def __init__(self, *args, **kwargs):
        self.sensor = BMP085.BMP085()

    def get_altitude(self):
        return self.sensor.read_altitude()


def main_loop():
    config = {'port': '/dev/ttyAMA0',
              'baud': 57600,
              'timeout': 0.1}
    serial = SerialInterface(config)

    rdf = UAVRadioFinder(serial=serial)
    rdf.start()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print 'Error: failed to enable real time scheduling'

    import logging.config
    #logging.config.fileConfig('')
    main_loop()


