#!usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import pymel.core as pm
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

import analysis_ui
import analysis_utils
import ui_utils

reload(analysis_ui)
reload(analysis_utils)
reload(ui_utils)


def run(command_dicts):
    """
    """
    window_name='mimic_analysis_window'
    mimic_analysis_window = None

    '''
    if pm.window(window_name, exists = True):
        pm.deleteUI(window_name, wnd = True)
        # Delete previous references to window object
        del mimic_analysis_window
    '''
    
    axis_numbers = analysis_utils.get_axis_numbers(command_dicts)    
    # Create the Mimic Analysis UI and parent it to Maya's main UI window
    parent_window = ui_utils.getMayaWindow()
    mimic_analysis_window = analysis_ui.MimicAnalysisWindow(
                            window_name=window_name,
                            axis_numbers=axis_numbers,
                            parent=parent_window)


    # Get the program data from Maya's animation, and assign it to the plot
    program_data, frames = analysis_utils.get_program_data(command_dicts)
    mimic_analysis_window.analysis_plot.add_plot_data(program_data, frames)

    #mimic_analysis_window.test_run()

    # Set toggles based on user config file
    mimic_analysis_window.initialize_toggle_states() 

    # return mimic_analysis_window
