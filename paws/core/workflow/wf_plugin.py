from ..operations import optools
from .. import pawstools
from ..plugins.plugin import PawsPlugin

class WorkflowPlugin(PawsPlugin):
    """
    Wrapper contains a workflow and 
    implements the PawsPlugin abc interface.
    """

    def __init__(self,wf):
        input_names = {}
        super(WorkflowPlugin,self).__init__(input_names)
        self.wf = wf 

    def start(self):
        pass 

    def stop(self):
        pass

    def content(self):
        #wf_dict = {'workflow':self.wf}
        #return wf_dict
        op_dict = {str(i):self.wf.build_dict(itm) for i,itm in zip(range(len(self.wf.root_items)),self.wf.root_items)}
        return op_dict

    def description(self):
        desc = str('Workflow Plugin for paws: '
            + 'This wraps a workflow in a plugin, providing its operations as tree content '
            + 'so that other workflows and plugins can gain access to them.')
        return desc

