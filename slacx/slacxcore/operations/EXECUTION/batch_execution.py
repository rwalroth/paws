import re
from collections import OrderedDict
import glob

from ..slacxop import Batch
from .. import optools

class BatchFromFiles(Batch):
    """
    Provides a sequence of inputs to be used in repeated execution of a workflow.
    Collects the outputs produced for each of the inputs.
    """

    def __init__(self):
        input_names = ['dir_path','regex','input_route','batch_ops','saved_items']
        output_names = ['batch_inputs','batch_outputs']
        super(BatchFromFiles,self).__init__(input_names,output_names)
        self.input_doc['dir_path'] = 'path to directory containing batch of files to be used as input'
        self.input_doc['regex'] = 'string with * wildcards that will be substituted to indicate input files'
        self.input_doc['input_route'] = 'inputs constructed by the batch executor are directed to this uri'
        self.input_doc['batch_ops'] = str('list of operation uris to be included in batch execution- '
        + 'the order of operations in batch_ops unimportant, as the proper execution stack is resolved at runtime')
        self.input_doc['saved_items'] = 'list of uris to be saved in the batch_outputs'
        self.output_doc['batch_inputs'] = 'list of dicts of [input_route:input_value]'
        self.output_doc['batch_outputs'] = 'list of dicts of [output_route:output_value] for all saved_items '
        self.input_src['dir_path'] = optools.fs_input
        self.input_src['regex'] = optools.user_input 
        self.input_src['input_route'] = optools.wf_input 
        self.input_src['batch_ops'] = optools.wf_input 
        self.input_src['saved_items'] = optools.wf_input 
        self.input_type['regex'] = optools.str_type
        self.input_type['batch_ops'] = optools.list_type 
        self.input_type['saved_items'] = optools.list_type 
        self.inputs['regex'] = '*.tif' 
        self.inputs['batch_ops'] = []
        self.inputs['saved_items'] = []
        
    def run(self):
        """
        Build a list of [uri:value] dicts to be used in the workflow.
        """
        dirpath = self.inputs['dir_path']
        rx = self.inputs['regex']
        inproute = self.inputs['input_route']
        #batch_list = [dirpath+'/'+rx.replace('*',sub) for sub in subs]
        batch_list = glob.glob(dirpath+'/'+rx)
        input_dict_list = []
        output_dict_list = []
        for filename in batch_list:
            inp_dict = OrderedDict() 
            inp_dict[inproute] = filename
            input_dict_list.append(inp_dict)
            output_dict_list.append(OrderedDict())
        self.outputs['batch_inputs'] = input_dict_list
        # Instantiate the batch_outputs list
        self.outputs['batch_outputs'] = output_dict_list 

    def input_list(self):
        return self.outputs['batch_inputs']

    def output_list(self):
        return self.outputs['batch_outputs']

    def input_routes(self):
        """Use the Batch.input_locator to list uri's of all input routes"""
        return optools.val_list(self.input_locator['input_route'])

    def batch_ops(self):
        """Use Batch.batch_ops to list uri's of ops to be included in batch execution"""
        return optools.val_list(self.input_locator['batch_ops'])

    def saved_items(self):
        """Use the Batch.input_locator to list uri's of ops to be saved/stored after execution"""
        return optools.val_list(self.input_locator['saved_items'])


