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
import mimic_external_axes


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
    _process_program(command_dicts, *program_settings)


def _process_program(command_dicts, robot, animation_settings, postproc_settings, user_options):
    """
    Process a command dictionary as a program using the selected post processor.
    :param robot: Name of the robot
    :param animation_settings: User-defined animation settings.
    :param animation_settings: User-defined program settings.
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
    :param robot: Name of the robot
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
    command_dicts = _sample_frames_get_command_dicts(robot, frames, animation_settings, user_options)
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

    if user_options.Include_external_axes:
        # TODO: Implement velocity check for external axes
        # warning = _check_velocity_of_external_axes(robot, command_dicts, animation_settings['Framerate'])
        # if warning != '':
        #     # Print this one always
        #     warning += '\n'
        #     pm.scrollField(OUTPUT_WINDOW_NAME, insertText=warning, edit=True)
        #     if not ignore_warnings:
        #         raise Exception(warning)
        pass

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
    :param framerate: Maya animation framerate (fps)
    :return:
    """
    frames = [c['Frame'] for c in command_dicts]
    axes_at_each_frame = [c[postproc.AXES] for c in command_dicts]
    velocity_limits = mimic_utils.get_velocity_limits(robot)

    violations = {}
    _previous_frame = 0
    _previous_axes = []
    for i in range(len(axes_at_each_frame)):
        # Get time and axes right now
        _current_frame = frames[i]
        _current_axes = axes_at_each_frame[i]
        if i > 0:  # skip zeroth
            displacement_time = abs(_current_frame - _previous_frame) / framerate
            for j in range(len(_current_axes)):
                _previous_axis = _previous_axes[j]
                _current_axis = _current_axes[j]
                displacement = abs(_current_axis - _previous_axis)
                velocity = displacement / displacement_time
                # Check if a limit has been violated
                if velocity > velocity_limits[j]:
                    # Add axis name to violations dict
                    axis_name = 'Axis {}'.format(j + 1)
                    if axis_name not in violations:
                        violations[axis_name] = []
                    # Add time to violations dict
                    violations[axis_name].append(_current_frame)
        _previous_frame = _current_frame
        _previous_axes = _current_axes

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


def _sample_frames_get_command_dicts(robot_name, frames, animation_settings, user_options):
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
    for frame in frames:
        # Set the background to the current frame
        # TODO: Implement this! This rocks:
        # pm.currentTime(frame)
        # Create a dict of datatypes per frame
        command_dict = {}
        # Add this frame number/step/index to the dictionary
        command_dict['Frame'] = frame
        command_dict['Framerate'] = animation_settings['Framerate']
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
                pass
            if user_options.Include_configuration:
                # TODO: Implement configurations
                # configuration = None
                # command_dict[postproc.CONFIGURATION] = postproc.Configuration(*configuration)
                pass
        # Get IO parameters
        if not user_options.Ignore_IOs:
            if user_options.Include_digital_outputs:
                # TODO: Implement digital outputs
                # digital_output = None
                # command_dict[postproc.DIGITAL_OUTPUT] = postproc.DigitalOutput(*digital_output)
                pass
            if user_options.Include_digital_inputs:
                # TODO: Implement digital inputs
                # digital_input = None
                # command_dict[postproc.DIGITAL_INPUT'] = postproc.DigitalOutput(*digital_input)
                pass
            if user_options.Include_analog_outputs:
                # TODO: Implement analog outputs
                # analog_output = None
                # command_dict[postproc.ANALOG_OUTPUT] = postproc.DigitalOutput(*analog_output)
                pass
            if user_options.Include_analog_inputs:
                # TODO: Implement analog inputs
                # analog_input = None
                # command_dict[postproc.ANALOG_INPUT] = postproc.DigitalOutput(*analog_input)
                pass
        command_dicts.append(command_dict)
    # Reset current frame (just in case)
    pm.currentTime(frames[0])
    return command_dicts


