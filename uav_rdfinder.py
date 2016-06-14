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
import Serial_CRC
import threading
import smbus
import time
import math
import Adafruit_BMP.BMP085 as BMP085
import zrc_base


class UAVRadioFinder(zrc_base.RadioFinderBase, gr.top_block):
    """
    Represents a radio finder located on a UAV. Detection is accomplished
    using gnuradio and a software defined radio.
    Arguments:
        gain - the gain of the SDR receiver
        scan_frequency - the center frequency of the SDR receiver in Hz
        snr_threshold - the snr value above the noise floor at which point the signal of interest is deemed detected
        freq_offset - the frequency offset from the center frequency in Hz
        sample_rate - the sample rate of the SDR
        altimeter - sensor device used to get current altitude of UAV
    """
    def __init__(self, *args, **kwargs):
        gr.top_block.__init__(self, "UAV Radio Finder")
        # kwargs.get(<named variable name>, <default value if None>)
        self._gain = kwargs.get('gain', 20)
        self._scan_frequency = kwargs.get('scan_frequency', 150.096e6)
        self._snr_threshold = kwargs.get('snr_threshold', 5.0)

        self.scanning = False
        self.freq_offset = kwargs.get('freq_offset', 3000)
        self._attitude = {'heading': 0.0, 'altitude': 0.0}

        self.altimeter = kwargs.get('altimeter', BarometerSensor())
        self._create_gr_blocks(kwargs.get('sample_rate', 192000))
        self._connect_gr_blocks()

    def _create_gr_blocks(self, sample_rate):
        self.fft_vxx_0 = fft.fft_vfc(512, True, (window.rectangular(512)), 1)
        self.fcdproplus_fcdproplus_0 = fcdproplus.fcdproplus("",1)
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

    def _init_communication(self):
        pass

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

    @gain.setter
    def scan_frequency(self, val):
        self._scan_frequency = val
        self.fcdproplus_fcdproplus_0.set_freq(self._scan_frequency - self.freq_offset)

    @property
    def snr_threshold(self):
        return self._snr_threshold

    @gain.setter
    def snr_threshold(self, val):
        self._snr_threshold = val

    def is_scanning(self):
        return self.scanning

    def start_scanning(self):
        pass

    def stop_scanning(self):
        pass

    def send_status_msg(self):
        pass

    def get_heading(self):
        if self.altimeter is None:
            raise TypeError("No barometer sensor found")

        return self.altimeter.get_altitude()

    def send_detection_msg:
        pass


class GPSCompass(object):
    """
    Represents an GPS compass using i2c interface
    Arguments:
        port - The I2C port number on which the device resides
        address - Address location of device
        byte_sample_rate - byte that sets sample rate for device
        byte_gain - byte that sets gain of device
    """
    def __init__(self, *args, **kwargs):
        self.bus = smbus.SMBus(kwargs.get('port', 1))
        self.address = kwargs.get('address', 0x1e)

        # Set initial sample rate to 8 samples at 15Hz
        self.set_sample_rate(kwargs.get('byte_sample_rate', 0b01110000))
        # 1.3 gain LSb / Gauss 1090 (default)
        self.set_gain(kwargs.get('byte_gain', 0b00100000))
        self.set_continuous_sampling()

    def set_sample_rate(self, config_byte):
        self.write_byte(0, config_byte)

    def set_gain(self, config_byte):
        self.write_byte(1, config_byte)

    def set_continuous_sampling(self):
        self.write_byte(2, 0b00000000)

    def read_byte(self, location):
        return self.bus.read_byte_data(self.address, location)

    def read_word(self, location):
        high_byte = self.bus.read_byte_data(self.address, location)
        low_byte = self.bus.read_byte_data(self.address, location + 1)
        # Construct the word in big endian format
        word = (high_byte >> 8) + low_byte
        return word


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
