import threading
from serial import SerialException
import time
from zrc_core import MessageString, MessageType
import logging

logger = logging.getLogger(__name__)


class UAVRadioFinder(object):
    def __init__(self, serial, *args, **kwargs):
        self.gain = 1.0
        self.scanFrequency = 150.096e6
        self.snrThreshold = 5.0

        self._heading = 0.0
        self._altitude = 0.0
        self._serial = serial

        self._scan_alive = threading.Event()
        self._scan_alive.set()
        self._scan_thread = threading.Thread(target=self._send_scanning)
        self._scan_thread.daemon = True
        self._scanning = False

        self._serial.subscribe(MessageString[MessageType.attitude], self.OnAttitudeReceived)

    def OnAttitudeReceived(self, msg):
        self._heading = msg.heading
        self._altitude = msg.altitude
        print msg

    def UpdateScanSettings(self, gain=None, freq=None, snr=None):
        """
        Update internal scan settings variables and send a packet
        to the UAV indicating SDR scan settings should be updated.
        :param gain: SDR receiver gain
        :param freq: scanning frequency of target
        :param snr: snr threshold in which to trigger scan frequency detection
        :return: True if packet sent, false otherwise.
        """
        self._scanning = False
        if not gain and not freq and not snr:
            return False
        else:
            try:
                self.gain = gain or self.gain
                self.scanFrequency = freq or self.scanFrequency
                self.snrThreshold = snr or self.snrThresholds

                self._serial.send_scan_settings(self.gain,
                                                self.scanFrequency,
                                                self.snrThreshold)
                return True
            except SerialException:
                return False

    def UpdateScanSettings(self):
        """
        Send scan settings packet to UAV indicating that the
        SDR scan setting should be updated
        :return: True if packet send, false otherwise
        """
        try:
            self._serial.send_scan_settings(self.gain,
                                            self.scanFrequency,
                                            self.snrThreshold)
            return True
        except SerialException:
            return False

    def StartScan(self):
        self._scanning = True
#
    def StopScan(self):
        self._scanning = False

    def IsScanning(self):
        return self._scanning

    def GetAltitude(self):
        return self._altitude

    def GetHeading(self):
        return self._heading

    def _send_scanning(self):
        while self._scan_alive:
            try:
                self._serial.send_scanning(self._scanning)
                time.sleep(1)
            except SerialException:
                time.sleep(1)



    def Start(self):
        self._scan_thread.start()

    def Dispose(self):
        if self._scan_thread.is_alive():
            self._scan_alive.clear()
            self._scan_thread.join(timeout=0.5)
