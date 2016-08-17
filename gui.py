import wx
import wx.lib.newevent
from pubsub import pub
#from wx.lib.pubsub import pub
import threading
import time
import logging

SetDetectSettingsEvent, EVT_SET_DETECT_SETTINGS = wx.lib.newevent.NewCommandEvent()

TITLE_FONT = wx.Font(15, style=wx.NORMAL, family=wx.MODERN, weight=wx.BOLD)

class SystemInfoViewBase(wx.Panel):
    """ Base form class for System Info controls that
        creates a bunch of controls and handlers for callbacks.
        Doing the layout of the controls is the responsibility
        of subclasses (by means of doLayout() method """

    def __init__(self, *args, **kwargs):
        super(SystemInfoViewBase, self).__init__(*args, **kwargs)
        pub.subscribe(self.update_labels, 'sys_info.update')
        self.create_controls()
        self.bind_events()
        self.do_layout()
        self.SetBackgroundColour('#FFFFD6')

    def create_controls(self):
        """ Create all controls necessary for the form """
        self.title_label = wx.StaticText(parent=self, label='SYSTEM INFO', style=wx.ALIGN_TOP)
        self.altitude_label = wx.StaticText(parent=self, label='Altitude:')
        self.altitude_value = wx.StaticText(parent=self, label='meters')
        self.heading_label = wx.StaticText(parent=self, label='Current Heading:')
        self.heading_value = wx.StaticText(parent=self, label='degrees')
        self.frequency_label = wx.StaticText(parent=self, label='Scan Frequency:')
        self.frequency_value = wx.StaticText(parent=self, label='MHz')

    def bind_events(self):
        """ Bind events for the control """

    def do_layout(self):
        """ Layout the controls that were created by createControls().
            Form.doLayout will raise NotImplementedError because it
            is the responsibility of subclasses to layout the controls """
        raise NotImplementedError

    def set_title_font(self, font):
        self.title_label.SetFont(font)

    def update_labels(self, info=None):
        """
        Set the altitude, bearing, and frequency if provided
        a dictionary of info. Then update the labels on the
        UI thread.
        :param info: dictionary of system info parameters
        :return: No return value
        """
        if info is not None:
            self.altitude = info['altitude']
            self.bearing = info['bearing']
            self.frequency = info['frequency']

        wx.CallAfter(self._set_labels)

    def _set_labels(self):
        """
        Set the labels for altitude, bearing, and frequency.
        Should only be called from the UI thread
        :return: No return value
        """
        self.altitude_value.SetLabel(str(self.altitude) + ' meters')
        self.heading_value.SetLabel(str(self.bearing) + ' degrees')
        self.frequency_value.SetLabel(str(self.frequency) + ' MHz')


class SystemInfoPanel(SystemInfoViewBase):
    def __init__(self, *args, **kwargs):
        super(SystemInfoPanel, self).__init__(*args, **kwargs)

    def do_layout(self):
        """ Define the layout of the controls """
        # Top level box sizer for control
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(self.title_label, 0, wx.TOP | wx.LEFT, border=20)

        control_grid = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)
        flags = wx.EXPAND | wx.ALL
        control_grid.AddMany([
            (self.altitude_label, 0, flags),
            (self.altitude_value, 0, flags),
            (self.heading_label, 0, flags),
            (self.heading_value, 0, flags),
            (self.frequency_label, 0, flags),
            (self.frequency_value, 0, flags)])
        top_sizer.Add(control_grid, 0, wx.ALL | wx.EXPAND, border=20)
        self.SetSizerAndFit(top_sizer)


