import sys
from MainWindow import Ui_MainWindow
from rdfinder import UAVRadioFinder
from resources import qInitResources, qCleanupResources
from PyQt5 import QtCore, QtGui, QtWidgets
from threading import Event
from zrc_core import TimerThread
from ConfigParser import ConfigParser
import usb.core

CONFIG_PATH = 'config.ini'

class ZarrController(object):
    def __init__(self):
        self.main = Ui_MainWindow()

        self.freqValCopy = None
        self.snrValCopy = None
        self.gainValCopy = None
        self.scanTime = None
        self.countdownTime = None
        self.scanComplete = False
        self.countdownComplete = False
        self.scanning = False

        self.updateThread = TimerThread(event=Event(), func=self.oneSecUpdate, interval=1.0)

    def start(self, window):
        self.main.setupUi(window)
        self.setup()
        self.updateThread.start()

    def oneSecUpdate(self):
        self._updateScanTimer()



    def setup(self):
        self.freqValCopy = self.main.freqVal.text()
        self.snrValCopy = self.main.snrVal.text()
        self.gainValCopy = self.main.gainVal.text()
        self.scanTime = float(self.main.scanTimeVal.text())
        self.countdownTime = float(self.main.countdownVal.text())

        doubleValidator = QtGui.QDoubleValidator()

        self.main.freqVal.setValidator(doubleValidator)
        # self.main.freqVal.textChanged.connect(self.validateDblTextEdit(self.main.freqVal))
        self.main.freqBtn.clicked.connect(self.freqBtnClicked)
        self.main.freqOkBtn.clicked.connect(self.freqOkBtnClicked)
        self.main.freqCancelBtn.clicked.connect(self.freqCancelBtnClicked)

        self.main.gainVal.setValidator(doubleValidator)
        # self.main.gainVal.textChanged.connect(self.validateDblTextEdit(self.main.freqVal))
        self.main.gainBtn.clicked.connect(self.gainBtnClicked)
        self.main.gainOkBtn.clicked.connect(self.gainOkBtnClicked)
        self.main.gainCancelBtn.clicked.connect(self.gainCancelBtnClicked)

        self.main.snrVal.setValidator(doubleValidator)
        # self.main.snrVal.textChanged.connect(self.validateDblTextEdit(self.main.freqVal))
        self.main.snrBtn.clicked.connect(self.snrBtnClicked)
        self.main.snrOkBtn.clicked.connect(self.snrOkBtnClicked)
        self.main.snrCancelBtn.clicked.connect(self.snrCancelBtnClicked)

        self.main.scanButton.clicked.connect(self.scanBtnClicked)



    def freqBtnClicked(self):
        self.main.freqVal.setReadOnly(False)
        self.main.freqVal.selectAll()
        self.main.freqVal.setFocus()
        self.main.freqStacked.setCurrentIndex(1)
        self.freqValCopy = self.main.freqVal.text()

    def freqOkBtnClicked(self):
        self.main.freqStacked.setCurrentIndex(0)
        self.main.freqVal.setReadOnly(True)

    def freqCancelBtnClicked(self):
        self.main.freqVal.setText(self.freqValCopy)
        self.main.freqStacked.setCurrentIndex(0)
        self.main.freqVal.setReadOnly(True)

    def gainBtnClicked(self):
        self.main.gainVal.setReadOnly(False)
        self.main.gainVal.selectAll()
        self.main.gainVal.setFocus()
        self.main.gainStacked.setCurrentIndex(1)
        self.gainValCopy = self.main.gainVal.text()

    def gainOkBtnClicked(self):
        self.main.gainStacked.setCurrentIndex(0)
        self.main.gainVal.setReadOnly(True)

    def gainCancelBtnClicked(self):
        self.main.gainVal.setText(self.freqValCopy)
        self.main.gainStacked.setCurrentIndex(0)
        self.main.gainVal.setReadOnly(True)

    def snrBtnClicked(self):
        self.main.snrVal.setReadOnly(False)
        self.main.snrVal.setFocus()
        self.main.snrVal.selectAll()
        self.main.snrStacked.setCurrentIndex(1)
        self.snrValCopy = self.main.snrVal.text()

    def snrOkBtnClicked(self):
        self.main.snrStacked.setCurrentIndex(0)
        self.main.snrVal.setReadOnly(True)

    def snrCancelBtnClicked(self):
        self.main.snrVal.setText(self.snrValCopy)
        self.main.snrStacked.setCurrentIndex(0)
        self.main.snrVal.setReadOnly(True)

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
        self.countdownComplete = False
        self.scanComplete = False
        self.scanning = not self.scanning
        if self.scanning:
            self.main.scanButton.setText('Stop')
        else:
            self.main.scanButton.setText('Scan')

    def _updateScanTimer(self):
        if self.scanning:
            if self.countdownComplete:
                self.scanTime -= 1

                if self.scanTime <= 0:
                    self.scanComplete = True
                    self.scanTime = 0
                self.main.scanTimeVal.setText(str(int(self.scanTime)))

            else:
                self.countdownTime -= 1
                if self.countdownTime <= 0:
                    self.countdownComplete = True
                    self.countdownTime = 0
                self.main.countdownVal.setText(str(int(self.countdownTime)))




def MapConfigSection(config, section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
        except:
            dict1[option] = None
    return dict1


def SaveConfig(config):
    cfgfile = open(configPath, 'w')
    # add the settings to the structure of the file, and lets write it out...
    Config.write(cfgfile)
    cfgfile.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()

    config = ConfigParser()
    config.read(CONFIG_PATH)

    telemConfig = MapConfigSection(config, 'Telemetry')
    scanTimerConfig = MapConfigSection(config, 'ScanTimer')
    receiverConfig = MapConfigSection(config, 'Receiver')


    zarr = ZarrController()
    zarr.start(window)
    qInitResources()


    window.show()
    sys.exit(app.exec_())
    qCleanupResources()
