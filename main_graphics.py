from wx.lib import sheet
from math import hypot, sin, cos, pi
import time
import wx

#global timer variables
countdown_tmr = 5
scanning_tmr = 0.0
total_scan_time = 40.0
total_countdown_tmr = 5


class SpreadSheet(sheet.CSheet):
    def __init__(self, parent):
        sheet.CSheet.__init__(self, parent)
        self.row = self.col = 0
        self.SetNumberRows(5)
        self.SetNumberCols(8)

        for i in range(5):
            self.SetRowSize(i, 20)

########################################################################
class TabPanel(wx.Panel):
    global total_scan_time
    global total_countdown_tmr
    #----------------------------------------------------------------------
    def __init__(self, parent, tab_type, main_frame):
        """"""
        font = wx.Font(15,style=wx.NORMAL,family=wx.MODERN,weight=wx.BOLD)

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        if tab_type == "control":


        #Panel for feedback and control of system settigns
            vbox = wx.BoxSizer(wx.VERTICAL)

            cs_vbox = wx.BoxSizer(wx.VERTICAL)
            ##current settings
            current_settings = wx.Panel(self, style=wx.SUNKEN_BORDER)
            current_settings.SetBackgroundColour('#FFFFD6')

            lbl1 = wx.StaticText(current_settings, -1, "SYSTEM INFO", style=wx.ALIGN_TOP)
            lbl1.SetFont(font)
            cs_vbox.Add(lbl1, 0, wx.TOP|wx.LEFT, 20)

            gs1 = wx.GridSizer(3, 2, 5, 5)

            gs1.AddMany([(wx.StaticText(current_settings, label='Altitude:'), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(current_settings, label='meters'), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(current_settings, label='Current Heading:'), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(current_settings, label='degrees'), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(current_settings, label='Scan Frequency:'), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(current_settings, label='MHz'), 0, wx.EXPAND|wx.ALL,20)])

            cs_vbox.Add(gs1, 0, wx.ALL, 20)
            current_settings.SetSizer(cs_vbox)
            vbox.Add(current_settings, proportion=1, flag=wx.EXPAND|wx.ALL)

            ##configure settings
            cs2_vbox = wx.BoxSizer(wx.VERTICAL)
            configure_settings = wx.Panel(self, style=wx.SUNKEN_BORDER)
            configure_settings.SetBackgroundColour('#C2D1B2')

            lbl2 = wx.StaticText(configure_settings, -1, "DETECTION SETTINGS", style=wx.ALIGN_TOP)
            lbl2.SetFont(font)
            cs2_vbox.Add(lbl2, 0, wx.TOP|wx.LEFT, 20)

            gs2 = wx.GridSizer(3, 2, 5, 5)

            gs2.AddMany([(wx.StaticText(configure_settings, label='Set Frequency (MHz):'), 0,wx.EXPAND|wx.ALL,20),
                (wx.TextCtrl(configure_settings), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(configure_settings, label='Set Gain (dB):'), 0,wx.EXPAND|wx.ALL,20),
                (wx.TextCtrl(configure_settings), 0, wx.EXPAND|wx.ALL,20),
                (wx.StaticText(configure_settings, label='Set SNR:'), 0, wx.EXPAND|wx.ALL,20),
                (wx.TextCtrl(configure_settings), 0, wx.EXPAND|wx.ALL,20)])

            cs2_vbox.Add(gs2, 0, wx.ALL, 20)
            configure_settings.SetSizer(cs2_vbox)
            vbox.Add(configure_settings, proportion=1, flag=wx.EXPAND)

            ##start and stop scan
            start_scan = wx.Panel(self, style=wx.SUNKEN_BORDER)
            start_scan.SetBackgroundColour('#FFFFD6')

            gs3 = wx.GridSizer(1, 2, 5, 5)
            gs6 = wx.GridSizer(5, 1, 5, 5)

            #start_btn.Bind(wx.EVT_BUTTON, self.StartTimer)
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.update, self.timer)
            self.toggleBtn = wx.Button(start_scan, wx.ID_ANY, "Start")
            self.toggleBtn.Bind(wx.EVT_BUTTON, self.onToggle)

            submit_btn = wx.Button(start_scan, wx.ID_ANY, "Submit")
            submit_btn.Bind(wx.EVT_BUTTON, self.submit)

            self.set_countdown = wx.TextCtrl(start_scan)
            self.set_countdown.SetValue(str(total_countdown_tmr))
            self.set_scanning = wx.TextCtrl(start_scan)
            self.set_scanning.SetValue(str(total_scan_time))

            gs6.AddMany([(wx.StaticText(start_scan, label='Count Down Timer:'), 1,wx.EXPAND),
                (self.set_countdown, 1, wx.EXPAND|wx.BOTTOM,20),
                (wx.StaticText(start_scan, label='Scanning Timer:'), 1,wx.EXPAND),
                (self.set_scanning, 1, wx.EXPAND|wx.BOTTOM,20),
                (submit_btn, 1,wx.EXPAND)])

            gs3.AddMany([(self.toggleBtn, 0,wx.EXPAND|wx.ALL,20),
            (gs6, 0, wx.EXPAND|wx.ALL,20)])

            start_scan.SetSizer(gs3)
            vbox.Add(start_scan, 1, wx.EXPAND)


            hsizer.Add(vbox, 1, wx.EXPAND|wx.ALL|wx.CENTER)

        #Panel for manual RDF assistance and feedback
            scan_assist = wx.Panel(self,style=wx.SUNKEN_BORDER)
            scan_assist.SetBackgroundColour('#E6E6E6')
            self.panel2 = Rotation_Assist(scan_assist)
            #panel2.SetBackgroundColour('#99FF99')
            sizer2 = wx.BoxSizer(wx.VERTICAL)

            #lbl5 = wx.StaticText(scan_assist, -1, "NORTH", style=wx.ALIGN_CENTER)
            #lbl5.SetFont(font)
            #sizer2.Add(lbl5, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER, 20)
            sizer2.Add(self.panel2, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER, 20)

            #lbl6 = wx.StaticText(scan_assist, -1, "SOUTH", style=wx.ALIGN_CENTER)
            #lbl6.SetFont(font)
            #sizer2.Add(lbl6, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER, 20)
            #sizer2.Add(panel2, 1, wx.EXPAND|wx.ALL)
            scan_assist.SetSizer(sizer2)

            hsizer.Add(scan_assist , 1, wx.ALL|wx.EXPAND)

        #Panel for immediate scan results and feedback
            vbox3 = wx.BoxSizer(wx.VERTICAL)
            vbox4 = wx.BoxSizer(wx.VERTICAL)
            vbox_scan = wx.BoxSizer(wx.VERTICAL)
            ##previous scan
            previous_scan = wx.Panel(self,style=wx.SUNKEN_BORDER)
            previous_scan.SetBackgroundColour('#C2D1B2')

            lbl3 = wx.StaticText(previous_scan, -1, "PREVIOUS SCAN RESULTS", style=wx.ALIGN_TOP)
            lbl3.SetFont(font)
            vbox3.Add(lbl3, 0, wx.TOP|wx.LEFT, 20)

            gs4 = wx.GridSizer(3, 2, 5, 5)

            gs4.AddMany([(wx.StaticText(previous_scan, label='Direction:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(previous_scan, label='degrees'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(previous_scan, label='Power:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(previous_scan, label=' '), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(previous_scan, label='Scan Frequency:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(previous_scan, label='MHz'), 0, wx.EXPAND|wx.ALL,40)])


            vbox3.Add(gs4, proportion=1, flag=wx.EXPAND|wx.ALL)

            current_scan = wx.Panel(self,style=wx.SUNKEN_BORDER)
            current_scan.SetBackgroundColour('#FFFFD6')

            lbl4 = wx.StaticText(current_scan, -1, "CURRENT SCAN RESULTS", style=wx.ALIGN_TOP)
            lbl4.SetFont(font)
            vbox4.Add(lbl4, 0, wx.TOP|wx.LEFT, 20)

            gs5 = wx.GridSizer(3, 2, 5, 5)

            gs5.AddMany([(wx.StaticText(current_scan, label='Direction:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(current_scan, label='degrees'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(current_scan, label='Power:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(current_scan, label=' '), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(current_scan, label='Scan Frequency:'), 0, wx.EXPAND|wx.ALL,40),
                (wx.StaticText(current_scan, label='MHz'), 0, wx.EXPAND|wx.ALL,40)])


            vbox4.Add(gs5, proportion=1, flag=wx.EXPAND|wx.ALL)

            previous_scan.SetSizer(vbox3)
            current_scan.SetSizer(vbox4)
            vbox_scan.Add(previous_scan, 1, wx.EXPAND)
            vbox_scan.Add(current_scan, 1, wx.EXPAND)

            hsizer.Add(vbox_scan, 1, wx.EXPAND)

        if tab_type == "results":
            sheet = SpreadSheet(self)
            hsizer.Add(sheet, 1)

        self.SetSizer(hsizer)

    def submit(self, event):
        global total_countdown_tmr
        global total_scan_time
        global countdown_tmr
        total_countdown_tmr = int(self.set_countdown.GetValue())
        countdown_tmr = total_countdown_tmr
        total_scan_time = float(self.set_scanning.GetValue())
        self.set_countdown.SetValue(str(total_countdown_tmr))
        self.set_scanning.SetValue(str(total_scan_time))
        self.panel2.OnPaint(self)


    def onToggle(self, event):
        global scanning_tmr
        global countdown_tmr
        global total_countdown_tmr
        btnLabel = self.toggleBtn.GetLabel()
        if btnLabel == "Start":
            self.timer.Start(1000)
            self.toggleBtn.SetLabel("Stop")
        else:
            scanning_tmr = 0.0
            countdown_tmr = total_countdown_tmr
            self.timer.Stop()
            self.toggleBtn.SetLabel("Start")
            self.panel2.OnPaint(self)

    def update(self, event):
        global scanning_tmr
        global total_scan_time
        global countdown_tmr
        if countdown_tmr <= 0:
            scanning_tmr = scanning_tmr + 1.0
            if scanning_tmr <= total_scan_time:
                self.panel2.OnPaint(self)
            else:
                scanning_tmr = 0.0
                countdown_tmr = total_countdown_tmr
                self.timer.Stop()
                self.toggleBtn.SetLabel("Start")
        else:
            countdown_tmr = countdown_tmr - 1
            self.panel2.OnPaint(self)

class Rotation_Assist(wx.Panel):

    def __init__(self, parent):
        # create a panel
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("#E6E6E6")
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        global total_scan_time
        global scanning_tmr
        global countdown_tmr
        #get panel size, so that circle can be drawn in the center
        x,y = self.GetSize()
        self.dc = wx.PaintDC(self)
        self.dc.BeginDrawing()
        #rotating guide line
        self.dc.SetPen(wx.Pen("green",style=wx.SOLID))
        self.dc.SetBrush(wx.Brush("white", wx.SOLID))
        center_x = x/2.0
        center_y = y/2.0
        r = x/2.0
        self.dc.DrawText("NORTH", center_x-25, center_y - r - 25.0)
        self.dc.DrawText("SOUTH", center_x-25, center_y + r + 10.0)
        self.dc.DrawCircle(center_x, center_y,r)

        #compass angle is the vehicle header
        compass_angle = 2.0
        #angle corresponds to timer value
        angle = (scanning_tmr/total_scan_time)*2*pi
        #how wide the target slice region is
        slice_angle = (15.0/360.0)*2*pi
        #calculate line end points
        #line 1
        x1 = r*cos(-pi/2.0+angle-slice_angle/2.0)
        y1 = r*sin(-pi/2.0+angle-slice_angle/2.0)
        #line 2
        x2 = r*cos(-pi/2.0+angle+slice_angle/2.0)
        y2 = r*sin(-pi/2.0+angle+slice_angle/2.0)
        #fill point
        x3 = r*cos(-pi/2.0+angle)/2.0
        y3 = r*sin(-pi/2.0+angle)/2.0
        #compass line
        x4 = r*cos(-pi/2.0+compass_angle)
        y4 = r*sin(-pi/2.0+compass_angle)

        self.dc.DrawLine(center_x, center_y,center_x+x1,center_y+y1)
        self.dc.DrawLine(center_x, center_y,center_x+x2,center_y+y2)
        self.dc.SetBrush(wx.Brush("#C2D1B2", wx.SOLID))
        self.dc.FloodFill(center_x+x3,center_y+y3,"green",style=wx.FLOOD_BORDER)
        self.dc.SetPen(wx.Pen("red",style=wx.SOLID))
        self.dc.DrawLine(center_x, center_y,center_x+x4,center_y+y4)
        font = wx.Font(50,style=wx.NORMAL,family=wx.MODERN,weight=wx.BOLD)
        self.dc.SetFont(font)
        if countdown_tmr > 0:
            self.dc.DrawText(str(countdown_tmr), center_x-20, center_y-35)
        else:
            self.dc.DrawText(str(int(total_scan_time-scanning_tmr)), center_x-40, center_y-35)

        self.dc.EndDrawing()
        del self.dc

########################################################################
class Tabbed(wx.Notebook):
    """
    Notebook class
    """

    #----------------------------------------------------------------------

    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             )

        # Create the first tab and add it to the notebook
        tabOne = TabPanel(self, "control", parent)
        tabOne.SetBackgroundColour("Gray")
        self.AddPage(tabOne, " Control ")

        # Create and add the second tab
        tabTwo = TabPanel(self, "results", parent)
        self.AddPage(tabTwo, " Scan Results ")


class Main_Frame(wx.Frame):

    def InitUI(self):

        #background
        panel = wx.Panel(self)
        panel.SetBackgroundColour('#4f5049')

        #setup tabbed panels
        notebook = Tabbed(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 15)
        panel.SetSizer(sizer)

        #setup menu and shortcuts
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        fitem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)

    def ShowMessage4(self):
        dial = wx.MessageDialog(None, 'Verify that Telemetry Unit is plugged in!', 'Hardware Check',
            wx.OK | wx.ICON_INFORMATION)
        dial.ShowModal()

    def OnQuit(self, e):
        self.Close()

def main():

    ex = wx.App()
    main = Main_Frame(None)
    main.InitUI()
    main.SetTitle('UAV Radio Direction Finder')
    main.Maximize()
    main.Show()
    main.ShowMessage4()
    ex.MainLoop()


if __name__ == '__main__':
    main()
