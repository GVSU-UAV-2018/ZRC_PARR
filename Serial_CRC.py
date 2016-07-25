from zlib import crc32
from protocolwrapper import (
    ProtocolWrapper, ProtocolStatus)
from RDF_Format import (
    message_format, message_crc, Container)
import serial
import time
from construct import *

PROTOCOL_HEADER = '\x11'
PROTOCOL_FOOTER = '\x12'
PROTOCOL_DLE = '\x90'

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=57600,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=None
)

closing = False

ser.isOpen()


def send_serial(direction, data_type, data, scanning):
    """ Given the data, builds a message for
        transmittion, computing the CRC and packing
        the protocol.
        Returns the packed message ready for
        transmission on the serial port.
    """
    # Build the raw message string. CRC is empty
    # for now
    #
    raw = message_format.build(Container(
        direction=direction,
        data_type=data_type,
        data=data,
        scanning=scanning,
        crc=0))

    # Compute the CRC field and append it to the
    # message instead of the empty CRC specified
    # initially.
    #
    msg_without_crc = raw[:-4]
    msg_crc = message_crc.build(Container(crc=crc32(msg_without_crc)))

    # Append the CRC field
    #
    msg = msg_without_crc + msg_crc

    pw = ProtocolWrapper(
        header=PROTOCOL_HEADER,
        footer=PROTOCOL_FOOTER,
        dle=PROTOCOL_DLE)

    ser.write(pw.wrap(msg))


def receive_serial():        pass  # Sample: receiving a message
ser.isOpen()
pw = ProtocolWrapper(
    header=PROTOCOL_HEADER,
    footer=PROTOCOL_FOOTER,
    dle=PROTOCOL_DLE)
msg = ''

while closing == False:
    byte = ser.read()
    status = map(pw.input, byte)
    try:
        if status[-1] == ProtocolStatus.MSG_OK:
            rec_msg = pw.last_message
            # Parse the received CRC into a 32-bit integer
            #
            rec_crc = message_crc.parse(rec_msg[-4:]).crc
            # Compute the CRC on the message
            #
            calc_crc = crc32(rec_msg[:-4])
            if rec_crc != calc_crc:
                print 'Error: CRC mismatch'
            else:
                rcvd_msg = message_format.parse(rec_msg)
                print "Data Received"
                panel.update_on_receive(rcvd_msg)
            msg = ''
    except Exception as ex:
        import sys

        print str(ex)
        print "Unexpected error:", sys.exc_info()[0]
        raise


def ser_close():
    closing = True
    time.sleep(2)
