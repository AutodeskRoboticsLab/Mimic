#!usr/bin/env python
"""
Postprocessor subclass.
"""

from collections import namedtuple

import general_utils
from . import rapid_config
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
__e1 = 'E1'
__e2 = 'E2'
__e3 = 'E3'
__e4 = 'E4'
__e5 = 'E5'
__e6 = 'E6'
__x = 'X'
__y = 'Y'
__z = 'Z'
__q1 = 'Q1'
__q2 = 'Q2'
__q3 = 'Q3'
__q4 = 'Q4'
__c1 = 'C1'
__c2 = 'C2'
__c3 = 'C3'
__c4 = 'C4'
__params = 'params'
__identifier = 'identifier'
__value = 'value'
__move_type = 'type'
__move_target = 'target'
__move_speed = 'speed'
__move_zone = 'zone'
__move_tool = 'tool'
__move_wobj = 'wobj'

# STRUCTURES
MOVE = 'MOVE'
MOVE_L = 'MoveL'
MOVE_J = 'MoveJ'
MOVE_ABS_J = 'MoveAbsJ'
__move_structure = namedtuple(
    MOVE, [
        __move_type,
        __move_target,
        __move_speed,
        __move_zone,
        __move_tool,
        __move_wobj
    ]
)

VARIABLE = 'VARIABLE'
__variable_structure = namedtuple(
    VARIABLE, [
        __params
    ]
)

JOINTTARGET = 'JOINTTARGET'
__jointtarget_structure = namedtuple(
    JOINTTARGET, [
        __a1,
        __a2,
        __a3,
        __a4,
        __a5,
        __a6,
        __e1,
        __e2,
        __e3,
        __e4,
        __e5,
        __e6
    ]
)

ROBTARGET = 'ROBTARGET'
__robtarget_structure = namedtuple(
    ROBTARGET, [
        __x,
        __y,
        __z,
        __q1,
        __q2,
        __q3,
        __q4,
        __c1,
        __c2,
        __c3,
        __c4,
        __e1,
        __e2,
        __e3,
        __e4,
        __e5,
        __e6
    ]
)

DIGITAL_OUT = 'DO'
__digital_out_structure = namedtuple(
    DIGITAL_OUT, [
        __identifier,
        __value
    ]
)

STRUCTURES = {
    JOINTTARGET: __jointtarget_structure,
    ROBTARGET: __robtarget_structure,
    DIGITAL_OUT: __digital_out_structure,
    MOVE: __move_structure,
    VARIABLE: __variable_structure
}

# TEMPLATES
__jointtarget_template = \
    '[' \
    '[{}, {}, {}, {}, {}, {}], ' \
    '[{}, {}, {}, {}, {}, {}]' \
    ']'

__robtarget_template = \
    '[' \
    '[{}, {}, {}], ' \
    '[{}, {}, {}, {}], ' \
    '[{}, {}, {}, {}], ' \
    '[{}, {}, {}, {}, {}, {}]' \
    ']'

__digital_out_template = \
    '\t\tSetDO {}, {};'

__variable_template = \
    '\t\t{}'

__move_template = \
    '\t\t{} {}, {}, {}, {}\\WObj:={};'

