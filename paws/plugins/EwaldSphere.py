import pandas as pd
import h5py
from threading import Condition
from pyFAI.multi_geometry import MultiGeometry

from .PawsPlugin import PawsPlugin
from .EwaldArch import EwaldArch
from .. import pawstools

class EwaldSphere(PawsPlugin):
    def __init__(self, name='scan0', arches=[], data_file='scan0',
                 scan_data=pd.DataFrame(), int_1d_args={},
                 int_2d_args={}, mg_args={}):
        self.name = name
        self.arches = arches
        self.data_file = data_file
        self.scan_data = scan_data
        self.int_1d_args = int_1d_args
        self.int_2d_args = int_2d_args
        self.mg_args = mg_args
        self.multiGeometry = MultiGeometry([a.integrator for a in self.arches],
                                           **mg_args)
        self.mg_1d_result = None
        self.mg_2d_result = None
        self.file_lock = Condition()
        self.sphere_lock = Condition()
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

    def add_arch(self, arch=None, calculate=True, update=True, **kwargs):
        with self.sphere_lock:
            if arch is None:
                arch = EwaldArch(**kwargs)
            if calculate:
                arch.integrate_1d(**self.int_1d_args)
                arch.integrate_2d(**self.int_2d_args)
            arch.file_lock = self.file_lock
            self.arches.append(arch)
            self.arches = sorted(self.arches, key=lambda a: a.idx)
            try:
                self.scan_data.loc[arch.idx] = pd.Series(arch.scan_info)
            except ValueError:
                self.scan_data = pd.DataFrame(
                    columns = arch.scan_info.keys()
                )
                self.scan_data.loc[arch.idx] = pd.Series(arch.scan_info)
            self.scan_data.sort_index(inplace=True)
            if update:
                self.multiGeometry = MultiGeometry(
                    [a.integrator for a in self.arches], **self.mg_args
                )
                self.int_1d_raw += arch.int_1d_raw
                self.int_1d_pcount += arch.int_1d_pcount
                self.int_1d_norm = self.int_1d_raw / self.int_1d_pcount
                self.int_1d_2theta = arch.int_1d_2theta
                self.int_1d_q = arch.int_1d_q
                self.int_2d_raw += arch.int_2d_raw
                self.int_2d_pcount += arch.int_2d_pcount
                self.int_2d_norm = self.int_2d_raw / self.int_2d_pcount
                self.int_2d_2theta = arch.int_2d_2theta
                self.int_2d_q = arch.int_2d_q

    def mg_integrate_1d(self, monitor=None, **kwargs):
        with self.sphere_lock:
            if monitor is None:
                try:
                    self.mg_1d_result = self.multiGeometry.integrate1d(
                        [a.map_norm for a in self.arches], **kwargs
                    )
                except e as exception:
                    print(e)
                    self.mg_1d_result = self.multiGeometry.integrate1d(
                        [a.map_raw for a in self.arches], **kwargs
                    )
            else:
                self.mg_1d_result = self.multiGeometry.integrate1d(
                    [a.map_raw for a in self.arches], 
                    normalization_factor=list(self.scan_data[monitor]), **kwargs
                )

    def save_to_h5(self, file):
        with self.file_lock:
            if self.name in file:
                del(file[self.name])
            grp = file.create_group(self.name)

            grp.create_group('arches')
            for arch in self.arches:
                arch.save_to_h5(grp['arches'])

            for name in [
                    "int_1d_raw", "int_1d_pcount", "int_1d_norm", 
                    "int_1d_2theta", "int_1d_q", "int_2d_raw", "int_2d_pcount", 
                    "int_2d_norm", "int_2d_2theta", "int_2d_q"]:
                data = getattr(self, name)
                grp.create_dataset(name, data=data)

            for name in ("int_1d_args", "int_2d_args", "mg_args"):
                grp.create_group(name)
                pawstools.dict_to_h5(getattr(self, name), grp[name])

            grp.create_group('scan_data')
            pawstools.dict_to_h5(self.scan_data.to_dict(), grp['scan_data'])




