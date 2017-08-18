"""
Integrate an image to 2d,
using an existing PyFAI.AzimuthalIntegrator,
with a bunch of input parameters
for calling AzimuthalIntegrator.integrate1d().
"""

import numpy as np
import pyFAI

from ... import Operation as opmod 
from ...Operation import Operation

class ApplyIntegrator2d(Operation):
    """
    Input image data (ndarray), PyFAI.AzimuthalIntegrator, 
    mask, ROI mask, dark field image, flat field image,
    q-range, chi-range, number of points for integration bin centers,
    polz factor, choice of unit (string), 
    and choice of integration method (string).
 
    Output arrays containing q and I(q) 
    """
    def __init__(self):
        input_names = list(['data','integrator','mask','ROI_mask','dark','flat',
        'radial_range','azimuth_range','npt_rad','npt_azim','polarization_factor','normalization_factor','unit','method','integration_mode'])
        output_names = ['q','I','q_I']
        super(ApplyIntegrator2d,self).__init__(input_names,output_names)
        self.input_doc['data'] = '2d array representing intensity for each pixel'
        self.input_doc['integrator'] = 'A PyFAI.AzimuthalIntegrator object'
        self.input_doc['mask'] = '2d array for image mask, same shape as image_data'
        self.input_doc['ROI_mask'] = '2d array for ROI mask, same shape as image_data'
        self.input_doc['dark'] = '2d array for dark field, same shape as image_data'
        self.input_doc['flat'] = '2d array for flat field, same shape as image_data'
        self.input_doc['radial_range'] = 'list with two values, lower and upper limits of q (scattering vector)'
        self.input_doc['azimuth_range'] = 'list with two values, lower and upper limits of chi (azimuthal angle)'
        self.input_doc['npt_rad'] = 'number of q-points to integrate, as evenly spaced bins between radial_range[0] and radial_range[1]'
        self.input_doc['npt_azim'] = 'number of q-points to integrate, as evenly spaced bins between radial_range[0] and radial_range[1]'
        self.input_doc['polarization_factor'] = 'polarization factor, if polarization correction is needed'
        self.input_doc['unit'] = 'choice of unit. See PyFAI documentation for options.'
        self.input_doc['method'] = 'choice of integration method. See PyFAI documentation for options.'
        self.input_doc['normalization_factor'] = 'normalization monitor value'

        self.input_type['data'] = opmod.workflow_item
        self.input_type['integrator'] = opmod.workflow_item
        self.input_type['mask'] = opmod.workflow_item
        self.input_type['ROI_mask'] = opmod.workflow_item
        self.input_type['dark'] = opmod.workflow_item
        self.input_type['flat'] = opmod.workflow_item
        self.input_type['radial_range'] = opmod.float_type
        self.input_type['azimuth_range'] = opmod.float_type
        self.input_type['npt_rad'] = opmod.integer_type
        self.input_type['npt_azim'] = opmod.integer_type
        self.input_type['polarization_factor'] = opmod.float_type
        self.input_type['unit'] = opmod.string_type
        self.input_type['method'] = opmod.string_type
        self.input_type['normalization_factor'] = opmod.workflow_item

        self.inputs['npt_rad'] = 1000
        self.inputs['polarization_factor'] = 1.
        self.inputs['unit'] = 'q_A^-1'
        self.inputs['method'] = 'BBox'

        self.output_doc['q'] = 'Scattering vector magnitude q array in 1/Angstrom.'
        self.output_doc['I'] = 'Integrated intensity at q.'
        self.output_doc['chi'] = 'Azimuthal angle array.'

    def run(self):
        if self.inputs['ROI_mask']: self.inputs['mask'] = self.inputs['mask'] | self.inputs['ROI_mask']
        # use a mask to screen negative pixels
        # mask should be 1 for masked pixels, 0 for unmasked pixels
        kwargexcludemask = ['ROI_mask', 'integrator','integration_mode']
        kwargs = {key:val for key,val in self.inputs.items() if key not in kwargexcludemask}

        integ_result = self.inputs['integrator'].integrate2d(**kwargs)
        # save results to self.outputs
        q = integ_result.radial
        I = integ_result.intensity
        chi = integ_result.chi
        self.outputs['q'] = q
        self.outputs['I'] = I
        self.outputs['chi'] = chi
