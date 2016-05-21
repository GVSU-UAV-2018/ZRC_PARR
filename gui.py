import wx
import wx.lib.newevent
import logging

UpdateSysInfoEvent, EVT_UPDATE_SYSINFO = wx.lib.newevent.NewEvent()

class SysInfoForm(wx.Panel):
    """ Base form class for System Info controls that
        creates a bunch of conrols and handlers for callbacks.
        Doing the layout of the controls is the responsibility
        of subclasses (by means of doLayout() method """

    def __init__(self, *args, **kwargs):
        super(SysInfoForm, self).__init__(*args, **kwargs)
        self.create_controls()
        self.bind_events()
        self.do_layout()
        self.SetBackgroundColour('#FFFFD6')

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
        self.Bind(EVT_UPDATE_SYSINFO, self.on_update_sysinfo)

    def do_layout(self):
        """ Layout the controls that were created by createControls().
            Form.doLayout will raise NotImplementedError because it
            is the responsibility of subclasses to layout the controls """
        raise NotImplementedError

    def set_altitude(self, altitude):
        if altitude is not None:
            label = str(altitude) + ' meters'
            self.altitudeValue.SetLabel(label)

    def set_heading(self, angle):
        if angle is not None:
            label = str(angle) + ' degrees'
            self.headingValue.SetLabel(label)

    def set_frequency(self, freq):
        if freq is not None:
            label = str(freq) + ' MHz'
            self.frequencyValue.SetLabel(label)

    def set_title_font(self, font):
        self.title_label.SetFont(font)

    def on_update_sysinfo(self, evt):
        None
        # self.set_altitude(evt.altitude)
        # self.set_heading(evt.heading)
        # self.set_frequency(evt.frequency)


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


