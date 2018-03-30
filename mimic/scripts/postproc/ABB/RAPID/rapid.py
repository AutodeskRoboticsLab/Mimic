#!usr/bin/env python
"""
Postprocessor subclass.
"""

from collections import namedtuple

import general_utils
import rapid_config
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
MotionCommand = namedtuple(
    MOTION_COMMAND, [
        postproc.AXES,
        postproc.EXTERNAL_AXES,
        postproc.POSE,
        postproc.CONFIGURATION
    ]
)

IO_COMMAND = 'io_command'
IOCommand = namedtuple(
    IO_COMMAND, [
        postproc.DIGITAL_OUTPUT
    ]
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
            output_file_extension='prg',
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
                program_template = self._get_program_template()  # don't overwrite original
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
                program_template = self._get_program_template()  # don't overwrite original
                return program_template.format(formatted_commands)
            except IndexError:
                message = 'To use motion parameters as commands, template requires ' \
                          '1 placeholder for the motion variables.'
                raise IndexError(message)

    def _process_command(self, command, opts):
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

    def get_formatted_commands(self, params):
        """
        Get formatted commands from raw axes.
        :param params:
        :return:
        """
        commands = []
        for axes in params:
            command = MotionCommand(
                axes=postproc.Axes(*axes),
                pose=None,
                external_axes=None,
                configuration=None)
            commands.append(command)
        return commands

    def _set_supported_options(self):
        """
        Set the supported options for this processor. Only set to True if the
        optional parameter is acutally supported by this processor!
        :return:
        """
        return postproc_options.configure_user_options(
            ignore_motion=True,
            use_motion_as_variables=True,
            use_nonlinear_motion=True,
            include_axes=True
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

            target_data.extend(_convert_pose(command.pose))
            if command.configuration is not None:
                target_data.append(_convert_configuration(command.configuration))
            else:
                target_data.extend(rapid_config.DEFAULT_CONF)
            if command.external_axes is not None:
                target_data.extend(command.external_axes)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)

        else:
            raise ValueError('Invalid command')

    # Interpret nonlinear motion command
    elif opts.Use_nonlinear_motion:
        if command.axes is not None:
            motion_type = MOVE_ABS_J
            target_data_type = JOINTTARGET
            target_data.extend(command.axes)
            if command.external_axes is not None:
                target_data.extend(command.external_axes)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)

        elif command.pose is not None:
            motion_type = MOVE_J
            target_data_type = ROBTARGET

            target_data.extend(_convert_pose(command.pose))
            if command.configuration is not None:
                target_data.extend(_convert_configuration(command.configuration))
            else:
                target_data.extend(rapid_config.DEFAULT_CONF)
            if command.external_axes is not None:
                target_data.extend(command.external_axes)
            else:
                target_data.extend(rapid_config.DEFAULT_EXAX)
        else:
            raise ValueError('Invalid command')

    # Format parameters into string
    target_data = [general_utils.num_to_str(d, include_sign=False, precision=3)
                   for d in target_data]

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
    # TODO: Calculate c1, c2, c3, c4 using configuration!
    c1 = configuration.configuration_1
    c2 = configuration.configuration_2
    c3 = configuration.configuration_3
    c4 = 0
    return [c1, c2, c3, c4]

# TODO: Consider the following structures instead:
# POS = 'POS'
# __pos_structure = namedtuple(
#     POS, [
#         __x,
#         __y,
#         __z
#     ]
# )
#
# ORIENT = 'ORIENT'
# __orient_structure = namedtuple(
#     ORIENT, [
#         __q1,
#         __q2,
#         __q3,
#         __q4
#     ]
# )
#
# CONFDATA = 'CONFDATA'
# __confdata_structure = namedtuple(
#     CONFDATA, [
#         __c1,
#         __c2,
#         __c3,
#         __c4
#     ]
# )
#
# ROBJOINT = 'ROBJOINT'
# __robjoint_structure = namedtuple(
#     ROBJOINT, [
#         __a1,
#         __a2,
#         __a3,
#         __a4,
#         __a5,
#         __a6,
#     ]
# )
#
# EXTJOINT = 'EXTJOINT'
# __extjoint_structure = namedtuple(
#     EXTJOINT, [
#         __e1,
#         __e2,
#         __e3,
#         __e4,
#         __e5,
#         __e6
#     ]
# )
#
# # DATA STRUCTURES
# JOINTTARGET = 'JOINTTARGET'
# __jointtarget_structure = namedtuple(
#     JOINTTARGET, [
#         ROBJOINT,
#         EXTJOINT
#     ]
# )
#
# ROBTARGET = 'ROBTARGET'
# __robtarget_structure = namedtuple(
#     ROBTARGET, [
#         POS,
#         ORIENT,
#         CONFDATA,
#         EXTJOINT
#     ]
# )
#
# MOVE_L = 'MoveL'
# __move_l_structure = namedtuple(
#     MOVE_L, [
#         __params
#     ]
# )
#
# MOVE_J = 'MoveJ'
# __move_j_structure = namedtuple(
#     MOVE_J, [
#         __params
#     ]
# )
#
# MOVE_ABS_J = 'MoveAbsJ'
# __move_abs_j_structure = namedtuple(
#     MOVE_ABS_J, [
#         __params
#     ]
# )
