from collections import namedtuple
from dataclasses import dataclass, field
import copy

import numpy as np
from pyFAI import units

from .. import pawstools


class nzarray1d():
    def __init__(self, arr=None):
        if isinstance(arr, self.__class__):
            self.data = copy.deepcopy(arr.data)
            self.shape = copy.deepcopy(arr.shape)
            self.corners = copy.deepcopy(arr.corners)
        elif arr is None:
            self.data = None
            self.shape = None
            self.corners = None
        else:
            self.shape = self.get_shape(arr)
            self.corners = self.get_corners(arr)
            self.data = self.get_data(arr)
    
    def get_shape(self, arr):
        assert len(arr.shape) == 1, "Must be 1d array."
        return arr.shape
    
    def get_corners(self, arr):
        if (arr == 0).all():
            return [0,0]
        else:
            c = np.nonzero(arr)[0]
            return (c[0], c[-1] + 1)
    
    def get_data(self, arr):
        data = arr[
            self.corners[0]:self.corners[1]
        ]
        return data
    
    def full(self):
        if self.data is None:
            return None
        full = np.zeros(self.shape, dtype=self.data.dtype)
        full[self.corners[0]:self.corners[1]] = self.data
        return full

    def intersect(self, other):
        assert \
            self.shape == other.shape, \
            "Can't divide nzarray of different shape"
        out = nzarray1d()
        
        out.shape = self.shape[:]
        out.corners = [min(self.corners[0], other.corners[0]),
                    max(self.corners[1], other.corners[1])]
        out.data = np.zeros((out.corners[1] - out.corners[0],))

        other_data = np.zeros_like(out.data)
        
        i0, i1 = out._shift_index(self.corners)
        out.data[i0:i1] = self.data
        
        i0, i1 = out._shift_index(other.corners)
        other_data[i0:i1] = other.data
        
        return out, other_data
    
    def _shift_index(self, idx):
        out = []
        for i, val in enumerate(idx):
            j = i - i % 2
            idx = self._get_idx(val, j)
            out.append(idx - self.corners[j])
        return out
    
    def _get_idx(self, x, i=0):
        if x >= 0:
            idx = x
        else:
            idx = self.shape[i] + x
        return idx
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.start is None or key.stop is None:
                return self.full()[key]
            elif self._get_idx(key.start) >= self.corners[0] and self._get_idx(key.stop) <= self.corners[1]:
                start, stop = self._shift_index([key.start, key.stop])
                return self.data[slice(start, stop, key.step)]
            else:
                return self.full()[key]
        elif type(key) == int:
            idx = self._get_idx(key)
            if self.corners[0] <= idx < self.corners[1]:
                return self.data[idx - self.corners[0]]
            else:
                return 0
        else:
            return self.full()[key]
    
    def __set__(self, obj, val):
        if isinstance(val, self.__class__):
            self.data = val.data
            self.corners = val.corners
            self.shape = val.shape
        else:
            self.__init__(val)
    
    def __add__(self, other):
        if isinstance(other, self.__class__):
            out, temp = self.intersect(other)
            out.data += temp
        elif np.isscalar(other) or type(other) == np.ndarray:
            out = self.__class__(self.full() + other)
        return out
    
    def __sub__(self, other):
        if isinstance(other, self.__class__):
            out, temp = self.intersect(other)
            out.data -= temp
        elif np.isscalar(other) or type(other) == np.ndarray:
            out = self.__class__(self.full() - other)
        return out
    
    def __mul__(self, other):
        if isinstance(other, self.__class__):
            out, temp = self.intersect(other)
            out.data *= temp
        elif np.isscalar(other) or type(other) == np.ndarray:
            out = self.__class__(self.full() * other)
        return out
    
    def __div__(self, other):
        return self.__truediv__(other)
    
    def __truediv__(self, other):
        if isinstance(other, self.__class__):
            out, temp = self.intersect(other)
            out.data = pawstools.div0(out.data, temp)
        elif np.isscalar(other) or type(other) == np.ndarray:
            out = self.__class__(pawstools.div0(self.full(), other))
        return out
    
    def __floordiv__(self, other):
        if isinstance(other, self.__class__):
            out, temp = self.intersect(other)
            out.data = pawstools.div0(out.data, temp).astype(int)
        elif np.isscalar(other) or type(other) == np.ndarray:
            out = self.__class__(
                pawstools.div0(self.full(), other).astype(int)
            )
        return out


class nzarray2d(nzarray1d):
    def __init__(self, arr=None):
        super().__init__(arr)
    
    def get_shape(self, arr):
        assert len(arr.shape) == 2, 'Must be 2D array.'
        return arr.shape[:]
    
    def get_corners(self, arr):
        if (arr == 0).all():
            return [0,0,0,0]
        else:
            r = np.nonzero(arr)[0]
            c = np.nonzero(arr)[1]
            return (min(r), max(r) + 1, min(c), max(c) + 1)
    
    def get_data(self, arr):
        data = arr[
            self.corners[0]:self.corners[1], 
            self.corners[2]:self.corners[3]
        ]
        return data
    
    def full(self):
        if self.data is None:
            return None
        arr = np.zeros(self.shape, dtype=self.data.dtype)
        arr[
            self.corners[0]:self.corners[1], 
            self.corners[2]:self.corners[3]
        ] = self.data
        return arr
    
    def intersect(self, other):
        if np.isscalar(other):
            out = nzarray2d(self.full())
            other_data = other
        assert self.shape == other.shape, "Can't divide nzarray of different shape"
        out = nzarray2d()
        
        out.shape = self.shape[:]
        out.corners = [min(self.corners[0], other.corners[0]),
                       max(self.corners[1], other.corners[1]),
                       min(self.corners[2], other.corners[2]),
                       max(self.corners[3], other.corners[3])]
        
        out.data = np.zeros((out.corners[1] - out.corners[0],
                         out.corners[3] - out.corners[2]))
        
        other_data = np.zeros_like(out.data)
        
        r0, r1, c0, c1 = out._shift_index(self.corners)
        
        out.data[r0:r1,c0:c1] = self.data
        
        r0, r1, c0, c1 = out._shift_index(other.corners)
        
        other_data[r0:r1,c0:c1] = other.data
        
        return out, other_data
    
    def __getitem__(self, key):
        print(key)
        return self.full()[key]


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
        self.raw = nzarray1d()
        self.pcount = nzarray1d()
        self.norm = nzarray1d()
        self.ttheta = nzarray1d()
        self.q = nzarray1d()

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
        
