import sys
from MainWindow import Ui_MainWindow
from rdfinder import UAVRadioFinder
from resources import qInitResources, qCleanupResources
from PyQt5 import QtCore, QtGui, QtWidgets
from threading import Event
from zrc_core import TimerThread, SerialInterface
from ConfigParser import ConfigParser
import usb.core

CONFIG_PATH = 'config.ini'

class ZarrUi(Ui_MainWindow):
    rdfinder = None
    config = None
    telemetry = None
    receiver = None

    def __init__(self, config):
        self.config = config

        super(Ui_MainWindow, self).__init__()

        self._startScanTime = int(self.config.scanTimerConfig['scanningtime'])
        self._startCountdownTime = int(self.config.scanTimerConfig['countdowntime'])

        self.freqValCopy = self.config.receiverConfig['frequency']
        self.snrValCopy = self.config.receiverConfig['snrthreshold']
        self.gainValCopy = self.config.receiverConfig['gain']

        self.scanTime = self._startScanTime
        self.countdownTime = self._startCountdownTime
        self.scanComplete = False
        self.countdownComplete = False
        self.scanning = False

        self.updateThread = TimerThread(event=Event(), func=self.oneSecUpdate, interval=1.0)

    def start(self, window):
        self.setupUi(window)
        self.setup()
        self.updateThread.start()

    def connectTelemetry(self):
        self.telemetry = SerialInterface()
        port = self.config.telemConfig['port']
        baud = int(self.config.telemConfig['baud'])
        timeout = float(self.config.telemConfig['timeout'])

        self.telemConnected = self.telemetry.setup(port=port, baud=baud, timeout=timeout)
        if self.telemConnected:
            self.rdfinder = UAVRadioFinder(serial=self.telemetry)




    def oneSecUpdate(self):
        self._updateScanTimer()

    def setup(self):
        self.connectTelemetry()
        self.scanTime = self._startScanTime
        self.countdownTime = self._startCountdownTime
        self.scanTimeVal.setText(str(self.scanTime))
        self.countdownVal.setText(str(self.countdownTime))

        doubleValidator = QtGui.QDoubleValidator()

        self.freqVal.setText(str(self.freqValCopy))
        self.freqVal.setValidator(doubleValidator)
        # self.freqVal.textChanged.connect(self.validateDblTextEdit(self.freqVal))
        self.freqBtn.clicked.connect(self.freqBtnClicked)
        self.freqOkBtn.clicked.connect(self.freqOkBtnClicked)
        self.freqCancelBtn.clicked.connect(self.freqCancelBtnClicked)

        self.gainVal.setText(str(self.gainValCopy))
        self.gainVal.setValidator(doubleValidator)
        # self.gainVal.textChanged.connect(self.validateDblTextEdit(self.freqVal))
        self.gainBtn.clicked.connect(self.gainBtnClicked)
        self.gainOkBtn.clicked.connect(self.gainOkBtnClicked)
        self.gainCancelBtn.clicked.connect(self.gainCancelBtnClicked)

        self.snrVal.setText(str(self.snrValCopy))
        self.snrVal.setValidator(doubleValidator)
        # self.snrVal.textChanged.connect(self.validateDblTextEdit(self.freqVal))
        self.snrBtn.clicked.connect(self.snrBtnClicked)
        self.snrOkBtn.clicked.connect(self.snrOkBtnClicked)
        self.snrCancelBtn.clicked.connect(self.snrCancelBtnClicked)

        self.scanButton.clicked.connect(self.scanBtnClicked)

    def freqBtnClicked(self):
        self.freqVal.setReadOnly(False)
        self.freqVal.selectAll()
        self.freqVal.setFocus()
        self.freqStacked.setCurrentIndex(1)
        self.freqValCopy = self.freqVal.text()

    def freqOkBtnClicked(self):
        self.freqStacked.setCurrentIndex(0)
        self.freqVal.setReadOnly(True)

    def freqCancelBtnClicked(self):
        self.freqVal.setText(self.freqValCopy)
        self.freqStacked.setCurrentIndex(0)
        self.freqVal.setReadOnly(True)

    def gainBtnClicked(self):
        self.gainVal.setReadOnly(False)
        self.gainVal.selectAll()
        self.gainVal.setFocus()
        self.gainStacked.setCurrentIndex(1)
        self.gainValCopy = self.gainVal.text()

    def gainOkBtnClicked(self):
        self.gainStacked.setCurrentIndex(0)
        self.gainVal.setReadOnly(True)

    def gainCancelBtnClicked(self):
        self.gainVal.setText(self.freqValCopy)
        self.gainStacked.setCurrentIndex(0)
        self.gainVal.setReadOnly(True)

    def snrBtnClicked(self):
        self.snrVal.setReadOnly(False)
        self.snrVal.setFocus()
        self.snrVal.selectAll()
        self.snrStacked.setCurrentIndex(1)
        self.snrValCopy = self.snrVal.text()

    def snrOkBtnClicked(self):
        self.snrStacked.setCurrentIndex(0)
        self.snrVal.setReadOnly(True)

    def snrCancelBtnClicked(self):
        self.snrVal.setText(self.snrValCopy)
        self.snrStacked.setCurrentIndex(0)
        self.snrVal.setReadOnly(True)

    def validateDblTextEdit(self, sender):
        def validate(*args, **kwargs):
            validator = sender.validator()
            state = validator.validate(sender.text(), 0)[0]
            if state == QtGui.QValidator.Acceptable:
                color = '#c4df9b'  # green
            elif state == QtGui.QValidator.Intermediate:
                color = '#fff79a'  # yellow
            else:
                color = '#f6989d'  # red
            sender.setStyleSheet('QLineEdit { background-color: %s }' % color)

        return validate

    def scanBtnClicked(self):
        self.scanning = not self.scanning
        if self.scanning:
            self.scanButton.setText('Stop')
        else:
            self.resetScanTimers()
            self.scanButton.setText('Scan')

        self.countdownComplete = False
        self.scanComplete = False

    def resetScanTimers(self):
        self.scanTime = self._startScanTime
        self.countdownTime = self._startCountdownTime
        self.scanTimeVal.setText(str(self.scanTime))
        self.countdownVal.setText(str(self.countdownTime))

    def _updateScanTimer(self):
        if self.scanning:
            if self.countdownComplete:
                self.scanTime -= 1

                if self.scanTime <= 0:
                    self.scanComplete = True
                    self.scanTime = 0

                self.scanTimeVal.setText(str(int(self.scanTime)))

            else:
                self.countdownTime -= 1
                if self.countdownTime <= 0:
                    self.countdownComplete = True
                    self.countdownTime = 0
                self.countdownVal.setText(str(int(self.countdownTime)))

    def closeEvent(self, event):
        if self.telemetry:
            self.telemetry.dispose()


class ZarrConfig(object):
    telemConfig = None
    scanTimerConfig = None
    receiverConfig = None

    def __init__(self, configPath):
        self.path = configPath
        self.config = ConfigParser()
        self.config.read(configPath)

        self.telemConfig = self.MapConfigSection(self.config, 'Telemetry');
        self.scanTimerConfig = self.MapConfigSection(self.config, 'ScanTimer')
        self.receiverConfig = self.MapConfigSection(self.config, 'Receiver')

    def MapConfigSection(self, config, section):
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
            except:
                dict1[option] = None
        return dict1

    def Save(self, path=None):
        if path is None:
            path = self.path

        cfgfile = open(path, 'w')
        # add the settings to the structure of the file, and lets write it out...
        self.config.write(cfgfile)
        cfgfile.close()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()

    zarrConfig = ZarrConfig(CONFIG_PATH)

    zarr = ZarrUi(zarrConfig)
    zarr.start(window)
    qInitResources()


    window.show()
    sys.exit(app.exec_())
    qCleanupResources()
