from collections import namedtuple
from dataclasses import dataclass, field
import numpy as np

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
    raw: np.ndarray = 0
    pcount: np.ndarray = 0
    norm: np.ndarray = 0
    ttheta: np.ndarray = 0
    q: np.ndarray = 0

@dataclass
class int_2d_data:
    raw: np.ndarray = 0
    pcount: np.ndarray = 0
    norm: np.ndarray = 0
    ttheta: np.ndarray = 0
    q: np.ndarray = 0
    chi: np.ndarray = 0
        
