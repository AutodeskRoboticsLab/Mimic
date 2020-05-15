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


def get_program_data(command_dicts):
    """
    Parses command_dicts to generate a dictionary of program values for each 
    axis, at every frame specified by the program settings; includes
    Position, Velocity, Acceleration, and Jerk 
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return program_data: dict {
        'Axis 1': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
        'Axis 2': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
                                   ...
        'Axis n': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]}
        }
    :return frames: list of frame numbers representing the given program
    """

    # Get structure definitions from postproc module
    axes = postproc.Axes
    external_axes = postproc.ExternalAxes

    # Generate analysis data (Velocity, Accel, Jerk) and store corresponding
    # command_dicts in a list
    combined_command_dicts = generate_data_for_analysis(command_dicts)

    # Get a list of frame numbers representing the program
    frames = get_program_frames(command_dicts)

    # Format the program data for graphing
    program_data = _format_program_data(combined_command_dicts)

    return program_data, frames 
        

def generate_data_for_analysis(command_dicts):
    """
    Takes program data from command_dicts and generates the derivative values
    Velocity, Accel, and Jerk and writes their corresponding command_dicts to
    a combined dictionary
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return combined_command_dicts: dict {
        'Position': position_dicts,
        'Velocity': velocity_dicts,
        'Accel': accel_dicts,
        'Jerk': jerk_dicts}
        }
    """
    position_dicts = command_dicts  # command_dicts is the position data
    velocity_dicts = _generate_derivative_dicts(command_dicts, 1)  # 1st order
    accel_dicts = _generate_derivative_dicts(velocity_dicts, 2)  # 2nd order
    jerk_dicts = _generate_derivative_dicts(accel_dicts, 3)  # 3rd order

    combined_command_dicts = {'Position': position_dicts,
                              'Velocity': velocity_dicts,
                              'Accel': accel_dicts,
                              'Jerk': jerk_dicts}

    return combined_command_dicts


def get_program_frames(command_dicts):
    """
    Parces command_dicts to produce a list of frames that represent the
    programs timestep
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return frames: list
    """
    frames = []

    for command in command_dicts:
        frames.append(command['Frame'])

    return frames


def _format_program_data(combined_command_dicts):
    """
    Takes input data and formats it in a way that's condusive to graphing
    :param combined_command_dicts: dict containing commmand_dicts for
        Position, Velocity, Acceleration, and Jerk values for the given program
    :return program_data: {
    'Axis 1': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
    'Axis 2': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
                                   ...
    'Axis n': {'Position':[], 'Velocity':[], 'Accel':[], 'Jerk':[]},
    }
    """

    # All command_dicts in combined_coomand_dicts share some program data
    # parameters, so we can get those parameters by sampling a
    # single command_dict
    sample_command_dict = combined_command_dicts['Position']
    # Get the total number of axes
    num_primary_axes = _get_num_primary_axes(sample_command_dict)
    num_external_axes = _get_num_external_axes(sample_command_dict)
    total_num_axes = _get_total_num_axes(sample_command_dict)

    # Initialize program_data dict
    program_data = {}

    # Format axis data for each primary axis and derivative
    for axis_index in range(num_primary_axes):
        axis_number = axis_index + 1  # Axis numbers are 1-indexed
        # Initializes program_data 'Axis n' key with an empty dict
        program_data['Axis {}'.format(axis_number)] = {}
            
        for derivative in combined_command_dicts:
            program_data['Axis {}'.format(axis_number)][derivative] = []
            
            for command in combined_command_dicts[derivative]:
                # Get the axis value for the current command line, axis, and derivative
                axis_val = command[postproc.AXES][axis_index]

                # Place the value in the program_data dict
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
    Returns the number of primary axis the robot has
    Typically 6 for a standard industrial arm
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return:
    """
    return len(command_dicts[0][postproc.AXES])


def _get_num_external_axes(command_dicts):
    """
    Returns the number of external axes that are included in the robot program
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return:
    """
    try:
        return len(_get_external_axes_indeces(command_dicts))
    except TypeError:
        return 0


def _get_external_axes_indeces(command_dicts):
    """
    Get's a list of external axis numbers for external axes that are included 
    in the current program
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return external_axis_indeces: list of external axis numbers
    """
    try:
        external_axis_indeces = [i for i, x in enumerate(command_dicts[0][postproc.EXTERNAL_AXES]) if not x is None]
    except KeyError:
        external_axis_indeces = None

    return external_axis_indeces


def _get_total_num_axes(command_dicts):
    """
    Gets the combined number of primary and external axes included in the 
    current program
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return total_num_axes: int, total number of axes in current program
    """
    num_primary_axes = _get_num_primary_axes(command_dicts)
    num_external_axes = _get_num_external_axes(command_dicts)

    total_num_axes = num_primary_axes + num_external_axes

    return total_num_axes


def get_axis_numbers(command_dicts):
    """
    Produces a list of axis number included in the current program
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :return axis_numbers: list of ints representing axis numbers for given
        program. e.g. [1, 2, 3, 4, 5, 6, 8, 10, 11]
    """
    axis_numbers = []
    num_primary_axes = _get_num_primary_axes(command_dicts)

    # Primary axes are always sequential
    for i in range(num_primary_axes):
        axis_numbers.append(i+1)  # Axis numbers are 1-indexed

    # External axis numbers are not always sequential
    # We get the numbers with the _get_external_axes_indeces then append them
    # to the axis_numbers list
    external_axis_numbers = _get_external_axes_indeces(command_dicts)
    if external_axis_numbers:
        for i in external_axis_numbers:
            axis_numbers.append(num_primary_axes + i+1)  # External Axis numbers are 1-indexed

    return axis_numbers


def _generate_derivative_dicts(command_dicts, order):
    """
    Generate a command dicts list that is the derivitive of the input 
    command_dicts
    :param command_dicts: list formatted by mimic_program containing dicts of
        program info at each program timestep
    :param order: int specifying the order of the derivative (e.g. 1, 2, 3)
    :return derivative_dicts: list containing command dicts for the current
        derivative. Follows the same structure as command_dicts
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
                displacement_time = current_command[postproc.TIME_INDEX] - previous_command[postproc.TIME_INDEX]
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
                    displacement_time = current_command[postproc.TIME_INDEX] - previous_command[postproc.TIME_INDEX]
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
        
    return derivative_dicts