import wx
import wx.lib.newevent
from pubsub import pub
import math
# from wx.lib.pubsub import pub
import threading
import time
import logging

SetDetectSettingsEvent, EVT_SET_DETECT_SETTINGS = wx.lib.newevent.NewCommandEvent()



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


class ScanControlPanel(wx.Panel):
    def __init__(self, scan_data, *args, **kwargs):
        super(ScanControlPanel, self).__init__(*args, **kwargs)
        TITLE_FONT = wx.Font(15, style=wx.NORMAL, family=wx.MODERN, weight=wx.BOLD)
        self.scan_data = scan_data

        self.SetBackgroundColour('#FFFFD6')
        # Create labels and text controls
        title_label = wx.StaticText(parent=self, id=wx.ID_ANY, label='SCAN SETTINGS', style=wx.ALIGN_TOP)
        title_label.SetFont(TITLE_FONT)

        timer_label = wx.StaticText(parent=self, label='Count Down:')
        self.timer_txt_ctrl = wx.TextCtrl(parent=self)
        self.timer_txt_ctrl.SetValue(str(self.scan_data['countdown_time']))

        scan_label = wx.StaticText(parent=self, label='Scan Timer:')
        self.scan_txt_ctrl = wx.TextCtrl(parent=self)
        self.scan_txt_ctrl.SetValue(str(self.scan_data['scan_time']))

        self.timer = wx.Timer(self)
        self.Bind(event=wx.EVT_TIMER, handler=self.on_timer_tick, source=self.timer)

        self.timer_toggle_btn = wx.Button(parent=self, id=wx.ID_ANY, label='Start')
        self.timer_toggle_btn.Bind(event=wx.EVT_BUTTON, handler=self.on_timer_toggle)

        self.submit_btn = wx.Button(parent=self, id=wx.ID_ANY, label='Submit')
        self.submit_btn.Bind(event=wx.EVT_BUTTON, handler=self.on_submit)
        # Arranging Controls
        inner_grid = wx.GridSizer(rows=3, cols=1, vgap=5, hgap=5)
        outer_grid = wx.GridSizer(rows=1, cols=2, vgap=5, hgap=5)

        for item, prop, flag, border in \
                [(inner_grid, 0, wx.ALL, 5),
                 (self.timer_toggle_btn, 0, wx.EXPAND | wx.ALL, 5)]:
            outer_grid.Add(item, prop, flag, border)

        timer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        timer_sizer.Add(item=timer_label,
                        proportion=0,
                        flag=wx.EXPAND | wx.RIGHT,
                        border=5)
        timer_sizer.Add(item=self.timer_txt_ctrl,
                        proportion=1)

        scan_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scan_sizer.Add(item=scan_label,
                       proportion=1,
                       flag=wx.EXPAND)
        scan_sizer.Add(item=self.scan_txt_ctrl,
                       proportion=2,
                       flag=wx.EXPAND)

        for item, prop, flag, border in \
            [(timer_sizer, 0, wx.EXPAND, 0),
             (scan_sizer, 0, wx.EXPAND, 0),
             (self.submit_btn, 0, wx.CENTER, 0)]:
            inner_grid.Add(item, prop, flag, border)

        # for item, prop, flag, border in \
        #         [(timer_label, 1, wx.ALIGN_BOTTOM, 0),
        #          (self.timer_txt_ctrl, 1, wx.SHAPED | wx.ALL, 0),
        #          (scan_label, 1, wx.ALIGN_BOTTOM, 0),
        #          (self.scan_txt_ctrl, 1, wx.SHAPED, 0),
        #          (self.submit_btn, 1, wx.ALIGN_BOTTOM | wx.SHAPED, 0)]:
        #     inner_grid.Add(item, prop, flag, border)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(item=title_label, proportion=0, flag=wx.TOP | wx.LEFT, border=20)
        panel_sizer.Add(item=outer_grid, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(panel_sizer)

    def on_timer_toggle(self, evt):
        countdown_time = self.scan_data['countdown_time']
        scan_time = self.scan_data['scan_time']
        timer_started = self.scan_data['timer_started']

        if timer_started is False:
            self.timer.Start(milliseconds=1000)
            self.timer_toggle_btn.SetLabel('Stop')
        else:
            self.scan_data['scan_time'] = 0.0
            self.scan_data['countdown_time'] = self.scan_data['total_countdown_time']
            self.timer.Stop()
            self.timer_toggle_btn.SetLabel('Start')
            self.Refresh()

    def on_timer_tick(self, evt):
        countdown_time = self.scan_data['countdown_time']
        scan_time = self.scan_data['scan_time']

        if countdown_time <= 0:
            scan_time += 1.0
            if scan_time <= self.scan_data['total_scan_time']:
                self.Refresh(eraseBackgroundd=False)
            else:
                scan_time = 0.0
                countdown_time = self.scan_data['total_countdown_time']
                self.timer.Stop()
                self.timer_toggle_btn.SetLabel('Start')
        else:
            countdown_time -= 1
            self.Refresh(eraseBackground=False)

        self.scan_data['countdown_time'] = countdown_time
        self.scan_data['scan_time'] = scan_time

    def on_submit(self, evt):
        self.scan_data['total_countdown_time'] = int(self.timer_txt_ctrl.GetValue())
        self.scan_data['countdown_time'] = self.scan_data['total_countdown_time']
        self.scan_data['total_scan_time'] = float(self.scan_txt_ctrl.GetValue())
        self.Refresh()


class ScanRotationPanel(wx.Panel):
    def __init__(self, scan_data, *args, **kwargs):
        super(ScanRotationPanel, self).__init__(*args, **kwargs)

        self.scan_data = scan_data
        self.SetBackgroundColour('#E6E6E6')
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self._buffer = wx.EmptyBitmap(width=0, height=0)
        self.scan_circle = wx.BufferedPaintDC(window=self, buffer=self._buffer)

    def on_paint(self, evt):
        # Get size of client window for creating bitmap
        win_size = self.ClientSize
        # Bitmap backing buffer for display
        self._buffer.SetWidth(win_size.width)
        self._buffer.SetHeight(win_size.height)

        width, height = self.GetSize()

        self.scan_circle.BeginDrawing()
        self.scan_circle.Clear()

        center_x = width / 2.0
        center_y = height / 2.0
        radius = (width / 2.0) - 5

        self.scan_circle.SetPen(wx.Pen('green', style=wx.SOLID))
        self.scan_circle.SetBrush(wx.Brush('white', style=wx.SOLID))
        self.scan_circle.DrawText('NORTH', center_x - 20, center_y - radius - 25.0)
        self.scan_circle.DrawText('SOUTH', center_x - 20, center_y + radius + 10.0)

        self.scan_circle.SetPen(wx.Pen('black', style=wx.SOLID))
        self.scan_circle.DrawCircle(center_x, center_y, (radius - 1))

        cur_scan_time = self.scan_data['scan_time']
        total_scan_time = self.scan_data['total_scan_time']
        compass_angle = self.scan_data['compass_angle']

        # Scan angle depends on current scan time
        angle = (cur_scan_time / total_scan_time) * 2 * math.pi
        # How wide the target slice region is
        slice_angle = (15.0 / 360.0) * 2 * math.pi

        # Calculate line end points
        x1 = radius * math.cos(-math.pi / 2.0 + angle - slice_angle / 2.0)
        y1 = radius * math.sin(-math.pi / 2.0 + angle - slice_angle / 2.0)
        # line 2
        x2 = radius * math.cos(-math.pi / 2.0 + angle + slice_angle / 2.0)
        y2 = radius * math.sin(-math.pi / 2.0 + angle + slice_angle / 2.0)
        # fill point
        x3 = radius * math.cos(-math.pi / 2.0 + angle) / 2.0
        y3 = radius * math.sin(-math.pi / 2.0 + angle) / 2.0
        # compass line
        x4 = radius * math.cos(-math.pi / 2.0 + compass_angle * 2 * math.pi / 360)
        y4 = radius * math.sin(-math.pi / 2.0 + compass_angle * 2 * math.pi / 360)

        self.scan_circle.DrawLine(center_x, center_y, center_x + x1, center_y + y1)
        self.scan_circle.DrawLine(center_x, center_y, center_x + x2, center_y + y2)

        self.scan_circle.SetBrush(wx.Brush('#C2D1B2', wx.SOLID))
        self.scan_circle.FloodFill(center_x + x3, center_y + y3, 'black', style=wx.FLOOD_BORDER)

        self.scan_circle.SetPen(wx.Pen('red', style=wx.SOLID))
        self.scan_circle.DrawLine(center_x, center_y, center_x + x4, center_y + y4)

        font = wx.Font(50, style=wx.NORMAL, family=wx.MODERN, weight=wx.BOLD)
        self.scan_circle.SetFont(font)

        countdown_time = self.scan_data['countdown_time']
        if countdown_time > 0:
            self.scan_data['is_scanning'] = False
            self.scan_circle.DrawText(str(countdown_time), center_x - 20, center_y - 35)
        else:
            self.scan_data['is_scanning'] = True
            self.scan_circle.DrawText(str(int(total_scan_time - cur_scan_time)), center_x - 40, center_y - 35)

        self.scan_circle.EndDrawing()


class ScanTabPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanTabPanel, self).__init__(*args, **kwargs)
        TITLE_FONT = wx.Font(15, style=wx.NORMAL, family=wx.MODERN, weight=wx.BOLD)

        self.scan_dict = {'countdown_time': 5,
                          'total_countdown_time': 5,
                           'scan_time': 0.0,
                          'total_scan_time': 40.0,
                           'timer_started': False,
                          'compass_angle': 0.0,
                          'is_scanning': False}

        root_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(root_sizer)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create system info panel
        self.sys_info_panel = SystemInfoPanel(parent=self, style=wx.SUNKEN_BORDER)
        self.sys_info_panel.set_title_font(TITLE_FONT)
        left_sizer.Add(self.sys_info_panel, proportion=1, flag=wx.EXPAND | wx.ALL)

        # Create detection settings input control
        self.detect_settings_panel = DetectSettingsPanel(parent=self, style=wx.SUNKEN_BORDER)
        self.detect_settings_panel.set_title_font(TITLE_FONT)
        left_sizer.Add(self.detect_settings_panel, proportion=1, flag=wx.EXPAND)

        self.scan_control_panel = ScanControlPanel(parent=self, scan_data=self.scan_dict, style=wx.SUNKEN_BORDER)
        left_sizer.Add(self.scan_control_panel, proportion=1, flag=wx.EXPAND)

        root_sizer.Add(item=left_sizer, proportion=1, flag=wx.EXPAND | wx.ALL | wx.CENTER)

        self.scan_display = ScanRotationPanel(parent=self, scan_data=self.scan_dict, style=wx.SUNKEN_BORDER)
        middle_sizer = wx.BoxSizer(wx.VERTICAL)
        middle_sizer.Add(self.scan_display, proportion=1, flag=wx.EXPAND | wx.ALL | wx.CENTER)

        root_sizer.Add(item=middle_sizer, proportion=1, flag=wx.ALL | wx.EXPAND)



