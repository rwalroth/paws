paws.core.plugins.EwaldSphere module
----------------------------------------

.. automodule:: paws.core.plugins.EwaldSphere
    :members:
    :undoc-members:
    :show-inheritance:
	
EwaldSphere is a class which stores data acquired by EwaldWorkflow. 
EwaldSphere inherits from the PawsPlugin class and relies on the class 
EwaldArch for storing 2D detector data, and the class SpecFile for storing 
data acquired by SPEC.

**Attributes**

* arches: dictionary of arches, keys are either single angles if one arm is moved or tuples of angles if multiple arms are used. 
* spec_scan: DataFrame of SPEC scan
* parameters: dictionary of parameters for integration step:
  * user: prefix for image files
  * step_size_tth: two theta spacing for integration
  * step_size_q: q spacing for integration
  * image_path: image directory
  * spec_path: directory to SPEC file
  * spec_name: name of SPEC file
  * scan_number: number of the scan in SPEC
* calibration: dictionary of calibration parameters for experiment
  * db_px: (x, y) tuple for the x and y position of the direct beam in pixels
  * detector_distance: distance from sample to detector in pixels
  * pixel_size: either sclalar value for square pixels or (x, y) tuple if rectangular pixels
  * sample_offset: (x, y, z) tuple for sample offset measured in mm
* global_1d_I: array containing the 1D diffraction pattern from all arches
* global_1d_2theta: array containing the 2 theta values for the global_1d array
* global_1d_q: array containing the q values for the global 1D array
* stitched: all images stitched into single 2-d histogram based on theta and phi
* stitched_ang: theta and phi values for stitched data
* stitched_q: q values for stitched data

**Methods**

* append_arch: creates and appends a new arch object to arches dictionary
* get_spec_scan: loads in DataFrame from SPEC dictionary 
* load_parameters: loads parameters from file
* load_calibration: loads the calibration info
* integrate_all_1D: integrates all arch segments and outputs the I, 2 theta, and q arrays
* stitch_images: stiches together images to create global 2D diffraction data