from collections import namedtuple
from dataclasses import dataclass
import numpy as np

@dataclass
class int_1d_data:
    raw: np.ndarray = 0
    pcount: np.ndarray = 0
    norm: np.ndarray = 0
    ttheta: np.ndarray = 0
    q: np.ndarray = 0

@dataclass
class int_2d_data:
    raw: np.ndarray = np.arange(1)
    pcount: np.ndarray = np.arange(1)
    norm: np.ndarray = np.arange(1)
    ttheta: np.ndarray = np.arange(1)
    q: np.ndarray = np.arange(1)
