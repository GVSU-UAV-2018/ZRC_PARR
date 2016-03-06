from zlib import crc32
from protocolwrapper import (
    ProtocolWrapper, ProtocolStatus)
from RDF_Format import (
    message_format, message_crc, Container)
import serial
import time

PROTOCOL_HEADER = '\x11'
PROTOCOL_FOOTER = '\x12'
PROTOCOL_DLE = '\x90'
#acknowledge that a packet has been received by the receipient
RCV_ACK = 0
#waiting for acknowledgement of receipt from receipient
SND_ACK = 0

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='COM10',
    baudrate=57600,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout = 0
)

def send_serial(direction, data_type, data):
    """ Given the data, builds a message for
        transmittion, computing the CRC and packing
        the protocol.
        Returns the packed message ready for
        transmission on the serial port.
    """

    global SND_ACK
    global RCV_ACK
    # Build the raw message string. CRC is empty
    # for now
    #
    raw = message_format.build(Container(
        direction=direction,
        data_type=data_type,
        ack=SND_ACK,
        data=data,
        crc = 0))

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

    send_timer = 0
    if(SND_ACK == 1):
        ser.write(pw.wrap(msg))
        #print "ACK Packet Sent\n"
        SND_ACK = 0
    else:
        while ((RCV_ACK == 0) and send_timer < 3):
            ser.write(pw.wrap(msg))
            #print "Data Packet Sent\n"
            send_timer = send_timer + 1
            time.sleep(1)

    RCV_ACK = 0
    send_timer = 0

def receive_serial(panel):
    # Sample: receiving a message
    #

    global SND_ACK
    global RCV_ACK

    pw = ProtocolWrapper(
            header=PROTOCOL_HEADER,
            footer=PROTOCOL_FOOTER,
            dle=PROTOCOL_DLE)
    msg = ''

    while True:

        status = map(pw.input, ser.read())
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
                if(rcvd_msg.ack == 0):
                    SND_ACK = 1
                    #print "Received Data Packet:\n"
                    #print message_format.parse(rec_msg)
                    #print "Sending ACK"
                    send_serial(rcvd_msg.direction,rcvd_msg.data_type,rcvd_msg.data)
                    panel.update_onreceive(rcvd_msg)
                else:
                    #print "Received ACK"
                    RCV_ACK = 1
            msg = ''
        elif(len(msg) > 21):
            msg = ''
