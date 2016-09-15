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

        pub.subscribe(self.UpdateScanSettings, 'scanSettings.Submit')

        self.serial = None
        self.uavSeeker = None
        try:
            self.serial = SerialInterface(config)
            self.uavSeeker = UAVRadioFinder(self.serial)
        except SerialException as ex:
            msgDlg = wx.MessageBox(parent=self.mainWinView, message='Failed to connect to serial port.')

        self.stopTimerFlag = Event()
        self.updateTimer = TimerThread(event=self.stopTimerFlag, func=self.OnTimerTick, interval=0.1)

    def Show(self):
        self.mainWinView.Maximize()
        self.mainWinView.Show()
        if self.serial:
            self.updateTimer.start()

    def OnTimerTick(self):
        if self.uavSeeker is None:
            return
        wx.CallAfter(self.statusView.SetAltitude, self.uavSeeker.GetAltitude())
        wx.CallAfter(self.statusView.SetHeading, self.uavSeeker.GetHeading())

    def UpdateScanSettings(self, params):
        self.uavSeeker.scanFrequency = params['freq']
        self.uavSeeker.gain = params['gain']
        self.uavSeeker.snrThreshold = params['snr']
        self.uavSeeker.UpdateScanSettings()

    def OnClose(self, evt):
        if self.serial:
            self.serial.Dispose()
        self.stopTimerFlag.set()
        if self.uavSeeker:
            self.uavSeeker.Dispose()
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
