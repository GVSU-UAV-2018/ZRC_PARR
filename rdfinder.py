import threading
import time
from zrc_core import MessageString, MessageType


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
        self.scanning = False

        self._serial.subscribe(MessageString[MessageType.attitude], self.OnAttitudeReceived)

    def OnAttitudeReceived(self, msg):
        self._heading = msg.heading
        self._altitude = msg.altitude

    def UpdateScanSettings(self):
        self._serial.send_scan_settings(self.gain,
                                        self.scanFrequency,
                                        self.snrThreshold)

    def StartScan(self):
        self.scanning = True

    def StopScan(self):
        self.scanning = False

    def GetAltitude(self):
        return self._heading

    def GetHeading(self):
        return self._altitude

    def _send_scanning(self):
        while self._scan_alive:
            self._serial.SendScanning(self.scanning)

    def Start(self):
        self._scan_thread.start()

    def Close(self):
        if self._scan_thread.is_alive():
            self._scan_alive.clear()
            self._scan_thread.join(timeout=0.5)