class DetectSettingViewBase(wx.Panel):
    def __init__(self, settings=None, *args, **kwargs):
        super(DetectSettingViewBase, self).__init__(*args, **kwargs)
        # Check if settings dictionary was passed from outside of the class
        if settings is not None:
            self.settings = settings
        else:
            self.settings = {'frequency': 0, 'gain': 1, 'snr': 1}

        self.parent = kwargs['parent']
        self.create_controls()
        self.bind_events()
        self.do_layout()
        self.SetBackgroundColour('#C2D1B2')

    def create_controls(self):
        self.title_label = wx.StaticText(parent=self, label='DETECTION SETTINGS', style=wx.ALIGN_TOP)
        self.frequency_label = wx.StaticText(parent=self, label='Set Frequency (MHz):')
        self.frequency_input = wx.TextCtrl(parent=self)
        self.gain_label = wx.StaticText(parent=self, label='Set Gain (dB):')
        self.gain_input = wx.TextCtrl(parent=self)
        self.snr_label = wx.StaticText(parent=self, label='Set SNR:')
        self.snr_input = wx.TextCtrl(parent=self)
        self.submit_button = wx.Button(parent=self, id=wx.ID_ANY, label="Submit")

    def bind_events(self):
        self.submit_button.Bind(wx.EVT_BUTTON, self.submit_handler)

    def do_layout(self):
        raise NotImplementedError

    def set_title_font(self, font):
        self.title_label.SetFont(font)

    def submit_handler(self, evt):
        self.set_settings()

    '''
    Set the frequency, gain, and signal to noise ratio in dictionary from the
    input boxes. Returns False and aborts entire set if any input failed to
    parse into float.
    '''
    def set_settings(self):
        try:
            freq = float(self.frequency_input.GetValue())
            gain = float(self.gain_input.GetValue())
            snr = float(self.snr_input.GetValue())
        except ValueError as ex:
            print 'Failed to convert a setting to float.\n%s' % ex.message
            return False

        self.settings['frequency'] = freq
        self.settings['gain'] = gain
        self.settings['snr'] = snr
        # Create new set event and post it to parent
        set_evt = SetDetectSettingsEvent(id=wx.ID_ANY, settings=self.settings)
        wx.PostEvent(self.parent, set_evt)
        print 'Posted set settings event'
        return True


class DetectSettingsPanel(DetectSettingViewBase):
    def __init__(self, *args, **kwargs):
        super(DetectSettingsPanel, self).__init__(*args, **kwargs)

    def do_layout(self):
        # top level container
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(item=self.title_label, proportion=0, flag=wx.TOP | wx.LEFT, border=20)

        # grid holding input controls and their labels
        label_grid = wx.GridSizer(rows=3, cols=1, vgap=5, hgap=5)
        input_grid = wx.GridSizer(rows=3, cols=1, vgap=5, hgap=5)
        container_grid = wx.GridSizer(rows=1, cols=3, vgap=5, hgap=5)

        # Adding wx.Sizer items (item, proportion, flag, border)
        flags = wx.EXPAND | wx.ALL
        proportion = 0
        lbl_border = 15
        label_grid.AddMany(items=[(self.frequency_label, proportion, flags, lbl_border),
                                  (self.gain_label, proportion, flags, lbl_border),
                                  (self.snr_label, proportion, flags, lbl_border)])

        border = 5
        input_grid.AddMany(items=[(self.frequency_input, proportion, flags, border),
                                  (self.gain_input, proportion, flags, border),
                                  (self.snr_input, proportion, flags, border)])
        container_grid.AddMany(items=[(label_grid, proportion, flags),
                                      (input_grid, proportion, flags),
                                      (self.submit_button, proportion, flags)])

        # outer container holding input and submit button
        top_sizer.Add(container_grid, proportion, wx.ALL, border)
        self.SetSizer(top_sizer)


