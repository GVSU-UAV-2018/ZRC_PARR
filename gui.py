import wx
import wx.lib.newevent
import threading
import time
import logging




UpdateSysInfoEvent, EVT_UPDATE_SYSINFO = wx.lib.newevent.NewEvent()

class SysInfoForm(wx.Panel):
    """ Base form class for System Info controls that
        creates a bunch of conrols and handlers for callbacks.
        Doing the layout of the controls is the responsibility
        of subclasses (by means of doLayout() method """

    def __init__(self, *args, **kwargs):
        super(SysInfoForm, self).__init__(*args, **kwargs)
        self.altitude = 0
        self.heading = 0
        self.frequency = 0
        self.create_controls()
        self.bind_events()
        self.do_layout()
        self.SetBackgroundColour('#FFFFD6')
        update_thread = threading.Thread(target=self.tick_event)
        #update_thread = threading.Thread(target=self.update_on_tick)
        update_thread.setDaemon(True)
        update_thread.start()

    def create_controls(self):
        """ Create all controls necessary for the form """
        self.title_label = wx.StaticText(parent=self, label='SYSTEM INFO', style=wx.ALIGN_TOP)
        self.altitudeLabel = wx.StaticText(parent=self, label='Altitude:')
        self.altitudeValue = wx.StaticText(parent=self, label='meters')
        self.headingLabel = wx.StaticText(parent=self, label='Current Heading:')
        self.headingValue = wx.StaticText(parent=self, label='degrees')
        self.frequencyLabel = wx.StaticText(parent=self, label='Scan Frequency:')
        self.frequencyValue = wx.StaticText(parent=self, label='MHz')

    def bind_events(self):
        """ Bind events for the control """
        self.Bind(EVT_UPDATE_SYSINFO, self.update_on_tick)

    def do_layout(self):
        """ Layout the controls that were created by createControls().
            Form.doLayout will raise NotImplementedError because it
            is the responsibility of subclasses to layout the controls """
        raise NotImplementedError

    def set_title_font(self, font):
        self.title_label.SetFont(font)

    def update_on_tick(self):
        print 'Updating Sys Info'
        self.altitudeValue.SetLabel(str(self.altitude) + ' meters')
        self.headingValue.SetLabel(str(self.heading) + ' degrees')
        self.frequencyValue.SetLabel(str(self.frequency) + ' MHz')

    def tick_event(self):
        while True:
            wx.CallAfter(self.update_on_tick)
            time.sleep(0.3)


class SystemInfoCtrl(SysInfoForm):

    def do_layout(self):
        """ Define the layout of the controls """
        # Top level box sizer for control
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(self.title_label, 0, wx.TOP | wx.LEFT, border=20)

        control_grid = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)
        flags = wx.EXPAND | wx.ALL
        control_grid.AddMany([
            (self.altitudeLabel, 0, flags),
            (self.altitudeValue, 0, flags),
            (self.headingLabel, 0, flags),
            (self.headingValue, 0, flags),
            (self.frequencyLabel, 0, flags),
            (self.frequencyValue, 0, flags)])
        top_sizer.Add(control_grid, 0, wx.ALL | wx.EXPAND, border=20)
        self.SetSizerAndFit(top_sizer)



