# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 16:39:57 2019

@author: walroth
"""
import os
from collections import OrderedDict
import pandas as pd
from copy import deepcopy

from ..Operation import Operation



date_format = '%a %b %d %H:%M:%S %Y'

inputs = OrderedDict(
        spec_file_path=None,
        spec_file_name=None
        )

outputs = OrderedDict(
        header=dict(
                meta={},
                motors={},
                motors_r={},
                detectors={},
                detectors_r={}
                ),
        scans={},
        scans_meta={},
        last_line_read=dict(
                number=0,
                text=''
                ),
        current_scan = None
        )

class LoadSpecFile(Operation):
    """Operation for loading in data from a spec file.
    """
    
    def __init__(self):
        super(LoadSpecFile, self).__init__(inputs, outputs)
    
    def run(self):
        last_line = self.outputs['last_line_read']['number']
        # goes back to original directory when done
        goback = os.getcwd()
        try:
            os.chdir(self.inputs['spec_file_path'])
            filename = self.inputs['spec_file_name']
            with open(filename, 'r') as file:
                self._read_spec(file, last_line)
            
        finally:
            os.chdir(goback)
        
        return self.outputs
    
    
    def _read_spec(self, file):
        # iterate lines and assign to either head or scan lists
        state = 'beginning'
        head = []
        scan = []

        for lin_num, lin in enumerate(file):
            line = lin.split()
            self.outputs['last_line_read']['number'] = lin_num
            self.outputs['last_line_read']['text'] = lin
            # blank lines are used as breaks separating scans
            if line == []:
                # state flag used to control how lines are parsed
                if state == 'beginning':
                    continue

                elif state == 'head':
                    self._parse_header(head)
                    head = []

                elif state == 'scan':
                    self._parse_scan(scan)
                    scan = []

            else:
                # first item defines what type of info it is
                key = line[0]
                if '#F' in key:
                    state = 'head'
                elif '#S' in key:
                    state = 'scan'
                elif '#L' in key:
                    self.outputs['current_scan'] = pd.DataFrame(columns=line[1:])
                elif '#' not in key:
                    try:
                        cs_idx = self.outputs['current_scan'].index[-1] + 1
                        self.outputs['current_scan'].loc[cs_idx] = soft_list_eval(line)
                    except IndexError:
                        cs_idx = 0
                        self.outputs['current_scan'].loc[cs_idx] = soft_list_eval(line)
                    except AttributeError:
                        self.outputs['current_scan'] = pd.DataFrame(columns=line)
                        self.outputs['current_scan'].loc[0] = soft_list_eval(line)

                if state == 'head':
                    head.append(line)
                elif state == 'scan':
                    scan.append(line)
    
    
    def _parse_header(self, head):
        if head == []:
            return None
        
        else:
            meta = {}
            motors = {}
            motors_r = {}
            detectors = {}
            detectors_r = {}
            for line in head:
                key = line[0][1:]
                if key == 'F': 
                    meta['File'] = line[1:]

                elif key == 'E':
                    meta['Epoch'] = eval(line[1])

                elif key == 'D':
                    meta['Date'] = ' '.join(line[1:])

                elif key == 'C':
                    meta['Comment'] = ' '.join(line[1:])
                    for i, val in enumerate(line):
                        if val == 'User' and line[i + 1] == '=':
                            meta['User'] = line[i+2]
                
                elif 'O' in key:
                    num = int(key[1:])
                    motors[num] = line[1:]
                
                elif 'o' in key:
                    num = int(key[1:])
                    motors_r[num] = line[1:]
                
                elif 'J' in key:
                    num = int(key[1:])
                    detectors[num] = line[1:]
                
                elif 'j' in key:
                    num = int(key[1:])
                    detectors_r[num] = line[1:]
            
            self.outputs['header']['meta'].update(meta)
            self.outputs['header']['motors'].update(motors)
            self.outputs['header']['motors_r'].update(motors_r)
            self.outputs['header']['detectors'].update(detectors)
            self.outputs['header']['detectors_r'].update(detectors_r)
    
    def _parse_scan(self, scan):
        if scan == []:
            return None

        else:
            meta = {'Goniometer': {},
                    'Motors': {}}
            row_list = []
            scan_df = pd.DataFrame()
            for line in scan:
                flag = line[0]
                if '#' in flag:
                    if 'S' in flag:
                        scan_num = int(line[1])
                        meta['Command'] = ' '.join(line[2:])
                        meta['Type'] = line[2]

                    elif 'D' in flag:
                        meta['Date'] = ' '.join(line[1:])

                    elif 'T' in flag or 'M' in flag:
                        meta['Counter'] = {'Amount': eval(line[1]),
                                           'Type': line[2]}

                    elif 'G' in flag:
                        key = int(flag[2:])
                        meta['Goniometer'][key] = soft_list_eval(line[1:])

                    elif 'Q' in flag:
                        meta['HKL'] = soft_list_eval(line[1:])

                    elif 'P' in flag:
                        motor_num = int(flag[2:])
                        names = self.outputs['header']['motors'][motor_num]
                        positions = [eval(x) for x in line[1:]]
                        meta['Motors'].update({name: position 
                            for name, position in zip(names, positions)})
                    # TODO: decide what to do with N;

                    elif 'L' in flag:
                        columns = line[1:]

                else:
                    vals = soft_list_eval(line)
                    row_list.append({col:val for col, val in zip(
                                     columns, vals)})

            scan_df = pd.DataFrame(row_list, columns=columns)
            
            self.outputs['scans'][scan_num] = scan_df.copy()
            self.outputs['scans_meta'][scan_num] = deepcopy(meta)
                        

def soft_list_eval(data):
    """Tries to create list of evaluated items in data. If exception
    is thrown by eval, it just adds the element as is to the list.
    
    args:
        data: list or array-like, input data to be evaluated
    
    returns:
        out: list of values in data with eval applied if possible
    """
    out = []
    for x in data:
        try:
            out.append(eval(x))
        except:
            out.append(x)
    
    return out
    