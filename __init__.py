import os

from xicam.plugins import base
from PySide import QtGui, QtCore, QtUiTools

from slacx.slacxui import slacxuiman
from slacx.slacxcore.operations import slacxopman
from slacx.slacxcore.workflow import slacxwfman

class SlacxPlugin(base.plugin):
    # The display name in the xi-cam plugin bar
    name = 'Slacx'

    def __init__(self, *args, **kwargs):

        # start slacx core objects    
        opman = slacxopman.OpManager()
        wfman = slacxwfman.WfManager()
        # start slacx ui objects
        uiman = slacxuiman.UiManager()
        # set up ui-core refs    
        uiman.opman = opman
        uiman.wfman = wfman
        # Make the slacx title box
        uiman.make_title()    
        # Connect the menu actions to UiManager functions
        uiman.connect_actions()
        # Take care of remaining details
        uiman.final_setup()

        # Set the widgets in base.plugin containers
        self.centerwidget = uiman.ui.center_frame
        self.leftwidget = uiman.ui.left_frame
        self.rightwidget = uiman.ui.right_frame

        super(SlacxPlugin, self).__init__(*args, **kwargs)


