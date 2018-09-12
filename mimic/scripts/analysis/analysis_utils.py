#!usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import pymel.core as pm
    import maya.mel as mel

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    mel = None
    MAYA_IS_RUNNING = False
import math

from postproc import postproc

'''
class Program(object):
    """
    """
    def __init__(self, program_data):
        super(Program, self).__init__()
        self.program_data = program_data
'''

def get_program_data(command_dicts):
    """
    """
    axes = postproc.Axes
    external_axes = postproc.ExternalAxes

    combined_command_dicts = generate_data_for_analysis(command_dicts)
    frames = get_program_frames(command_dicts)

    program_data = _format_program_data(combined_command_dicts)

    return program_data, frames 
        

def generate_data_for_analysis(command_dicts):
    """
    """
    position_dicts = command_dicts
    velocity_dicts = _generate_derivative_dicts(command_dicts, 1)
    accel_dicts = _generate_derivative_dicts(velocity_dicts, 2)
    jerk_dicts = _generate_derivative_dicts(accel_dicts, 3)

    combined_command_dicts = {'Position': position_dicts,
                              'Velocity': velocity_dicts,
                              'Accel': accel_dicts,
                              'Jerk': jerk_dicts}

    return combined_command_dicts


def get_program_frames(command_dicts):
    """
    Produces an array of frames that represent the programs timestep
    """
    frames = []

    for command in command_dicts:
        frames.append(command['Frame'])

    return frames


def _format_program_data(combined_command_dicts):
    """
    program_data = {
    'Axis 1': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
    'Axis 2': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
                                   ...
    'Axis n': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
    }
    """

    sample_command_dict = combined_command_dicts['Position']
    # Get the total number of axes
    num_primary_axes = _get_num_primary_axes(sample_command_dict)
    num_external_axes = _get_num_external_axes(sample_command_dict)
    total_num_axes = _get_total_num_axes(sample_command_dict)

    program_data = {}

    # Format axis data for each primary axis and derivative
    for axis_index in range(num_primary_axes):
        axis_number = axis_index + 1  # Axis numbers are 1-indexed
        program_data['Axis {}'.format(axis_number)] = {}
            
        for derivative in combined_command_dicts:
            program_data['Axis {}'.format(axis_number)][derivative] = []
            
            for command in combined_command_dicts[derivative]:
                axis_val = command[postproc.AXES][axis_index]                          
                program_data['Axis {}'.format(axis_number)][derivative].append(axis_val)

    # If external axes exist, format axis data for each external axis
    # and derivative
    if num_external_axes > 0:
        external_axes_ideces = _get_external_axes_indeces(sample_command_dict)

        for axis_index in external_axes_ideces:
            axis_number = num_primary_axes + axis_index + 1  # Axis numbers are 1-indexed
            program_data['Axis {}'.format(axis_number)] = {}
                
            for derivative in combined_command_dicts:
                program_data['Axis {}'.format(axis_number)][derivative] = []
                
                for command in combined_command_dicts[derivative]:
                    axis_val = command[postproc.EXTERNAL_AXES][axis_index]                          
                    program_data['Axis {}'.format(axis_number)][derivative].append(axis_val)

    return program_data


def _get_num_primary_axes(command_dicts):
    """
    """
    return len(command_dicts[0][postproc.AXES])


def _get_num_external_axes(command_dicts):
    """
    """
    try:
        return len(_get_external_axes_indeces(command_dicts))
    except TypeError:
        return 0


def _get_external_axes_indeces(command_dicts):
    """
    """
    try:
        a = [i for i, x in enumerate(command_dicts[0][postproc.EXTERNAL_AXES]) if not x is None]
    except KeyError:
        a = None

    return a


def _get_total_num_axes(command_dicts):
    """
    """
    num_primary_axes = _get_num_primary_axes(command_dicts)
    num_external_axes = _get_num_external_axes(command_dicts)

    total_num_axes = num_primary_axes + num_external_axes

    return total_num_axes


