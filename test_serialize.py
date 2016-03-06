import Serial_CRC
import serial
import time
import threading

#raw = Serial_CRC.send_serial("RPI_to_GS","SYS_INFO",[343.0,2.2,100.0])

receiver = threading.Thread(target = Serial_CRC.receive_serial)
receiver.start()
