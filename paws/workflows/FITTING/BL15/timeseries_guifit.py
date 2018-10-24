import os

from paws import pawstools
from paws.workflows.WfManager import WfManager

wfmgr = WfManager()

wfmgr.load_packaged_wfm('FITTING.BL15.batch_fit')

wfmgr.load_operations('read_and_fit',
    fit='PROCESSING.FITTING.XRSDFitGUI'
    )

wf = wfmgr.workflows['batch_fit']
wf.set_op_inputs('t_filenames',x_sort_flag=True)
wf.set_op_inputs('t_q_I_files',x_sort_flag=True)
wf.set_op_inputs('t_system_files',x_sort_flag=True)
wf.set_op_input('run_fits','serial_params',{'system':'system'})

wfmgr.save_to_wfm(os.path.join(pawstools.sourcedir,'workflows','FITTING','BL15','timeseries_guifit.wfm'))

