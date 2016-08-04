from  zrc_base import SerialInterface
from pubsub import pub


class SystemInfoController:
    def __init__(self, serial_com):
        self.tracker_comm = serial_com

