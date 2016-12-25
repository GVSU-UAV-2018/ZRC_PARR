from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

import os
dir = os.path.dirname(__file__)
kv_file = os.path.join(dir, 'ReceiverParams.kv')
Builder.load_file(kv_file)

class ReceiverParamsWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(ReceiverParamsWidget, self).__init__(**kwargs)

