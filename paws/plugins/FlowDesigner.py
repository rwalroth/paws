from __future__ import print_function
from collections import OrderedDict
import os
import copy
import time

from citrination_client.models.design import Target,constraints 

from .PawsPlugin import PawsPlugin

class FlowDesigner(PawsPlugin):

    def __init__(self,citrination_client,dataset_id,dataview_id,
        target={},constraints={},range_constraints={},categorical_constraints={},
        n_candidates=1,design_effort=30,verbose=False,log_file=''):
        """Create a FlowDesigner plugin.

        Parameters
        ----------
        citrination_client : CitrinationClient
            A running CitrinationClient PawsPlugin
        dataset_id : int
            Integer id of the dataset to upload PIFs of results
        dataview_id : int
            Integer id of the dataview to run the design queries against
        target : dict 
            Property name key (str) and target value ('Min', 'Max', or float) 
            for the optimization objective
        constraints : dict
            Property names (keys) and constraints (values)
        range_constraints : dict
            Property names (keys) and [min, max] lists (values)
        categorical_constraints : dict        
            Property names (keys) and categorical constraints (values)
        n_candidates : int
            Number of candidates to generate in each design query
        design_effort : int 
            how hard to try to meet the targets (int from 1 to 30) 
        """
        super(FlowDesigner,self).__init__(thread_blocking=False,verbose=verbose,log_file=log_file)
        self.citrination_client = citrination_client
        self.dataset_id = dataset_id
        self.dataview_id = dataview_id
        self.target = target
        self.constraints = constraints
        self.range_constraints = range_constraints
        self.categorical_constraints = categorical_constraints
        self.n_candidates = n_candidates
        self.design_effort = design_effort 
        self.best_materials = []
        self.next_experiments = []

    def start(self):
        super(FlowDesigner,self).start() 

    def get_candidate_recipes(self):
        straints = []
        for prop_name, val in self.constraints.items():
            straints.append(constraints.RealValueConstraint('Property '+prop_name,val))
        for prop_name, lmts in self.range_constraints.items():
            straints.append(constraints.RealRangeConstraint('Property '+prop_name,lmts[0],lmts[1]))
        for prop_name, cats in self.categorical_constraints.items():
            straints.append(constraints.CategoricalConstraint('Property '+prop_name,cats))
        tgt_name = 'Property '+list(self.target.keys())[0]
        tgt_val = list(self.target.values())[0]
        tgt = Target(tgt_name,tgt_val)
        #DOC: cc.submit_design_run(
        #       data_view_id,
        #       num_candidates (int in [1,20]),
        #       effort (int in [1,30]),
        #       target=None, constraints=[],
        #       sampler='Default') 
        msg = 'Designing for: \nTarget: {} \nConstraints: {} \nRange constraints: {} \nCategorical constraints: {}'.format(
            self.target,self.constraints,self.range_constraints,self.categorical_constraints)
        if self.verbose: self.message_callback(msg)
        self.add_to_history(msg)
        #try_again = True
        #while try_again:
        #    try:
        des = self.citrination_client.client.submit_design_run(
            self.dataview_id,
            self.n_candidates,
            self.design_effort,
            tgt, straints
            ) 
        fin = False
        while not fin:
            time.sleep(10)
            stat = self.citrination_client.client.get_design_run_status(self.dataview_id, des.uuid)
            if self.verbose: self.message_callback('design finished: {} ({}/100)'.format(stat.finished(),stat.progress))
            if int(stat.progress) == 100:
                fin = True
        desres = self.citrination_client.client.get_design_run_results(self.dataview_id,des.uuid)
        #        try_again = False 
        #    except:
        #        pass
        for result in desres.best_materials:
            rcp = dict(
                flowrate = float(result['descriptor_values']['Property flowrate']),
                T_set = float(result['descriptor_values']['Property T_set']),
                TOP_fraction = float(result['descriptor_values']['Property TOP_fraction']),
                oleylamine_fraction = float(result['descriptor_values']['Property oleylamine_fraction']),
                ODE_extra_fraction = float(result['descriptor_values']['Property ODE_extra_fraction'])  
                )
            self.best_materials.append(rcp)
        for result in desres.next_experiments:
            rcp = dict(
                flowrate = float(result['descriptor_values']['Property flowrate']),
                T_set = float(result['descriptor_values']['Property T_set']),
                TOP_fraction = float(result['descriptor_values']['Property TOP_fraction']),
                oleylamine_fraction = float(result['descriptor_values']['Property oleylamine_fraction']),
                ODE_extra_fraction = float(result['descriptor_values']['Property ODE_extra_fraction'])  
                )
            self.next_experiments.append(rcp)