def _sample_frame_get_axes(robot_name, frame):
    """
    Get robot Axes from an animation frame.
    :param robot_name: Name of the robot
    :param frame: Frame to sample
    :return:
    """
    axes = []
    for i in range(6):
        axis_name = '{}|robot_GRP|target_CTRL.axis{}'.format(robot_name, i + 1)
        axis = pm.getAttr(axis_name, time=frame)
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

    tool_name = '{}|robot_GRP|tool_CTRL'.format(robot_name)
    try:  # Try to grab the named tool
        tool_object = pm.ls(tool_name)[0]  # Try to get tool, may raise an exception
    except IndexError:  # No tool attached, use flange
        tool_name = '{}|robot_GRP|robot_GEOM|Base|' \
                    'axis1|axis2|axis3|axis4|axis5|axis6|tcp_GRP|tcp_HDL'.format(robot_name)

    # Local Base Frame controller (circle control at base of the robot).
    base_name = pm.ls('{}|robot_GRP|local_CTRL'.format(robot_name))[0]

    # Get name of the tcp and base
    world_matrix = '.worldMatrix'
    tcp_name_world_matrix = tool_name + world_matrix
    base_name_world_matrix = base_name + world_matrix

    # TRANSLATIONS

    # Get translation with respect to Maya's world frame
    tcp_translation = pm.xform(tool_name, query=True, rp=True, ws=True)
    base_translation = pm.xform(base_name, query=True, rp=True, ws=True)
    general_utils.matrix_print([tcp_translation], 'tcp_translation')
    general_utils.matrix_print([base_translation], 'base_translation')

    # Translate the TCP, reset the base
    tcp_translation = [tcp_translation[i] - base_translation[i] for i in range(3)]

    # Create zero translation (origin) to serve as temporary base for rotations
    zero_translation = [0 for _ in range(3)]

    # ROTATIONS

    # Get TCP rotation with respect to Maya's world frame
    _tcp_matrix = pm.getAttr(tcp_name_world_matrix, time=frame)
    tcp_rotation = general_utils.matrix_get_rotations(_tcp_matrix)
    general_utils.matrix_print(tcp_rotation, 'tcp_rotation')

    # Get Base rotation with respect to Maya's world frame
    _base_matrix = pm.getAttr(base_name_world_matrix, time=frame)
    base_rotation = general_utils.matrix_get_rotations(_base_matrix)
    general_utils.matrix_print(base_rotation, 'base_rotation')

    # Invert the base rotation matrix
    base_rotation_inverse = general_utils.matrix_get_inverse(base_rotation)
    general_utils.matrix_print(base_rotation_inverse, 'base_rotation_inverse')

    # TRANSFORMATIONS

    # Compose 4x4 matrices using the rotation and translation from the above
    tcp_matrix_4x4 = general_utils.matrix_compose_4x4(tcp_rotation, tcp_translation)
    base_matrix_4x4 = general_utils.matrix_compose_4x4(base_rotation_inverse, zero_translation)
    general_utils.matrix_print(tcp_matrix_4x4, 'tcp_matrix_4x4')
    general_utils.matrix_print(base_matrix_4x4, 'base_matrix_4x4')

    # Get pose itself
    initial_pose_matrix = general_utils.matrix_multiply(base_matrix_4x4, tcp_matrix_4x4)
    general_utils.matrix_print(initial_pose_matrix, 'initial_pose_matrix')

    # CONVERSIONS

    # Decompose the initial pose matrix
    initial_translation = general_utils.matrix_get_translation(initial_pose_matrix)
    initial_rotations = general_utils.matrix_get_rotations(initial_pose_matrix)

    # Translate the TCP
    initial_translation = [initial_translation[i] + base_translation[i] for i in range(3)]

    # Rearrange from Maya CS (mcs) to Robot CS (rcs)
    indices = [2, 0, 1]
    new_translation = [initial_translation[i] * 10 for i in indices]  # cm to mm
    new_rotation = [[initial_rotations[i][j] for i in indices] for j in indices]

    # Define rotation matrix and convert the rotations based robot type
    # TODO: Integrate this with rigs, unclear and shouldn't be hardcoded
    robot_type = mimic_utils.get_robot_type(robot_name)
    if robot_type == 'ABB':
        conversion_matrix = [
            [0, 0, -1],
            [0, 1, 0],
            [1, 0, 0]
        ]
    elif robot_type == 'KUKA':
        conversion_matrix = [
            [0, -1, 0],
            [0, 0, 1],
            [-1, 0, 0]
        ]
    else:
        raise Exception('Robot type not supported for Pose movement')

    # Perform the conversion operation itself
    converted_rotation = general_utils.matrix_multiply(conversion_matrix, new_rotation)
    general_utils.matrix_print(converted_rotation, 'converted_rotation')

    # Compose pose
    pose_matrix = general_utils.matrix_compose_4x4(converted_rotation, new_translation)
    general_utils.matrix_print(pose_matrix, 'pose_matrix')

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
