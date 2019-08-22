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
* specfile: SpecFile object for scan
* parameters: dictionary of parameters for integration step:
  * step_size: spacing 
  * step_type: either 2theta or q
  * db_x: direct beam x pixel
  * db_y: direct beam y pixel
  * detector_distance_px: distance from sample to detector in pixels
  * pixel_size: edge length of pixel, or (x, y) tuple if different
  * image_path: image directory
  * spec_path: 
* global_1d_I: array containing the 1D diffraction pattern from all arches
* global_1d_2theta: array containing the 2 theta values for the global_1d array
* global_1d_q: array containing the q values for the global 1D array
* stitched: all images stitched into single 2-d histogram based on theta and phi
* stitched_ang: theta and phi values for stitched data
* stitched_q: q values for stitched data

**Methods**