TEMPLATES = {
    JOINTTARGET: __jointtarget_template,
    ROBTARGET: __robtarget_template,
    DIGITAL_OUT: __digital_out_template,
    MOVE: __move_template,
    VARIABLE: __variable_template
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


class SimpleRAPIDProcessor(postproc.PostProcessor):
    """
    Postprocessor subclass.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleRAPIDProcessor, self).__init__(
            type_robot='ABB',
            type_processor='RAPID',
            program_file_extension=rapid_config.DEFAULT_FILE_EXTENSION,
            def_program_template=rapid_config.DEFAULT_PROGRAM)

        # Initialize internal parameters
        self.supported_options = self._set_supported_options()

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :param opts: UserOptions tuple
        :return:
        """
        # Get program structure and template
        if opts.Use_motion_as_variables:
            formatted_commands = ',\n'.join(processed_commands)
            count = len(processed_commands)
            try:
                program_template = self._read_program_template()  # don't overwrite original
                if program_template.count('{}') != 2:
                    raise IndexError
                return program_template.format(count, formatted_commands)
            except IndexError:
                message = 'To use motion parameters as variables, template requires ' \
                          '2 placeholders, one for number of motion variables and ' \
                          'another for the motion variables.'
                raise IndexError(message)
        else:
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
        # TODO: implement include_pose and use_linear_motion
        return postproc_options.configure_user_options(
            ignore_motion=True,
            use_motion_as_variables=True,
            use_nonlinear_motion=True,
            use_linear_motion=True,
            include_axes=True,
            include_external_axes=True,
            include_pose=True,
            include_configuration=True
        )


def _process_motion_command(command, opts):  # Implement in base class!
    """
    Process motion command.
    :param command: Command tuple
    :param opts: UserOptions tuple
    :return:
    """
    motion_type = None
    target_data_type = None
    target_data = []

    # Interpret linear motion command
    if opts.Use_linear_motion:
        if command.pose is not None:
            motion_type = MOVE_L
            target_data_type = ROBTARGET
            pose = _convert_pose(command.pose)
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in pose]
            target_data.extend(params)
            if command.configuration is not None:
                configuration = _convert_configuration(command.configuration)
                params = [general_utils.num_to_str(p, include_sign=False, precision=3, simplify_ints=True)
                          for p in configuration]
                target_data.extend(params)
            else:
                target_data.extend(rapid_config.DEFAULT_CONF)
            if command.external_axes is not None:
                external_axes = [axis if axis is not None else '9E9'
                                 for axis in command.external_axes]
                external_axes = external_axes[:6]
                params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                          for p in external_axes]
                target_data.extend(params)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)

        else:
            raise ValueError('Invalid command')

    # Interpret nonlinear motion command
    elif opts.Use_nonlinear_motion:
        if command.axes is not None:
            motion_type = MOVE_ABS_J
            target_data_type = JOINTTARGET
            axes = command.axes
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in axes]
            target_data.extend(params)
            if command.external_axes is not None:
                external_axes = [axis if axis is not None else '9E9'
                                 for axis in command.external_axes]
                external_axes = external_axes[:6]
                params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                          for p in external_axes]
                target_data.extend(params)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)

        elif command.pose is not None:
            motion_type = MOVE_J
            target_data_type = ROBTARGET

            pose = _convert_pose(command.pose)
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in pose]
            target_data.extend(params)
            if command.configuration is not None:
                configuration = _convert_configuration(command.configuration)
                params = [general_utils.num_to_str(p, include_sign=False, precision=3, simplify_ints=True)
                          for p in configuration]
                target_data.extend(params)
            else:
                target_data.extend(rapid_config.DEFAULT_CONF)
            if command.external_axes is not None:
                external_axes = [axis if axis is not None else '9E9'
                                 for axis in command.external_axes]
                external_axes = external_axes[:6]
                params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                          for p in external_axes]
                target_data.extend(params)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)
        else:
            raise ValueError('Invalid command')

    else:  # User never supplied a motion type
        raise ValueError('Invalid motion type')

    # Structure and format data, command
    formatted_target_data = postproc.fill_template(
        target_data,
        STRUCTURES[target_data_type],
        TEMPLATES[target_data_type])

    if opts.Use_motion_as_variables:
        formatted_variable = postproc.fill_template(
            formatted_target_data,
            STRUCTURES[VARIABLE],
            TEMPLATES[VARIABLE])
        return formatted_variable
    else:
        motion_data = [
            motion_type,
            formatted_target_data,
            rapid_config.DEFAULT_SPEED,
            rapid_config.DEFAULT_ZONE,
            rapid_config.DEFAULT_TOOL,
            rapid_config.DEFAULT_WOBJ]

        formatted_motion = postproc.fill_template(
            motion_data,
            STRUCTURES[MOVE],
            TEMPLATES[MOVE])
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
    if opts.Include_digital_output:
        if command.digital_output is not None:
            io_type = DIGITAL_OUT
            for io in command.digital_output:
                formatted_io = postproc.fill_template(
                    io,
                    STRUCTURES[io_type],
                    TEMPLATES[io_type])
                io_data.append(formatted_io)
        # if command.analog_outputs is not None:
        #     io_type = ANALOG_OUT
        #     for io in command.analog_outputs:
        #         formatted_io = postproc.fill_template(
        #             io,
        #             STRUCTURES[io_type],
        #             TEMPLATES[io_type])
        #         io_data.append(formatted_io)

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
    q1, q2, q3, q4 = transforms.quaternion_by_vectors(i_vector, j_vector, k_vector)
    return [pose.pose_x, pose.pose_y, pose.pose_z, q1, q2, q3, q4]


def _convert_configuration(configuration):
    """
    Convert a Configuration tuple to subclass conventions.
    :param configuration: Configuration tuple
    :return:
    """
    # TODO: This might not be correct!
    c1 = not configuration.configuration_1
    c2 = not configuration.configuration_2
    c3 = not configuration.configuration_3
    c4 = 0  # unused
    return [c1, c2, c3, c4]
