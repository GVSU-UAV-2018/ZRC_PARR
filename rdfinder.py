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

        self.scan_alive = threading.Event()
        self.scan_alive.set()
        self.scan_thread = threading.Thread(target=self._send_scanning)
        self.scanning = False

        self._serial.subscribe(MessageString[MessageType.attitude], self.OnAttitudeReceived)

    def OnAttitudeReceived(self, msg):
        self._heading = msg.heading
        self._altitude = msg.altitude

    def UpdateReceiver(self):
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

    def SendScanning(self):
        self._serial.SendScanning(self.scanning)

    def Start(self):
        self.scan_thread.start()

    def Close(self):
        self.scan_alive.clear()
        self.scan_thread.join(timeout=0.5)
        self.serial_com.Close()
