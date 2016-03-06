import time
import serial

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='COM10',
    baudrate=57600,
    timeout=None,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

#ser.open()
ser.isOpen()

while 1:
    msg = ser.readline(3)
    print msg
