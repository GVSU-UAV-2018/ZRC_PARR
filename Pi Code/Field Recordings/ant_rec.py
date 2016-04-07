#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Ant Rec
# Generated: Fri Nov 20 17:39:23 2015
##################################################

from PyQt4 import Qt
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import fcdproplus
import sys

from distutils.version import StrictVersion
class ant_rec(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Ant Rec")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Ant Rec")
        try:
             self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
             pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "ant_rec")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())


        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 192000
        self.gain = gain = 20
        self.collar_freq = collar_freq = 150.742e6-3000
        self.SNR = SNR = 5

        ##################################################
        # Blocks
        ##################################################
        self.fcdproplus_fcdproplus_0 = fcdproplus.fcdproplus("",1)
        self.fcdproplus_fcdproplus_0.set_lna(1)
        self.fcdproplus_fcdproplus_0.set_mixer_gain(1)
        self.fcdproplus_fcdproplus_0.set_if_gain(gain)
        self.fcdproplus_fcdproplus_0.set_freq_corr(22)
        self.fcdproplus_fcdproplus_0.set_freq(collar_freq - 3000)
          
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, "b_3", False)
        self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.fcdproplus_fcdproplus_0, 0), (self.blocks_file_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "ant_rec")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.fcdproplus_fcdproplus_0.set_if_gain(self.gain)

    def get_collar_freq(self):
        return self.collar_freq

    def set_collar_freq(self, collar_freq):
        self.collar_freq = collar_freq
        self.fcdproplus_fcdproplus_0.set_freq(self.collar_freq - 3000)

    def get_SNR(self):
        return self.SNR

    def set_SNR(self, SNR):
        self.SNR = SNR

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."
    if(StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0")):
        Qt.QApplication.setGraphicsSystem(gr.prefs().get_string('qtgui','style','raster'))
    qapp = Qt.QApplication(sys.argv)
    tb = ant_rec()
    tb.start()
    tb.show()
    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()
    tb = None #to clean up Qt widgets
