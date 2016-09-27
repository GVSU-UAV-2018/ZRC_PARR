# -*- coding: utf-8 -*-

import zrc_core

import wx
from pubsub import pub
import platform
import wx.lib.newevent
import sys, os
import json
from math import pi, cos, sin, radians, degrees, fabs
import threading
import time
import logging
import controllers
import string
import logging

COLORS = {'normalText': '#000000',
          'lightText': '#728CB0',
          'panelPrimary': '#2196F3',
          'panelSecondary': '#496892',
          'panelTertiary': '#64B5F6',
          'windowBg': '#1A2C45'}



DIRECTORY = os.path.dirname(__file__)

ALPHA_ONLY = 1
INT_ONLY = 2
FLOAT_ONLY = 3

CURRENT_SYS = platform.system()
LOCAL_ENCODING = 'utf-8'
if CURRENT_SYS == 'Windows':
    DEGREE_SIGN = chr(176)
else:
    DEGREE_SIGN = u'\xb0'.encode(LOCAL_ENCODING)

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
        self.compassPanel = CompassControl(parent=self.childPanel)
        self.statusDisplayPanel = StatusDisplayPanel(parent=self.childPanel)

        self.topSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.topSizer.Add(
            item=self.settingsDisplayPanel,
            proportion=3,
            flag=wx.RIGHT | wx.EXPAND,
            border=3)
        self.topSizer.Add(
            item=self.compassPanel,
            proportion=5,
            flag=wx.EXPAND)
        self.topSizer.Add(
            item=self.statusDisplayPanel,
            proportion=3,
            flag=wx.LEFT | wx.EXPAND,
            border=3)
        self.mainSizer.Add(
            item=self.topSizer,
            proportion=3,
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
            proportion=1,
            flag=wx.ALL | wx.EXPAND,
            border=1)

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

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.circle = CompassControl(parent=self)
        self.sizer.Add(item=self.circle, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)


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

        self._countdownTimeDisp = DisplayControl(
            parent=self,
            label='Countdown')
        self._countdownTimeDisp.SetValue(0)


        self._scanTimeDisp = DisplayControl(
            parent=self,
            label='Scanning Time')
        self._scanTimeDisp.SetValue(0)

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
            item=self._countdownTimeDisp,
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

    def SetCountdownTime(self, time):
        formTime = '{0:.1f}'.format(time)
        self._countdownTimeDisp.SetValue(formTime)

    def SetScanTime(self, time):
        formTime = '{0:.1f}'.format(time)
        self._scanTimeDisp.SetValue(formTime)


class ScanSettingsPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(ScanSettingsPanel, self).__init__(*args, **kwargs)
        self.SetBackgroundColour(COLORS['panelPrimary'])

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        self.freqCtrl = NumTextCtrl(parent=self, label='Scan Frequency (MHz)')
        self.freqCtrl.numCtrl.SetMaxSize((100,100))
        self.gainCtrl = NumTextCtrl(parent=self, label='Receiver Gain (dB)')
        self.snrCtrl = NumTextCtrl(parent=self, label='SNR Threshold')

        self.submitBtn = wx.Button(parent=self, id=wx.ID_ANY, label='Submit')
        self.submitBtn.SetFont(wx.Font(pointSize=20, family=wx.MODERN, style=wx.NORMAL, weight=wx.NORMAL))
        self.submitBtn.SetForegroundColour(COLORS['normalText'])
        self.submitBtn.SetBackgroundColour(COLORS['panelTertiary'])
        self.submitBtn.Bind(event=wx.EVT_BUTTON, handler=self.OnSubmit)
        self.submitBtn.SetMinSize((-1, 60))
        self.submitBtn.SetMaxSize((-1, 60))

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        btnSizer.Add(self.submitBtn, proportion=1, flag=wx.EXPAND)

        sizer.Add(item=self.freqCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.gainCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.snrCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.AddSpacer(item=(0, 0), proportion=2, flag=wx.EXPAND)
        sizer.Add(item=btnSizer, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)

    def ValidInput(self):
        for ctrl in [self.freqCtrl, self.gainCtrl, self.snrCtrl]:
            if ctrl.numCtrl.GetValidator().Validate(ctrl.numCtrl) is False:
                return False

        return True

    def OnSubmit(self, event):
        if not self.ValidInput():
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
        self.powerDisplay = DisplayControl(parent=self, label='Power', unit=' dB')
        self.powerDisplay.SetValue(13.0)
        self.freqDisplay = DisplayControl(parent=self, label='Frequency', unit=' MHz')
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

        self.countdownCtrl = NumTextCtrl(parent=self, label='Countdown Time (s)', flag=INT_ONLY)
        self.scanTimeCtrl = NumTextCtrl(parent=self, label='Scanning Time (s)', flag=INT_ONLY)

        self.startBtn = wx.Button(parent=self, id=wx.ID_ANY, label='Start')
        self.startBtn.SetFont(wx.Font(pointSize=20, family=wx.MODERN, style=wx.NORMAL, weight=wx.NORMAL))
        self.startBtn.SetForegroundColour(COLORS['normalText'])
        self.startBtn.SetBackgroundColour(COLORS['panelTertiary'])
        self.startBtn.Bind(event=wx.EVT_BUTTON, handler=self._OnToggleScan)
        self.startBtn.SetMinSize((-1, 60))
        self.startBtn.SetMaxSize((-1, 60))

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        btnSizer.Add(item=self.startBtn, proportion=1, flag=wx.EXPAND)

        sizer.Add(item=self.countdownCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.Add(item=self.scanTimeCtrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        sizer.AddSpacer(item=(0, 0), proportion=1, flag=wx.EXPAND)
        sizer.Add(item=btnSizer, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)

    def ValidInput(self):
        for ctrl in [self.countdownCtrl, self.scanTimeCtrl]:
            if ctrl.numCtrl.GetValidator().Validate(ctrl.numCtrl) is False:
                return False

        return True

    def _OnToggleScan(self, evt):
        if not self.ValidInput():
            return

        labelText = self.startBtn.GetLabelText()

        if labelText == 'Start':
            self.Start()

        elif labelText == 'Stop':
            self.Stop()

    def Start(self):
        countdown = self.countdownCtrl.GetValue()
        scanTime = self.scanTimeCtrl.GetValue()
        self.startBtn.SetLabelText('Stop')
        params = {'totalCountdown': countdown,
                  'totalScanTime': scanTime}
        pub.sendMessage('scanStart.Start', params=params)

    def Stop(self):
        self.startBtn.SetLabelText('Start')
        pub.sendMessage('scanStart.Stop')


class CompassControl(wx.PyPanel):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER, name='CompassControl'):

        super(CompassControl, self).__init__(parent, id, pos, size, style, name)
        self.InheritAttributes()
        self.SetInitialSize(size)
        self.SetBackgroundColour('#FFFFFF')
        self.SetForegroundColour('#000000')
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self._centerX = 0
        self._centerY = 0
        self._radius = 0
        self._tickSize = 0

        # Angle offset to make 0 degrees direction different from unit circle
        self._angleOffset = radians(90)
        self._expectedAngle = radians(0)
        self._expectedWidth = radians(10)
        self._currentAngle = radians(15)
        self._expectedAngleVis = False

        font = wx.Font(pointSize=24, style=wx.NORMAL, family=wx.MODERN, weight=wx.BOLD)
        self.SetFont(font)

    def OnSize(self, event):
        '''
        Event handler that responds to panel resize event.
        :param event: event arguments
        '''
        self.Refresh()

    def SetExpectedAngleVisibility(self, visible):
        self._expectedAngleVis = visible
        self.Refresh()


    def SetExpectedAngle(self, angle, refresh=True):
        newAngle = radians(angle % 360)

        if newAngle == self._expectedAngle:
            return

        self._expectedAngle = newAngle
        if refresh:
            self.Refresh()

    def SetExpectedSliceWidth(self, angle, refresh=True):
        newAngle = radians(angle % 360)

        if newAngle == self._expectedWidth:
            return

        self._expectedWidth = newAngle
        if refresh:
            self.Refresh()

    def SetCurrentAngle(self, angle, refresh=True):
        newAngle = radians(angle % 360)

        if newAngle == self._currentAngle:
            return

        self._currentAngle = newAngle
        if refresh:
            self.Refresh()

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc = wx.GCDC(dc)
        self.Draw(dc)

    def Draw(self, dc):
        width, height = self.GetClientSize()
        if not width or not height:
            return

        dc.SetBackground(wx.Brush(self.GetBackgroundColour(), wx.SOLID))
        foreColour = self.GetForegroundColour()
        dc.SetTextForeground(foreColour)

        dc.Clear()

        font = self.GetFont()
        if not font:
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

        width, height = self.GetClientSize()
        ptSize = int(min([width, height]) * 0.07)
        font.SetPointSize(ptSize)
        self.SetFont(font)
        dc.SetFont(font)

        self._centerX = width / 2.0
        self._centerY = height / 2.0

        txtSpacingX, txtSpacingY = dc.GetTextExtent('W')
        txtSpacing = max([txtSpacingX, txtSpacingY])
        self._radius = min([self._centerX, self._centerY]) - (txtSpacing * 1.15)
        self._tickSize = self._radius * 0.05

        self.DrawExpectedDirection(dc)
        self.DrawCompassTicks(dc)
        self.DrawCompass(dc)
        self.DrawCurrentDirection(dc)

    def DrawCompass(self, dc):

        dc.SetFont(self.GetFont())
        dc.SetPen(wx.Pen(self.GetForegroundColour(), width=3, style=wx.SOLID))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        # Draw the main circle
        dc.DrawCircle(self._centerX, self._centerY, self._radius)

        # Draw center-point circle
        dc.SetBrush(wx.BLACK_BRUSH)
        dc.DrawCircle(self._centerX, self._centerY, 2)

        # Draw cardinal direction labels
        txtSpacingX, txtSpacingY = dc.GetTextExtent('W')
        xPos = self._centerX - self._radius - (1.5 * txtSpacingX), self._centerY - (txtSpacingY // 2.0)
        dc.DrawText('W', self._centerX - self._radius - (1.4 * txtSpacingX), self._centerY - (txtSpacingY // 2.0))

        txtSpacingX, txtSpacingY = dc.GetTextExtent('N')
        dc.DrawText('N', self._centerX - (txtSpacingX / 2.0), self._centerY - self._radius - txtSpacingY)

        txtSpacingX, txtSpacingY = dc.GetTextExtent('E')
        dc.DrawText('E', self._centerX + self._radius + (txtSpacingX / 2.0), self._centerY - (txtSpacingY // 2.0))

        txtSpacingX, txtSpacingY = dc.GetTextExtent('S')
        dc.DrawText('S', self._centerX - (txtSpacingX / 2.0), self._centerY + self._radius)

    def DrawCompassTicks(self, dc):
        dc.SetPen(wx.Pen(self.GetForegroundColour(), width=2, style=wx.SOLID))
        tickStep = 30

        dc.SetFont(wx.Font(pointSize=self.GetFont().GetPointSize() // 2, style=wx.NORMAL, family=wx.SWISS, weight=wx.NORMAL))
        for tickAngle in range(0, 360, tickStep):
            tickX1, tickY1 = self.DrawTick(dc, tickAngle, self._tickSize)

            txtX, txtY = dc.GetTextExtent(str(tickAngle))
            txtX = (txtX / 2) * sin(radians(tickAngle) + self._angleOffset)
            txtY = (txtY / 2) * cos(radians(tickAngle) + self._angleOffset)
            dc.DrawRotatedText(str(tickAngle), tickX1 - txtX, tickY1 - txtY, tickAngle)

    def DrawTick(self, dc, angle, tickSize):
        tickRadian = radians(-angle) - self._angleOffset
        tickX1 = self._centerX + (self._radius - tickSize) * cos(tickRadian)
        tickY1 = self._centerY + (self._radius - tickSize) * sin(tickRadian)
        tickX2 = self._centerX + self._radius * cos(tickRadian)
        tickY2 = self._centerY + self._radius * sin(tickRadian)
        dc.DrawLine(tickX1, tickY1, tickX2, tickY2)
        return (tickX1, tickY1)

    def DrawExpectedDirection(self, dc):
        if not self._expectedAngleVis:
            return

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush('#3FE044', wx.SOLID))

        rAngle1 = self._angleOffset + self._expectedAngle - (self._expectedWidth / 2.0)
        rAngle2 = self._angleOffset + self._expectedAngle + (self._expectedWidth / 2.0)

        dc.DrawEllipticArc(x=self._centerX - self._radius,
                           y=self._centerY - self._radius,
                           w=2.0 * self._radius,
                           h=2.0 * self._radius,
                           start=degrees(rAngle1),
                           end=degrees(rAngle2))

        dc.SetPen(wx.BLACK_PEN)
        self.DrawTick(dc, degrees(self._expectedAngle), self._tickSize)

    def DrawCurrentDirection(self, dc):
        angle = self._currentAngle - self._angleOffset
        x = self._centerX - self._radius * cos(-angle)
        y = self._centerY - self._radius * sin(-angle)

        gc = dc.GetGraphicsContext()

        if gc:
            gc.SetPen(wx.Pen('#000000', width=2, style=wx.NORMAL))
            path = gc.CreatePath()
            path.MoveToPoint(self._centerX, self._centerY)
            path.AddLineToPoint(x, y)
            gc.StrokePath(path)

    # def DoGetBestSize(self, dc):
    #     font = self.GetFont()
    #
    #     if not font:
    #         font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    #
    #     dc = wx.ClientDC(self)
    #     dc.SetFont(font)

    def AcceptsFocusFromKeyboard(self):
        return False

    def OnEraseBackground(self, event):
        pass


class TextValidator(wx.PyValidator):
    def __init__(self, flag=None, validate=None, *args, **kwargs):
        super(TextValidator, self).__init__(*args, **kwargs)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

        if validate:
            self.Validate = validate

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

        if (self.flag == INT_ONLY or self.flag == FLOAT_ONLY) and chr(key) in string.digits:
            event.Skip()
            return

        if self.flag == FLOAT_ONLY and (key == 46):
            event.Skip()
            return

        if not wx.Validator_IsSilent():
            wx.Bell()

        return

class NumTextCtrl(wx.BoxSizer):
    def __init__(self, parent, label, flag=FLOAT_ONLY):
        super(NumTextCtrl, self).__init__(wx.HORIZONTAL)

        self.flag = flag
        font = wx.Font(
            pointSize=22,
            family=wx.DECORATIVE,
            style=wx.NORMAL,
            weight=wx.BOLD)

        self.labelText = wx.StaticText(parent=parent, label=label)
        self.labelText.SetFont(font)
        self.labelText.SetForegroundColour('#000000')

        self.numCtrl = wx.TextCtrl(parent=parent, id=wx.ID_ANY, style=wx.TE_RIGHT, validator=TextValidator(self.flag))
        self.numCtrl.SetFont(font)
        self.numCtrl.SetForegroundColour(COLORS['normalText'])
        self.numCtrl.SetMinSize((150, -1))

        self.Add(item=self.labelText, proportion=1, flag=wx.ALL | wx.EXPAND, border=3)
        self.AddSpacer(item=(0, 0), proportion=0, flag=wx.EXPAND)
        self.Add(item=self.numCtrl, proportion=0, flag=wx.ALL | wx.ALIGN_RIGHT, border=3)

    def GetValue(self):
        try:
            if self.flag is FLOAT_ONLY:
                val = float(self.numCtrl.GetValue())
            elif self.flag is INT_ONLY:
                val = int(self.numCtrl.GetValue())
            else:
                val = self.numCtrl.GetValue()
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
    #logging.basicConfig(format='%(asctime)s --%(levelname)s-- %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
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
        print type(ex)
