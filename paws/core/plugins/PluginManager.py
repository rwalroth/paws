import importlib
from collections import OrderedDict

from PySide import QtCore

from ..operations import optools
from ..models.QTreeSelectionModel import QTreeSelectionModel
from ..models.TreeItem import TreeItem
from .. import plugins as pgns
from .PawsPlugin import PawsPlugin

class PluginManager(QTreeSelectionModel):
    """
    Tree structure for managing paws plugins.
    """

    def __init__(self,**kwargs):
        super(PluginManager,self).__init__({'select':False})
        self.logmethod = None

    @QtCore.Slot(str)
    def update_plugin(self,pgin_name):
        if self.contains_uri(pgin_name):
            pgin = self.get_data_from_uri(pgin_name)
            self.tree_update(self.root_index(),pgin_name,pgin)

    def load_from_dict(self,pgin_dict):
        """
        Load plugins from a dict that specifies their setup parameters.
        """
        for uri, pgin_spec in pgin_dict.items():
            pgin_type = pgin_spec['type']
            pgin = self.get_plugin(pgin_type)
            if pgin is not None:
                if not issubclass(pgin,PawsPlugin):
                    self.write_log('Did not find Plugin {} - skipping.'.format(pgin_type))
                else:
                    pgin = pgin()
                    for name in pgin.inputs.keys():
                        if name in pgin_spec[optools.inputs_tag]:
                            pgin.inputs[name] = pgin_spec[optools.inputs_tag][name]
                    pgin.start()
                    # if already have this uri, first generate auto_tag
                    if self.tree_contains_uri(uri):
                        uri = self.auto_tag(uri)
                    self.add_plugin(uri,pgin)
            else:
                self.write_log('Did not find Plugin {} - skipping.'.format(pgin_name))

    def get_plugin(self,pgin_type):    
        try:
            mod = importlib.import_module('.'+pgin_type,pgns.__name__)
            if pgin_type in mod.__dict__.keys():
                return mod.__dict__[pgin_type]
            else:
                self.write_log('Did not find plugin {} in module {}'.format(pgin_type,mod.__name__))
                return None 
        except Exception as ex:
            self.write_log('Trouble loading module for plugin {}. Error message: '.format(pgin_name) + ex.message)
            return None

    def list_plugins(self):
        r = self.get_from_idx(self.root_index())
        return [itm.tag for itm in r.children]

    def write_log(self,msg):
        if self.logmethod:
            self.logmethod(msg)
        else:
            print(msg)

    def add_plugin(self,pgin_tag,pgin):
        """Add a Plugin to the tree as a new top-level TreeItem."""
        self.set_item(pgin_tag,optools.build_dict(pgin),self.root_index())

    def remove_plugin(self,rm_idx):
        """Remove a Plugin from the tree"""
        p_idx = self.parent(rm_idx)
        if not p_idx == self.root_index():
            msg = '[{}] Called remove_plugin on non-Plugin at QModelIndex {}. \n'.format(__name__,rm_idx)
            raise ValueError(msg)
        self.remove_item(rm_itm.tag,p_idx)

    # Overloaded headerData() for PluginManager 
    def headerData(self,section,orientation,data_role):
        if (data_role == QtCore.Qt.DisplayRole and section == 0):
            return "Plugins: {} active".format(self.root_item().n_children())
        elif (data_role == QtCore.Qt.DisplayRole and section == 1):
            return super(PluginManager,self).headerData(section,orientation,data_role)    
        else:
            return None

