import numpy as np
from PIL import Image

from ... import Operation as opmod 
from ...Operation import Operation

class LoadTif_PIL(Operation):
    """
    Takes a filesystem path that points to a .tif,
    outputs image data and metadata from the file. 
    """

    def __init__(self):
        input_names = ['file_path']
        output_names = ['image_data','metadata']
        super(LoadTif_PIL,self).__init__(input_names,output_names)
        self.input_doc['file_path'] = 'path to a .tif image'
        self.output_doc['image_data'] = '2D array representing pixel values'
        self.output_doc['metadata'] = 'Dictionary of image metadata'
        
    def run(self):
        p = self.inputs['file_path']
        if p is None:
            return
        pil_img = Image.open(p)
        self.outputs['image_data'] = np.array(pil_img)
        self.outputs['metadata'] = pil_img.info

