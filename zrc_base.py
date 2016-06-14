from abc import ABCMeta, abstractmethod, abstractproperty

class RadioFinderBase(metaclass=ABCMeta, object):
    @property
    def gain(self):
        pass

    @gain.setter
    @abstractproperty
    def gain(self, val):
        pass

    @property
    def scan_frequency(self):
        pass

    @gain.setter
    @abstractproperty
    def scan_frequency(self, val):
        pass

    @property
    def snr_threshold(self):
        pass

    @gain.setter
    @abstractproperty
    def snr_threshold(self, val):
        pass

    @abstractmethod
    def is_scanning(self):
        pass

    @abstractmethod
    def start_scanning(self):
        pass

    @abstractmethod
    def stop_scanning(self):
        pass