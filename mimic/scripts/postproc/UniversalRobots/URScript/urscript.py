#!usr/bin/env python
"""
Postprocessor subclass.
"""

import math
from collections import namedtuple

import general_utils
from . import urscript_config
from postproc import postproc
from postproc import postproc_options
from robotmath import transforms

# PARAMS
__a1 = 'A1'
__a2 = 'A2'
__a3 = 'A3'
__a4 = 'A4'
__a5 = 'A5'
__a6 = 'A6'
__x = 'X'
__y = 'Y'
__z = 'Z'
__a = 'A'
__b = 'B'
__c = 'C'
__identifier = 'identifier'
__value = 'value'
__move_target = 'target'
__move_speed = 'speed'
__move_acceleration = 'acceleration'
__move_blend_radius = 'blend_radius'

# STRUCTURES
AXIS = 'AXIS'
__axis_structure = namedtuple(
    AXIS, [
        __a1,
        __a2,
        __a3,
        __a4,
        __a5,
        __a6
    ]
)

POSE = 'POSE'
__pose_structure = namedtuple(
    POSE, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c
    ]
)

DIGITAL_OUT = 'set_standard_digital_out'
__set_standard_digital_out_structure = namedtuple(
    DIGITAL_OUT, [
        __identifier,
        __value
    ]
)

MOVE_L = 'movel'
__movel_structure = namedtuple(
    MOVE_L, [
        __move_target,
        __move_acceleration,
        __move_speed,
        __move_blend_radius
    ]
)

MOVE_J = 'movej'
__movej_structure = namedtuple(
    MOVE_J, [
        __move_target,
        __move_acceleration,
        __move_speed,
        __move_blend_radius
    ]
)

STRUCTURES = {
    AXIS: __axis_structure,
    POSE: __pose_structure,
    MOVE_J: __movej_structure,
    MOVE_L: __movel_structure,
    DIGITAL_OUT: __set_standard_digital_out_structure
}

# TEMPLATES
__axis_template = \
    '[{},{},{},{},{},{}]'

__pose_template = \
    'p[{},{},{},{},{},{}]'

__movej_template = \
    'movej({}, {}, {}, 0, {})'

__movel_template = \
    'movel({}, {}, {}, 0, {})'

__set_standard_digital_out_template = \
    'set_standard_digital_out({}, {})'

TEMPLATES = {
    AXIS: __axis_template,
    POSE: __pose_template,
    MOVE_J: __movej_template,
    MOVE_L: __movel_template,
    DIGITAL_OUT: __set_standard_digital_out_template
}

# COMMANDS
MOTION_COMMAND = 'motion_command'
_motion_command_fields = [
    postproc.AXES,
    postproc.EXTERNAL_AXES,
    postproc.POSE,
    postproc.CONFIGURATION
]
MotionCommand = namedtuple(
    MOTION_COMMAND, _motion_command_fields
)

IO_COMMAND = 'io_command'
_io_command_fields = [
    postproc.DIGITAL_OUTPUT,
    postproc.ANALOG_OUTPUT
]
IOCommand = namedtuple(
    IO_COMMAND, _io_command_fields
)


class SimpleURScriptProcessor(postproc.PostProcessor):
    """
    Postprocessor subclass.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleURScriptProcessor, self).__init__(
            type_robot='Universal Robots',
            type_processor='URScript',
            program_file_extension=urscript_config.DEFAULT_FILE_EXTENSION,
            def_program_template=urscript_config.DEFAULT_PROGRAM)

        # Initialize internal parameters
        self.supported_options = self._set_supported_options()

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        formatted_commands = '\n'.join(processed_commands)
        try:
            program_template = self._read_program_template()  # don't overwrite original
            return program_template.format(formatted_commands)
        except IndexError:
            message = 'To use motion parameters as commands, template requires ' \
                        '1 placeholder for the motion variables.'
            raise IndexError(message)

    @staticmethod
    def _process_command(command, opts):
        """
        Process a single command with user options.
        :param command: Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        command_type = postproc.get_structure_type(command)
        if not opts.Ignore_motion and command_type == MOTION_COMMAND:
            return _process_motion_command(command, opts)
        elif not opts.Ignore_IOs and command_type == IO_COMMAND:
            return _process_io_command(command, opts)

    @staticmethod
    def _format_command(params_dict):
        """
        Processor-specific function. Certain types of commands are very specific
        to the processor in use or application, such as EntertainTech, requiring
        in some cases both Motion and IO datatypes in a single line of code. This
        function allows PostProcessor (processor) subclasses to format the input
        params flexibly and as needed.

        For this processor:
        Can create a MotionCommand namedTuple from optional input parameters.
        Can create a IOCommand namedTuple from optional input parameters.
        Returns a list of commands to allow possibly mutliple commands on separate
        lines to be exported per frame.

        :param params_dict: Dictionary of namedtuple containing all command
        parameters (i.e. Axes, ExternalAxes, etc).
        :return:
        """
        
        commands = []

        # Try to get a MotionCommand
        params = []
        for field in _motion_command_fields:
            param = params_dict[field] if field in params_dict else None
            params.append(param)
        if params.count(None) != len(params):
            commands.append(MotionCommand(*params))
        
        # Try to get an IO command
        params = []
        for field in _io_command_fields:
            param = params_dict[field] if field in params_dict else None
            params.append(param)
        if params.count(None) != len(params):
            commands.append(IOCommand(*params))
        
        return commands

    @staticmethod
    def _set_supported_options():
        """
        Set the supported options for this processor. Only set to True if the
        optional parameter is actually supported by this processor!
        :return:
        """
        return postproc_options.configure_user_options(
            ignore_motion=True,
            ignore_ios=True,
            use_nonlinear_motion=True,
            use_linear_motion=True,
            use_continuous_motion=True,
            include_axes=True,
            include_pose=True,
            include_digital_outputs=True
        )

