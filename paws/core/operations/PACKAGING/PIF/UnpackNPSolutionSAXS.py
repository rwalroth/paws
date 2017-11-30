from collections import OrderedDict

from ... import Operation as opmod 
from ...Operation import Operation
from saxskit import saxs_piftools

inputs=OrderedDict(pif=None)
outputs=OrderedDict(
    experiment_id=None,
    t_utc=None,
    q_I=None,
    temperature=None,
    features=None,
    populations=None,
    params=None,
    report=None)

class UnpackNPSolutionSAXS(Operation):
    """Unpack a nanoparticle solution SAXS record"""

    def __init__(self):
        super(UnpackNPSolutionSAXS,self).__init__(inputs,outputs)
        self.input_doc['pif'] = 'pif object to be unpacked'
        self.output_doc['experiment_id'] = 'string experiment id'
        self.output_doc['t_utc'] = 'time in seconds utc'
        self.output_doc['q_I'] = 'n-by-2 array of q values and measured saxs intensities'
        self.output_doc['temperature'] = 'temperature in degrees C'
        self.output_doc['features'] = 'dict of numerical features of `q_I`'
        self.output_doc['populations'] = 'dict enumerating scatterer populations'
        self.output_doc['params'] = 'dict of scattering equation parameters for each of the `populations`'
        self.output_doc['report'] = 'dict reporting fit objectives and related quantities'
        self.input_type['pif'] = opmod.workflow_item

    def run(self):
        pp = self.inputs['pif']

        expt_id, t_utc, q_I, T_C, feats, pops, params, rpt = saxs_piftools.unpack_pif(pp)

        if bool(pops['guinier_porod']) and not 'D_gp' in params.keys():
            params['D_gp'] = [4.]

        #for pkey in pops.keys():
        #    if pops[pkey] is None:
        #        pops.pop(pkey)

        #for pkey in params.keys():
        #    if params[pkey] is None:
        #        params.pop(pkey)

        self.outputs['experiment_id'] = expt_id 
        self.outputs['t_utc'] = t_utc 
        self.outputs['q_I'] = q_I 
        self.outputs['temperature'] = T_C 
        self.outputs['features'] = feats 
        self.outputs['populations'] = pops 
        self.outputs['params'] = params
        self.outputs['report'] = rpt 

