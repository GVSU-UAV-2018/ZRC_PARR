from gstation import MainWindow
from zrc_core import SerialInterface, MessageString, MessageType
from rdfinder import UAVRadioFinder
from threading import Thread, Event
from pubsub import pub
from serial import SerialException
import wx


class MainWindowController(object):
    def __init__(self, config):
        self.mainWinView = MainWindow(parent=None)
        self.mainWinView.Bind(event=wx.EVT_MENU,
                              handler=self.OnClose,
                              source=self.mainWinView.exitMenuItem)
        self.mainWinView.Bind(event=wx.EVT_CLOSE,
                              handler=self.OnClose)

        self.statusView = self.mainWinView.statusDisplayPanel
        self.compassView = self.mainWinView.compassPanel

        self.scanControlData = {'currentCountdown': 5.0,
                                'totalCountdown': 5,
                                'currentScanTime': 45.0,
                                'totalScanTime': 45,
                                'scanStartAngle': 0.0,
                                'expectedAngle': 0.0}

        pub.subscribe(self.UpdateScanSettings, 'scanSettings.Submit')
        pub.subscribe(self._OnScanStart, 'scanStart.Start')
        pub.subscribe(self._OnScanStop, 'scanStart.Stop')

        self.serialConfig = config
        self.serial = None
        self.uavSeeker = None

        try:
            self.serial = SerialInterface(self.serialConfig)
            self.uavSeeker = UAVRadioFinder(self.serial)
        except SerialException as ex:
            msgDlg = wx.MessageBox(parent=self.mainWinView, message='Failed to connect to serial port.')

        self.exitUpdateThread = Event()
        self.updateTimer = TimerThread(event=self.exitUpdateThread, func=self._OnUpdateUI, interval=0.1)

        self.exitScanThread = Event()
        self.scanTimer = TimerThread(event=self.exitScanThread, func=self._OnScanTimerTick, interval=0.1)

    def Initialize(self, serial=None):
        '''Use to try to connect/reconnect to serial port later'''
        try:
            self.serial = serial or SerialInterface(self.serialConfig)
            self.uavSeeker = UAVRadioFinder(self.serial)
        except SerialException as ex:
            pass # swallow for now

    def _OnScanStart(self, params):
        """
        Event handler for scan start event. Resets timer variables
        and starts scan timer thread.
        :param params: dictionary containing total scan time and countdown time
        :return: None
        """
        self.scanControlData['currentCountdown'] = params['totalCountdown']
        self.scanControlData['totalCountdown'] = params['totalCountdown']
        self.scanControlData['totalScanTime'] = params['totalScanTime']
        self.scanControlData['currentScanTime'] = params['totalScanTime']
        self.scanControlData['scanStartAngle'] = self.uavSeeker.GetHeading()

    def _OnScanStop(self):
        self.uavSeeker.StopScan()

    def _OnScanTimerTick(self):
        """
        Event handler for timer tick of scanning timer.
        :return: None
        """
        countdown = self.scanControlData['currentCountdown']
        scanTime = self.scanControlData['currentScanTime']

        if countdown > 0:
                self.scanControlData['currentCountdown'] -= 0.1

        elif countdown <= 0 < scanTime and not self.uavSeeker.IsScanning():
            self.uavSeeker.StartScan()
            self.scanControlData['currentScanTime'] -= 0.1

        elif self.uavSeeker.IsScanning() and scanTime > 0:
            self.scanControlData['currentScanTime'] -= 0.1

        elif self.uavSeeker.IsScanning() and scanTime <= 0:
            self.uavSeeker.StopScan()

    def _OnUpdateUI(self):
        if self.uavSeeker is None:
            return

        wx.CallAfter(self.statusView.SetAltitude, self.uavSeeker.GetAltitude())
        wx.CallAfter(self.statusView.SetHeading, self.uavSeeker.GetHeading())

        self._UpdateCompass()

    def _UpdateCompass(self):
        if self.uavSeeker is None:
            return

        def CalcExpectedAngle():
            try:
                angle = self.scanControlData['scanStartAngle'] + \
                        self.scanControlData['currentScanTime'] / self.scanControlData['totalScanTime']
                return angle
            except ZeroDivisionError:
                return 0.0

        if self.uavSeeker.IsScanning():
            expAngle = CalcExpectedAngle()
            wx.CallAfter(self.compassView.SetExpectedAngle(angle=expAngle, refresh=False))

        currentHeading = self.uavSeeker.GetHeading()
        wx.CallAfter(self.compassView.SetCurrentAngle(angle=currentHeading))

    def UpdateScanSettings(self, params):
        self.uavSeeker.scanFrequency = params['freq']
        self.uavSeeker.gain = params['gain']
        self.uavSeeker.snrThreshold = params['snr']
        self.uavSeeker.UpdateScanSettings()

    def Show(self):
        self.mainWinView.Maximize()
        self.mainWinView.Show()
        self.updateTimer.start()

    def OnClose(self, evt):
        if self.serial:
            self.serial.Dispose()
        self.exitUpdateThread.set()
        if self.uavSeeker:
            self.uavSeeker.Dispose()
        if self.updateTimer.is_alive():
            self.updateTimer.join(timeout=0.1)
        self.mainWinView.Destroy()


class TimerThread(Thread):
    def __init__(self, event, func, interval=0.5):
        super(TimerThread, self).__init__()
        self.stopped = event
        self.interval = interval

        if callable(func):
            self.func = func
        else:
            raise TypeError('Function provided must be callable')

    def run(self):
        while not self.stopped.wait(self.interval):
            if self.func is not None:
                self.func()
