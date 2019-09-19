import pandas as pd
import h5py
from threading import Condition
from pyFAI.multi_geometry import MultiGeometry
import copy
import numpy as np

from .PawsPlugin import PawsPlugin
from .EwaldArch import EwaldArch, parse_unit
from .. import pawstools

class EwaldSphere(PawsPlugin):
    def __init__(self, name='scan0', arches=[], data_file='scan0',
                 scan_data=pd.DataFrame(), mg_args={'wavelength':1e-10}, 
                 bai_1d_args={}, bai_2d_args={}):
        self.name = name
        self.arches = arches
        self.data_file = data_file
        self.scan_data = scan_data
        self.mg_args = mg_args
        self.multi_geo = MultiGeometry([a.integrator for a in arches], **mg_args)
        self.bai_1d_args = bai_1d_args
        self.bai_2d_args = bai_2d_args
        self.mgi_1d_2theta = 0
        self.mgi_1d_q = 0
        self.mgi_2d_2theta = 0
        self.mgi_2d_q = 0
        self.file_lock = Condition()
        self.sphere_lock = Condition()
        self.bai_1d_raw = 0
        self.bai_1d_pcount = 0
        self.bai_1d_norm = 0
        self.bai_1d_2theta = 0
        self.bai_1d_q = 0
        self.bai_2d_raw = 0
        self.bai_2d_pcount = 0
        self.bai_2d_norm = 0
        self.bai_2d_2theta = 0
        self.bai_2d_q = 0

    def add_arch(self, arch=None, calculate=True, update=True, get_sd=True, 
                 **kwargs):
        with self.sphere_lock:
            if arch is None:
                arch = EwaldArch(**kwargs)
            else:
                arch = arch.copy()
            if calculate:
                arch.integrate_1d(**self.bai_1d_args)
                #arch.integrate_2d(**self.bai_2d_args)
            arch.file_lock = self.file_lock
            self.arches.append(arch)
            self.arches = sorted(self.arches, key=lambda a: a.idx)
            if arch.scan_info != {} and get_sd:
                if len(self.scan_data.columns) > 0:
                    try:
                        self.scan_data.loc[arch.idx] = arch.scan_info
                    except ValueError:
                        print('Mismatched columns')
                else:
                    self.scan_data = pd.DataFrame(
                        arch.scan_info, index=[arch.idx]
                    )
            self.scan_data.sort_index(inplace=True)
            if update:
                self.multi_geo = MultiGeometry(
                    [a.integrator for a in self.arches], **self.mg_args
                )
                self._update_bai_1d(arch)
                #self._update_bai_2d(arch)

    def by_arch_integrate_1d(self, args=self.bai_1d_args):
        with self.sphere_lock:
            self.bai_1d_raw = 0
            self.bai_1d_pcount = 0
            self.bai_1d_norm = 0
            self.bai_1d_2theta = 0
            self.bai_1d_q = 0
            for arch in self.arches:
                arch.integrate_1d(**args)
                self._update_bai_1d(arch)
    
    def _update_bai_1d(self, arch):
        self.bai_1d_raw += arch.int_1d_raw
        self.bai_1d_pcount += arch.int_1d_pcount
        self.bai_1d_norm = pawstools.div0(self.bai_1d_raw, self.bai_1d_pcount)
        self.bai_1d_2theta = arch.int_1d_2theta
        self.bai_1d_q = arch.int_1d_q
    
    def set_multi_geo(self, **args):
        with self.sphere_lock:
            self.multi_geo = MultiGeometry(
                [a.integrator for a in self.arches], **args
            )
            self.mg_args = args
                
    def multigeometry_integrate_1d(self, monitor=None, **kwargs):
        with self.sphere_lock:
            lst_mask = [a.mask for a in self.arches]
            if monitor is None:
                try:
                    result = self.multi_geo.integrate1d(
                        [a.map_norm for a in self.arches], lst_mask=lst_mask, 
                        **kwargs
                    )
                except Exception as e:
                    print(e)
                    result = self.multi_geo.integrate1d(
                        [a.map_raw for a in self.arches], lst_mask=lst_mask,
                        **kwargs
                    )
            else:
                result = self.multi_geo.integrate1d(
                    [a.map_raw for a in self.arches], lst_mask=lst_mask,
                    normalization_factor=list(self.scan_data[monitor]), **kwargs
                )
            
            self.mgi_1d_intensity = result.intensity

            self.mgi_1d_2theta, self.mgi_1d_q = parse_unit(
                result, self.multi_geo.wavelength)
        return result


    def save_to_h5(self, file):
        with self.file_lock:
            if self.name in file:
                del(file[self.name])
            grp = file.create_group(self.name)

            grp.create_group('arches')
            for arch in self.arches:
                arch.save_to_h5(grp['arches'])

            lst_attr = [
                "data_file", "scan_data", "mg_args", "bai_1d_args", 
                "bai_2d_args", "mgi_1d_2theta", "mgi_1d_q", "mgi_2d_2theta", 
                "mgi_2d_q", "bai_1d_raw", "bai_1d_pcount", "bai_1d_norm", 
                "bai_1d_2theta", "bai_1d_q", "bai_2d_raw", "bai_2d_pcount", 
                "bai_2d_norm", "bai_2d_2theta", "bai_2d_q"
            ]
            pawstools.attributes_to_h5(self, lst_attr, grp)
    
    def load_from_h5(self, file):
        with self.file_lock:
            with self.sphere_lock:
                if self.name not in file:
                    return "No data can be found"
                grp = file[self.name]

                self.arches = []
                for key in grp['arches'].keys():
                    arch = EwaldArch(idx=int(key))
                    arch.load_from_h5(grp['arches'])
                    self.add_arch(
                        arch.copy(), calculate=False, update=False, 
                        get_sd=False
                    )

                lst_attr = [
                    "data_file", "scan_data", "mg_args", "bai_1d_args", 
                    "bai_2d_args", "mgi_1d_2theta", "mgi_1d_q", "mgi_2d_2theta", 
                    "mgi_2d_q", "bai_1d_raw", "bai_1d_pcount", "bai_1d_norm", 
                    "bai_1d_2theta", "bai_1d_q", "bai_2d_raw", "bai_2d_pcount", 
                    "bai_2d_norm", "bai_2d_2theta", "bai_2d_q"
                ]
                pawstools.attributes_to_h5(self, lst_attr, grp)

                self.set_multi_geo(**self.mg_args)
            
            

            




