#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check and save program functionality used by Mimic.
"""

try:
    import pymel.core as pm
    import maya.mel as mel

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    mel = None
    MAYA_IS_RUNNING = False
import math

import general_utils
import mimic_utils
import mimic_external_axes
import mimic_io

from analysis import analysis
from analysis import analysis_utils
reload(analysis)
reload(analysis_utils)

from postproc import postproc
from postproc import postproc_setup
from postproc import postproc_options

OUTPUT_WINDOW_NAME = 'programOutputScrollField'


def analyze_program(*args):
    """
    Check program parameters, raise exception on failure
    :return:
    """
    # Do this first upon button click!
    _clear_output_window()
    _initialize_export_progress_bar()

    # Check program, commands, raise exception on failure
    program_settings = _get_settings()
    robot_name = program_settings[0]

    animation_settings = program_settings[1]
    start_frame = animation_settings['Start Frame']
    pm.currentTime(start_frame)

    # Force evaluation of reconcile rotation to ensure proper export
    mimic_utils.reconcile_rotation(force_eval=True)
    
    command_dicts = _get_command_dicts(*program_settings)
    limit_data = mimic_utils.get_all_limits(robot_name)


    violation_exception, violation_warning = _check_command_dicts(command_dicts, *program_settings)
    _initialize_export_progress_bar(is_on=False)

    # If PyQtGraph imports correctly, we can run the analysis graphing utility
    # Likeliest cause of import failure is no or improper installation of numPy
    # See Mimic installation instructions for more details on installing numPy
    try:
        import pyqtgraph as pg
        analysis.run(robot_name, command_dicts, limit_data)
    except ImportError:
        pm.warning('MIMIC: Analysis module did not load successfully; ' \
                   'analysis graphing feature disabled. ' \
                   'Check that you have numPy installed properly; ' \
                   'see Mimic installation instructions for more details')

    # If we're sampling keyframes only, we assume it's for a post-processor
    # that's not time-dependent, and, therefore, we shouldn't raise exceptions
    # for limit violations
    postproc_settings = program_settings[2]
    using_keyframes_only = postproc_settings['Using Keyframes Only']

    if violation_exception and not using_keyframes_only:
        raise mimic_utils.MimicError('Limit violations found. ' \
                                     'See Mimic output window for details.')


def save_program(*args):
    """
    Save the program.
    :return:
    """
    # Do this first upon button click!
    _clear_output_window()
    _initialize_export_progress_bar()

    # Check program, commands, raise exception on failure
    program_settings = _get_settings()

    animation_settings = program_settings[1]
    start_frame = animation_settings['Start Frame']

    pm.currentTime(start_frame)

    # Force evaluation of reconcile rotation to ensure proper export
    mimic_utils.reconcile_rotation(force_eval=True)

    command_dicts = _get_command_dicts(*program_settings)

    violation_exception, violation_warning = _check_command_dicts(command_dicts, *program_settings)

    # If we're sampling keyframes only, we assume it's for a post-processor
    # that's not time-dependent, and, therefore, we shouldn't raise exceptions
    # for limit violations
    postproc_settings = program_settings[2]
    using_keyframes_only = postproc_settings['Using Keyframes Only']

    if not using_keyframes_only:
        if violation_exception:
            _initialize_export_progress_bar(is_on=False)

            pm.scrollField(OUTPUT_WINDOW_NAME,
                   insertText='\n\nNO PROGRAM EXPORTED!',
                   edit=True)

            pm.headsUpMessage('WARNINGS: No Program Exported; ' \
                              'See Mimic output window for details')
            
            raise mimic_utils.MimicError('Limit violations found. ' \
                                         'No Program Exported. ' \
                                         'See Mimic output window for details.')

    # Continue to save program:
    _process_program(command_dicts, *program_settings)

    if violation_warning:
        if not using_keyframes_only:
            pm.headsUpMessage('Program exported with warnings; ' \
                              'See Mimic output window for details')
        else:
            pm.headsUpMessage('Program exported successfuly; ' \
                              'See Mimic output window for details')
    else:
        pm.headsUpMessage('Program exported successfuly; ' \
                          'See Mimic output window for details')

    _initialize_export_progress_bar(is_on=False)


def _process_program(command_dicts, robot, animation_settings, postproc_settings, user_options):
    """
    Process a command dictionary as a program using the selected post processor.
    :param robot: Name of the robot
    :param animation_settings: User-defined animation settings.
    :param postproc_settings: User-defined program settings.
    :param user_options: User-defined postproc options.
    :return:
    """
    # Get the selected post processor
    processor_type = postproc_settings['Processor Type']
    processor = postproc_setup.POST_PROCESSORS[processor_type]()

    # Apply processor-specific formatting to commands
    commands = processor.format_commands(command_dicts)

    # Make sure we're using the right directory
    output_directory = postproc_settings['Output Directory']
    processor.set_program_directory(output_directory)

    # Process the raw_commands into relevant robot control code
    template_filename = postproc_settings['Template Filename']
    program = processor.process(commands, user_options, template_filename)

    # write the processed animation as robot code to a file
    overwrite_option = postproc_settings['Overwrite Option']
    output_filename = postproc_settings['Output Filename']
    output_path = processor.write(
        program,
        output_filename=output_filename,
        overwrite=overwrite_option)

    # Show us what we did!
    _show_program_in_output_window(robot, processor, program)


def _clear_output_window():
    """
    Clear the output window
    :return:
    """
    pm.scrollField(OUTPUT_WINDOW_NAME, clear=True, edit=True)


def _show_program_in_output_window(robot, processor, program):
    """
    Display program in the output window.
    :param robot:
    :param processor:
    :param program:
    :return:
    """

    # Update the output-text viewer in the Mimic UI
    details = 'Type of robot     : {} {} ({})\n' \
              'Type of processor : {} {} ({})\n' \
              'Path to template  : {}\n' \
              'Path to output    : {}\n' \
              '\n'

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot)
    filled_details = details.format(
        mimic_utils.get_robot_type(robot),
        mimic_utils.get_robot_subtype(robot),
        robot,
        processor.type_robot,
        processor.type_processor,
        processor.__class__.__name__,
        postproc.confirm_path_exists(processor.get_program_template_path()),
        postproc.confirm_path_exists(processor.get_program_output_path())
    )

    pm.scrollField(OUTPUT_WINDOW_NAME,
                   insertText=filled_details,
                   edit=True)

    pm.scrollField(OUTPUT_WINDOW_NAME,
                   insertText=program + '\n',
                   edit=True)


def _get_settings():
    """
    Get program parameters.
    :return:
    """
    # Get parameters
    robot = mimic_utils.get_selected_robot_name()
    animation_settings = _get_settings_for_animation(robot)
    postproc_settings = _get_settings_for_postproc(robot)
    user_options = postproc_options.get_user_selected_options()
    # Return all of these
    return robot, animation_settings, postproc_settings, user_options


def _get_settings_for_animation(robot):
    """
    Get the animation parameters start frame, end frame, framerate, and total time
    in seconds from Maya.
    :return:
    """
    start_frame = pm.intField("i_programStartFrame", query=True, value=True)
    end_frame = pm.intField("i_programEndFrame", query=True, value=True)
    framerate = mimic_utils.get_maya_framerate()

    # Define the animation time in seconds.
    animation_time_sec = ((end_frame) - start_frame) / framerate

    # Raise warning if end frame and start frame incompatible
    if end_frame <= start_frame:
        warning = 'End Frame must be larger than Start Frame'
        raise mimic_utils.MimicError(warning)

    '''
    # Raise warning if no keyframes are set
    closest_ik_key = mimic_utils.get_closest_ik_keyframe(robot, start_frame)[0]
    if not type(closest_ik_key) == float:
        warning = 'You must set an IK or FK keyframe to ensure ' \
                  'proper evaluation when saving a program; ' \
                  'no program written'
        raise mimic_utils.MimicError(warning)
    '''
    # All good, create output dictionary
    animation_settings = {'Start Frame': start_frame,
                          'End Frame': end_frame,
                          'Framerate': framerate,
                          'Animation Time (sec)': animation_time_sec}
    return animation_settings


def _get_settings_for_postproc(robot):
    """
    Get program settings from the Mimic UI.
    :return program_settings: dictionary
    """
    # Get all important settings
    using_time_interval = pm.radioCollection(
        'sample_rate_radio_collection', query=True, select=True) == 'rb_timeInterval'
    using_keyframes_only = not using_time_interval  # TODO: Clever, but not expandable
    time_interval_value = pm.textField('t_timeBetweenSamples', query=True, text=True)
    time_interval_units = 'seconds' \
        if pm.radioButtonGrp('time_unit_radio_group', query=True, sl=True) == 1 \
        else 'frames'
    ignore_warnings = pm.checkBox('cb_ignoreWarnings', value=True, query=True)
    processor_type = pm.optionMenu('postProcessorList', query=True, value=True)
    output_directory = pm.textField('t_programDirectoryText', text=True, query=True)
    output_filename = pm.textField('t_outputFileName', text=True, query=True)
    template_filename = pm.textField('t_templateFileName', text=True, query=True)
    overwrite_option = pm.checkBox('cb_overwriteFile', value=True, query=True)

    # Get time interval in seconds
    animation_settings = _get_settings_for_animation(robot)
    framerate = animation_settings['Framerate']
    if time_interval_units == 'seconds':
        sample_rate_sec = float(time_interval_value)
    else:  # time_interval_units == 'frames'
        sample_rate_sec = float(time_interval_value) / float(framerate)
    time_interval_in_seconds = sample_rate_sec

    # Check for warnings
    if using_time_interval:
        # Confirm that the time interval is valid
        try:
            time_interval_value = float(time_interval_value)
            assert time_interval_value > 0
        except ValueError:
            if time_interval_units == 'seconds':
                warning = 'Time interval must be a float'
                raise mimic_utils.MimicError(warning)
            else:  # time_interval_units == 'frames'
                warning = 'Time interval must be a float'
                raise mimic_utils.MimicError(warning)
        except AssertionError:
            if time_interval_units == 'seconds':
                warning = 'Time interval must be greater than zero'
                raise mimic_utils.MimicError(warning)
            else:  # time_interval_units = 'frames'
                warning = 'Time interval must be greater than zero'
                raise mimic_utils.MimicError(warning)

    # Check if the robot-postproc compatibility warning was triggered
    processor = postproc_setup.POST_PROCESSORS[processor_type]()
    warning = _check_robot_postproc_compatibility(robot, processor)
    if warning != '':
        if not ignore_warnings:
            raise mimic_utils.MimicError(warning)
        else:
            warning += '\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)

    # Assign values to output dict
    postproc_settings = {
        'Using Time Interval': using_time_interval,
        'Using Keyframes Only': using_keyframes_only,
        'Time Interval Value': time_interval_value,
        'Time Interval Units': time_interval_units,
        'Time Interval in Seconds': time_interval_in_seconds,
        'Ignore Warnings': ignore_warnings,
        'Processor Type': processor_type,
        'Output Directory': output_directory,
        'Output Filename': output_filename,
        'Template Filename': template_filename,
        'Overwrite Option': overwrite_option
    }
    return postproc_settings


def _get_command_dicts(robot, animation_settings, postproc_settings, user_options):
    """
    Get robot commands from animation and options.
    :param robot: Name of the robot
    :param animation_settings: User-defined animation settings.
    :param animation_settings: User-defined program settings.
    :param user_options: User-defined postproc options.
    :return:
    """
    
    # Determine sample mode
    using_sample_rate = postproc_settings['Using Time Interval']
    using_keyframes_only = postproc_settings['Using Keyframes Only']
    time_interval_in_seconds = postproc_settings['Time Interval in Seconds']

    # Get frames to sample
    frames = []
    if using_sample_rate:
        frames = _get_frames_using_sample_rate(animation_settings, postproc_settings)
    elif using_keyframes_only:
        frames = _get_frames_using_keyframes_only(robot, animation_settings)
    else:  # add other sampling modes here
        pass

    # Get commands from sampled frames
    command_dicts = _sample_frames_get_command_dicts(robot, frames, animation_settings, time_interval_in_seconds,
                                                     user_options)
    
    if using_sample_rate:
        # Check commands for axis flips and reconcile them if necessary
        command_dicts = _check_command_rotations(robot, animation_settings, command_dicts)

    return command_dicts


def _check_command_dicts(command_dicts, robot, animation_settings, postproc_settings, user_options):
    """
    Check command dictionary for warnings.
    :param command_dicts: A list of list of robot axes
    :param robot_name: Name of the robot
    :param animation_settings: User-defined animation settings.
    :param postproc_settings: User-defined program settings.
    :param user_options: User-defined postproc options.
    :return: True if warning, False otherwise
    """
    # Check to see if the user has elected to ignore warnings
    ignore_warnings = postproc_settings['Ignore Warnings']
    warning = ''  # Temporary holder

    # Check if limits have been exceeded (i.e. velocity, acceleration)
    if user_options.Include_axes and not user_options.Ignore_motion:
        # TODO: Add UI options to select which violations, max/min/avg user wants to check

        # Check velocity limits
        velocity_limits = mimic_utils.get_velocity_limits(robot)
        velocity_dicts = analysis_utils._generate_derivative_dicts(command_dicts, 1)
        if velocity_limits['Axis 1']['Min Limit'] is None:
            velocity_warning = 'Unable to check velocity limits. Robot rig does not contain velocity data.\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=velocity_warning, edit=True)
        velocity_violations, velocity_stats = _check_command_dicts_limits(velocity_dicts, limits=velocity_limits, get_min=True, get_max=True, get_average=True)

        # Check acceleration limits
        acceleration_limits = mimic_utils.get_acceleration_limits(robot)
        acceleration_dicts = analysis_utils._generate_derivative_dicts(velocity_dicts, 2)
        if acceleration_limits['Axis 1']['Min Limit'] is None:
            acceleration_warning = 'Unable to check acceleration limits. Robot rig does not contain acceleration data.\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=acceleration_warning, edit=True)
        acceleration_violations, acceleration_stats = _check_command_dicts_limits(acceleration_dicts, limits=acceleration_limits, get_min=True, get_max=True, get_average=True)

        # Check jerk limits
        jerk_limits = mimic_utils.get_jerk_limits(robot)
        jerk_dicts = analysis_utils._generate_derivative_dicts(acceleration_dicts, 3)
        if jerk_limits['Axis 1']['Min Limit'] is None:
            jerk_warning = 'Unable to check jerk limits. Robot rig does not contain jerk data.\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=jerk_warning, edit=True)
        jerk_violations, jerk_stats = _check_command_dicts_limits(jerk_dicts, limits=jerk_limits, get_min=True, get_max=True, get_average=True)

        # Format and print axis statistics
        _print_axis_stats(velocity_stats, "Velocity")
        _print_axis_stats(acceleration_stats, "Acceleration")
        _print_axis_stats(jerk_stats, "Jerk")


    if user_options.Include_external_axes and not user_options.Ignore_motion:
        # TODO: Implement velocity check for external axes
        # warning = _check_velocity_of_external_axes(robot, command_dicts, animation_settings['Framerate'])
        # if warning != '':
        #     # Print this one always
        #     warning += '\n'
        #     pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)
        #     if not ignore_warnings:
        #         raise mimic_utils.MimicError(warning)
        pass

    if user_options.Include_pose and not user_options.Ignore_motion:
        # TODO: Implement velocity check for poses
        # warning = _check_velocity_of_pose(robot, command_dicts, animation_settings['Framerate'])
        # if warning != '':
        #     # Print this one always
        #     warning += '\n'
        #     pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)
        #     if not ignore_warnings:
        #         raise mimic_utils.MimicError(warning)
        pass

    # If all checks passed then we don't have any warnings...
    # Format and print warnings
    violation_exception = False
    violation_warning = False
    if velocity_violations or acceleration_violations or jerk_violations:
        # Print this one always
        pm.headsUpMessage('WARNINGS: See Mimic output window for details')
        if velocity_violations:
            _print_violations(velocity_violations, velocity_limits, "Velocity")
        if acceleration_violations:
            _print_violations(acceleration_violations, acceleration_limits, "Acceleration")
        if jerk_violations:
            _print_violations(jerk_violations, jerk_limits, "Jerk")
        if not ignore_warnings:
            violation_exception = True
        violation_warning = True
    else:
        no_warning = 'All checks passed!\n'
        pm.scrollField(OUTPUT_WINDOW_NAME, insertText=no_warning, edit=True)
        pm.headsUpMessage('All Checks Passed!')
        violation_warning = False

    return violation_exception, violation_warning 


def _print_violations(violation_dicts, limits, limit_type):
    """
    Format and print limit violations.
    :param violation_dicts: A list of dicts of axis violations
    :param limits: A list of robot robot axes limits
    :param limit_type: Name string of the limit type
    :return:
    """
    warning = ''
    warning_template = '   {0:>{time_padding}}{1:>{frame_padding}}{2:>{limit_padding}}{3:>{val_padding}}\n'
    padding = {'val_padding' : 13, 'limit_padding' : 10, 'time_padding' : 10, 'frame_padding' : 10}
    
    for axis_name in sorted(violation_dicts):
        warning += axis_name + " {} Warnings:\n".format(limit_type)
        axis_num = int(axis_name.split(' ')[-1]) - 1  # This is super hacky... should fix.
        warning += warning_template.format('Time', 'Frame', 'Limit', 'Actual', **padding)
        for violation in violation_dicts[axis_name]:
            if limits[axis_name]['Max Limit']:
                axis_limit = general_utils.num_to_str(limits[axis_name]['Max Limit'], precision=3)
            else:
                return 

            warning += warning_template.format(
                general_utils.num_to_str(violation['Time Index'], precision=3),
                general_utils.num_to_str(violation['Frame'], precision=3),
                axis_limit,
                general_utils.num_to_str(violation[postproc.AXES][axis_num], precision=3),
                **padding)

    pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)


def _print_axis_stats(axis_stats, limit_type):
    """
    Format and print axis statistics.
    :param axis_stats: A dict of axis statistics
    :param limit_type: Name string of the limit type
    :return:
    """
    # TODO: This function is a mess. Should definitely be cleaned up,
    # but since this is all getting graphed anyway... 
    # TODO: stop hardcoding num_axes
    num_axes = 6
    axis_template = '>>> {0:>{axis_padding}} '
    axis_padding = {'axis_padding' : 2}

    res = [None] * (num_axes + 1)

    # Header        
    res[0] = axis_template.format('A', **axis_padding)
    for axis_index in range(num_axes):
        res[axis_index + 1] = axis_template.format(axis_index + 1, **axis_padding)

    # Min
    min_max_template = '{0:>{time_padding}}{1:>{frame_padding}}{2:>{val_padding}}   |'
    min_max_padding = {'val_padding' : 13, 'time_padding' : 10, 'frame_padding' : 10}
    if axis_stats['min']:
        res[0] += min_max_template.format('Time', 'Frame', 'Min', **min_max_padding)
        for axis_index, command in enumerate(axis_stats['min']):
            res[axis_index+1] += min_max_template.format(
                general_utils.num_to_str(command['Time Index'], precision=3),
                general_utils.num_to_str(command['Frame'], precision=3),
                general_utils.num_to_str(command[postproc.AXES][axis_index], precision=3),
                **min_max_padding)

    # Max
    if axis_stats['max']:
        res[0] += min_max_template.format('Time', 'Frame', 'Max', **min_max_padding)
        for axis_index, command in enumerate(axis_stats['max']):
            res[axis_index+1] += min_max_template.format(
                general_utils.num_to_str(command['Time Index'], precision=3),
                general_utils.num_to_str(command['Frame'], precision=3),
                general_utils.num_to_str(command[postproc.AXES][axis_index], precision=3),
                **min_max_padding)

    # Avg
    avg_template = '{0:>{avg_padding}}'
    avg_padding = {'avg_padding' : 10}
    if axis_stats['avg']:
        res[0] += avg_template.format('Avg', **avg_padding)
        for axis_index, axis_avg in enumerate(axis_stats['avg']):
            res[axis_index+1] += avg_template.format(
                general_utils.num_to_str(axis_avg, precision=3), **avg_padding)

    # Formatting
    stats_str = '{} Stats:\n'.format(limit_type) + '\n'.join(res) + '\n'
    pm.scrollField(OUTPUT_WINDOW_NAME, insertText=stats_str, edit=True)


def _check_command_dicts_limits(command_dicts, limits=None, get_min=False, get_max=False, get_average=False):
    """
    Check a command dicts for limit errors. Return a dict of commands for all violations.
    :param command_dicts: A list of list of robot axes
    :param limits: A list of robot robot axes limits
    :param get_min: Record min axis values 
    :param get_max: Record max axis values
    :param get_avg: Record avg axis values
    :return:
    """
    # Seed initial values
    # TODO: Stop hardcoding num_axes
    num_axes = 6
    violations = {}
    min_vals = [command_dicts[0] for _ in range(num_axes)]
    max_vals = [command_dicts[0] for _ in range(num_axes)]
    running_totals = [0 for _ in range(num_axes)]

    for current_command in command_dicts:
        current_axes = current_command[postproc.AXES]
        for axis_index, current_axis in enumerate(current_axes):
            axis_number = axis_index + 1  # Axis numbers are 1-indexed
            axis_name = 'Axis {}'.format(axis_number)

            # Check limits
            if limits:
                if limits[axis_name]['Max Limit']:
                    if current_axis > limits[axis_name]['Max Limit']:
                        violations.setdefault(axis_name,[]).append(current_command)
                    elif current_axis < limits[axis_name]['Min Limit']:
                        violations.setdefault(axis_name,[]).append(current_command)

            # Min
            if get_min:
                if current_axis < min_vals[axis_index][postproc.AXES][axis_index]:
                    # TODO: this only records the first time a min val has been reached.
                    # It doesn't account for multiple frames with the same min val
                    min_vals[axis_index] = current_command

            # Max
            if get_max:
                if current_axis > max_vals[axis_index][postproc.AXES][axis_index]:
                    # TODO: this only records the first time a max val has been reached.
                    # It doesn't account for multiple frames with the same max val
                    max_vals[axis_index] = current_command

            # Average
            if get_average:
                running_totals[axis_index] += current_axis

    # TODO: This data structure should probably be better defined.
    stats = {'min': None, 'max' : None, 'avg': None}
    if get_min:
        stats['min'] = min_vals
    if get_max:
        stats['max'] = max_vals
    if get_average:
        stats['avg'] = [axis_total / len(command_dicts) for axis_total in running_totals]

    return violations, stats


def _check_robot_postproc_compatibility(robot, processor):
    """
    Verify the compatibility of the selected robot and the processor.
    :return:
    """
    warning = ''
    robot_type = mimic_utils.get_robot_type(robot)
    processor_type = processor.type_robot

    if robot_type != processor_type:
        warning = 'WARNING!\n' \
                  'The type of robot ({}) \n' \
                  'and type of processor ({}) \n' \
                  'selected are incompatible!\n' \
            .format(robot_type, processor_type)
    return warning


def _check_command_rotations(robot, animation_settings, command_dicts):
    """
    Check commands that used a sample rate.
    :param robot:
    :param animation_settings:
    :param command_dicts:
    :return:
    """
    # TODO: Do this check using userOptions instead...
    # Get axes, if they exist
    command_axes = []
    for command_dict in command_dicts:
        axes = command_dict[postproc.AXES] if postproc.AXES in command_dict else None
        command_axes.append(list(axes))

    # Make sure the user has selected use of axes
    if not all(x is None for x in command_axes):
        start_frame = animation_settings['Start Frame']
        # Get indices for command and axis
        for command_index in range(len(command_dicts)):
            for axis_index in range(6):
                # Get the initial value
                value = command_axes[command_index][axis_index]
                # Operate on the value depending on conditional
                if axis_index == 3 or axis_index == 5:  # zero-indexed
                    rotation_axis = 'Z'
                    if command_index == 0:  # Get initial value
                        axis_number = axis_index + 1
                        value = mimic_utils.get_reconciled_rotation_value(
                            robot,
                            axis_number,
                            rotation_axis,
                            start_frame)[0]
                    else:  # Perform the check
                        previous_value = command_axes[command_index - 1][axis_index]
                        value = mimic_utils.accumulate_rotation(
                            value,
                            previous_value)
                    # Replace original value with new value
                    command_axes[command_index][axis_index] = value
                else:  # Not a problem axis
                    pass
            # Replace the original commands with the new commands
            reconciled_axes = postproc.Axes(*command_axes[command_index])
            command_dicts[command_index][postproc.AXES] = reconciled_axes
    return command_dicts


def _get_frames_using_sample_rate(animation_settings, postproc_settings):
    """
    Get frames from animation using a sample rate.
    :param animation_settings:
    :return:
    """
    # Get relevant animation parameters.
    start_frame = animation_settings['Start Frame']
    end_frame = animation_settings['End Frame']
    framerate = animation_settings['Framerate']
    animation_time_sec = animation_settings['Animation Time (sec)']
    time_interval_units = postproc_settings['Time Interval Units']
    time_interval_value = postproc_settings['Time Interval Value']

    animation_time_frames = end_frame - start_frame
    # Convert time interval from frames to seconds if necessary
    if time_interval_units == 'seconds':
        step_sec = float(time_interval_value)
        # Find the closest multiple of the number of steps in our animation
        num_steps = int(math.ceil(float(animation_time_sec) / step_sec) + 1)

        # Create array of time-steps in milliseconds.
        time_array_sec = [round(i * step_sec, 5) for i in range(0, num_steps)]
        # Create list of frames (time-steps).
        frames = [round(start_frame + (framerate * t_sec), 3) for t_sec in time_array_sec]
    else:  # time_interval_units == 'frames'
        step_frame = float(time_interval_value)
        num_steps = int(math.ceil(float(animation_time_frames) / step_frame) + 1)
        frames = [start_frame + round(i * step_frame, 3) for i in range(0, num_steps)]

    return frames
 

    return frames
 

def _get_frames_using_keyframes_only(robot, animation_settings):
    """
    Get frames from animation using a robot's keyframes only.
    :param robot:
    :param animation_settings:
    :return:
    """
    # Get relevant animation parameters.
    start_frame = animation_settings['Start Frame']
    end_frame = animation_settings['End Frame']
    # Get list of keyframes on robots IK attribute for the given range
    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot)
    ik_keyframes = pm.keyframe(
        target_ctrl_path,
        attribute='ik',
        query=True,
        time='{}:{}'.format(start_frame, end_frame))
    # Verify that there is also a keyframe set on the FK controls' rotate
    # attributes. If there's not, we remove it from the list
    # Note: we only need to check on controller as they are all keyframed
    # together
    fk_test_handle_path = mimic_utils.format_path('{0}|{1}robot_GRP|{1}FK_CTRLS|{1}a1FK_CTRL.rotateY', robot)
    frames = [frame for frame in ik_keyframes if pm.keyframe(
        fk_test_handle_path,
        query=True,
        time=frame)]
    return frames


def _sample_frames_get_command_dicts(robot_name, frames, animation_settings, time_interval_in_seconds, user_options):
    """
    Sample robot commands using a list of frames and user options.
    :param robot_name:
    :param frames:
    :param animation_settings:
    :param user_options:
    :return:
    """
    # Initialize output array.
    command_dicts = []
    time_index_count = 0
    start_frame = animation_settings['Start Frame']
    end_frame = animation_settings['End Frame']

    for frame in frames:
        # Set the background to the current frame
        # TODO: Implement this! This rocks:
        # pm.currentTime(frame)
        # Create a dict of datatypes per frame
        command_dict = {}
        # Add this frame number/step/index to the dictionary
        command_dict['Frame'] = frame
        command_dict['Framerate'] = animation_settings['Framerate']
        command_dict['Time Index'] = time_index_count * time_interval_in_seconds
        time_index_count += 1

        # Get motion parameters
        if not user_options.Ignore_motion:
            if user_options.Include_axes:
                axes = _sample_frame_get_axes(robot_name, frame)
                command_dict[postproc.AXES] = postproc.Axes(*axes)
            if user_options.Include_pose:
                pose = _sample_frame_get_pose(robot_name, frame)
                command_dict[postproc.POSE] = postproc.Pose(*pose)
            if user_options.Include_external_axes:
                external_axes = _sample_frame_get_external_axes(robot_name, frame)
                command_dict[postproc.EXTERNAL_AXES] = postproc.ExternalAxes(*external_axes)
            if user_options.Include_configuration:
                configuration = _sample_frame_get_configuration(robot_name, frame)
                command_dict[postproc.CONFIGURATION] = postproc.Configuration(*configuration)
        # Get IO parameters
        if not user_options.Ignore_IOs:
            if user_options.Include_digital_outputs:
                digital_output = _sample_frame_get_outs(robot_name, frame, 'digital')
                command_dict[postproc.DIGITAL_OUTPUT] = digital_output
            if user_options.Include_digital_inputs:
                # TODO: Implement digital inputs
                # digital_input = None
                # command_dict[postproc.DIGITAL_INPUT'] = postproc.DigitalOutput(*digital_input)
                pass
            if user_options.Include_analog_outputs:
                analog_output = _sample_frame_get_outs(robot_name, frame, 'analog')
                command_dict[postproc.ANALOG_OUTPUT] = analog_output
            if user_options.Include_analog_inputs:
                # TODO: Implement analog inputs
                # analog_input = None
                # command_dict[postproc.ANALOG_INPUT] = postproc.DigitalOutput(*analog_input)
                pass
        command_dicts.append(command_dict)
        pm.refresh()
        _update_export_progress_bar(start_frame, end_frame, frame)
    # Reset current frame (just in case)
    pm.currentTime(frames[0])
    mimic_utils.reconcile_rotation(force_eval=True)

    return command_dicts


def _sample_frame_get_axes(robot_name, frame):
    """
    Get robot Axes from an animation frame.
    :param robot_name: Name of the robot
    :param frame: Frame to sample
    :return:
    """

    axes = []
    pm.currentTime(frame)

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)
    for i in range(6):
        axis_number = i + 1  # Axis numbers are 1-indexed
        axis_path = target_ctrl_path + '.axis{}'.format(axis_number)
        axis = pm.getAttr(axis_path)

        axes.append(axis)
        
    return axes


def _sample_frame_get_pose(robot_name, frame):
    """
    Get robot Pose from an animation frame.
    :param robot_name: Name of the robot
    :param frame: Frame to sample
    :return:
    """
    # Set the time
    # TODO: Implement this in parent function
    pm.currentTime(frame)

    # tool_name = get_tool_name(robot_name)
    tool_name = mimic_utils.get_tool_ctrl_path(robot_name)
    try:  # Try to grab the named tool
        tool_object = pm.ls(tool_name)[0]  # Try to get tool, may raise an exception
    except IndexError:  # No tool attached, use flange
        tool_name = mimic_utils.get_tcp_hdl_path(robot_name)

    # Local Base Frame controller (circle control at base of the robot).
    base_name = pm.ls(mimic_utils.get_local_ctrl_path(robot_name))[0]

    # Get name of the tcp and base
    world_matrix = '.worldMatrix'
    tcp_name_world_matrix = tool_name + world_matrix
    base_name_world_matrix = base_name + world_matrix

    # TRANSLATIONS

    # Get translation with respect to Maya's world frame
    tcp_translation = pm.xform(tool_name, query=True, rp=True, ws=True)
    base_translation = pm.xform(base_name, query=True, rp=True, ws=True)

    # ROTATIONS

    # Get TCP rotation with respect to Maya's world frame
    _tcp_matrix = pm.getAttr(tcp_name_world_matrix, time=frame)
    tcp_rotation = general_utils.matrix_get_rotations(_tcp_matrix)

    # Get Base rotation with respect to Maya's world frame
    _base_matrix = pm.getAttr(base_name_world_matrix, time=frame)
    base_rotation = general_utils.matrix_get_rotations(_base_matrix)

    # TRANSFORMATIONS

    # Compose 4x4 matrices using the rotation and translation from the above
    tcp_matrix_4x4 = general_utils.matrix_compose_4x4(tcp_rotation, tcp_translation)
    base_matrix_4x4 = general_utils.matrix_compose_4x4(base_rotation, base_translation)

    # Invert the base matrix
    base_matrix_4x4 = general_utils.matrix_get_inverse(base_matrix_4x4)

    # Get pose itself
    initial_pose_matrix = general_utils.matrix_multiply(base_matrix_4x4, tcp_matrix_4x4)

    # CONVERSIONS

    # Decompose the initial pose matrix
    initial_translation = general_utils.matrix_get_translation(initial_pose_matrix)
    initial_rotations = general_utils.matrix_get_rotations(initial_pose_matrix)

    # Rearrange from Maya CS (mcs) to Robot CS (rcs)
    indices = [2, 0, 1]
    new_translation = [initial_translation[i] * 10 for i in indices]  # cm to mm
    new_rotation = [[initial_rotations[i][j] for j in indices] for i in indices]

    # Define rotation matrix and convert the rotations based robot type
    # Based on the orientation of the coordinate frame of the mounting flange
    # TODO: Integrate this with rigs, unclear and shouldn't be hardcoded
    robot_type = mimic_utils.get_robot_type(robot_name)
    if robot_type == 'ABB':
        conversion_rotation = [
            [0, 0, -1],
            [0, 1, 0],
            [1, 0, 0]
        ]
    # elif robot_type == 'KUKA':
    #     conversion_rotation = [
    #         [0, -1, 0],
    #         [0, 0, 1],
    #         [-1, 0, 0]
    #     ]
    else:
        raise mimic_utils.MimicError('Robot type not supported for Pose movement')

    # Perform the conversion operation itself
    converted_rotation = general_utils.matrix_multiply(conversion_rotation, new_rotation)

    # Compose pose
    pose_matrix = general_utils.matrix_compose_4x4(converted_rotation, new_translation)

    # Decompose pose as expected for output
    pose = general_utils.matrix_decompose_4x4_completely(pose_matrix)
    return pose


def _sample_frame_get_external_axes(robot_name, frame):
    """
    Get robot External Axes from an animation frame.
    :param robot_name: Name of the robot
    :param frame: Frame to sample
    :return:
    """
    # Set up keys
    key_ignore = 'Ignore'
    key_axis_number = 'Axis Number'
    key_position = 'Position'
    # Create an list of Nones for initial external axes
    external_axes = [None for _ in range(6)]
    # Get all external axes for this robot
    external_axis_names = mimic_external_axes.get_external_axis_names(robot_name)
    # Get info dict for each of those external axes
    for external_axis_name in external_axis_names:
        info = mimic_external_axes.get_external_axis_info_simple(robot_name, external_axis_name, frame)
        # Get values from info dict
        ignore = info[key_ignore]
        if not ignore:
            # Put it in the right place
            axis_number = info[key_axis_number]
            axis_index = axis_number - 1
            position = info[key_position]
            external_axes[axis_index] = position
    # Return an ordered list of Nones and/or positions
    return external_axes


def _sample_frame_get_outs(robot_name, frame, out_type='digital'):
    """
    Get robot Digital Out from an animation frame.
    :param robot_name: Name of the robot
    :param frame: Frame to sample
    :return:
    """
    # Set up keys
    key_ignore = 'Ignore'
    key_io_number = 'IO Number'
    key_value = 'Value'
    key_postproc_id = 'Postproc ID'
    key_type = 'Type'

    # Create a list of Nones for initial external axes
    io_dict = {}
    ios = []

    # Get all external axes for this robot
    io_names = mimic_io.get_io_names(robot_name)
    # Get info dict for each of those IOs
    for io_name in io_names:
        info = mimic_io.get_io_info_simple(robot_name, io_name, frame)
        # Get values from info dict
        ignore = info[key_ignore]
        if not ignore:
            # Put it in the right place
            io_number = info[key_io_number]
            postproc_id = info[key_postproc_id]
            value = info[key_value]
            io_type = info[key_type]

            if io_type == out_type:
                # Convert bool values to integers for digital outs
                if out_type == 'digital':
                    value = int(value)
                    io_dict[io_number] = postproc.DigitalOutput(postproc_id, value)
                else:
                    io_dict[io_number] = postproc.AnalogOutput(postproc_id, value)

    # Convert io_dict to ordered list
    io_sorted_numbers = sorted(io_dict)
    for io_number in io_sorted_numbers:
        ios.append(io_dict[io_number])
        
    # Return an ordered list of Nones and/or positions
    return ios


def _sample_frame_get_configuration(robot_name, frame):
    """
    Get robot Configuration from an animation frame.
    :param robot_name:
    :param frame:
    :return:
    """
    configuration = mimic_utils.get_robot_configuration(robot_name, frame)
    return configuration


def _initialize_export_progress_bar(is_on=True):
    """
    """
    pm.progressBar('pb_exportProgress', edit=True, progress=0)
    pm.progressBar('pb_exportProgress', edit=True, visible=is_on)


def _update_export_progress_bar(start_frame, end_frame, frame_index):
    """
    """
    frame_range = end_frame - start_frame

    if (frame_range == 0):
        step = 0
    else:
        export_bar_range = 100
        step = ((frame_index - start_frame) * export_bar_range) / frame_range
        pm.progressBar('pb_exportProgress', edit=True, progress=int(step))

