from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

import os
dir = os.path.dirname(__file__)
kv_file = os.path.join(dir, 'StatusWidget.kv')
Builder.load_file(kv_file)

class StatusWidget(GridLayout):
    def __init__(self, **kwargs):
        super(StatusWidget, self).__init__(**kwargs)
