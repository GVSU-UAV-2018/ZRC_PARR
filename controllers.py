from gstation import MainWindow
from zrc_core import SerialInterface, MessageString, MessageType
from rdfinder import UAVRadioFinder
from threading import Thread, Event
from pubsub import pub
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

        self.serial = SerialInterface(config)

        self.rdfinder = UAVRadioFinder(self.serial)

        self.stopTimerFlag = Event()
        self.updateTimer = TimerThread(event=self.stopTimerFlag, func=self.OnTimerTick, interval=0.1)

    def Show(self):
        self.mainWinView.Maximize()
        self.mainWinView.Show()
        self.serial.start()
        self.updateTimer.start()

    def OnTimerTick(self):
        wx.CallAfter(self.statusView.SetAltitude, self.rdfinder.GetAltitude())
        wx.CallAfter(self.statusView.SetHeading, self.rdfinder.GetHeading())

    def UpdateScanSettings(self, params):
        self.rdfinder.scanFrequency = params['freq']
        self.rdfinder.gain = params['gain']
        self.rdfinder.snrThreshold = params['snr']
        self.rdfinder.UpdateScanSettings()

    def OnClose(self, evt):
        self.serial.close()
        self.stopTimerFlag.set()
        self.rdfinder.Close()
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
