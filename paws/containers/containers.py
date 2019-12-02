from collections import namedtuple
from dataclasses import dataclass, field
import copy

import numpy as np
from pyFAI import units
import h5py

from .nzarrays import nzarray1d, nzarray2d
from .. import pawstools


class NoZeroArray():
    def __get__(self, instance, owner):
        if self.data is None:
            return None
        else:
            arr = np.zeros(self.shape)
            arr[
                self.corners[0]:self.corners[1], 
                self.corners[2]:self.corners[3]
            ] = self.data
            return arr[()]
    
    def __set__(self, instance, value):
        if value is None:
            self.shape = None
            self.corners = None
            self.data = None
        else:
            self.shape = value.shape
            r = np.nonzero(np.sum(value, axis=0))[0]
            c = np.nonzero(np.sum(value, axis=1))[0]
            self.corners = (r[0], r[-1], c[0], c[-1])
            self.data = value[r[0]:r[-1], c[0]:c[-1]]

class int_1d_data:
    def __init__(self, raw=None, pcount=None, norm=None, ttheta=None, q=None):
        self.raw = nzarray1d(raw)
        self.pcount = nzarray1d(pcount)
        self.norm = nzarray1d(norm)
        self.ttheta = ttheta
        self.q = q

    def from_result(self, result, wavelength):
        self.ttheta, self.q = self.parse_unit(
            result, wavelength)

        self.pcount = result._count
        self.raw = result._sum_signal
        self.norm = self.raw/self.pcount
    
    def parse_unit(self, result, wavelength):
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
                (4 * np.pi / (wavelength*1e10)) *
                np.sin(np.radians(int_1d_2theta / 2))
            )
        elif result.unit == units.Q_A or str(result.unit) == 'q_A^-1':
            int_1d_q = result.radial
            int_1d_2theta = (
                2*np.degrees(
                    np.arcsin(
                        int_1d_q *
                        (wavelength * 1e10) /
                        (4 * np.pi)
                    )
                )
            )
        # TODO: implement other unit options for unit
        return int_1d_2theta, int_1d_q

    def to_hdf5(self, grp, compression=None):
        raw = grp.create_group('raw')
        self.raw.to_hdf5(raw, compression)
        pcount = grp.create_group('pcount')
        self.pcount.to_hdf5(pcount, compression)
        norm = grp.create_group('norm')
        self.norm.to_hdf5(norm, compression)
        grp.create_dataset('ttheta', data=self.ttheta, compression=compression)
        grp.create_dataset('q', data=self.q, compression=compression)
    
    def from_hdf5(self, grp):
        self.raw.from_hdf5(grp['raw'])
        self.pcount.from_hdf5(grp['pcount'])
        self.norm.from_hdf5(grp['norm'])
        self.ttheta = grp['ttheta'][()]
        self.q = grp['q'][()]
    
    def __add__(self, other):
        self.raw += other.raw
        self.pcount += other.pcount
        self.norm = self.raw/self.pcount
        

class int_2d_data(int_1d_data):
    def __init__(self,  raw=None, pcount=None, norm=None, ttheta=None, q=None,
                 chi=None):
        self.raw = nzarray2d(raw)
        self.pcount = nzarray2d(pcount)
        self.norm = nzarray2d(norm)
        self.ttheta = ttheta
        self.q = q
        self.chi = chi

    def from_result(self, result, wavelength):
        super(int_2d_data, self).from_result(result, wavelength)
        self.chi = result.azimuthal
    
    def from_hdf5(self, grp):
        super().from_hdf5(grp)
        self.chi = grp['chi'][()]
    
    def to_hdf5(self, grp, compression=None):
        super().to_hdf5(grp, compression)
        grp.create_dataset('chi', data=self.chi, compression=compression)
