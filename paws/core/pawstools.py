import os
from datetime import datetime as dt

import yaml

p = os.path.abspath(__file__)
# p = (pawsroot)/paws/core/pawstools.py

d = os.path.dirname(p)
# d = (pawsroot)/paws/core/

d = os.path.dirname(d)
# d = (pawsroot)/paws/
sourcedir = str(d)

d = os.path.dirname(d)
# d = (pawsroot)/
rootdir = str(d)

user_homedir = os.path.expanduser("~")

paws_scratch_dir = os.path.join(user_homedir,'.paws_scratch')
paws_cfg_dir = os.path.join(user_homedir,'.paws_cfg')
if not os.path.exists(paws_cfg_dir):
    os.mkdir(paws_cfg_dir)
if not os.path.exists(paws_scratch_dir):
    os.mkdir(paws_scratch_dir)

# Get the code version from the paws_config.py file, store as __version__
with open(os.path.join(sourcedir,'paws_config.py')) as f: 
    exec(f.read())
version=__version__

class WorkflowAborted(Exception):
    pass
    #def __init__(self,msg):
    #    super(WorkflowAborted,self).__init__(self,msg)

class OperationDisabledError(Exception):
    pass
    #def __init__(self,msg):
    #    super(WorkflowAborted,self).__init__(self,msg)

class WfNameError(Exception):
    pass

class PluginNameError(Exception):
    pass

class PluginLoadError(Exception):
    pass

def dtstr():
    """Return date and time as a string"""
    return dt.strftime(dt.now(),'%Y %m %d, %H:%M:%S')

def timestr():
    """Return time as a string"""
    return dt.strftime(dt.now(),'%H:%M:%S')

def save_file(filename,d):
    """
    Create or replace file indicated by filename,
    as a yaml serialization of dict d.
    """
    f = open(filename, 'w')
    yaml.dump(d, f)
    f.close()
    
def update_file(filename,d):
    """
    Save the items in dict d into filename,
    without removing members not included in d.
    """
    if os.path.exists(filename):
        f_old = open(filename,'r')
        d_old = yaml.load(f_old)
        f_old.close()
        d_old.update(d)
        d = d_old
    f = open(filename, 'w')
    yaml.dump(d, f)
    f.close()

def save_cfg(cfg_data,cfg_file):
    cfg = open(cfg_file,'w')
    yaml.dump(cfg_data,cfg)
    cfg.close()

def load_cfg(cfg_file):
    cfg = open(cfg_file,'r')
    cfg_data = yaml.load(cfg)
    cfg.close()
    if not cfg_data:
        cfg_data = OrderedDict() 
    return cfg_data



# TODO: move to pawstools
def save_to_dict(wf_manager):
    d = {} 
    d['OP_ACTIVATION_FLAGS'] = {k:True for k in ops.op_keys if wf_manager.op_manager.is_op_activated(k)}
    d['PAWS_VERSION'] = version 
    wfman_dict = OrderedDict()
    for wfname,wf in wf_manager.workflows.items():
        wfman_dict[wfname] = wf.setup_dict() 
    d['WORKFLOWS'] = wfman_dict
    pgin_dict = OrderedDict() 
    for pgin_name in wf_manager.plugin_manager.plugins.keys():
        pgin = wf_manager.plugin_manager.get_data_from_uri(pgin_name)
        pgin_dict[pgin_name] = pgin.setup_dict()
    d['PLUGINS'] = pgin_dict
    return d

def save_to_wfl(wfl_filename,wf_manager):
    """Save workflows, plugins, and active operations to a .wfl file.

    The .wfl file is really just a YAML file. 

    Parameters
    ----------
    wfl_filename : str
        full path of the .wfl file to be saved-
        extension is optional, 
        and an existing file will be overwritten.
    """
    if not os.path.splitext(wfl_filename)[1] == '.wfl':
        wfl_filename = wfl_filename + '.wfl'
    d = save_to_dict(wf_manager)
    save_file(wfl_filename,d)

def load_packaged_wfl(workflow_uri):
    workflow_modpath = workflow_uri.split('.')

    wf_mod = importlib.import_module('.'+workflow_uri,wfs.__name__)

    wfl_path = sourcedir
    wfl_path = os.path.join(wfl_path,'core','workflows')
    for mp in workflow_modpath:
        wfl_path = os.path.join(wfl_path,mp)
    wfl_filename = wfl_path+'.wfl'
    load_from_wfl(wfl_filename)

def load_wfl(self,wfl_filename,wf_manager):
    """Set up a OpManager, PluginManager, and WfManager from a .wfl file.

    Parameters
    ----------
    wfl_filename : str
        path to a .wfl file to be loaded
    """
    f = open(wfl_filename,'r')
    d = yaml.load(f)
    f.close()
    if 'PAWS_VERSION' in d.keys():
        wfl_version = d['PAWS_VERSION']
    else:
        wfl_version = '0.0.0'
    wfl_vparts = re.match(r'(\d+)\.(\d+)\.(\d+)',wfl_version)
    wfl_vparts = list(map(int,wfl_vparts.groups()))
    current_vparts = re.match(r'(\d+)\.(\d+)\.(\d+)',pawstools.version)  
    current_vparts = list(map(int,current_vparts.groups()))
    if wfl_vparts[0] < current_vparts[0] or wfl_vparts[1] < current_vparts[1]:
        warnings.warn('WARNING: paws (version {}) '\
        'is trying to load a state built in version {} - '\
        'this is likely to cause things to crash, '\
        'until the workflows and plugins are reviewed/refactored '\
        'under the current version.'.format(pawstools.version,wfl_version))  
    if 'OP_ACTIVATION_FLAGS' in d.keys():
        for op_module,flag in d['OP_ACTIVATION_FLAGS'].items():
            if op_module in ops.op_modules:
                if flag:
                    wf_manager.op_manager.activate_op(op_module)
    if 'WORKFLOWS' in d.keys():
        wf_dict = d['WORKFLOWS']
        if wf_names is None:
            wf_names = wf_dict.keys()
        for wf_name,wf_setup_dict in zip(wf_names,wf_dict.values()):
            wf_manager.load_workflow(wf_name,wf_setup_dict,wf_manager.op_manager)
    if 'PLUGINS' in d.keys():
        plugins_dict = d['PLUGINS']
        if plugin_names is None:
            plugin_names = plugins_dict.keys()
        for plugin_name,plugin_setup_dict in plugins_dict.items():
            wf_manager.plugin_manager.load_plugin(plugin_name,plugin_setup_dict)



