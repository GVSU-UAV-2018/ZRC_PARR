from gstation import MainWindow
from zrc_core import SerialInterface, MessageString, MessageType
from rdfinder import UAVRadioFinder
from threading import Thread, Event
from pubsub import pub
from serial import SerialException
import wx


class MainWindowController(object):
    SCAN_TIMER_INTERVAL = 0.05
    UPDATE_TIMER_INTERVAL = 0.05
    def __init__(self, config):
        self.mainWinView = MainWindow(parent=None)
        self.mainWinView.Bind(event=wx.EVT_MENU,
                              handler=self.OnClose,
                              source=self.mainWinView.exitMenuItem)
        self.mainWinView.Bind(event=wx.EVT_CLOSE,
                              handler=self.OnClose)

        self.settingsView = self.mainWinView.settingsDisplayPanel
        self.statusView = self.mainWinView.statusDisplayPanel
        self.compassView = self.mainWinView.compassPanel
        self.scanControlView = self.mainWinView.scanStartPanel
        self.scanResultsView = self.mainWinView.scanResultsPanel
        self.scanResultsView.waterfall.start(True)


        self.currentCountdown = 5.0
        self.totalCountdown = 5
        self.currentScanTime = 45
        self.totalScanTime = 45
        self.scanStartAngle = 0.0
        self.expectedAngle = 0.0
        self.countdownStarted = False

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
        self.updateTimer = TimerThread(event=self.exitUpdateThread,
                                       func=self._OnUpdateUI,
                                       interval=self.UPDATE_TIMER_INTERVAL)

        self.exitScanThread = Event()
        self.scanTimer = TimerThread(event=self.exitScanThread,
                                     func=self._OnScanTimerTick,
                                     interval=self.SCAN_TIMER_INTERVAL)

        if self.serial:
            self.serial.subscribe(MessageString[MessageType.detection], self._OnDetectionReceived)

    def Initialize(self, serial=None):
        """Use to try to connect/reconnect to serial port later"""
        try:
            self.serial = serial or SerialInterface(self.serialConfig)
            self.uavSeeker = UAVRadioFinder(self.serial)
        except SerialException as ex:
            raise

    def _OnDetectionReceived(self, msg):
        magnitude = msg.magnitude
        heading = msg.heading
        self.scanResultsView.SetResults(heading, magnitude, self.uavSeeker.scanFrequency)

    def _OnScanStart(self, params):
        """
        Event handler for scan start event. Resets timer variables
        and starts scan timer thread.
        :param params: dictionary containing total scan time and countdown time
        :return: None
        """
        self.currentCountdown = params['totalCountdown']
        self.totalCountdown = params['totalCountdown']
        self.totalScanTime = params['totalScanTime']
        self.currentScanTime = params['totalScanTime']
        self.countdownStarted = True

    def _OnScanStop(self):
        self.countdownStarted = False
        self.uavSeeker.StopScan()
        wx.CallAfter(self.compassView.SetExpectedAngleVisibility, visible=False)

    def _OnScanTimerTick(self):
        """
        Event handler for timer tick of scanning timer.
        :return: None
        """
        if self.countdownStarted is not True:
            return

        # Countdown time
        if self.currentCountdown > 0 and self.countdownStarted:
                self.currentCountdown -= self.SCAN_TIMER_INTERVAL
                if(self.currentCountdown < 0):
                    self.currentCountdown = 0
        # Once countdown reaches zero, start the scanning
        elif self.uavSeeker.IsScanning() is False and self.currentScanTime >= 0:
            self.uavSeeker.StartScan()
            wx.CallAfter(self.compassView.SetExpectedAngleVisibility, visible=True)
            self.scanStartAngle = self.uavSeeker.GetHeading()
        # Decrement scanning timer
        elif self.uavSeeker.IsScanning() and self.currentScanTime > 0:
            self.currentScanTime -= self.SCAN_TIMER_INTERVAL
            # If current scan time less than timer resolution, stop the scan
            if self.currentScanTime <= 0:
                self.uavSeeker.StopScan()
                self.currentScanTime = 0.0
                wx.CallAfter(self.compassView.SetExpectedAngle, self.scanStartAngle)
                wx.CallAfter(self.scanControlView.Stop)


        self.UpdateScanDirection()
        wx.CallAfter(self.statusView.SetScanTime, self.currentScanTime)
        wx.CallAfter(self.statusView.SetCountdownTime, self.currentCountdown)

    def _OnUpdateUI(self):

        if self.uavSeeker is None:
            return

        wx.CallAfter(self.statusView.SetAltitude, self.uavSeeker.GetAltitude())
        wx.CallAfter(self.statusView.SetHeading, self.uavSeeker.GetHeading())

        if not self.uavSeeker:
            return

        currentHeading = self.uavSeeker.GetHeading()
        wx.CallAfter(self.compassView.SetCurrentAngle, currentHeading, True)

    def UpdateScanDirection(self):
        if not self.uavSeeker:
            return

        def CalcExpectedAngle():
            try:
                angle = self.scanStartAngle - 360 * (self.currentScanTime / self.totalScanTime)
                return angle
            except ZeroDivisionError:
                return 0.0

        if self.uavSeeker.IsScanning():
            expAngle = CalcExpectedAngle()
            wx.CallAfter(self.compassView.SetExpectedAngle, expAngle, True)

    def UpdateScanSettings(self, params):
        self.settingsView.update(params['freq'] / 1e6, params['gain'], params['snr'])
        self.uavSeeker.scanFrequency = params['freq']
        self.uavSeeker.gain = params['gain']
        self.uavSeeker.snrThreshold = params['snr']
        self.uavSeeker.UpdateScanSettings()

    def Show(self):
        self.mainWinView.Maximize()
        self.mainWinView.Show()
        self.serial.start()
        self.updateTimer.start()
        self.scanTimer.start()
        self.uavSeeker.Start()


    def OnClose(self, evt):

        self.exitUpdateThread.set()
        self.exitScanThread.set()

        if self.updateTimer.is_alive():
            self.updateTimer.join(timeout=0.1)
        if self.scanTimer.is_alive():
            self.scanTimer.join(timeout=0.1)
        if self.uavSeeker:
            self.uavSeeker.Dispose()
        if self.serial:
            self.serial.Dispose()

        self.mainWinView.Destroy()


class TimerThread(Thread):
    def __init__(self, event, func, interval=0.5):
        super(TimerThread, self).__init__()
        self.stopped = event
        self.interval = interval
        self.daemon = True

        if callable(func):
            self.func = func
        else:
            raise TypeError('Function provided must be callable')

    def run(self):
        while not self.stopped.wait(self.interval):
            if self.func is not None:
                self.func()
