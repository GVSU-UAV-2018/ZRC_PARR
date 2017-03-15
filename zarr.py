import sys
from MainWindow import Ui_MainWindow
from rdfinder import UAVRadioFinder
from resources import qInitResources, qCleanupResources
from PyQt5 import QtCore, QtGui, QtWidgets


class ZarrController(object):
    def __init__(self):
        self.main = Ui_MainWindow()




    def start(self, window):
        self.main.setupUi(window)
        self.setup()


    def setup(self):
        self.freqValCopy = self.main.freqVal.text()
        self.snrValCopy = self.main.snrVal.text()
        self.gainValCopy = self.main.gainVal.text()

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


    def freqBtnClicked(self):
        self.main.freqVal.setReadOnly(False)
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
        self.main.snrVal.setReadOnly(False)
        self.main.snrStacked.setCurrentIndex(1)
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
        self.main.snrStacked.setCurrentIndex(1)
        self.snrValCopy = self.main.snrVal.text()

    def snrOkBtnClicked(self):
        self.main.snrStacked.setCurrentIndex(0)
        self.main.snrVal.setReadOnly(True)

    def snrCancelBtnClicked(self):
        self.main.snrVal.setText(self.freqValCopy)
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





if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()

    zarr = ZarrController()
    zarr.start(window)
    qInitResources()


    window.show()
    sys.exit(app.exec_())
    qCleanupResources()
