import numpy as np

from ..operation import Operation
from .. import optools

class WindowZip(Operation):
    """
    From input sequences for x and y, 
    produce an n-by-2 array 
    where x is bounded by the specified limits 
    """

    def __init__(self):
        input_names = ['x','y','x_min','x_max']
        output_names = ['x_window','y_window','x_y_window']
        super(WindowZip,self).__init__(input_names,output_names)        
        self.input_src['x'] = optools.wf_input
        self.input_src['y'] = optools.wf_input
        self.input_src['x_min'] = optools.text_input
        self.input_src['x_max'] = optools.text_input
        self.input_type['x'] = optools.ref_type
        self.input_type['y'] = optools.ref_type
        self.input_type['x_min'] = optools.float_type
        self.input_type['x_max'] = optools.float_type
        self.inputs['x_min'] = 0.02 
        self.inputs['x_max'] = 0.6 
        self.input_doc['x'] = 'list (or iterable) of x values'
        self.input_doc['y'] = 'list (or iterable) of y values'
        self.input_doc['x_min'] = 'inclusive minimum x value of output'
        self.input_doc['x_max'] = 'inclusive maximum x value of output'
        self.output_doc['x_window'] = 'n-by-1 array of x_min <= x <= x_max'
        self.output_doc['y_window'] = 'n-by-1 array of y for x_min <= x <= x_max'
        self.output_doc['x_y_window'] = 'n-by-2 array with x, y pairs for x_min <= x <= x_max'

    def run(self):
        xvals = self.inputs['x']
        yvals = self.inputs['y']
        x_min = self.inputs['x_min']
        x_max = self.inputs['x_max']
        idx_good = ((xvals >= x_min) & (xvals <= x_max))
        x_y_window = np.zeros((idx_good.sum(),2))
        x_y_window[:,0] = xvals[idx_good]
        x_y_window[:,1] = yvals[idx_good]
        self.outputs['x_window'] = x_y_window[:,0]
        self.outputs['y_window'] = x_y_window[:,1]
        self.outputs['x_y_window'] = x_y_window

