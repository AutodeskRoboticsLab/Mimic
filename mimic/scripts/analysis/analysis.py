#!usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import pymel.core as pm
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

from analysis import analysis_ui
from analysis import analysis_utils
import ui_utils

import importlib

importlib.reload(analysis_ui)
importlib.reload(analysis_utils)
importlib.reload(ui_utils)


def run(robot_name, command_dicts, limit_data):
    """
    Main function that runs Mimic Analysis graphing module
    Takes input params and generates/formats the program's derivatives,
    generates graphing UI, and adds data to the UI for the user to interract
    with
    :param robot_name: str, name of robot whose program is to be analyzed
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :param limit_data: dict containing the position/velocity/acce;/jerk limits
        for given robot
    """
    window_name='mimic_analysis_window'

    # Clear any old instances is mimic_analysis_window
    mimic_analysis_window = None
    
    # Get list of axis numbers from the program data
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

    # Add axis limit data to the plot
    # TO-DO: add external axis limit data
    mimic_analysis_window.analysis_plot.add_limit_data(limit_data)

    mimic_analysis_window.initialize_toggle_states() 

