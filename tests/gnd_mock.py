from zrc_base import SerialPort, msg_id_to_type
import Queue
import threading
import time

global alive
alive = threading.Event()
global suppress
suppress = True

def receive_loop(in_q):
    global alive
    global suppress
    alive.set()

    while alive.isSet():
        try:
            msg = in_q.get(block=True, timeout=0.1)
            if msg is not None:
                if msg_id_to_type[msg.msg_id] == 'attitude' and suppress is False:
                    print 'Received ATTITUDE packet'
                    print "altitude: {0}".format(str(msg.altitude))
                    print "heading: {0}".format(str(msg.heading))
                    print '---------------------'
                elif msg_id_to_type[msg.msg_id] == 'detection' and suppress is False:
                    print 'Received DETECTION packet'
                    print "snr: {0}".format(str(msg.snr))
                    print "heading: {0}".format(str(msg.heading))
                    print '---------------------'

        except Queue.Empty as e:
            continue

if __name__ == '__main__':
    global suppress
    input_q = Queue.Queue()
    output_q = Queue.Queue()

    serial_port = SerialPort(in_q=input_q, output_q=output_q, port="COM10")
    serial_port.start()

    receive_thread = threading.Thread(target=receive_loop, args=(input_q,))
    receive_thread.daemon = True
    receive_thread.start()


    while True:
        user_input = raw_input("Enter input:")

        if user_input == "q":
            break
        elif user_input == "ns":
            suppress = False
        elif user_input == "s":
            suppress = True
        elif user_input == "set_settings":
            serial_port.send_scan_settings(gain=3,freq=154.096e6,snr=3)
            print 'sending scan settings'
        serial_port.send_scanning(scanning=1)
        time.sleep(1)

    receive_thread.join(timeout=0.2)