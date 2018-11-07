import os
import copy
from collections import OrderedDict

import numpy as np

from ...Workflow import Workflow 
from ...IO.BL15.LEGACY.ReadTimeSeries import ReadTimeSeries 
from .. import IntegrateTimeSeries as IntegrateTimeSeries_new

class IntegrateTimeSeries(IntegrateTimeSeries_new.IntegrateTimeSeries):
    
    def __init__(self):
        super(IntegrateTimeSeries,self).__init__(inputs,outputs)
        # replace reader with LEGACY reader
        self.add_operation(read = ReadTimeSeries())

