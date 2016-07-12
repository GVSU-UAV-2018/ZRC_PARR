from abc import ABCMeta, abstractmethod, abstractproperty
import Queue
import threading
import time
import serial
from zlib import crc32
from protocolwrapper import ProtocolWrapper, ProtocolStatus
from construct import Struct, ULInt32, SLInt32, ULInt16, Flag, Embed, LFloat32, Container


# class RadioFinderBase(metaclass=ABCMeta, object):
    # __metaclass__ = ABCMeta
    #
    # @property
    # def gain(self):
    #     pass
    #
    # @gain.setter
    # @abstractproperty
    # def gain(self, val):
    #     pass
    #
    # @property
    # def scan_frequency(self):
    #     pass
    #
    # @scan_frequency.setter
    # @abstractproperty
    # def scan_frequency(self, val):
    #     passpy
    #
    # @property
    # def snr_threshold(self):
    #     pass
    #
    # @snr_threshold.setter
    # @abstractproperty
    # def snr_threshold(self, val):
    #     pass
    #
    # @abstractmethod
    # def is_scanning(self):
    #     pass
    #
    # @abstractmethod
    # def start_scanning(self):
    #     pass
    #
    # @abstractmethod
    # def stop_scanning(self):
    #     pass


class SerialReadThread(threading.Thread):
    def __init__(self, in_q, serial_p):
        super(SerialReadThread, self).__init__()
        self.in_q = in_q
        self.serial = serial_p
        self.alive = threading.Event()

        self.pwrap = ProtocolWrapper(
            header=PROTOCOL_HEADER,
            footer=PROTOCOL_FOOTER,
            dle=PROTOCOL_DLE
        )

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)

    def run(self):
        self.alive.set()
        while self.alive.isSet():
            # Will block until a byte is read
            byte = self.serial.read(size=1)
            status = map(self.pwrap.input, byte)

            try:
                # Next loop iteration if end of message not found
                if status[-1] != ProtocolStatus.MSG_OK:
                    continue

                recv_msg = self.pwrap.last_message
                if self._check_crc(recv_msg):
                    self._parse_msg(recv_msg)

            except Exception as e:
                # TODO: Put in error logging here
                print 'Error while receiving serial message'

    def _parse_msg(self, recv_msg):
        try:
            header = msg_header.parse(recv_msg[:2])
            if msg_id_to_type[header.msg_id] == 'scanning':
                msg = msg_scanning.parse(recv_msg)
            elif msg_id_to_type[header.msg_id] == 'scan_settings':
                msg = msg_scan_settings.parse(recv_msg)
            elif msg_id_to_type[header.msg_id] == 'attitude':
                msg = msg_attitude.parse(recv_msg)
            elif msg_id_to_type[header.msg_id] == 'detection':
                msg = msg_detection.parse(recv_msg)

            # put the given message on the queue (block and wait if full for timeout)
            if msg is not None:
                self.in_q.put(msg, block=True, timeout=0.1)

        except Queue.Full as e:
            # TODO put in error logging here
            print 'Input queue is full'

    def _check_crc(self, msg):
        recv_crc = msg_crc.parse(msg[-4:]).crc
        calc_crc = crc32(msg[:-4])
        return recv_crc == calc_crc


class SerialWriteThread(threading.Thread):
    def __init__(self, out_q, serial_p):
        super(SerialWriteThread, self).__init__()
        self.out_q = out_q
        self.serial = serial_p
        self.alive = threading.Event()

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(timeout)

    def run(self):
        self.alive.set()
        while self.alive.isSet():
            try:
                msg = self.out_q.get(block=True, timeout=0.1)
                self.serial.write(msg)
            except Queue.Empty as e:
                print e.message
                continue


class SerialPort(object):
    def __init__(self, in_q=None, out_q=None, *args, **kwargs):
        super(SerialPort, self).__init__()
        self.in_q = in_q or Queue.Queue()
        self.out_q = out_q or Queue.Queue()
        self.pwrap = ProtocolWrapper(
            header=PROTOCOL_HEADER,
            footer=PROTOCOL_FOOTER,
            dle=PROTOCOL_DLE
        )

        port = kwargs.get('port', '/dev/ttyUSB0')
        baud = kwargs.get('baud', 57600)
        timeout = kwargs.get('timeout', None)

        self.serial = serial.Serial(
            port=port,
            baudrate=baud,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=timeout
        )

        self.receive_thread = SerialReadThread(self.in_q, self.serial)
        self.send_thread = SerialWriteThread(self.out_q, self.serial)

    def start(self):
        self.receive_thread.start()
        self.send_thread.start()

    def send_attitude(self, alt, heading):

        msg_str = msg_attitude.build(
            Container(
                msg_id=2,
                altitude=alt,
                heading=heading,
                crc=0
            )
        )

        msg_no_crc = msg_str[:-4]
        crc = msg_crc.build(
            Container(crc=crc32(msg_no_crc))
        )

        packet = self.pwrap.wrap(msg_no_crc + crc)
        for i in packet:
            print i


        try:
            self.out_q.put(packet, block=True, timeout=0.1)
        except Queue.Full as e:
            #TODO Put in error/warning logging
            print 'Queue is full. Did not append attitude packet'

    def close(self):
        self.receive_thread.join(timeout=0.2)
        self.send_thread.join(timeout=0.2)
        self.serial.close()




PROTOCOL_HEADER = '\x11'
PROTOCOL_FOOTER = '\x12'
PROTOCOL_DLE = '\x90'

msg_crc = Struct('msg_crc', SLInt32('crc'))

msg_header = Struct('msg_header',
                    ULInt32('msg_id')
)

msg_scanning = Struct('msg_scanning',
                      Embed(msg_header),
                      Flag('scanning'),
                      Embed(msg_crc)
)

msg_scan_settings = Struct('msg_scan_settings',
                           Embed(msg_header),
                           LFloat32('gain'),
                           LFloat32('scan_frequency'),
                           LFloat32('snr_threshold'),
                           Embed(msg_crc)
)

msg_attitude = Struct('msg_attitude',
                      Embed(msg_header),
                      LFloat32('altitude'),
                      LFloat32('heading'),
                      Embed(msg_crc)
)

msg_detection = Struct('msg_detection',
                       Embed(msg_header),
                       LFloat32('snr'),
                       LFloat32('heading'),
                       Embed(msg_crc)
)

msg_id_to_type = {
    0: 'scanning',
    1: 'scan_settings',
    2: 'attitude',
    3: 'detection'
}