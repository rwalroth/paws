"""
Operations config and processing routines
"""

from collections import OrderedDict

from PySide import QtCore

import operation

# tags for inputs and outputs TreeItems    
inputs_tag = 'inputs'
outputs_tag = 'outputs'

# Declarations of valid sources and types for workflow and plugin inputs
##### TODO: the following but gracefully
no_input = 0
text_input = 1
fs_input = 2
wf_input = 3
plugin_input = 4
batch_input = 5 
valid_sources = [no_input,text_input,fs_input,wf_input,plugin_input,batch_input]
input_sources = ['none','text','filesystem','workflow','plugins','batch'] 

none_type = 0
str_type = 1
int_type = 2
float_type = 3
bool_type = 4
ref_type = 5
path_type = 6
auto_type = 7
valid_types = [none_type,str_type,int_type,float_type,bool_type,ref_type,path_type,auto_type]
input_types = ['none','string','integer','float','boolean','reference','path','auto']

invalid_types = {}                
invalid_types[no_input] = [str_type,int_type,float_type,bool_type,ref_type,path_type,auto_type]
invalid_types[text_input] = [ref_type,path_type,auto_type]
invalid_types[fs_input] = [str_type,int_type,float_type,bool_type,ref_type,auto_type]
invalid_types[wf_input] = [str_type,int_type,float_type,bool_type,auto_type]
invalid_types[plugin_input] = [str_type,int_type,float_type,bool_type,auto_type]
invalid_types[batch_input] = [str_type,int_type,float_type,bool_type,ref_type,path_type]

class InputLocator(object):
    """
    Objects of this class are used as containers for inputs to an Operation,
    and should by design contain the information needed to find the relevant input data.
    After the data is loaded, it should be stored in InputLocator.data.
    """
    def __init__(self,src=no_input,tp=none_type,val=None):
        self.src = src
        self.tp = tp
        self.val = val 
        self.data = None 


def cast_type_val(tp,val):
    """
    Perform type casting for operation inputs.
    This should be called only for source = text_input.
    """
    if tp == none_type:
        val = None 
    elif tp == int_type:
        val = int(val)
    elif tp == float_type:
        val = float(val)
    elif tp == str_type:
        val = str(val)
    elif tp == bool_type:
        val = bool(eval(str(val)))
    else:
        msg = 'type selection {}, should be one of {}'.format(tp,valid_types)
        raise ValueError(msg)
    return val

def get_uri_from_dict(uri,d):
    keys = uri.split('.')
    itm = d
    for k in keys:
        if not k in itm.keys():
            msg = 'did not find uri {} in dict'.format(uri)
            raise KeyError(msg)
        else:
            itm = itm[k]
    return itm

def dict_contains_uri(uri,d):
    keys = uri.split('.')
    itm = d
    for k in keys:
        if not k in itm.keys():
            return False
        else:
            itm = itm[k]
    return True

def parameter_doc(name,value,doc):
    if isinstance(value, InputLocator):
        src_str = input_sources[value.src]
        tp_str = input_types[value.tp]
        v_str = str(value.val)
        return "- name: {} \n- source: {} \n- type: {} \n- value: {} \n- doc: {}".format(name,src_str,tp_str,v_str,doc) 
    else:
        tp_str = type(value).__name__
        return "- name: {} \n- type: {} \n- doc: {}".format(name,tp_str,doc) 

def stack_size(stk):
    sz = 0
    for lst in stk:
        if isinstance(lst[0].data,operation.Batch) or isinstance(lst[0].data,operation.Realtime):
            sz += stack_size(lst[1])+1
        else:
            sz += len(lst)
    return sz

def stack_contains(itm,stk):
    for lst in stk:
        if isinstance(lst[0].data,operation.Batch) or isinstance(lst[0].data,operation.Realtime):
            if itm == lst[0] or stack_contains(itm,lst[1]):
                return True
        else:
            if itm in lst:
                return True
    return False

def print_stack(stk):
    stktxt = ''
    opt_newline = '\n'
    for i,lst in zip(range(len(stk)),stk):
        if i == len(stk)-1:
            opt_newline = ''
        if isinstance(lst[0].data,operation.Batch) or isinstance(lst[0].data,operation.Realtime):
            substk = lst[1]
            stktxt += ('[\'{}\':\n{}\n]'+opt_newline).format(lst[0].tag(),print_stack(lst[1]))
        else:
            stktxt += ('{}'+opt_newline).format([itm.tag() for itm in lst])
    return stktxt

#def loader_extensions():
#    return str(
#    "ALL (*.*);;"
#    + "TIFF (*.tif *.tiff);;"
#    + "RAW (*.raw);;"
#    + "MAR (*.mar*)"
#    )

