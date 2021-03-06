from threading import Condition
import time
import pandas as pd
from pyFAI.multi_geometry import MultiGeometry

from ..PawsPlugin import PawsPlugin
from .EwaldArch import EwaldArch, parse_unit
from ...containers import int_1d_data, int_2d_data
from ... import pawstools


class EwaldSphere(PawsPlugin):
    """Class for storing multiple arch objects, and stores a MultiGeometry
    integrator from pyFAI.

    Attributes:
        name: str, name of the sphere
        arches: Series, list of arches indexed by their idx value
        data_file: str, file to save data to
        scan_data: DataFrame, stores all scan metadata
        mg_args: arguments for MultiGeometry constructor
        multi_geo: MultiGeometry instance
        bai_1d_args: dict, arguments for invidivual arch integrate1d method
        bai_2d_args: not implemented
        mgi_1d_I: array, intensity from MultiGeometry based integration
        mgi_1d_2theta: array, two theta from MultiGeometry based integration
        mgi_1d_q: array, q data from MultiGeometry based integration
        mgi_2d_I: not implemented
        mgi_2d_2theta: not implemented
        mgi_2d_q: not implemented
        file_lock: lock for ensuring one writer to hdf5 file
        sphere_lock: lock for modifying data in sphere
        bai_1d: int_1d_data object for by-arch integration
        bai_2d: not implemented

    Methods:
        add_arch: adds new arch and optionally updates other data
        by_arch_integrate_1d: integrates each arch individually and sums them
        set_multi_geo: sets the MultiGeometry instance
        multigeometry_integrate_1d: wrapper for MultiGeometry integrate1d
            method
        save_to_h5: saves data to hdf5 file
        load_from_h5: loads data from hdf5 file
    """
    def __init__(self, name='scan0', arches=[], data_file='scan0',
                 scan_data=pd.DataFrame(), mg_args={'wavelength': 1e-10},
                 bai_1d_args={}, bai_2d_args={}):
        # TODO: add docstring for init
        super().__init__()
        self.name = name
        if arches:
            self.arches = pd.Series(arches, index=[a.idx for a in arches])
        else:
            self.arches = pd.Series()
        self.data_file = data_file
        self.scan_data = scan_data
        self.mg_args = mg_args
        self.multi_geo = MultiGeometry([a.integrator for a in arches], **mg_args)
        self.bai_1d_args = bai_1d_args
        self.bai_2d_args = bai_2d_args
        self.mgi_1d_I = 0
        self.mgi_1d_2theta = 0
        self.mgi_1d_q = 0
        self.mgi_2d_I = 0
        self.mgi_2d_2theta = 0
        self.mgi_2d_q = 0
        self.file_lock = Condition()
        self.sphere_lock = Condition()
        self.bai_1d = int_1d_data()
        self.bai_2d = int_2d_data()

    def add_arch(self, arch=None, calculate=True, update=True, get_sd=True,
                 set_mg=True, **kwargs):
        """Adds new arch to sphere.

        args:
            arch: EwaldArch instance, arch to be added. Recommended to always
                pass a copy of an arch with the arch.copy method
            calculate: whether to run the arch's calculate methods after adding
            update: bool, if True updates the bai_int attribute
            get_sd: bool, if True tries to get scan data from arch
            set_mg: bool, if True sets the MultiGeometry attribute. Takes a
                long time, especially with longer lists. Recommended to run
                set_multi_geo method after all arches are loaded.

        returns None
        """
        with self.sphere_lock:
            if arch is None:
                arch = EwaldArch(**kwargs)
            if calculate:
                arch.integrate_1d(**self.bai_1d_args)
                # arch.integrate_2d(**self.bai_2d_args)
            arch.file_lock = self.file_lock
            self.arches = self.arches.append(pd.Series(arch, index=[arch.idx]))
            self.arches.sort_index(inplace=True)
            if arch.scan_info and get_sd:
                ser = pd.Series(arch.scan_info, dtype='float64')
                if list(self.scan_data.columns):
                    try:
                        self.scan_data.loc[arch.idx] = ser
                    except ValueError:
                        print('Mismatched columns')
                else:
                    self.scan_data = pd.DataFrame(
                        arch.scan_info, index=[arch.idx], dtype='float64'
                    )
            self.scan_data.sort_index(inplace=True)
            if update:
                self._update_bai_1d(arch)
                # self._update_bai_2d(arch)
            if set_mg:
                self.multi_geo = MultiGeometry(
                    [a.integrator for a in self.arches], **self.mg_args
                )

    def by_arch_integrate_1d(self, **args):
        """Integrates all arches individually, then sums the results for
        the overall integration result.

        args: see EwaldArch.integrate_1d
        """
        if not args:
            args = self.bai_1d_args
        else:
            self.bai_1d_args = args.copy()
        with self.sphere_lock:
            self.bai_1d = int_1d_data()
            for arch in self.arches:
                arch.integrate_1d(**args)
                self._update_bai_1d(arch)

    def _update_bai_1d(self, arch):
        """helper function to update overall bai variables.
        """
        self.bai_1d.raw += arch.int_1d.raw
        self.bai_1d.pcount += arch.int_1d.pcount
        self.bai_1d.norm = pawstools.div0(self.bai_1d.raw, self.bai_1d.pcount)
        self.bai_1d.ttheta = arch.int_1d.ttheta
        self.bai_1d.q = arch.int_1d.q

    def set_multi_geo(self, **args):
        """Sets the MultiGeometry instance stored in the arch.

        args: see pyFAI.multiple_geometry.MultiGeometry
        """
        with self.sphere_lock:
            self.multi_geo = MultiGeometry(
                [a.integrator for a in self.arches], **args
            )
            self.mg_args = args

    def multigeometry_integrate_1d(self, monitor=None, **kwargs):
        """Wrapper for integrate1d method of MultiGeometry.

        args:
            monitor: channel with normalization value
            kwargs: see MultiGeometry.integrate1d

        returns:
            result: result from MultiGeometry.integrate1d
        """
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
                    normalization_factor=list(self.scan_data[monitor]),
                    **kwargs
                )

            self.mgi_1d_I = result.intensity

            self.mgi_1d_2theta, self.mgi_1d_q = parse_unit(
                result, self.multi_geo.wavelength)
        return result

    def save_to_h5(self, file, arches=None, data_only=False, replace=False):
        """Saves data to hdf5 file.

        args:
            file: h5py file or group object
        """
        with self.file_lock:
            if self.name in file:
                if replace:
                    del(file[self.name])
                    grp = file.create_group(self.name)
                    grp.create_group('arches')
                else:
                    grp = file[self.name]
                    if 'arches' not in grp:
                        grp.create_group('arches')
            else:
                grp = file.create_group(self.name)
                grp.create_group('arches')

            if arches is None:
                for arch in self.arches:
                    arch.save_to_h5(grp['arches'])
            else:
                for arch in self.arches[
                        list(set(self.arches.index).intersection(
                        set(arches)))]:
                    arch.save_to_h5(grp['arches'])
            if data_only:
                lst_attr = [
                    "scan_data", "mgi_1d_q", "mgi_1d_I", "mgi_2d_2theta", 
                    "mgi_2d_q", "mgi_2d_I"
                ]
            else:
                lst_attr = [
                    "data_file", "scan_data", "mg_args", "bai_1d_args",
                    "bai_2d_args", "mgi_1d_2theta", "mgi_1d_q", "mgi_1d_I",
                    "mgi_2d_2theta", "mgi_2d_q", "mgi_2d_I"
                ]
            pawstools.attributes_to_h5(self, grp, lst_attr)
            for key in ('bai_1d', 'bai_2d'):
                if key not in grp:
                    grp.create_group(key)
            pawstools.attributes_to_h5(self.bai_1d, grp['bai_1d'])
            pawstools.attributes_to_h5(self.bai_2d, grp['bai_2d'])

    def load_from_h5(self, file):
        """Loads data from hdf5 file.

        args:
            file: h5py file or group object
        """
        with self.file_lock:
            with self.sphere_lock:
                if self.name not in file:
                    print("No data can be found")
                grp = file[self.name]

                self.arches = pd.Series()
                for key in grp['arches'].keys():
                    arch = EwaldArch(idx=int(key))
                    arch.load_from_h5(grp['arches'])
                    self.add_arch(
                        arch.copy(), calculate=False, update=False,
                        get_sd=False, set_mg=False
                    )

                lst_attr = [
                    "data_file", "scan_data", "mg_args", "bai_1d_args",
                    "bai_2d_args", "mgi_1d_2theta", "mgi_1d_q", "mgi_1d_I",
                    "mgi_2d_2theta", "mgi_2d_q", "mgi_2d_I"
                ]
                pawstools.h5_to_attributes(self, grp, lst_attr)
                pawstools.h5_to_attributes(self.bai_1d, grp['bai_1d'])
                pawstools.h5_to_attributes(self.bai_2d, grp['bai_2d'])
                self.set_multi_geo(**self.mg_args)
