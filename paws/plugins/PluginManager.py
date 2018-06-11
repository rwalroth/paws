from __future__ import print_function
from collections import OrderedDict
from functools import partial
import importlib

from ..models.TreeModel import TreeModel
from .. import plugins as pgns
from .. import pawstools
from .PawsPlugin import PawsPlugin

class PluginManager(TreeModel):
    """Tree for storing, browsing, and managing PawsPlugins"""

    def __init__(self):
        flag_dict = OrderedDict(selected=False,running=False)
        super(PluginManager,self).__init__(flag_dict)
        self.plugins = self._root_dict
        self.connections = OrderedDict()
        self.message_callback = self.tagged_print 

    def tagged_print(self,msg):
        print('[{}] {}'.format(type(self).__name__,msg))

    def add_plugin(self,plugin_name,plugin_module):
        """Import, name, and add a plugin.

        After a plugin is added to a plugin_manager,
        it is available as plugin_manager.plugins[plugin_name].

        Parameters
        ----------
        plugin_name : str
            Name that will be used to refer to this plugin after it is added.
        plugin_module : str
            Name of the plugin module.
            Example: If class MyPlugin is in the CATEGORY.MyPlugin module,
            retrieve it with `plugin_module` = 'CATEGORY.MyPlugin'.
        """
        p = self.get_plugin(plugin_module)
        if not self.is_tag_valid(plugin_name): 
            raise pawstools.PluginNameError(self.tag_error_message(plugin_name))
        #p.message_callback = self.message_callback
        p.data_callback = partial(self.set_plugin_item,plugin_name)
        self.set_item(plugin_name,p)
        self.get_from_uri(plugin_name).flags['running'] = False 

    def set_plugin_item(self,pgn_name,item_uri,item_data):
        full_uri = pgn_name+'.'+item_uri
        self.set_item(full_uri,item_data)

    def get_plugin(self,plugin_module): 
        """Import, instantiate, return a PawsPlugin from its module.

        This can also be used to test the Python environment 
        for compatibility with a plugin.

        Parameters
        ----------
        plugin_module : str
            Name of the plugin module.
            See add_plugin().

        Returns
        -------
        PawsPlugin 
            An instance of the PawsPlugin subclass defined in `plugin_module`. 
        """
        mod = importlib.import_module('.'+plugin_module,pgns.__name__)
        return mod.__dict__[plugin_module]()

    def set_input(self,plugin_name,input_name,val):
        """Set a plugin input to the provided value.

        Parameters
        ----------
        plugin_name : str
            Name that will be used to refer to this plugin after it is added.
        input_name : str
            name of the input to be set
        val : object
            the data to be used as plugin input
        """
        self.set_item(plugin_name+'.inputs.'+input_name,val)

    def connect(self,item_uri,input_map):
        """Connect the data at `item_uri` to one or more inputs.

        Sets up Plugin inputs listed in `input_map`
        to take the value at `item_uri`.
        `input_map` can be a TreeItem uri (string) or a list thereof.
        """
        if item_uri in self.connections:
            if isinstance(input_map,list):
                self.connections[item_uri].extend(input_map)
            else:
                self.connections[item_uri].append(input_map)
        else:
            if not isinstance(input_map,list): input_map = [input_map]
            self.connections[item_uri] = input_map

    def start_plugins(self,plugin_name_list):
        for pn in plugin_name_list:
            self.start_plugin(pn)

    def start_plugin(self,plugin_name):
        """Start the plugin referred to by `plugin_name`."""
        for item_uri,input_map in self.connections.items():
            for input_uri in input_map:
                self.set_item(input_uri,self.get_data_from_uri(item_uri))
        self.message_callback('starting plugin {}'.format(plugin_name))
        # keep track of run state with treeitem flags
        self.get_from_uri(plugin_name).flags['running'] = True 
        self.plugins[plugin_name].start()

    def stop_plugin(self,plugin_name):
        self.message_callback('stopping plugin {}'.format(plugin_name))
        self.plugins[plugin_name].stop()
        # keep track of run state with treeitem flags
        self.get_from_uri(plugin_name).flags['running'] = False 

    def setup_dict(self):
        pg_dict = OrderedDict()
        pg_dict['PLUGINS'] = OrderedDict()
        pg_dict['INPUTS'] = OrderedDict()
        pg_dict['CONNECTIONS'] = self.connections 
        for pg_name,pg in self.plugins.items():
            pg_dict['PLUGINS'][pg_name] = pg.__module__[pg.__module__.find('plugins.')+1:] 
            pg_dict['INPUTS'][pg_name] = pg.inputs
        return pg_dict

    def load_plugins(self,pg_dict):
        """Load plugins from a setup dict.

        Written for loading plugins from saved data.

        Parameters
        ----------
        pg_dict : dict 
            Dict specifying plugin setup
        """
        for pg_name, pg_mod in pg_dict['PLUGINS'].items():
            self.add_plugin(pg_name,pg_mod)
        for pg_name, inps in pg_dict['INPUTS'].items():
            for inp_name,val in inps.items():
                self.set_input(pg_name,inp_name,val)
        for item_uri,input_map in pg_dict['CONNECTIONS'].items():
            self.connect(item_uri,input_map)

    def n_plugins(self):
        """Return number of plugins currently loaded."""
        return len(self.plugins) 

    def build_tree(self,x):
        """Return a dict describing a tree-like structure of this object.

        This is a reimplemention of TreeModel.build_tree() 
        to define this object's child tree structure.
        For a PluginManager, a dict is provided for each PawsPlugin,
        where the dict contains the results of calling
        self.build_tree(plugin.inputs)
        """
        if isinstance(x,PawsPlugin):
            d = OrderedDict()
            d['inputs'] = self.build_tree(x.inputs)
            d.update(x.get_plugin_content())
        else:
            return super(PluginManager,self).build_tree(x) 
        return d


