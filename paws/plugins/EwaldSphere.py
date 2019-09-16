from . import PawsPlugin
from .EwaldArch import EwaldArch
import h5py

class EwaldSphere(PawsPlugin):
    def __init__(self, arches=[], data_file=None, int_1d_args=None, 
                 int_2d_args=None):
        self.arches = arches
        self.data_file = data_file
        self.int_1d_args = int_1d_args
        self.int_2d_args = int_2d_args
        self.file_lock = Condition()
        self.int_1d_raw = 0
        self.int_1d_pcount = 0
        self.int_1d_norm = 0
        self.int_1d_2theta = 0
        self.int_1d_q = 0
        self.int_2d_raw = 0
        self.int_2d_pcount = 0
        self.int_2d_norm = 0
        self.int_2d_2theta = 0
        self.int_2d_q = 0
    
    def add_arch(self, arch, calculate=True, update=True):
        if calculate:
            arch.integrate_1d(**self.int_1d_args)
            arch.integrate_2d(**self.int_2d_args)
        arch.file_lock = self.file_lock
        self.arches.append(arch)
        if update:
            self.int_1d_raw += arch.int_1d_raw
            self.int_1d_pcount += arch.int_1d_pcount
            self.int_1d_norm += arch.int_1d_norm
            self.int_1d_2theta += arch.int_1d_2theta
            self.int_1d_q += arch.int_1d_q
            self.int_2d_raw += arch.int_2d_raw
            self.int_2d_pcount += arch.int_2d_pcount
            self.int_2d_norm += arch.int_2d_norm
            self.int_2d_2theta += arch.int_2d_2theta
            self.int_2d_q += arch.int_2d_q

