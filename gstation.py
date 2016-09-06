# -*- coding: utf-8 -*-

import zrc_core

import wx
import wx.lib.newevent
import sys, os
import json
import math
import threading
import time
import logging
import controllers

COLORS = {'normalText': '#08244A',
          'panelPrimary': '#2E4F7C',
          'panelSecondary': '#496892',
          'panelTertiary': '#728CB0',
          'windowBg': '#1A2C45'}

LOCAL_ENCODING = 'utf-8'
DEGREE_SIGN = u'\xb0'.encode(LOCAL_ENCODING)

DIRECTORY = os.path.dirname(__file__)


class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.SetTitle('UAV Radio Direction Finder')
        self.childPanel = wx.Panel(parent=self)
        self.childPanel.SetBackgroundColour(COLORS['windowBg'])

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()

        exit_menu_item = wx.MenuItem(parentMenu=self.fileMenu,
                                     id=wx.ID_EXIT,
                                     text='Shutdown')

        self.fileMenu.AppendItem(exit_menu_item)
        self.Bind(event=wx.EVT_MENU,
                  handler=self.OnClose,
                  source=exit_menu_item)

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

        self.scanStartPanel = wx.Panel(parent=self.childPanel)
        self.scanStartPanel.SetBackgroundColour(COLORS['panelSecondary'])

        self.scanResultsPanel = wx.Panel(parent=self.childPanel)
        self.scanResultsPanel.SetBackgroundColour(COLORS['panelPrimary'])

        self.bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomSizer.Add(
            item=self.scanSettingsPanel,
            proportion=3,
            flag=wx.RIGHT | wx.EXPAND,
            border=3)
        self.bottomSizer.Add(
            item=self.scanStartPanel,
            proportion=5,
            flag=wx.EXPAND)
        self.bottomSizer.Add(
            item=self.scanResultsPanel,
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

        self.scanFreqDisp = PropertyDisplayControl(
            parent=self,
            label='Scan Frequency',
            unit=' MHz')
        self.scanFreqDisp.SetValue(150.245)

        self.gainDisp = PropertyDisplayControl(
            parent=self,
            label='Receiver Gain',
            unit=' dB')
        self.gainDisp.SetValue(5.00)

        self.snrDisp = PropertyDisplayControl(
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

        self._altDisp = PropertyDisplayControl(
            parent=self,
            label='Altitude',
            unit=' meters')
        self._altDisp.SetValue(125.60)

        self._headingDisp = PropertyDisplayControl(
            parent=self,
            label='UAV Heading',
            unit=DEGREE_SIGN)
        self._headingDisp.SetValue(128)

        self._scanDirDisp = PropertyDisplayControl(
            parent=self,
            label='Target Heading',
            unit=DEGREE_SIGN)
        self._scanDirDisp.SetValue(320)

        self._scanTimeDisp = PropertyDisplayControl(
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
        self._altDisp.SetValue(altitude)

    def SetHeading(self, heading):
        self._headingDisp.SetValue(heading)

    def SetScanDirection(self, direction):
        self._scanDirDisp.SetValue(direction)

    def SetScanTime(self, time):
        self._scanTimeDisp.SetValue(time)


class ScanSettingsPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanSettingsPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])


class PropertyDisplayControl(wx.Panel):
    def __init__(self, label, unit=None, *args, **kwargs):
        super(PropertyDisplayControl, self).__init__(*args, **kwargs)
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
