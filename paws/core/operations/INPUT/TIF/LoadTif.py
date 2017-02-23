import os
import re

import numpy as np
from PIL import Image

from ...operation import Operation
from ... import optools

class LoadTif(Operation):
    """
    Takes a filesystem path that points to a .tif,
    outputs image data and metadata from the file. 
    """

    def __init__(self):
        input_names = ['path']
        output_names = ['image','metadata']
        super(LoadTif,self).__init__(input_names,output_names)
        # default behavior: load from filesystem
        self.input_doc['path'] = 'string representing the path to a .tif image'
        self.input_src['path'] = optools.fs_input
        self.input_type['path'] = optools.path_type
        self.output_doc['image'] = '2D array representing pixel values taken from the input file'
        self.output_doc['metadata'] = 'Dictionary containing all image metadata loaded from the input file'
        
    def run(self):
        img_url = self.inputs['path']
        try:
            pil_img = Image.open(img_url)
            self.outputs['image'] = np.array(pil_img)
            self.outputs['metadata'] = pil_img.info
        except IOError as ex:
            ex.message = "[{}] IOError for file {}. \nError message:".format(__name__,img_url,ex.message)
            raise ex
        except ValueError as ex:
            ex.message = "[{}] ValueError for file {}. \nError message:".format(__name__,img_url,ex.message)
            raise ex
