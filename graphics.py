import wx

class MyPanel(wx.Panel):
    """ class MyPanel creates a panel to draw on, inherits wx.Panel """
    def __init__(self, parent, id):
        # create a panel
        wx.Panel.__init__(self, parent, id)
        self.SetBackgroundColour("green")
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        """set up the device context (DC) for painting"""
        self.dc = wx.PaintDC(self)
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen("grey",style=wx.TRANSPARENT))
        self.dc.SetBrush(wx.Brush("white", wx.SOLID))
        # set x, y, w, h for rectangle
        self.dc.DrawRectangle(250,250,50, 50)
        self.dc.EndDrawing()
        del self.dc

#app = wx.PySimpleApp()
## create a window/frame, no parent, -1 is default ID
#frame = wx.Frame(None, -1, "Drawing A Rectangle...", size = (500, 500))
## call the derived class, -1 is default ID
#MyPanel(frame,-1)
## show the frame
#frame.Show(True)
## start the event loop
#app.MainLoop()


class Main_Frame(wx.Frame):

    def InitUI(self):

        #background
        #frame = wx.Frame(None, -1, "Drawing A Rectangle...", size = (500, 500))
        #box = wx.BoxSizer()

        current_settings = wx.Panel(self, style=wx.SUNKEN_BORDER)
        current_settings.SetBackgroundColour('#FFFFD6')

        panel1 = MyPanel(current_settings,-1)
        panel1.SetBackgroundColour('#4f5049')

        panel2 = MyPanel(current_settings,-1)
        panel2.SetBackgroundColour('#99FF99')

        #setup tabbed panels
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel1, 1, wx.ALL|wx.EXPAND, 15)
        sizer.Add(panel2, 1, wx.ALL|wx.EXPAND, 15)

        #current_settings.SetSizer(sizer)
        #box.Add(current_settings,1, wx.ALL|wx.EXPAND, 15)
        #box.Add(sizer,1, wx.ALL|wx.EXPAND, 15)
        current_settings.SetSizer(sizer)
        #self.SetSizer(sizer)

        #setup menu and shortcuts
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        fitem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')

        self.SetMenuBar(menubar)

        #self.Bind(wx.EVT_PAINT, self.OnPaint)


        self.Bind(wx.EVT_MENU, self.OnQuit, fitem)

    def ShowMessage4(self):
        dial = wx.MessageDialog(None, 'Verify that Telemetry Unit is plugged in!', 'Hardware Check',
            wx.OK | wx.ICON_INFORMATION)
        dial.ShowModal()

    def OnQuit(self, e):
        self.Close()

def main():

    ex = wx.App()
    test = Main_Frame(None)
    test.InitUI()
    test.SetTitle('UAV Radio Direction Finder')
    test.Maximize()
    test.Show()
    test.ShowMessage4()
    ex.MainLoop()


if __name__ == '__main__':
    main()
