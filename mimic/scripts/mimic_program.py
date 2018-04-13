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
from postproc import postproc
from postproc import postproc_setup
from postproc import postproc_options


OUTPUT_WINDOW_NAME = 'programOutputScrollField'


def check_program(*args):
    """
    Check program parameters, raise exception on failure
    :return:
    """
    # Do this first upon button click!
    _clear_output_window()

    # Check program, commands, raise exception on failure
    program_settings = _get_settings()
    command_dicts = _get_command_dicts(*program_settings)
    _check_command_dicts(command_dicts, *program_settings)


def save_program(*args):
    """
    Save the program.
    :return:
    """
    # Do this first upon button click!
    _clear_output_window()

    # Check program, commands, raise exception on failure
    program_settings = _get_settings()
    command_dicts = _get_command_dicts(*program_settings)
    _check_command_dicts(command_dicts, *program_settings)

    # Continue to save program:

    robot = program_settings[0]
    # animation_settings = program_settings[1]
    postproc_settings = program_settings[2]
    user_options = program_settings[3]

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

    filled_details = details.format(
        pm.getAttr('{}|robot_GRP|target_CTRL.robotType'.format(robot)),
        pm.getAttr('{}|robot_GRP|target_CTRL.robotSubtype'.format(robot)),
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
    animation_time_sec = ((end_frame + 1) - start_frame) / framerate
    if end_frame <= start_frame:
        warning = 'End Frame must be larger than Start Frame'
        raise Exception(warning)
    else:
        # If no keyframes are set, exit the function.
        closest_ik_key = mimic_utils.get_closest_ik_keyframe(robot, start_frame)[0]
        if not type(closest_ik_key) == float:
            warning = 'You must set an IK or FK keyframe to ensure ' \
                      'proper evaluation when saving a program; ' \
                      'no program written'
            raise Exception(warning)

    # Raise warning if end frame and start frame incompatible
    if end_frame <= start_frame:
        warning = 'End Frame must be larger than Start Frame'
        raise Exception(warning)

    # Raise warning if no keyframes are set
    closest_ik_key = mimic_utils.get_closest_ik_keyframe(robot, start_frame)[0]
    if not type(closest_ik_key) == float:
        warning = 'You must set an IK or FK keyframe to ensure ' \
                  'proper evaluation when saving a program; ' \
                  'no program written'
        raise Exception(warning)

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

    # Check for warnings
    if using_time_interval:
        # Confirm that the time interval is valid
        try:
            time_interval_value = float(time_interval_value)
            assert time_interval_value > 0
        except ValueError:
            if time_interval_units == 'seconds':
                warning = 'Time interval must be a float'
                raise Exception(warning)
            else:  # time_interval_units == 'frames'
                warning = 'Time interval must be a float'
                raise Exception(warning)
        except AssertionError:
            if time_interval_units == 'seconds':
                warning = 'Time interval must be greater than zero'
                raise Exception(warning)
            else:  # time_interval_units = 'frames'
                warning = 'Time interval must be greater than zero'
                raise Exception(warning)

    # Check if the robot-postproc compatibility warning was triggered
    processor = postproc_setup.POST_PROCESSORS[processor_type]()
    warning = _check_robot_postproc_compatibility(robot, processor)
    if warning != '':
        if not ignore_warnings:
            raise Exception(warning)
        else:
            warning += '\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)

    # Assign values to output dict
    postproc_settings = {
        'Using Time Interval': using_time_interval,
        'Using Keyframes Only': using_keyframes_only,
        'Time Interval Value': time_interval_value,
        'Time Interval Units': time_interval_units,
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
    :param robot:
    :param animation_settings: User-defined animation settings.
    :param animation_settings: User-defined program settings.
    :param user_options: User-defined postproc options.
    :return:
    """
    # Determine sample mode
    using_sample_rate = postproc_settings['Using Time Interval']
    using_keyframes_only = postproc_settings['Using Keyframes Only']

    # Get frames to sample
    frames = []
    if using_sample_rate:
        frames = _get_frames_using_sample_rate(animation_settings, postproc_settings)
    elif using_keyframes_only:
        frames = _get_frames_using_keyframes_only(robot, animation_settings)
    else:  # add other sampling modes here
        pass

    # Get commands from sampled frames
    command_dicts = _sample_frames(robot, frames, user_options)
    return command_dicts


def _check_command_dicts(command_dicts, robot, animation_settings, postproc_settings, user_options):
    """
    Check command dictionary for warnings.
    :param command_dicts:
    :return:
    """
    # Check to see if the user has elected to ignore warnings
    ignore_warnings = postproc_settings['Ignore Warnings']

    # Check if limits have been exceeded (i.e. velocity, acceleration)
    if user_options.Include_axes:
        command_dicts = _check_command_rotations(robot, animation_settings, command_dicts)
        warning = _check_velocity_of_axes(robot, command_dicts, animation_settings['Framerate'])
        if warning != '':
            # Print this one always
            warning += '\n'
            pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)
            if not ignore_warnings:
                raise Exception(warning)

    if user_options.Include_pose:
        # TODO: Implement velocity check for poses
        # warning = _check_velocity_of_pose(robot, command_dicts, animation_settings['Framerate'])
        # if warning != '':
        #     # Print this one always
        #     warning += '\n'
        #     pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)
        #     if not ignore_warnings:
        #         raise Exception(warning)
        pass


def _check_velocity_of_axes(robot, command_dicts, framerate):
    """
    Check a list of commands for velocity errors. Construct string to return
    printable statement of all exceeded velocities for each axis; ex. range
    [0, 1, 2, 3] will be formatted '0-3'.
    :param robot: name string of the selected robot
    :param command_dicts: A list of list of robot axes
    :param command_dicts: Maya animation framerate (fps)
    :return:
    """
    velocity_limits = mimic_utils.get_velocity_limits(robot)
    violations = {}

    count = len(command_dicts)
    previous_frame = 0
    previous_axes = []

    for command_index in range(count):
        # Get time and axes right now
        command_frame = command_dicts[command_index]['Frame']
        command_axes = command_dicts[command_index]['Axes']
        if command_index > 0:  # skip zeroth
            displacement_time = abs(command_frame - previous_frame) / framerate
            for axis_index in range(6):
                displacement = abs(command_axes[axis_index] - previous_axes[axis_index])
                velocity = displacement / displacement_time
                # Check if a limit has been violated
                if velocity > velocity_limits[axis_index]:
                    # Add axis name to violations dict
                    axis_name = 'Axis {}'.format(axis_index + 1)
                    if axis_name not in violations:
                        violations[axis_name] = []
                    # Add time to violations dict
                    violations[axis_name].append(command_frame)
        previous_frame = command_frame
        previous_axes = command_axes

    # Format a warning
    warning_params = []
    # Get axis keys in order
    axes = violations.keys()
    if axes:
        axes.sort()
        for axis_name in axes:
            # Check if the axis key has values
            times = violations[axis_name]
            time_ranges = general_utils.list_as_range_strings(times)
            time_ranges_formatted = '\n'.join('\t{}'.format(time_range) for time_range in time_ranges)
            warning_params.append(axis_name)
            warning_params.append(time_ranges_formatted)
        # Create warning
        warning = 'WARNING!\n' \
                  'Velocity limits have been violated!\n' \
                  'See the following frames:\n'
        warning_params.insert(0, warning)
        return '\n'.join(warning_params) + '\n'
    else:
        return ''


def _check_robot_postproc_compatibility(robot, processor):
    """
    Verify the compatibility of the selected robot and the processor.
    :return:
    """
    warning = ''
    robot_type = pm.getAttr('{}|robot_GRP|target_CTRL.robotType'.format(robot))
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
        axes = command_dict['Axes'] if 'Axes' in command_dict else None
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
            command_dicts[command_index]['Axes'] = reconciled_axes
    return command_dicts


def _get_frames_using_sample_rate(animation_settings, postproc_settings):
    """
    Get frames from animation using a sample rate.
    :param animation_settings:
    :return:
    """
    # Get relevant animation parameters.
    start_frame = animation_settings['Start Frame']
    # end_frame = animation_settings['End Frame']
    framerate = animation_settings['Framerate']
    animation_time_sec = animation_settings['Animation Time (sec)']
    time_interval_units = postproc_settings['Time Interval Units']
    time_interval_value = postproc_settings['Time Interval Value']
    # Convert time interval from frames to seconds if necessary
    if time_interval_units == 'seconds':
        step_sec = float(time_interval_value)
    else:  # time_interval_units == 'frames'
        step_sec = float(time_interval_value) / float(framerate)
    # Find the closest multiple of the number of steps in our animation
    num_steps = int(math.ceil(float(animation_time_sec) / step_sec) + 1)
    # Create array of time-steps in milliseconds.
    time_array_sec = [round(i * step_sec, 5) for i in range(0, num_steps)]
    # Create list of frames (time-steps).
    frames = [round(start_frame + (framerate * t_sec), 3) for t_sec in time_array_sec]
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
    ik_keyframes = pm.keyframe(
        '{}|robot_GRP|target_CTRL'.format(robot),
        attribute='ik',
        query=True,
        time='{}:{}'.format(start_frame, end_frame))
    # Verify that there is also a keyframe set on the FK controls' rotate
    # attributes. If there's not, we remove it from the list
    # Note: we only need to check on controller as they are all keyframed
    # together
    frames = [frame for frame in ik_keyframes if pm.keyframe(
        '{}|robot_GRP|FK_CTRLS|a1FK_CTRL.rotateY'.format(robot),
        query=True,
        time=frame)]
    return frames


def _sample_frames(robot, frames, user_options):
    """
    Sample robot commands using a list of frames and user options.
    :param robot:
    :param frames:
    :param user_options:
    :return:
    """
    # Initialize output array.
    command_dicts = []
    for frame in frames:
        # Set the background to the current frame
        # TODO: Implement this! This rocks:
        # pm.currentTime(frame)
        # Create a dict of datatypes per frame
        command_dict = {}
        # Add this frame number/step/index to the dictionary
        command_dict['Frame'] = frame
        # Get motion parameters
        if not user_options.Ignore_motion:
            if user_options.Include_axes:
                axes = _sample_frame_get_axes(robot, frame)
                command_dict['Axes'] = postproc.Axes(*axes)
            if user_options.Include_pose:
                pose = _sample_frame_get_pose(robot, frame)
                command_dict['Pose'] = postproc.Pose(*pose)
            if user_options.Include_external_axes:
                # external_axes = None
                # command_dict['External Axes'] = postproc.ExternalAxes(*external_axes)
                pass
            if user_options.Include_configuration:
                # configuration = None
                # command_dict['Configuration'] = postproc.Configuration(*configuration)
                pass
        # Get IO parameters
        if not user_options.Ignore_IOs:
            if user_options.Include_digital_outputs:
                # digital_output = None
                # command_dict['Digital Output'] = postproc.DigitalOutput(*digital_output)
                pass
        command_dicts.append(command_dict)
    # Reset current frame (just in case)
    pm.currentTime(frames[0])
    return command_dicts


def _sample_frame_get_axes(robot, frame):
    """
    Get robot Axes from an animation frame.
    :param robot:
    :param frame:
    :return:
    """
    axes = []
    for i in range(6):
        axis_name = '{}|robot_GRP|target_CTRL.axis{}'.format(robot, i + 1)
        axis = pm.getAttr(axis_name, time=frame)
        axes.append(axis)
    return axes


def _sample_frame_get_pose(robot_name, frame):
    """
    Get robot Pose from an animation frame.
    :param robot_name: Name of the robot
    :param frame:
    :return:
    """
    # Set the time
    # TODO: Implement this in parent function
    pm.currentTime(frame)

    tool_name = '{}|robot_GRP|tool_CTRL'.format(robot_name)
    try:  # Try to grab the named tool
        tool_object = pm.ls(tool_name)[0]  # Try to get tool, may raise an exception
    except IndexError:  # No tool attached, use flange
        tool_name = '{}|robot_GRP|robot_GEOM|Base|' \
                    'axis1|axis2|axis3|axis4|axis5|axis6|tcp_GRP|tcp_HDL'.format(robot_name)

    # Local Base Frame controller (circle control at base of the robot).
    base_name = pm.ls('{}|robot_GRP|local_CTRL'.format(robot_name))[0]

    world_matrix = '.worldMatrix'
    tool_name_world_matrix = tool_name + world_matrix
    base_name_world_matrix = base_name + world_matrix

    # Get rotation with respect to Maya's world frame
    tool_matrix = pm.getAttr(tool_name_world_matrix, time=frame)
    base_matrix = pm.getAttr(base_name_world_matrix, time=frame)
    tool_rotation = general_utils.matrix_get_3x3_from_4x4(tool_matrix)
    base_rotation = general_utils.matrix_get_3x3_from_4x4(base_matrix)

    # Get translation per Maya's world frame
    # pm.currentTime(frame)  # Must actually update the animation...
    tool_translation = pm.xform(tool_name, query=True, rp=True, ws=True)
    base_translation = pm.xform(base_name, query=True, rp=True, ws=True)

    # Get translation and rotation
    pose_translation = [tool_translation[i] - base_translation[i] for i in range(3)]
    pose_rotation = general_utils.matrix_multiply_3x3(tool_rotation, base_rotation)

    # Reorder position of parameters
    order = [2, 0, 1]  # Indices to re-order; from Maya CS to Robot CS
    reordered_translation = [pose_translation[i] * 10 for i in order]
    reordered_rotation = [[pose_rotation[i][j] for j in order] for i in order]

    # Apply rotation depending on robot type
    # TODO: Integrate this with rigs, unclear and shouldn't be hardcoded
    robot_type = mimic_utils.get_robot_type(robot_name)
    if robot_type == 'ABB':
        conversion_matrix = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
    elif robot_type == 'KUKA':
        conversion_matrix = [[0, -1, 0], [0, 0, 1], [-1, 0, 0]]
    else:
        raise Exception('Robot type not supported for Pose movement')

    # Convert parameters from Maya-space to Robot-space
    converted_rotation = general_utils.matrix_multiply_3x3(reordered_rotation, conversion_matrix)
    converted_translation = general_utils.matrix_multiply_1xm_nxm([reordered_translation], reordered_rotation)[0]

    pose = []
    pose.extend(converted_translation)
    [pose.extend(rotation) for rotation in converted_rotation]
    return pose
