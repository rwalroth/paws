paws.core.plugins.EwaldSphere module
----------------------------------------

.. automodule:: paws.core.plugins.EwaldSphere
    :members:
    :undoc-members:
    :show-inheritance:
	
EwaldSphere is a class which stores data acquired by scanning area detectors. 
EwaldSphere inherits from the PawsPlugin class and relies on the class 
EwaldArch for storing 2D detector data.

**Attributes**

* name: str, name of the sphere
* arches: Series, list of arches indexed by their idx value
* data_file: str, file to save data to
* scan_data: DataFrame, stores all scan metadata
* mg_args: arguments for MultiGeometry constructor
* multi_geo: MultiGeometry instance
* bai_1d_args: dict, arguments for invidivual arch integrate1d method
* bai_2d_args: not implemented
* mgi_1d_I: array, intensity from MultiGeometry based integration
* mgi_1d_2theta: array, two theta from MultiGeometry based integration
* mgi_1d_q: array, q data from MultiGeometry based integration
* mgi_2d_I: not implemented
* mgi_2d_2theta: not implemented
* mgi_2d_q: not implemented
* file_lock: lock for ensuring one writer to hdf5 file
* sphere_lock: lock for modifying data in sphere
* bai_1d: int_1d_data object for by-arch integration
* bai_2d: not implemented

**Methods**

* add_arch: adds new arch and optionally updates other data
* by_arch_integrate_1d: integrates each arch individually and sums them
* set_multi_geo: sets the MultiGeometry instance
* multigeometry_integrate_1d: wrapper for MultiGeometry integrate1d method
* save_to_h5: saves data to hdf5 file
* load_from_h5: loads data from hdf5 file