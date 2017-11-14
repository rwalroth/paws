from collections import OrderedDict

from ... import Operation as opmod 
from ...Operation import Operation
from saxskit import saxs_pif

inputs=OrderedDict(pif=None)
outputs=OrderedDict(
    q_I=None,
    temperature=None,
    flags=None,
    params=None,
    report=None)

class UnpackNPSolutionSAXS(Operation):
    """Unpack a nanoparticle solution SAXS record"""

    def __init__(self):
        super(UnpackNPSolutionSAXS,self).__init__(inputs,outputs)
        self.input_doc['pif'] = 'pif object to be unpacked'
        self.output_doc['q_I'] = 'n-by-2 array of q values and corresponding saxs intensities'
        self.output_doc['temperature'] = 'temperature in degrees C'
        self.output_doc['flags'] = 'dict of boolean flags indicating scatterer populations'
        self.output_doc['params'] = 'dict of scattering equation parameters fit to q_I'
        self.output_doc['report'] = 'dict reporting fit objectives, etc. '
        self.input_type['pif'] = opmod.workflow_item

    def run(self):
        pp = self.inputs['pif']

        q_I, T_C, flg, par, rpt = saxs_pif.unpack_pif(pp)

        self.outputs['q_I'] = q_I 
        self.outputs['temperature'] = T_C 
        self.outputs['flags'] = flg
        self.outputs['params'] = par
        self.outputs['report'] = rpt

