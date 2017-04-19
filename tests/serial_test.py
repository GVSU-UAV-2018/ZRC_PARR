from zrc_core import SerialInterface, MessageString, MessageType
import Queue
import random
import time


def main():
    port=None
    try:

        config = {'port': '/dev/ttyUSB0',
                  'baud': 57600,
                  'timeout': 0.1}
        port = SerialInterface(config)
        port.start()
        var = 'n'
        while var is not 'y':
            port.send_attitude(altitude=random.uniform(20.0, 100.0), heading=random.uniform(0.0, 360.0))
            print 'sent attitude'
            time.sleep(1)
    except Exception as e:
        print e.message

    port.dispose()
    print 'Closing  serial test'


if __name__ == '__main__':
    main()
