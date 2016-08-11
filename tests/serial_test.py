import Queue
import time

from zrc_base import SerialPort


def main():
    port=None
    try:
        in_q = Queue.Queue()
        out_q = Queue.Queue()

        port = SerialPort(in_q=in_q, out_q=out_q)
        port.start()
        var = 'n'
        while var is not 'y':
            port.send_attitude(alt=0.2, heading=180.0)
            print 'sent attitude'
            time.sleep(60)
    except Exception as e:
        print e.message

    port.close()
    print 'Closing  serial test'


if __name__ == '__main__':
    main()
