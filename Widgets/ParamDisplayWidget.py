from kivy.uix.label import Label
from kivy.lang import Builder


import os
dir = os.path.dirname(__file__)
kv_file = os.path.join(dir, 'ParamDisplayWidget.kv')
Builder.load_file(kv_file)

class ParamDisplayWidget(Label):
    def __init__(self, label, param_default=0,**kwargs):
        super(ParamDisplayWidget, self).__init__(**kwargs)
        self.label = Label(str(label))
        self.param = Label(str(param_default))
        self.add_widget(label,0)
        self.add_widget(param, 1)


    def do_layout(self, *args):
        self.label.height = self.height - self.padding_y
        self.label.width = self.label.text_size.x

        self.param.height = self.height - self.padding_y
        self.param.width = self.width - (self.padding_y * 2) - self.label.width