class MainView(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainView, self).__init__(*args, **kwargs)

        # Create background panel
        self.background = wx.Panel(self)
        self.background.SetBackgroundColour('#4f5049')

        # Create menu bar and its menu items
        self.menu_bar = wx.MenuBar()

        self.file_menu = wx.Menu()
        app_exit = self.file_menu.Append(id=wx.ID_EXIT, text='Exit', help='Exit Application')
        self.Bind(event=wx.EVT_MENU, handler=self.on_exit, source=app_exit)

        self.menu_bar.Append(self.file_menu, '&File')
        self.SetMenuBar(self.menu_bar)

        # Create tab control which holds the majority of application content
        self.tab_view = wx.Notebook(parent=self.background, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.scan_page = ScanTabPanel(parent=self.tab_view, id=wx.ID_ANY)
        self.tab_view.AddPage(page=self.scan_page, text='Scan')

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(item=self.tab_view, proportion=1, flag=wx.ALL | wx.EXPAND, border=15)
        self.background.SetSizer(main_sizer)

    def update(self):
        pass

    def on_exit(self):
        self.Close()

if __name__ == '__main__':
    try:
        app = wx.App()
        main_view = MainView(parent=None)
        main_view.SetTitle('UAV Radio Direction Finder')
        main_view.Maximize()
        main_view.Show()

        app.MainLoop()
    except Exception as ex:
        print ex
