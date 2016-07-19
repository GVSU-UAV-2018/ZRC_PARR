from abc import ABCMeta, abstractmethod, abstractproperty
import Queue
import threading
import serial
from zlib import crc32
from protocolwrapper import ProtocolWrapper, ProtocolStatus
from construct import Struct, SLInt32, ULInt32, ULInt16, Flag, Embed, LFloat32, Container


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
        super(SerialReadThread, self).Thread.join(self, timeout)

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
        super(SerialWriteThread, self).join(timeout)

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

    def _put_message(self, msg):
        try:
            self.out_q.put(msg, block=True, timeout=0.1)
        except Queue.Full as e:
            #TODO put in error logging
            print 'Output queue is full. Did not append message'
            print e.message

    def _append_crc(self, packet):
        msg_no_crc = packet[:-4]
        crc = msg_crc.build(
            Container(crc=crc32(msg_no_crc))
        )

        packet_crc = msg_no_crc + crc
        return packet_crc

    def send_scanning(self, scanning):
        msg_str = msg_scanning.build(
            Container(
                msg_id=0,
                scanning=scanning
            )
        )

        fin_msg = self._append_crc(msg_str)
        packet = self.pwrap(fin_msg)
        self._put_message(packet)

    def send_scan_settings(self, gain, freq, snr):
        msg_str = msg_scan_settings.build(
            Container(
                msg_id=1,
                gain=gain,
                scan_frequency=freq,
                snr_threshold=snr,
                crc=0
            )
        )

        fin_msg = self._append_crc(msg_str)
        packet = self.pwrap.wrap(fin_msg)
        self._put_message(packet)

    def send_attitude(self, alt, heading):
        msg_str = msg_attitude.build(
            Container(
                msg_id=2,
                altitude=alt,
                heading=heading,
                crc=0
            )
        )

        fin_msg = self._append_crc(msg_str)
        packet = self.pwrap.wrap(fin_msg)
        self._put_message(packet)

    def send_detection(self, snr, heading):
        msg_str = msg_detection.build(
            Container(
                msg_id=3,
                snr=snr,
                heading=heading,
                crc=0
            )
        )

        fin_msg = self._append_crc(msg_str)
        packet = self.pwrap.wrap(fin_msg)
        self._put_message(packet)

    def close(self):
        self.receive_thread.join(timeout=0.2)
        self.send_thread.join(timeout=0.2)
        self.serial.close()




PROTOCOL_HEADER = '\x11'
PROTOCOL_FOOTER = '\x12'
PROTOCOL_DLE = '\x90'

msg_crc = Struct('msg_crc', SLInt32('crc'))

msg_header = Struct('msg_header',
                    ULInt16('msg_id')
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