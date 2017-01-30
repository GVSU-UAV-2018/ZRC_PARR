import json
import sys
import glob
import serial

import platform


# def serial_ports():
#     if platform.system() == 'Windows':
#         ports = list(serial.tools.list_ports.comports())
#         return ports

settings_json = json.dumps([
    {'type': 'title',
     'title': 'Communication'},
    {'type': 'options',
     'title': 'Telemetry Device',
     'section': 'communication',
     'desc': 'Telemetry unit device location. Example /dev/ttyUSB0',
     'key': 'telemetry_device',
     'options': ['/dev/ttyUSB0']},
    {'type': 'options',
     'title': 'Baud Rate',
     'section': 'communication',
     'desc': 'Baud rate of serial telemetry device',
     'key': 'telemetry_baud',
     'options': [str(38000), str(56000), str(57600), str(115200)]}
])




