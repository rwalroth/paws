# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 14:21:58 2019

@author: walroth
"""
import copy
from threading import Condition

from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from pyFAI import units
import numpy as np

from ..PawsPlugin import PawsPlugin

from ... import pawstools
from ...containers import PONI, int_1d_data, int_2d_data


def parse_unit(result, wavelength):
    """Helper function to take integrator result and return a two theta
    and q array regardless of the unit used for integration.

    args:
        result: result from 1dintegrator
        wavelength: wavelength for conversion in Angstroms

    returns:
        int_1d_2theta: two theta array
        int_1d_q: q array
    """
    if wavelength is None:
        return result.radial, None

    if result.unit == units.TTH_DEG or str(result.unit) == '2th_deg':
        int_1d_2theta = result.radial
        int_1d_q = (
            (4 * np.pi / wavelength*1e10) *
            np.sin(np.radians(int_1d_2theta / 2))
        )
    elif result.unit == units.Q_A or str(result.unit) == 'q_A^-1':
        int_1d_q = result.radial
        int_1d_2theta = (
            2*np.degrees(
                np.arcsin(
                    int_1d_q *
                    wavelength *
                    1e10 /
                    (4 * np.pi)
                )
            )
        )
    # TODO: implement other unit options for unit
    return int_1d_2theta, int_1d_q


class EwaldArch(PawsPlugin):
    """Class for storing area detector data collected in
    X-ray diffraction experiments.

    Attributes:
        idx: integer name of arch
        map_raw: numpy 2d array of the unprocessed image data
        poni: poni data for integration
        mask: map of pixels to be masked out of integration
        scan_info: information from any relevant motors and sensors
        ai_args: arguments passed to AzimuthalIntegrator
        file_lock: lock to ensure only one writer to data file
        integrator: AzimuthalIntegrator object from pyFAI
        arch_lock: threading lock used to ensure only one process can
            access data at a time
        map_norm: normalized image data
        map_q: reciprocal space coordinates for data
        int_1d: int_1d_data object from containers
        int_2d: int_2d_data object from containers

    Methods:
        integrate_1d: integrate the image data to create I, 2theta, q,
            and normalization arrays
        integrate_2d: not implemented
        set_integrator: set new integrator
        set_map_raw: replace raw data
        set_poni: replace poni object
        set_mask: replace mask data
        set_scan_info: replace scan_info
        save_to_h5: save data to hdf5 file
        load_from_h5: load data from hdf5 file
        copy: create copy of arch
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, idx=None, map_raw=None, poni=PONI(), mask=None,
                 scan_info={}, ai_args={}, file_lock=Condition()):
        # pylint: disable=too-many-arguments
        super(EwaldArch, self).__init__()
        self.idx = idx
        self.map_raw = map_raw
        self.poni = poni
        if mask is None and map_raw is not None:
            self.mask = np.where(map_raw < 0, 1, 0)
        else:
            self.mask = mask
        self.scan_info = scan_info
        self.ai_args = ai_args
        self.file_lock = file_lock
        self.integrator = AzimuthalIntegrator(
            dist=self.poni.dist,
            poni1=self.poni.poni1,
            poni2=self.poni.poni2,
            rot1=self.poni.rot1,
            rot2=self.poni.rot2,
            rot3=self.poni.rot3,
            wavelength=self.poni.wavelength,
            detector=self.poni.detector,
            **ai_args
        )
        self.arch_lock = Condition()
        self.map_norm = 0
        self.map_q = 0
        self.int_1d = int_1d_data()
        self.int_2d = int_2d_data()
        self.xyz = None  # TODO: implement rotations to generate pixel coords
        self.tcr = None
        self.qchi = None

    def integrate_1d(self, numpoints=10000, radial_range=[0, 180],
                     monitor=None, unit=units.TTH_DEG, **kwargs):
        """Wrapper for integrate1d method of AzimuthalIntegrator from pyFAI.
        Sets 1d integration variables for object instance.

        args:
            numpoints: int, number of points in final array
            radial_range: tuple or list, lower and upper end of integration
            monitor: str, keyword for normalization counter in scan_info
            unit: pyFAI unit for integration, units.TTH_DEG or units.Q_A
            kwargs: other keywords to be passed to integrate1d, see pyFAI docs.

        returns:
            result: integrate1d result from pyFAI.
        """
        with self.arch_lock:
            if monitor is not None:
                self.map_norm = self.map_raw/self.scan_info[monitor]
            else:
                self.map_norm = self.map_raw
            if self.mask is None:
                self.mask = np.where(self.map_raw < 0, 1, 0)

            result = self.integrator.integrate1d(
                self.map_norm, numpoints, unit=unit, radial_range=radial_range,
                mask=self.mask, **kwargs
            )

            self.int_1d.ttheta, self.int_1d.q = parse_unit(
                result, self.poni.wavelength)

            self.int_1d.pcount = result._count
            self.int_1d.raw = result._sum_signal
            self.int_1d.norm = pawstools.div0(
                self.int_1d.raw, self.int_1d.pcount
            )
        return result

    def integrate_2d(self):
        """Not implemented.
        """
        with self.arch_lock:
            pass

    def set_integrator(self, **args):
        """Sets AzimuthalIntegrator with new arguments and instances poni
        attribute.

        args:
            args: see pyFAI for acceptable arguments for the integrator
                constructor.

        returns:
            None
        """

        with self.arch_lock:
            self.ai_args = args
            self.integrator = AzimuthalIntegrator(
                dist=self.poni.dist,
                poni1=self.poni.poni1,
                poni2=self.poni.poni2,
                rot1=self.poni.rot1,
                rot2=self.poni.rot2,
                rot3=self.poni.rot3,
                wavelength=self.poni.wavelength,
                detector=self.poni.detector,
                **args
            )

    def set_map_raw(self, new_data):
        with self.arch_lock:
            self.map_raw = new_data
            if self.mask is None:
                self.mask = np.where(self.map_raw < 0, 1, 0)

    def set_poni(self, new_data):
        with self.arch_lock:
            self.poni = new_data

    def set_mask(self, new_data):
        with self.arch_lock:
            self.mask = new_data

    def set_scan_info(self, new_data):
        with self.arch_lock:
            self.scan_info = new_data

    def save_to_h5(self, file):
        """Saves data to hdf5 file using h5py as backend.

        args:
            file: h5py group or file object.

        returns:
            None
        """
        with self.file_lock:
            if str(self.idx) in file:
                del(file[str(self.idx)])
            grp = file.create_group(str(self.idx))
            lst_attr = [
                "map_raw", "mask", "map_norm", "map_q", "xyz", "tcr", "qchi",
                "scan_info", "ai_args"
            ]
            pawstools.attributes_to_h5(self, grp, lst_attr)
            grp.create_group('int_1d')
            pawstools.attributes_to_h5(self.int_1d, grp['int_1d'])
            grp.create_group('int_2d')
            pawstools.attributes_to_h5(self.int_2d, grp['int_2d'])
            grp.create_group('poni')
            pawstools.dict_to_h5(self.poni.to_dict(), grp['poni'])

    def load_from_h5(self, file):
        """Loads data from hdf5 file and sets attributes.

        args:
            file: h5py file or group object

        returns:
            None
        """
        with self.file_lock:
            with self.arch_lock:
                if str(self.idx) not in file:
                    print("No data can be found")
                grp = file[str(self.idx)]
                lst_attr = [
                    "map_raw", "mask", "map_norm", "map_q", "xyz", "tcr",
                    "qchi", "scan_info", "ai_args"
                ]
                pawstools.h5_to_attributes(self, grp, lst_attr)
                pawstools.h5_to_attributes(self.int_1d, grp['int_1d'])
                pawstools.h5_to_attributes(self.int_2d, grp['int_2d'])
                self.poni = PONI.from_yamdict(
                    pawstools.h5_to_dict(grp['poni'])
                )
                self.integrator = AzimuthalIntegrator(
                    dist=self.poni.dist,
                    poni1=self.poni.poni1,
                    poni2=self.poni.poni2,
                    rot1=self.poni.rot1,
                    rot2=self.poni.rot2,
                    rot3=self.poni.rot3,
                    wavelength=self.poni.wavelength,
                    detector=self.poni.detector,
                    **self.ai_args
                )

    def copy(self):
        arch_copy = EwaldArch(
            copy.deepcopy(self.idx), copy.deepcopy(self.map_raw),
            copy.deepcopy(self.poni), copy.deepcopy(self.mask),
            copy.deepcopy(self.scan_info), copy.deepcopy(self.ai_args),
            self.file_lock
        )
        arch_copy.integrator = copy.deepcopy(self.integrator)
        arch_copy.arch_lock = Condition()
        arch_copy.map_norm = copy.deepcopy(self.map_norm)
        arch_copy.map_q = copy.deepcopy(self.map_q)
        arch_copy.int_1d = copy.deepcopy(self.int_1d)
        arch_copy.int_2d = copy.deepcopy(self.int_2d)
        arch_copy.xyz = copy.deepcopy(self.xyz)
        arch_copy.tcr = copy.deepcopy(self.tcr)
        arch_copy.qchi = copy.deepcopy(self.qchi)

        return arch_copy
