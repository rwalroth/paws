# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 16:39:57 2019

@author: walroth
"""
import os
import h5py
from collections import OrderedDict
import pandas as pd

from ..Operation import Operation



inputs = OrderedDict(
        spec_file_path=None,
        spec_file_name=None,
        write_h5=False,
        out_file_path=None,
        out_file_name=None
        )

outputs = OrderedDict(
        header=dict(
                meta={},
                motors={},
                motors_r={},
                detectors={},
                detectors_r={}
                ),
        scans=dict(
                scan=pd.DataFrame(),
                meta={}
                ),
        last_line_read=dict(
                number=0,
                text=''
                )
        )

class LoadSpecFile(Operation):
    """Operation for loading in data from a spec file.
    """
    
    def __init__(self):
        super(LoadSpecFile, self).__init__(inputs, outputs)
    
    def run(self):
        goback = os.getcwd()
        try:
            os.chdir(self.inputs['spec_file_path'])
            filename = self.inputs['spec_file_name']
            with open(filename, 'r') as file:
                self.outputs['header'] = self._parse_header(file)
        finally:
            os.chdir(goback)
    
    def _parse_header(self, file):
        return None
    
    def _parse_scan(self, file):
        return None
    