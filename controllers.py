import gui

class MainPageController(object):
    def __init__(self):
        self.altitude = 0.0
        self.heading = 0.0
        self.scan_frequency = 0.0
        self.gain = 0.0
        self.snr = 0.0

        self.view = gui.MainView()
        self.child = ScanTabController(parent=self.view)



class ScanTabController(object):
    def __init__(self, parent_view, *args, **kwargs):
        self.view = gui.ScanTabPanel(parent=parent_view, id=wx.ID_ANY)



