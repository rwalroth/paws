from collections import namedtuple
from dataclasses import dataclass, field

import numpy as np
from pyFAI import units

from .. import pawstools


class nzarray2d():
    def __init__(self, arr=None, ref=None):
        if arr is not None:
            if len(arr.shape) != 2:
                raise IndexError ("Must be 2d array")
            self.data, self.corners = self.get_no_zero(arr, ref)
            self.shape = arr.shape
        else:
            self.data = None
            self.shape = None
            self.corners = None
    
    def get_no_zero(self, arr, ref):
        if ref is None:
            corners = self.get_corners(arr)
        else:
            assert arr.shape == ref.shape, "Reference array has wrong shape"
            corners = self.get_corners(ref)
        
        data = arr[
            corners[0]:corners[1], 
            corners[2]:corners[3]
        ]
        return data, corners
    
    def get_corners(self, arr):
        r = np.nonzero(np.sum(arr, axis=1))[0]
        print(r)
        c = np.nonzero(np.sum(arr, axis=0))[0]
        print(c)
        return (r[0], r[-1], c[0], c[-1])
    
    def full(self):
        arr = np.zeros(self.shape, dtype=self.data.dtype)
        arr[
            self.corners[0]:self.corners[1], 
            self.corners[2]:self.corners[3]
        ] = self.data
        return arr
    
    def __set__(self, obj, val):
        self.__init__(val)
    
    def __add__(self, other):
        full = self.full() + other.full()
        return nzarray2d(full)
    
    def __sub__(self, other):
        full = self.full() - other.full()
        return nzarray2d(full)
    
    def __mul__(self, other):
        full = self.full() * other.full()
        return nzarray2d(full)
    
    def __truediv__(self, other):
        full = self.full() / other.full()
        return nzarray2d(full)
    
    def __div__(self, other):
        full = self.full() / other.full()
        return nzarray2d(full)
    
    def __floordiv__(self, other):
        full = self.full() // other.full()
        return nzarray2d(full)



class nzarray1d():
    def __init__(self, arr=None):
        if arr is not None:
            if len(arr.shape) != 1:
                arr = arr.flatten()
            self.data, self.corners = self.get_no_zero(arr)
            self.shape = arr.shape
        else:
            self.data = None
            self.shape = None
            self.corners = None
    
    def get_no_zero(self, arr):
        c = np.nonzero(arr)[0]
        corners = (c[0], c[-1])
        data = arr[c[0]:c[-1]]
        return data, corners
    
    def full(self):
        arr = np.zeros(self.shape, dtype=self.data.dtype)
        arr[self.corners[0]:self.corners[1]] = self.data
        return arr
    
    def __set__(self, obj, val):
        self.__init__(val)


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

@dataclass
class int_1d_data:
    raw = nzarray1d()
    pcount = nzarray1d()
    norm = nzarray1d()
    ttheta = nzarray1d()
    q = nzarray1d()

    def from_result(self, result, wavelength):
        self.ttheta, self.q = self.parse_unit(
            result, wavelength)

        self.pcount = result._count
        self.raw = result._sum_signal
        self.norm = pawstools.div0(
            self.raw, self.pcount
        )
    
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

@dataclass
class int_2d_data(int_1d_data):
    raw = nzarray2d()
    pcount = nzarray2d()
    chi = nzarray1d()

    def from_result(self, result, wavelength):
        super(int_2d_data, self).from_result(result, wavelength)
        self.chi = result.azimuthal
        
