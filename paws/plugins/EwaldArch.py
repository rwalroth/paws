# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 14:21:58 2019

@author: walroth

From docs:
    
EwaldArch is a Class for storing single diffraction images collected by EwaldWorkflow. 
Basic functions for mapping pixels, rotating them, and integrating them are stored here. 
EwaldArch objects are meant to be stored in a larger EwaldSphere object for global integration. 
EwaldArch inherits from the PawsPlugin class. The arch_lock condition should be used when modifying any 
data contained in an EwaldArch object.

**Attributes**

* map_raw: numpy 2d array of the unprocessed image data
* map_corr: image data corrected for any masks, flat filed, dark current, etc corrections
* map_xyz: rotated Cartesian coordinates for the pixels
* map_tpr: rotated spherical coordinates for the pixels (theta, phi, r)
* map_q: reciprocal space coordinates for the 2D data
* int_raw: raw integrated 1D pattern
* int_pcount: values to use for normalizing the 1D pattern by number of pixels in each two-theta bin
* int_norm: normalized 1D pattern
* int_2theta: 1D 2 theta array
* int_q: q values for 1D array
* scan_info: information from any relevant motors and sensors 
* rotations: dictionary of the order of rotations to be done, and the angles to apply
* arch_lock: threading lock used to ensure only one process can access data at a time

**Methods**

