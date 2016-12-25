import json

settings_json = json.dumps([
    {'type': 'title',
     'title': 'Communication'},
    {'type': 'path',
     'title': 'Telemetry Device',
     'section': 'communication',
     'desc': 'Device file of telemetry unit. Example /dev/ttyUSB0',
     'key': 'telemetry_device'},
    {'type': 'options',
     'title': 'Baud Rate',
     'section': 'communication',
     'desc': 'Baud rate of serial telemetry device',
     'key': 'telemetry_baud',
     'options': [str(38000), str(56000), str(57600), str(115200)]}
])