class MainView(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainView, self).__init__(*args, **kwargs)
        # Create background panel
        self.background = wx.Panel(self)
        self.background.SetBackgroundColour('#4f5049')

        # Create menu bar and its menu items
        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()

        # Create tab control which holds the majority of application content
        self.tab_view = wx.Notebook(parent=self,id=wx.ID_ANY, style=wx.BK_DEFAULT)
        # Create live scanning main page
        self.page1 = ScanTabPanel(parent=self.tab_view, id=wx.ID_ANY)
        self.tab_view.AddPage(self.page1)

        self.do_layout()

    def create_controls(self):
        self.background = wx.Panel(self)

    def bind_events(self):
        pass

    def do_layout(self):
        # Add the exit button to the applications file menu
        app_exit = self.file_menu.Append(id=wx.ID_EXIT, text='Exit', help='Exit Application')
        self.file_menu.Append(app_exit)
        self.Bind(event=wx.EVT_MENU, handler=self.on_exit, source=app_exit)

        self.menu_bar.Append(self.file_menu, '&File')

    def update(self):
        pass


class ScanTabPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanTabPanel, self).__init__(*args, **kwargs)

        outer_horz_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create system info panel
        self.sys_info_panel = SystemInfoPanel(parent=self, style=wx.SUNKEN_BORDER)
        self.sys_info_panel.set_title_font(TITLE_FONT)
        left_sizer.Add(self.sys_info_panel)

        # Create detection settings input control
        self.detect_settings_panel = DetectSettingsPanel(parent=self)
        self.detect_settings_panel.set_title_font(TITLE_FONT)
        left_sizer.Add(self.detect_settings_panel)

        self.scan_control_panel = ScanControlPanel(parent=self)
        left_sizer.Add(self.scan_control_panel)

        outer_horz_sizer.Add(item=left_sizer, proportion=1, flag=wx.EXPANDD | wx.ALL | wx.CENTER)


class ScanControlPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanControlPanel, self).__init__(*args, **kwargs)

        self.SetBackgroundColour('#FFFFD6')
        # Create labels and text controls
        title_label = wx.StaticText(parent=self, id=wx.ID_ANY, label='SCAN SETTINGS', style=wx.ALIGN_TOP)
        title_label.SetFont(TITLE_FONT)

        timer_label = wx.StaticText(parent=self, label='Count Down:')
        timer_txt_ctrl = wx.TextCtrl(parent=self)
        timer_txt_ctrl.SetValue(0)

        scan_label = wx.StaticText(parent=self, label='Scan Timer:')
        scan_txt_ctrl = wx.TextCtrl(parent=self)
        scan_txt_ctrl.SetValue(0)

        # Create buttons and timer
        self.timer = wx.Timer(self)
        self.submit_btn = wx.Button(parent=self, id=wx.ID_ANY, label='Submit')
        self.start_btn = wx.Button(parent=self, id=wx.ID_ANY, label='Start')
        # Bind button and timer
        self.Bind(event=wx.EVT_TIMER, handler=self.on_timer_tick, source=self.timer)
        self.submit_btn.Bind(event=wx.EVT_BUTTON, handler=self.on_submit)
        self.start_btn.Bind(event=wx.EVT_BUTTON, handler=self.on_start)

        # Arranging Controls
        inner_sizer = wx.GridSizer(rows=5, cols=1, vgap=5, hgap=5)
        outer_sizer = wx.GridSizer(rows=1, cols=2, vgap=5, hgap=5)

        for item, prop, flag, border in \
            [(self.start_btn, 0, wx.EXPAND | wx.ALL, 5),
             (self.inner_sizer, 0, wx.EXPAND | wx.ALL, 5)]:
            outer_sizer.Add(item, prop, flag, border)

        for item, prop, flag, border in \
            [(timer_label, 1, wx.ALIGN_BOTTOM, 0),
             (timer_txt_ctrl, 1, wx.EXPAND, 0),
             (scan_label, 1, wx.EXPAND, 0),
             (scan_txt_ctrl, 1, wx.EXPAND, 0),
             (self.submit_btn, 1, wx.EXPAND, 0)]:
            inner_sizer.Add(item, prop, flag, border)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(item=title_label, proportion=0, flag=wx.TOP | wx.LEFT, border=20)
        panel_sizer.Add(item=outer_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=5 )
        self.SetSizer(panel_sizer)


