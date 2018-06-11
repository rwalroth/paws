from __future__ import print_function
from collections import OrderedDict
from functools import partial
import importlib
import copy
import os
import re
#from multiprocessing import Process,Pool

import yaml

from .. import operations
from ..operations.OpManager import OpManager
from ..plugins.PluginManager import PluginManager
from .Workflow import Workflow
from .. import pawstools

class WfManager(object):
    """Manager for paws Workflows. 

    The WfManager is the most-used object in paws.
    WfManager keeps a reference to a PluginManager and OpManager
    for access to whatever PawsPlugins and Operations
    are found in the current installation of paws.
    """

    def __init__(self,op_manager=None,plugin_manager=None):
        """Initialize a workflow manager.

        Parameters
        ----------
        op_manager : OpManager (optional)
            an operations manager (see paws.operations.OpManager)-
            if not provided, a default OpManager will be created.
        plugin_manager : PluginManager (optional)
            a plugins manager (see paws.plugins.PluginManager)-
            if not provided, a default PluginManager will be created.
        """
        super(WfManager,self).__init__()
        if not op_manager:
            op_manager = OpManager()
        if not plugin_manager:
            plugin_manager = PluginManager()
        self.op_manager = op_manager 
        self.plugin_manager = plugin_manager 
        self.workflows = OrderedDict() 
        # dict of workflow clones for executing across threads:
        self.wf_clones = OrderedDict()
        # dict of bools to keep track of who is at work:
        self.wf_running = OrderedDict() 
        self.message_callback = self.tagged_print
        self.pool=None

    def tagged_print(self,msg):
        print('[{}] {}'.format(type(self).__name__,msg))

    def add_workflow(self,wf_name):
        """Name and add a workflow.

        If `wf_name` is not unique (i.e. a workflow with that name already exists),
        this method will overwrite the existing workflow with a new one.

        Parameters
        ----------
        wf_name : str
            name to give to the new Workflow

        Returns
        -------
        wf : Workflow
            a reference to the new Workflow
        """
        wf = Workflow()
        if not wf.is_tag_valid(wf_name): 
            raise pawstools.WfNameError(wf.tag_error_message(wf_name))
        #wf.message_callback = self.message_callback
        self.workflows[wf_name] = wf
        self.wf_running[wf_name] = False
        return wf

    def add_operation(self,wf_name,op_name,op_uri):
        """Name and add an Operation to a Workflow.

        Parameters
        ----------
        wf_name : str
            name of the Workflow to add the Operation to
        op_name : str
            name to give to the new Operation
        op_uri : str
            uri for locating the Operation
        """
        self.workflows[wf_name].add_operation(op_name,self.get_operation(op_uri))

    def get_operation(self,op_uri):
        """Get the Operation at `op_uri` from self.op_manager"""
        return self.op_manager.get_operation(op_uri)

    def n_workflows(self):
        """Return the current number of Workflows"""
        return len(self.workflows)

    def run_workflow(self,wf_name):
        # TODO: support running these off the main thread:
        # implement running_lock for running flag, 
        # data_lock (use in data_callback) for updating inputs/outputs
        """Execute the workflow indicated by `wf_name`"""
        wf = self.workflows[wf_name]
        self.message_callback('preparing workflow {} for execution'.format(wf_name))
        stk,diag = wf.execution_stack()
        wf_clone = self.prepare_wf(wf_name,stk)
        wf_clone.data_callback = wf.data_callback
        self.wf_clones[wf_name] = wf_clone
        self.wf_running[wf_name] = True
        wf_clone.run()
        self.message_callback('execution finished')

    def stop_workflow(self,wf_name):
        """Stop the workflow indicated by `wf_name`"""
        self.message_callback('stopping workflow {}'.format(wf_name))
        if wf_name in self.wf_clones.keys():
            wf = self.wf_clones.pop(wf_name)
            wf.stop()
        self.wf_running[wf_name] = False

    def prepare_wf(self,wf_name,stk):
        wf_clone = self.workflows[wf_name].build_clone()
        for input_uri,pgn_itm_uri in wf_clone.plugin_connections.items():
            pgn_itm = self.plugin_manager.get_data_from_uri(pgn_itm_uri)
            wf_clone.set_item(input_uri,pgn_itm)
        for input_uri,wf_name in wf_clone.workflow_connections.items():
            stk,diag = self.workflows[wf_name].execution_stack()
            new_wf = self.prepare_wf(wf_name,stk)
            wf_clone.set_item(input_uri,wf)
            # TODO: think about appropriate way for these workflows to callback,
            # keep in mind they may be batch-executed, maybe in parallel 
            #new_wf.message_callback = self.workflows[wf_name].message_callback
            #new_wf.data_callback = self.workflows[wf_name].data_callback
        return wf_clone


    def load_workflow(self,wf_name,wf_dict):
        """Load a workflow from a dict that specifies its parameters.

        If `wf_name` is not unique, self.workflows[wf_name] is overwritten.

        Parameters
        ----------
        wf_name : str
            name to be given to the new workflow
        wf_dict : dict
            dict specifying workflow setup
        """
        self.add_workflow(wf_name)
        for op_tag, op_module in wf_dict['OPERATIONS'].items():
            self.load_operation(wf_name,op_tag,op_module)
        for inpname,inpval in wf_dict['INPUTS'].items():
            self.workflows[wf_name].connect_input(inpname,inpval)
        for outname,outval in wf_dict['OUTPUTS'].items():
            self.workflows[wf_name].connect_output(outname,outval)
        for out_uri, in_map in wf_dict['CONNECTIONS'].items():
            self.workflows[wf_name].connect(out_uri,in_map)
        for op_name, dep_ops in wf_dict['DEPENDENCIES'].items():
            self.workflows[wf_name].set_dependency(op_name,dep_ops)
        for op_name, flag in wf_dict['ENABLED_FLAGS'].items():
            self.workflows[wf_name].set_op_enabled(op_name,flag)

    def load_operations(self,wf_name,**kwargs):
        for op_name,op_uri in kwargs.items():
            self.load_operation(wf_name,op_name,op_uri)
    
    def load_operation(self,wf_name,op_name,op_module):
        """Load an Operation from a dict that specifies its parameters.

        If `op_name` is not unique, the Operation is overwritten.

        Parameters
        ----------
        wf_name : str
            name of workflow to add Operation 
        op_name : str
            name to be given to the new Operation 
        op_module : str 
            uri of Operation module 
        """
        if not self.op_manager.is_op_enabled(op_module):
            self.op_manager.enable_op(op_module)
        op = self.op_manager.get_data_from_uri(op_module)()
        self.workflows[wf_name].add_operation(op_name,op)

    def setup_dict(self):
        d = {} 
        d['PAWS_VERSION'] = pawstools.__version__
        d['OP_ENABLED_FLAGS'] = {k:True for k in self.op_manager.keys() if self.op_manager.is_op_enabled(k)}
        wfman_dict = OrderedDict.fromkeys(self.workflows.keys())
        for wfname in self.workflows.keys():
            wfman_dict[wfname] = self.wf_setup_dict(wfname)
        d['WORKFLOWS'] = wfman_dict
        pgin_dict = OrderedDict.fromkeys(self.plugin_manager.plugins.keys()) 
        for pgin_name in self.plugin_manager.plugins.keys():
            pgin_dict[pgin_name] = self.plugin_manager.plugin_setup_dict(pgin_name)
        d['PLUGINS'] = self.plugin_manager.setup_dict()
        return d
    
    def wf_setup_dict(self,wf_name):
        """Return a dict that describes the Workflow setup.""" 
        wf_dict = OrderedDict()
        wf = self.workflows[wf_name]
        wf_dict['OPERATIONS'] = OrderedDict.fromkeys(wf.operations)
        for op_name,op in wf.operations.items():
            wf_dict['OPERATIONS'][op_name] = op.__module__[op.__module__.find('operations.')+11:] 
        wf_dict['INPUTS'] = wf.inputs
        wf_dict['OUTPUTS'] = wf.outputs
        wf_dict['OP_INPUTS'] = wf.op_inputs
        wf_dict['CONNECTIONS'] = wf.op_connections
        wf_dict['DEPENDENCIES'] = wf.op_dependencies
        wf_dict['ENABLED_FLAGS'] = wf.op_enabled_flags()
        return wf_dict

    def save_to_wfm(self,wfm_filename):
        """Save workflows, plugins, and active operations to a .wfm file.

        The .wfm file is really just a YAML file. 

        Parameters
        ----------
        wfm_filename : str
            full path of the .wfm file to be saved-
            extension is automatically appended if not provided, 
            and an existing file will be overwritten.
        """
        if not os.path.splitext(wfm_filename)[1] == '.wfm':
            wfm_filename = wfm_filename + '.wfm'
        print('saving workflow manager setup to {}'.format(wfm_filename))
        pawstools.save_file(wfm_filename,self.setup_dict())

    def save_to_wfl(self,wf_name,wfl_filename):
        if not os.path.splitext(wfl_filename)[1] == '.wfl':
            wfl_filename = wfl_filename + '.wfl'
        print('saving {} to {}'.format(wf_name,wfl_filename))
        pawstools.save_file(wfl_filename,self.wf_setup_dict(wf_name))

    def load_packaged_wfm(self,workflow_uri):
        # the following import saves a .wfm configuration file 
        importlib.import_module('.'+workflow_uri,pawstools.wf_module)
        wfm_path = pawstools.sourcedir
        wfm_path = os.path.join(wfm_path,'workflows')
        p = workflow_uri.split('.')
        for mp in p:
            wfm_path = os.path.join(wfm_path,mp)
        wfm_filename = wfm_path+'.wfm'
        self.load_wfm(wfm_filename)

    def load_packaged_workflow(self,wf_name,wf_uri):
        importlib.import_module('.'+wf_uri,pawstools.wf_module)
        wf_path = pawstools.sourcedir
        wf_path = os.path.join(wf_path,'workflows')
        p = wf_uri.split('.')
        for mp in p:
            wf_path = os.path.join(wf_path,mp)
        wf_filename = wf_path+'.wfl'
        f = open(wf_filename,'r')
        d = yaml.load(f)
        f.close()
        self.load_workflow(wf_name,d)

    def load_wfm(self,wfm_filename):
        """Set up the WfManager and its OpManager and PluginManager, from a .wfm file.

        Parameters
        ----------
        wfm_filename : str
            path to a .wfm file to be loaded
        """
        f = open(wfm_filename,'r')
        d = yaml.load(f)
        f.close()
        if 'PAWS_VERSION' in d.keys():
            wfm_version = d['PAWS_VERSION']
        else:
            wfm_version = '0.0.0'
        wfm_vparts = re.match(r'(\d+)\.(\d+)\.(\d+)',wfm_version)
        wfm_vparts = list(map(int,wfm_vparts.groups()))
        current_vparts = re.match(r'(\d+)\.(\d+)\.(\d+)',pawstools.__version__)  
        current_vparts = list(map(int,current_vparts.groups()))
        if wfm_vparts[0] < current_vparts[0] or wfm_vparts[1] < current_vparts[1]:
            warnings.warn('WARNING: paws (version {}) '\
            'is trying to load a state built in version {} - '\
            'this is likely to cause things to crash, '\
            'until the workflows and plugins are reviewed/refactored '\
            'under the current version.'.format(pawstools.__version__,wfm_version))  
        if 'OP_ENABLED_FLAGS' in d.keys():
            for op_module,flag in d['OP_ENABLED_FLAGS'].items():
                if not op_module in operations.op_modules:
                    raise Exception('Operation module {} not found'.format(op_module))
                self.op_manager.enable_op(op_module)
        if 'WORKFLOWS' in d.keys():
            wf_dict = d['WORKFLOWS']
            for wf_name,wf_setup_dict in wf_dict.items():
                self.load_workflow(wf_name,wf_setup_dict)
        if 'PLUGINS' in d.keys():
            self.plugin_manager.load_plugins(d['PLUGINS'])