def get_axis_numbers(command_dicts):
    """
    e.g. [1, 2, 3, 4, 5, 6, 8, 10, 11]
    """
    axis_numbers = []
    num_primary_axes = _get_num_primary_axes(command_dicts)

    for i in range(num_primary_axes):
        axis_numbers.append(i+1)  # Axis numbers are 1-indexed

    external_axis_numbers = _get_external_axes_indeces(command_dicts)
    if external_axis_numbers:
        for i in external_axis_numbers:
            axis_numbers.append(num_primary_axes + i+1)  # External Axis numbers are 1-indexed

    return axis_numbers


def _generate_derivative_dicts(command_dicts, order):
    """
    Generate a command dicts that is a derivitive of a command dicts.
    :param command_dicts: A list of list of robot axes
    :param order: int specifying the order of the derivative
    :return:
    """
    import copy
    derivative_dicts = copy.deepcopy(command_dicts)

    num_axes = _get_num_primary_axes(derivative_dicts)
    previous_axes = []

    for command_index, current_command in enumerate(command_dicts):
        current_axes = current_command[postproc.AXES]
        current_axes_derivative = [0] * num_axes
        if command_index > 0:  # skip zeroth
            for axis_index, current_axis in enumerate(current_axes):
                previous_axis = previous_axes[axis_index]

                displacement = current_axis - previous_axis
                # Do we need to compute displacement_time between every frame? Does this change?
                displacement_time = current_command['Time Index'] - previous_command['Time Index']
                derivative = displacement / displacement_time
                current_axes_derivative[axis_index] = derivative

        derivative_dicts[command_index][postproc.AXES] =  postproc.Axes(*current_axes_derivative)
        
        previous_axes = current_axes
        previous_command = current_command

    # Replace order-th value with with zeros; this is not a derivitive
    # We do this to ensure the lengths of our command remain constant
    for i in range(order):
        try:
            derivative_dicts[i][postproc.AXES] = postproc.Axes(*[0] * num_axes)
        except IndexError:
            pm.warning('Insufficient number of sample points to generate derivatives. ' \
                       'Increase sample rate or add additional IK/FK keys for proper ' \
                       'analysis if using time-based post-processor')

    # If external axes exist, repeat derivative process on them
    if 'external_axes' in derivative_dicts[0]:
        num_external_axes = len(command_dicts[0][postproc.EXTERNAL_AXES])
        
        # Get the indeces of external axes that are being used
        active_axes = [i for i, x in enumerate(derivative_dicts[0][postproc.EXTERNAL_AXES]) if not x is None]

        num_active_external_axes = len(active_axes)
        previous_axes = []

        for command_index, current_command in enumerate(command_dicts):
            current_axes = [current_command[postproc.EXTERNAL_AXES][x] for x in active_axes]
            current_axes_derivative = [0] * num_active_external_axes
            
            if command_index > 0:  # skip zeroth
                for derivative_index, current_axis in enumerate(current_axes):
                    previous_axis = previous_axes[derivative_index]
                    displacement = current_axis - previous_axis
                    displacement_time = current_command['Time Index'] - previous_command['Time Index']
                    derivative = displacement / displacement_time
                    current_axes_derivative[derivative_index] = derivative


            # We have to pass the same amount of axes that are in the
            # Postprocess EXTERNAL_AXIS structure, so we have to build an array
            # That matches the number of axis, with 'None' values for
            # inactive axes.
            external_axis_derivatives = [None] * num_external_axes

            for derivative_index, axis_index in enumerate(active_axes):
                external_axis_derivatives[axis_index] = current_axes_derivative[derivative_index]

            # Replace the current command entry with the command's derivatives
            derivative_dicts[command_index][postproc.EXTERNAL_AXES] =  postproc.ExternalAxes(*external_axis_derivatives)

            previous_axes = current_axes
            previous_command = current_command      

        # Replace order-th value with with zeros; this is not a derivitive
        # We do this to ensure the lengths of our command remain constant
        axis_pop =  [None] * num_external_axes
        for a, _ in enumerate(axis_pop):
            if not derivative_dicts[i][postproc.EXTERNAL_AXES][a] is None:
                axis_pop[a] = 0

        for i in range(order):
            derivative_dicts[i][postproc.EXTERNAL_AXES] = postproc.ExternalAxes(*axis_pop)
        

        # num_external_axes = len([x for x in command_dicts[0][postproc.EXTERNAL_AXES] if not x is None])
        
    return derivative_dicts