def _process_motion_command(command, opts):
    """
    Process motion command.
    :param command: Command tuple
    :param opts: UserOptions tuple
    :return:
    """
    motion_type = None
    target_data_type = None
    target_data = []
    target_speed = 0
    target_acceleration = 0

    # Interpret linear motion command
    if opts.Use_linear_motion:
        if command.pose is not None:
            motion_type = MOVE_L
            target_data_type = POSE
            target_speed = urscript_config.DEFAULT_CARTESIAN_SPEED
            target_acceleration = urscript_config.DEFAULT_CARTESIAN_ACCELERATION
            pose = _convert_pose(command.pose)
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in pose]
            target_data.extend(params)
        else:
            raise ValueError('Invalid command')

    # Interpret nonlinear motion command
    elif opts.Use_nonlinear_motion:
        if command.axes is not None:
            motion_type = MOVE_J
            target_data_type = AXIS
            target_speed = urscript_config.DEFAULT_JOINT_SPEED
            target_acceleration = urscript_config.DEFAULT_JOINT_ACCELERATION
            axes = command.axes
            params = [general_utils.num_to_str(math.radians(p), include_sign=False, precision=3)
                      for p in axes]
            target_data.extend(params)
        else:
            raise ValueError('Invalid command')

    else:  # User never supplied a motion type
        raise ValueError('Invalid motion type')

    # Structure and format data, command
    formatted_target_data = postproc.fill_template(
        target_data,
        STRUCTURES[target_data_type],
        TEMPLATES[target_data_type])

    blend_radius = 0
    if opts.Use_continuous_motion:
        blend_radius = urscript_config.DEFAULT_BLEND # blend radius 1cm
    
    motion_data = [
        formatted_target_data,
        target_speed,
        target_acceleration,
        blend_radius
    ]

    formatted_motion = postproc.fill_template(
        motion_data,
        STRUCTURES[motion_type],
        TEMPLATES[motion_type])
    
    return formatted_motion


def _process_io_command(command, opts):
    """
    Process io command.
    :param command: Command tuple
    :param opts: UserOptions tuple
    :return:
    """
    io_data = []  # empty data container

    # Interpret digital output command
    if opts.Include_digital_outputs:
        print("doing IO")
        if command.digital_output is not None:
            print("IO not None")
            io_type = DIGITAL_OUT
            for io in command.digital_output:
                formatted_io = postproc.fill_template(
                    [
                        io[0],
                        True if io[1] else False
                    ],
                    STRUCTURES[io_type],
                    TEMPLATES[io_type])
                io_data.append(formatted_io)

    if io_data:
        formatted_ios = '\n'.join(io_data)
        return formatted_ios


def _convert_pose(pose):
    """
    Convert a Pose tuple to subclass conventions.
    :param pose: Pose tuple
    :return:
    """
    i_vector = [pose.pose_ix, pose.pose_iy, pose.pose_iz]
    j_vector = [pose.pose_jx, pose.pose_jy, pose.pose_jz]
    k_vector = [pose.pose_kx, pose.pose_ky, pose.pose_kz]
    m = [i_vector, j_vector, k_vector]
    a, b, c = transforms.euler_angles_by_matrix(m)
    # convert mm to mm and degrees to radians
    return [pose.pose_x/1000, pose.pose_y/1000, pose.pose_z/1000, math.radians(a), math.radians(b), math.radians(c)]