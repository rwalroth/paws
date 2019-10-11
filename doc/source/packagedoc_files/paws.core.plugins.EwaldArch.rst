paws.core.plugins.EwaldArch module
----------------------------------------

.. automodule:: paws.core.plugins.EwaldArch
    :members:
    :undoc-members:
    :show-inheritance:

EwaldArch is a Class for storing single diffraction images from area detectors. 
EwaldArch objects are meant to be stored in a larger EwaldSphere object for global integration. 
EwaldArch inherits from the PawsPlugin class. The arch_lock condition should be used when modifying any 
data contained in an EwaldArch object.

**Attributes**

* idx: integer name of arch
* map_raw: numpy 2d array of the unprocessed image data
* poni: poni data for integration
* mask: map of pixels to be masked out of integration
* scan_info: information from any relevant motors and sensors
* ai_args: arguments passed to AzimuthalIntegrator
* file_lock: lock to ensure only one writer to data file
* integrator: AzimuthalIntegrator object from pyFAI
* arch_lock: threading lock used to ensure only one process can access data at a time
* map_norm: normalized image data
* map_q: reciprocal space coordinates for data
* int_1d: int_1d_data object from containers
* int_2d: int_2d_data object from containers

**Methods**

* integrate_1d: integrate the image data to create I, 2theta, q, and normalization arrays
* integrate_2d: not implemented
* set_integrator: set new integrator
* set_map_raw: replace raw data
* set_poni: replace poni object
* set_mask: replace mask data
* set_scan_info: replace scan_info
* save_to_h5: save data to hdf5 file
* load_from_h5: load data from hdf5 file
* copy: create copy of arch
