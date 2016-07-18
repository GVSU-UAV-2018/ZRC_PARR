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
import Queue
import Serial_CRC
import threading
import smbus
import time
import math
import Adafruit_BMP.BMP085 as BMP085
from zrc_base import SerialPort, msg_id_to_type


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
    def __init__(self, *args, **kwargs):
        gr.top_block.__init__(self, "UAV Radio Finder")
        # kwargs.get(<named variable name>, <default value if None>)
        self._gain = kwargs.get('gain', 20)
        self._scan_frequency = kwargs.get('scan_frequency', 150.096e6)
        self._snr_threshold = kwargs.get('snr_threshold', 5.0)

        self.serial_port = kwargs.get('serial_port', None)

        self.scanning = False
        self.freq_offset = kwargs.get('freq_offset', 3000)
        self._attitude = {'heading': 0.0, 'altitude': 0.0}

        self.altimeter = kwargs.get('altimeter', BarometerSensor())
        self.compass = kwargs.get('compass', Compass())
        
        self._create_gr_blocks(kwargs.get('sample_rate', 192000))
        self._connect_gr_blocks()
        # TODO Subscribe to event here which gets published from Burst_detection and store bursts

    def _create_gr_blocks(self, sample_rate):
        self.fft_vxx_0 = fft.fft_vfc(512, True, (window.rectangular(512)), 1)
        self.fcdproplus_fcdproplus_0 = fcdproplus.fcdproplus("", 1)
        self.fcdproplus_fcdproplus_0.set_lna(1)
        self.fcdproplus_fcdproplus_0.set_mixer_gain(1)
        self.fcdproplus_fcdproplus_0.set_if_gain(self.gain)
        self.fcdproplus_fcdproplus_0.set_freq_corr(0)
        self.fcdproplus_fcdproplus_0.set_freq(self.scan_frequency - self.freq_offset)

        self.collar_detect_Burst_Detection_0 = collar_detect.Burst_Detection(self.snr_threshold)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_float*1, 512)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(512)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(512)
        self.band_pass_filter_0 = filter.fir_filter_ccf(12, firdes.band_pass(
        	100, sample_rate, 2.5e3, 3.5e3, 600, firdes.WIN_RECTANGULAR, 6.76))

    def _connect_gr_blocks(self):
        self.connect((self.fcdproplus_fcdproplus_0, 0), (self.band_pass_filter_0, 0))
        self.connect((self.band_pass_filter_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.fft_vxx_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.collar_detect_Burst_Detection_0, 0))

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, val):
        self._gain = val
        self.fcdproplus_fcdproplus_0.set_if_gain(self._gain)

    @property
    def scan_frequency(self):
        return self._scan_frequency

    @scan_frequency.setter
    def scan_frequency(self, val):
        self._scan_frequency = val
        self.fcdproplus_fcdproplus_0.set_freq(self._scan_frequency - self.freq_offset)

    @property
    def snr_threshold(self):
        return self._snr_threshold

    @snr_threshold.setter
    def snr_threshold(self, val):
        self._snr_threshold = val

    def is_scanning(self):
        return self.scanning

    def scan(self):
        try:
            msg = self.serial_port.in_q.get(block=True, timeout=0.1)
            if msg is not None:
                self._handle_msg(msg)
        except Queue.Empty as e:
            pass
        #TODO Put this on a timer sometime after testing
        # Send UAV attitude to the ground station
        self.serial_port.send_attitude(
            alt=self.get_altitude(),
            heading=self.get_heading())

    def start(self, max_noutput_items=10000000):
        super(UAVRadioFinder, self).start(max_noutput_items)
        self.serial_p.start()

    def get_heading(self):
        if self.compass is None:
            raise TypeError('No compass sensor found')

        return self.compass.get_heading()

    def get_altitude(self):
        if self.altimeter is None:
            raise TypeError('No altimeter sensor found')

        return self.altimeter.get_altitude()

    def _handle_msg(self, msg):
        if msg_id_to_type[msg.msg_id] == 'scanning':
            if msg.scanning == 1 and self.scanning is False:
                self.scanning = True
            elif msg.scanning == 0 and self.scanning is True:
                self.scanning = False

        if msg_id_to_type[msg.msg_id] == 'scan_settings':
            self.gain = msg.gain
            self.scan_frequency = msg.scan_frequency
            self.snr_threshold = msg.snr_threshold

    def close(self):
        self.serial_p.close()


class Compass(object):
    def __init__(self, *args, **kwargs):
        self.sensor = HMC5883L(args, kwargs)
        self.x_offset = 180
        self.y_offset = 709
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
        # TODO Revisit this and figure out what is going on here
        x = (x - self.x_offset) * self.scale
        y = (y - self.y_offset) * self.scale
        heading = math.atan2(y, x) - 0.1745329
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
        word = (high_byte >> 8) + low_byte
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
    input_q = Queue.Queue()
    output_q = Queue.Queue()
    serial_port = SerialPort(in_q=input_q, out_q=output_q, port='/dev/ttyAMA0')

    rdf = UAVRadioFinder(serial_port=serial_port)
    rdf.start()

    while True:
        try:
            rdf.scan()
        except Exception as e:
            print e.message
            rdf.close()
            break

if __name__ == '__main__':
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print 'Error: failed to enable real time scheduling'

    main_loop()


