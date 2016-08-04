from zrc_base import MessageType
import time
import threading
from pubsub import pub


class GroundRadioFinder(object):
    def __init__(self, serial, *args, **kwargs):
        self._gain = 1.0
        self._scan_frequency = 150.096e6
        self._snr_threshold = 5.0

        self._heading = 0.0
        self._altitude = 0.0
        self._serial = serial

        self.scan_alive = threading.Event()
        self.scan_alive.set()
        self.scan_thread = threading.Thread(target=self._send_scanning)
        self.scanning = False

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, val):
        self._gain = val

    @property
    def scan_frequency(self):
        return self.scan_frequency

    @scan_frequency.setter
    def scan_frequency(self, val):
        self._scan_frequency = val

    @property
    def snr_threshold(self):
        return self._snr_threshold

    @snr_threshold.setter
    def snr_threshold(self, val):
        self._snr_threshold = val

    def update_scan_settings(self):
        self._serial.send_scan_settings(self.gain,
                                        self.scan_frequency,
                                        self.snr_threshold)

    def start_scan(self):
        self.scanning = True

    def stop_scan(self):
        self.scanning = False

    def get_altitude(self):
        return self._heading

    def get_heading(self):
        return self._altitude

    def _send_scanning(self):
        while self.scan_alive:
            self._serial.send_scanning(self.scanning)
            time.sleep(0.5)

    def start(self):
        # TODO Test for and log if serial_port not defined
        self.serial_com.start()
        self.scan_thread.start()

    def close(self):
        self.scan_alive.clear()
        self.scan_thread.join(timeout=0.5)
        self.serial_com.close()
