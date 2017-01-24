
from kivy.lang import Builder
from kivy.graphics import Rectangle, Color
from kivy.app import App
from kivy.uix.gridlayout import GridLayout

import os
dir = os.path.dirname(__file__)
kv_file = os.path.join(dir, 'StatusWidget.kv')
Builder.load_file(kv_file)

class StatusWidget(GridLayout):
    def __init__(self, **kwargs):
        super(StatusWidget, self).__init__(**kwargs)
        

