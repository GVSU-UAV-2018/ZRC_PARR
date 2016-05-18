import wx
import logging



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

    def do_layout(self):
        """ Layout the controls that were created by createControls().
            Form.doLayout will raise NotImplementedError because it
            is the responsibility of subclasses to layout the controls """
        raise NotImplementedError

    def set_frequency(self, freq):
        try:
            self.frequencyValue.SetLabel("This is a test")
            #self.frequencyValue.SetLabelText(freq.join(" MHz"))
        except Exception as ex:
            print str(ex)
            raise


    def set_heading(self, angle):
        self.headingValue.SetLabelText(angle.join(" degrees"))

    def set_altitude(self, altitude):
        self.altitudeValue.SetLabelText(altitude.join(" meters"))

    def set_title_font(self, font):
        self.title_label.SetFont(font)

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


