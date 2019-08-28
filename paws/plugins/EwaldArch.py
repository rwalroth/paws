# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 14:21:58 2019

@author: walroth

From docs:
    
EwaldArch is a Class for storing single diffraction images collected by EwaldWorkflow. 
Basic functions for mapping pixels, rotating them, and integrating them are stored here. 
EwaldArch objects are meant to be stored in a larger EwaldSphere object for global integration. 
EwaldArch inherits from the PawsPlugin class. The arch_lock condition should be used when modifying any 
data contained in an EwaldArch object.

**Attributes**

* map_raw: numpy 2d array of the unprocessed image data
* map_corr: image data corrected for any masks, flat filed, dark current, etc corrections
* map_xyz: rotated Cartesian coordinates for the pixels
* map_tpr: rotated spherical coordinates for the pixels (theta, phi, r)
* map_q: reciprocal space coordinates for the 2D data
* int_raw: raw integrated 1D pattern
* int_pcount: values to use for normalizing the 1D pattern by number of pixels in each two-theta bin
* int_norm: normalized 1D pattern
* int_2theta: 1D 2 theta array
* int_q: q values for 1D array
* scan_info: information from any relevant motors and sensors 
* rotations: dictionary of the order of rotations to be done, and the angles to apply
* arch_lock: threading lock used to ensure only one process can access data at a time

**Methods**

* read_file: read in data from file as a numpy array
* apply_corrections: apply any corrections needed for the data
* rotate: rotates the provided xyz_map based on the provided rotation order and angles
* cart_to_sphere: converts Cartesian coordinates to spherical
* sphere_to_q: converts spherical coordinates to reciprocal space
* integrate_1d: integrate the image data to create I, 2θ, q, and normalization arrays
* read_raw (static): reads in raw file format and returns a numpy array
* mask: applies a provided mask to make any undesired pixels negative
* rot_x (static): rotates about x axis (orthogonal to beam, horizontal)
* rot_y (static): rotates about the y axis (orthogonal to beam, vertical)
* rot_z (static): rotates about the z axis (collinear with the beam)
"""
import sys
import os
from threading import Condition
from .PawsPlugin import PawsPlugin

from .. import pawstools


class EwaldArch(PawsPlugin):
    """Class for storing area detector data collected in
    X-ray diffraction experiments.

    Attributes:
        map_raw: numpy 2d array of the unprocessed image data
        map_corr: image data corrected for any masks, flat filed,
            dark current, etc corrections
        map_xyz: rotated Cartesian coordinates for the pixels
        map_tpr: rotated spherical coordinates for the pixels (theta, phi, r)
        map_q: reciprocal space coordinates for the 2D data
        int_raw: raw integrated 1D pattern
        int_pcount: values to use for normalizing the 1D pattern by number
            of pixels in each two-theta bin
        int_norm: normalized 1D pattern
        int_2theta: 1D 2 theta array
        int_q: q values for 1D array
        scan_info: information from any relevant motors and sensors
        rotations: dictionary of the order of rotations to be done,
            and the angles to apply
        arch_lock: threading lock used to ensure only one process can
            access data at a time

    Methods:
        read_file: read in data from file as a numpy array
        apply_corrections: apply any corrections needed for the data
        rotate: rotates the provided xyz_map based on the provided
            rotation order and angles
        cart_to_sphere: converts Cartesian coordinates to spherical
        sphere_to_q: converts spherical coordinates to reciprocal space
        integrate_1d: integrate the image data to create I, 2theta, q, and
            normalization arrays
        read_raw (static): reads in raw file format and returns a numpy array
        mask: applies a provided mask to make any undesired pixels negative
        rot_x (static): rotates about x axis (orthogonal to beam, horizontal)
        rot_y (static): rotates about the y axis (orthogonal to beam, vertical)
        rot_z (static): rotates about the z axis (collinear with the beam)
    """
    
    def __init__(self, file=None, map_raw=None):
        pass
