# -*- coding: utf-8 -*-

import zrc_core

import wx
from wx.lib.masked import NumCtrl
from pubsub import  pub
import wx.lib.newevent
import sys, os
import json
import math
import threading
import time
import logging
import controllers
import string

COLORS = {'normalText': '#000000',
          'lightText': '#728CB0',
          'panelPrimary': '#2196F3',
          'panelSecondary': '#496892',
          'panelTertiary': '#64B5F6',
          'windowBg': '#1A2C45'}

LOCAL_ENCODING = 'utf-8'
DEGREE_SIGN = u'\xb0'.encode(LOCAL_ENCODING)

DIRECTORY = os.path.dirname(__file__)

ALPHA_ONLY = 1
INT_ONLY = 2
FLOAT_ONLY = 3


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.SetTitle('UAV Radio Direction Finder')
        self.childPanel = wx.Panel(parent=self)
        self.childPanel.SetBackgroundColour(COLORS['windowBg'])

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()

        self.exitMenuItem = wx.MenuItem(parentMenu=self.fileMenu,
                                        id=wx.ID_EXIT,
                                        text='Shutdown')

        self.fileMenu.AppendItem(self.exitMenuItem)

        self.menuBar.Append(menu=self.fileMenu,
                            title='&File')

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.childPanel.SetSizer(self.mainSizer)

        self.settingsDisplayPanel = SettingsDisplayPanel(parent=self.childPanel)
        self.scanCirclePanel = ScanCirclePanel(parent=self.childPanel)
        self.statusDisplayPanel = StatusDisplayPanel(parent=self.childPanel)

        self.topSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.topSizer.Add(
            item=self.settingsDisplayPanel,
            proportion=3,
            flag=wx.RIGHT | wx.EXPAND,
            border=3)
        self.topSizer.Add(
            item=self.scanCirclePanel,
            proportion=5,
            flag=wx.EXPAND)
        self.topSizer.Add(
            item=self.statusDisplayPanel,
            proportion=3,
            flag=wx.LEFT | wx.EXPAND,
            border=3)
        self.mainSizer.Add(
            item=self.topSizer,
            proportion=10,
            flag=wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND,
            border=3)

        self.scanSettingsPanel = ScanSettingsPanel(parent=self.childPanel)

        self.scanResultsPanel = ScanResultsPanel(parent=self.childPanel)

        self.scanStartPanel = ScanStartPanel(parent=self.childPanel)

        self.bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomSizer.Add(
            item=self.scanSettingsPanel,
            proportion=3,
            flag=wx.RIGHT | wx.EXPAND,
            border=3)
        self.bottomSizer.Add(
            item=self.scanResultsPanel,
            proportion=5,
            flag=wx.EXPAND)
        self.bottomSizer.Add(
            item=self.scanStartPanel,
            proportion=3,
            flag=wx.LEFT | wx.EXPAND,
            border=3)

        self.mainSizer.Add(
            item=self.bottomSizer,
            proportion=5,
            flag=wx.ALL | wx.EXPAND,
            border=3)

    def OnClose(self, evt):
        self.Close()


class SettingsDisplayPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(SettingsDisplayPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        self.scanFreqDisp = DisplayControl(
            parent=self,
            label='Scan Frequency',
            unit=' MHz')
        self.scanFreqDisp.SetValue(150.245)

        self.gainDisp = DisplayControl(
            parent=self,
            label='Receiver Gain',
            unit=' dB')
        self.gainDisp.SetValue(5.00)

        self.snrDisp = DisplayControl(
            parent=self,
            label='SNR Threshold')
        self.snrDisp.SetValue(10)

        settingsSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.SetSizer(settingsSizer)
        settingsSizer.Add(
            item=self.scanFreqDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)
        settingsSizer.Add(
            item=self.gainDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)
        settingsSizer.Add(
            item=self.snrDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)

    def update(self, freq, gain, snr):
        self.scanFreqDisp.SetValue(freq)
        self.gainDisp.SetValue(gain)
        self.snrDisp.SetValue(snr)


class ScanCirclePanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanCirclePanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelSecondary'])


class StatusDisplayPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(StatusDisplayPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        self._altDisp = DisplayControl(
            parent=self,
            label='Altitude',
            unit=' meters')
        self._altDisp.SetValue(125.60)

        self._headingDisp = DisplayControl(
            parent=self,
            label='UAV Heading',
            unit=DEGREE_SIGN)
        self._headingDisp.SetValue(128)

        self._scanDirDisp = DisplayControl(
            parent=self,
            label='Target Heading',
            unit=DEGREE_SIGN)
        self._scanDirDisp.SetValue(320)

        self._scanTimeDisp = DisplayControl(
            parent=self,
            label='Scanning Time')
        self._scanTimeDisp.SetValue('00:00')

        statusSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.SetSizer(statusSizer)
        statusSizer.Add(
            item=self._altDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)
        statusSizer.Add(
            item=self._headingDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)
        statusSizer.Add(
            item=self._scanDirDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)
        statusSizer.Add(
            item=self._scanTimeDisp,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=2)

    def SetAltitude(self, altitude):
        alt = '{0:.2f}'.format(altitude)
        self._altDisp.SetValue(alt)

    def SetHeading(self, heading):
        hd = '{0:.2f}'.format(heading)
        self._headingDisp.SetValue(hd)

    def SetScanDirection(self, direction):
        dir = '{0:.2f}'.format(direction)
        self._scanDirDisp.SetValue(dir)

    def SetScanTime(self, time):
        self._scanTimeDisp.SetValue(time)


class ScanSettingsPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanSettingsPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        self.freqCtrl = FloatTextControl(parent=self, label='Scan Frequency (MHz)')
        #self.freqCtrl.numCtrl.SetFractionWidth(3)
        self.freqCtrl.numCtrl.SetMaxSize((100,100))
        self.gainCtrl = FloatTextControl(parent=self, label='Receiver Gain (dB)')
        #self.gainCtrl.numCtrl.SetFractionWidth(1)
       # self.gainCtrl.numCtrl.SetAllowNegative(True)
        self.snrCtrl = FloatTextControl(parent=self, label='SNR Threshold')
       # self.snrCtrl.numCtrl.SetFractionWidth(1)

        self.submitBtn = wx.Button(parent=self, id=wx.ID_ANY, label='Submit')
        self.submitBtn.SetFont(wx.Font(pointSize=20, family=wx.MODERN, style=wx.NORMAL, weight=wx.NORMAL))
        self.submitBtn.SetForegroundColour(COLORS['normalText'])
        self.submitBtn.SetBackgroundColour(COLORS['panelTertiary'])
        self.submitBtn.Bind(event=wx.EVT_BUTTON, handler=self.OnSubmit)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        btnSizer.Add(self.submitBtn, proportion=1, flag=wx.EXPAND)

        sizer.Add(item=self.freqCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.gainCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.snrCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.AddSpacer(item=(0, 0), proportion=2, flag=wx.EXPAND)
        sizer.Add(item=btnSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

    def ValidInput(self):
        for ctrl in [self.freqCtrl, self.gainCtrl, self.snrCtrl]:
            if ctrl.numCtrl.GetValidator().Validate(ctrl.numCtrl) is False:
                return False

        return True

    def OnSubmit(self, event):
        if self.ValidInput() is False:
            return

        freq = self.freqCtrl.GetValue() * 1000000
        gain = self.gainCtrl.GetValue()
        snr = self.snrCtrl.GetValue()
        params = {'freq': freq,
                  'gain': gain,
                  'snr': snr}
        pub.sendMessage('scanSettings.Submit', params=params)


class ScanResultsPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanResultsPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        self.directionDisplay = DisplayControl(parent=self, label='Direction', unit=DEGREE_SIGN)
        self.directionDisplay.SetValue(140.0)
        self.powerDisplay = DisplayControl(parent=self, label='Power', unit='dB')
        self.powerDisplay.SetValue(13.0)
        self.freqDisplay = DisplayControl(parent=self, label='Frequency', unit='MHz')
        self.freqDisplay.SetValue(153.405)

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(item=self.directionDisplay, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(item=self.powerDisplay, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        leftSizer.Add(item=self.freqDisplay, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(item=leftSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.ALL | wx.EXPAND, border=5)


class ScanStartPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanStartPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        self.countdownCtrl = FloatTextControl(parent=self, label='Countdown Time (s)')
        self.scanTimeCtrl = FloatTextControl(parent=self, label='Scanning Time (s)')

        self.startBtn = wx.Button(parent=self, id=wx.ID_ANY, label='Start')
        self.startBtn.SetFont(wx.Font(pointSize=20, family=wx.MODERN, style=wx.NORMAL, weight=wx.NORMAL))
        self.startBtn.SetForegroundColour(COLORS['normalText'])
        self.startBtn.SetBackgroundColour(COLORS['panelTertiary'])
        self.startBtn.Bind(event=wx.EVT_BUTTON, handler=self.OnStart)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        btnSizer.Add(item=self.startBtn, proportion=0, flag=wx.EXPAND)

        sizer.Add(item=self.countdownCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.scanTimeCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        sizer.Add(item=btnSizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

    def OnStart(self, evt):
        countdown = self.countdownCtrl.GetValue()
        scanTime = self.scanTimeCtrl.GetValue()
        params = {'countdown': countdown,
                  'scanTime': scanTime}
        pub.sendMessage('scanStart.Start', params=params)


class TextValidator(wx.PyValidator):
    def __init__(self, flag=None, *args, **kwargs):
        super(TextValidator, self).__init__(*args, **kwargs)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return TextValidator(self.flag)

    def Validate(self, win):
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()

        def invalid():
            textCtrl.SetBackgroundColour('pink')
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False

        def valid():
            textCtrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)
            )
            textCtrl.Refresh()
            return True

        if len(text) == 0:
            return invalid()

        elif self.flag == FLOAT_ONLY:
            try:
                value = float(text)
            except ValueError:
                return invalid()

        elif self.flag == INT_ONLY:
            try:
                value = int(text)
            except ValueError:
                return invalid()

        elif self.flag == ALPHA_ONLY:
            for x in text:
                if x not in string.letters:
                    return invalid()

        return valid()

    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if self.flag == ALPHA_ONLY and chr(key) in string.letters:
            event.Skip()
            return

        if self.flag == INT_ONLY or self.flag == FLOAT_ONLY and chr(key) in string.digits:
            event.Skip()
            return

        if self.flag == FLOAT_ONLY \
                and (key == 46):
            event.Skip()
            return

        if not wx.Validator_IsSilient():
            wx.Bell()

        return

class FloatTextControl(wx.BoxSizer):
    def __init__(self, parent, label):
        super(FloatTextControl, self).__init__(wx.HORIZONTAL)

        font = wx.Font(
            pointSize=22,
            family=wx.DECORATIVE,
            style=wx.NORMAL,
            weight=wx.BOLD)

        self.labelText = wx.StaticText(parent=parent, label=label)
        self.labelText.SetFont(font)
        self.labelText.SetForegroundColour('#000000')

        self.numCtrl = wx.TextCtrl(parent=parent, id=wx.ID_ANY, style=wx.TE_RIGHT, validator=TextValidator(FLOAT_ONLY))
        self.numCtrl.SetFont(font)
        self.numCtrl.SetForegroundColour(COLORS['normalText'])
        self.numCtrl.SetMinSize((150, -1))

        self.Add(item=self.labelText, proportion=1, flag=wx.ALL | wx.EXPAND, border=3)
        self.AddSpacer(item=(0, 0), proportion=0, flag=wx.EXPAND)
        self.Add(item=self.numCtrl, proportion=0, flag=wx.ALL | wx.ALIGN_RIGHT, border=3)

    def GetValue(self):
        try:
            val = float(self.numCtrl.GetValue())
        except ValueError:
            return None

        return val



class DisplayControl(wx.Panel):
    def __init__(self, label, unit=None, *args, **kwargs):
        super(DisplayControl, self).__init__(*args, **kwargs)
        font = wx.Font(
            pointSize=32,
            family=wx.DECORATIVE,
            style=wx.NORMAL,
            weight=wx.BOLD)

        self.SetBackgroundColour(COLORS['panelTertiary'])
        self.SetForegroundColour(COLORS['normalText'])
        self.unitText = unit
        self.labelCtrl = wx.StaticText(parent=self, label=label)
        self.labelCtrl.SetFont(font)

        self.propertyCtrl = wx.StaticText(parent=self)
        self.propertyCtrl.SetFont(wx.Font(
            pointSize=22,
            family=wx.MODERN,
            style=wx.NORMAL,
            weight=wx.NORMAL))

        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        sizer.Add(
            item=self.labelCtrl,
            proportion=0,
            flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL,
            border=5)
        sizer.Add(
            item=self.propertyCtrl,
            proportion=0,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL,
            border=5)

        self.SetSizer(sizer)

    def SetLabel(self, text):
        self.labelCtrl.SetLabel(text)

    def SetValue(self, value):
        disp_str = str(value)

        if self.unitText is not None:
            disp_str += str(self.unitText)

        self.propertyCtrl.SetLabel(disp_str)


if __name__ == '__main__':
    try:
        try:
            with open('config.json') as data_file:
                data = json.load(data_file)

        except IOError:
            data = {'port': '/dev/ttyUSB0',
                     'baud': 57600,
                     'timeout': 0.1}


        app = wx.App()

        mainControl = controllers.MainWindowController(data)
        mainControl.Show()

        app.MainLoop()

        with open('config.json', 'w') as outfile:
            json.dump(data, outfile)

    except Exception as ex:
        print ex