* read_file: read in data from file as a numpy array
* apply_corrections: apply any corrections needed for the data
* rotate: rotates the provided xyz_map based on the provided rotation order and angles
* cart_to_sphere: converts Cartesian coordinates to spherical
* sphere_to_q: converts spherical coordinates to reciprocal space
* integrate_1d: integrate the image data to create I, 2θ, q, and normalization arrays
* read_raw (static): reads in raw file format and returns a numpy array
* mask: applies a provided mask to make any undesired pixels negative
* rot_x (static): rotates about x axis (orthogonal to beam, horizontal)
* rot_y (static): rotates about the y axis (orthogonal to beam, vertical)
* rot_z (static): rotates about the z axis (collinear with the beam)
"""
import sys
import os
import h5py
from threading import Condition
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from pyFAI import units
import numpy as np
import yaml

from .PawsPlugin import PawsPlugin

from .. import pawstools
from ..containers import PONI


class EwaldArch(PawsPlugin):
    """Class for storing area detector data collected in
    X-ray diffraction experiments.

    Attributes:
        map_raw: numpy 2d array of the unprocessed image data
        mask: map of pixels to be masked out of integration
        PONI: poni data for integration
        int_raw: raw integrated 1D pattern
        int_pcount: values to use for normalizing the 1D pattern by number
            of pixels in each two-theta bin
        int_norm: normalized 1D pattern
        int_2theta: 1D 2 theta array
        int_q: q values for 1D array
        map_q: reciprocal space coordinates for data
        scan_info: information from any relevant motors and sensors
        rotations: dictionary of the order of rotations to be done,
            and the angles to apply
        arch_lock: threading lock used to ensure only one process can
            access data at a time

    Methods:
        integrate_1d: integrate the image data to create I, 2theta, q, and
            normalization arrays
        integrate_2d: integrate the image data in 2D
    """
    
    def __init__(self, idx=None, map_raw=None, PONI=PONI(), mask=None,
                 scan_info={}, file_lock=Condition()):
        self.idx = idx
        self.map_raw = map_raw
        self.mask = mask
        self.PONI = PONI
        self.integrator = AzimuthalIntegrator(
            dist=self.PONI.dist,
            poni1=self.PONI.poni1, 
            poni2=self.PONI.poni2, 
            rot1=self.PONI.rot1,
            rot2=self.PONI.rot2,
            rot3=self.PONI.rot3,
            wavelength=self.PONI.wavelength,
            detector=self.PONI.detector
        )
        self.scan_info = scan_info
        self.file_lock = file_lock
        self.arch_lock = Condition()
        self.map_norm = 0
        self.map_q = 0
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
        self.xyz = None # TODO: implement rotations to generate pixel coordinates
        self.tcr = None
        self.qchi = None
    
    
    def integrate_1d(self, numpoints=10000, radial_range=[0,180],
                     monitor='i0', unit=units.TTH_DEG, **kwargs):
        with self.arch_lock:
            self.map_norm = self.map_raw/self.scan_info[monitor]
            if self.mask is None:
                self.mask_from_raw()
            
            result = self.integrator.integrate1d(
                self.map_norm, numpoints, unit=unit, radial_range=radial_range, 
                mask=self.mask, **kwargs
            )
            
            if unit == units.TTH_DEG:
                self.int_1d_2theta = result.radial
                self.int_1d_q = (
                    (4 * np.pi / self.PONI.wavelength*1e10)
                    * np.sin(np.radians(self.int_1d_2theta / 2))
                )
            elif unit == units.Q_A:
                self.int_1d_q = result.radial
                self.int_1d_q = (
                    2*np.degrees(
                        np.arcsin(
                            self.int_1d_q *
                            self.PONI.wavelength *
                            1e10 /
                            (4 * np.pi)
                        )
                    )
                )
            # TODO: implement other unit options for unit
            self.int_1d_pcount = result._count
            self.int_1d_raw = result._sum_signal
            self.int_1d_norm = self.int_1d_raw/self.int_1d_pcount
    
    
    def integrate_2d(self):
        with self.arch_lock:
            pass
    
    def mask_from_raw(self):
        with self.arch_lock:
            self.mask = np.where(self.map_raw < 0, 1, 0)
    
    def set_map_raw(self, new_data):
        with self.arch_lock:
            self.map_raw = new_data
    
    
    def set_PONI(self, new_data):
        with self.arch_lock:
            self.PONI = new_data
            
    
    def set_mask(self, new_data):
        with self.arch_lock:
            self.mask = new_data
    
    
    def set_scan_info(self, new_data):
        with self.arch_lock:
            self.scan_info = new_data
    
    def save_to_h5(self, file):
        with self.file_lock:
            if str(self.idx) in file:
                del(file[str(self.idx)])
            grp = file.create_group(str(self.idx))
            for name in [
                    "map_raw", "set_mask", "map_norm", "map_q", "int_1d_raw",
                    "int_1d_pcount", "int_1d_norm", "int_1d_2theta", "int_1d_q",
                    "int_2d_raw", "int_2d_pcount", "int_2d_norm", 
                    "int_2d_2theta", "int_2d_q", "xyz", "tcr", "qchi"]:
                data = self.__getattribute__(name)
                if data is None:
                    data = h5py.Empty("f")
                grp.create_dataset(name, data=data)
            grp.create_group('PONI')
            pawstools.dict_to_h5(self.PONI.to_dict(), grp['PONI'])
            grp.create_group('scan_info')
            pawstools.dict_to_h5(self.scan_info, grp['scan_info'])
    
    def load_from_h5(self, file):
        with self.file_lock:
            if str(self.idx) not in file:
                return "No data can be found"
            grp = file[str(self.idx)]
            for name in [
                    "map_raw", "set_mask", "map_norm", "map_q", "int_1d_raw",
                    "int_1d_pcount", "int_1d_norm", "int_1d_2theta", "int_1d_q",
                    "int_2d_raw", "int_2d_pcount", "int_2d_norm",
                    "int_2d_2theta", "int_2d_q", "xyz", "tcr", "qchi"]:
                data = grp[name]
                if data == h5py.Empty("f"):
                    data = None
                elif data.shape == ():
                    data = data[...].item()
                else:
                    data = data[()]
                self.__setattr__(name, data)
            self.PONI = PONI.from_yamdict(pawstools.h5_to_dict(grp['PONI']))
            self.scan_info = pawstools.h5_to_dict(grp['scan_info'])
    
