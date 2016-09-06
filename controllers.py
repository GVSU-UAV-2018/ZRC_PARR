from gstation import MainWindow
from zrc_core import SerialInterface, MessageString, MessageType
from rdfinder import UAVRadioFinder
from threading import Thread, Event


class MainWindowController(object):
    def __init__(self, config):
        self.mainWinView = MainWindow(parent=None)

        self.statusView = self.mainWinView.statusDisplayPanel

        self.serial = SerialInterface(config)

        self.rdfinder = UAVRadioFinder(self.serial)

        self.timerControl = Event()
        self.updateTimer = TimerThread(event=self.timerControl, func=self.OnTimerTick, interval=0.5)

    def Show(self):
        self.mainWinView.Maximize()
        self.mainWinView.Show()

    def OnTimerTick(self):
        self.statusView.SetAltitude(self.rdfinder.GetAltitude())
        self.statusView.SetHeading(self.rdfinder.GetHeading())


class TimerThread(Thread):
    def __init__(self, event, func, interval=0.5):
        super(TimerThread, self).__init__(self)
        self.stopped = event
        self.interval = interval

        if callable(func):
            self.func = func
        else:
            raise TypeError('Function provided must be callable')

    def run(self):
        while not self.stopped.wait(self.interval):
            self.func()
