#!usr/bin/env python
"""
Postprocessor subclass.
"""

from collections import namedtuple

import general_utils
import krl_config
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
__a = 'A'
__b = 'B'
__c = 'C'
__s = 'S'
__t = 'T'
__params = 'params'
__identifier = 'identifier'
__value = 'value'

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

E6AXIS = 'E6AXIS'
__e6axis_structure = namedtuple(
    E6AXIS, [
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

FRAME = 'FRAME'
__frame_structure = namedtuple(
    FRAME, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c
    ]
)

POS = 'POS'
__pos_structure = namedtuple(
    POS, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c,
        __s,
        __t
    ]
)

E6POS = 'E6POS'
__e6pos_structure = namedtuple(
    E6POS, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c,
        __s,
        __t,
        __e1,
        __e2,
        __e3,
        __e4,
        __e5,
        __e6
    ]
)

BINARY_OUT = 'OUT'
__out_structure = namedtuple(
    BINARY_OUT, [
        __identifier,
        __value
    ]
)

MOVE_LIN = 'LIN'
__lin_structure = namedtuple(
    MOVE_LIN, [
        __params
    ]
)

MOVE_PTP = 'PTP'
__ptp_structure = namedtuple(
    MOVE_PTP, [
        __params
    ]
)

STRUCTURES = {
    AXIS: __axis_structure,
    E6AXIS: __e6axis_structure,
    FRAME: __frame_structure,
    POS: __pos_structure,
    E6POS: __e6pos_structure,
    MOVE_LIN: __lin_structure,
    MOVE_PTP: __ptp_structure,
    BINARY_OUT: __out_structure
}

# TEMPLATES
__axis_template = \
    '{{' \
    'A1 {}, A2 {}, A3 {}, A4 {}, A5 {}, A6 {}' \
    '}}'

__e6axis_template = \
    '{{' \
    'A1 {}, A2 {}, A3 {}, A4 {}, A5 {}, A6 {}, ' \
    'E1 {}, E2 {}, E3 {}, E4 {}, E5 {}, E6 {}' \
    '}}'

__frame_template = \
    '{{' \
    'X {}, Y {}, Z {}, A {}, B {}, C {}' \
    '}}'

__pos_template = \
    '{{' \
    'X {}, Y {}, Z {}, A {}, B {}, C {}, ' \
    'INT S {}, T {}' \
    '}}'

__e6pos_template = \
    '{{' \
    'X {}, Y {}, Z {}, A {}, B {}, C {}, ' \
    'E1 {}, E2 {}, E3 {}, E4 {}, E5 {}, E6 {}, ' \
    'INT S {}, T {}' \
    '}}'

__ptp_template = \
    '  PTP {}'

__lin_template = \
    '  LIN {}'

__out_template = \
    '  $OUT[{}] = {}'

TEMPLATES = {
    AXIS: __axis_template,
    E6AXIS: __e6axis_template,
    FRAME: __frame_template,
    POS: __pos_template,
    E6POS: __e6pos_template,
    MOVE_LIN: __lin_template,
    MOVE_PTP: __ptp_template,
    BINARY_OUT: __out_template
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


class SimpleKRLProcessor(postproc.PostProcessor):
    """
    Postprocessor subclass.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleKRLProcessor, self).__init__(
            type_robot='KUKA',
            type_processor='KRL',
            output_file_extension='src',
            def_program_template=krl_config.DEFAULT_PROGRAM)

        # Initialize internal parameters
        self.supported_options = self._set_supported_options()

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        # Get program structure and template
        program_template = self._get_program_template()  # don't overwrite original
        formatted_commands = '\n'.join(processed_commands)
        return program_template.format(formatted_commands)

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
    motion_data_type = None
    motion_data = []  # empty data container

    # Interpret linear motion command
    if opts.Use_linear_motion:
        motion_type = MOVE_LIN
        if command.pose is not None:
            motion_data.extend(_convert_pose(command.pose))
            if command.configuration is not None:
                if command.external_axes is not None:
                    motion_data_type = E6POS
                    motion_data.extend(command.external_axes)
                else:
                    motion_data_type = POS
                motion_data.extend(_convert_configuration(command.configuration))
            else:
                motion_data_type = FRAME
        else:
            raise ValueError('Invalid command')

    # Interpret nonlinear motion command
    elif opts.Use_nonlinear_motion:
        motion_type = MOVE_PTP
        if command.axes is not None:
            motion_data.extend(command.axes)
            if command.external_axes is not None:
                motion_data_type = E6AXIS
                motion_data.extend(command.external_axes)
            else:
                motion_data_type = AXIS
        elif command.pose is not None:
            motion_data_type = FRAME
            motion_data.extend(_convert_pose(command.pose))
        else:
            raise ValueError('Invalid command')
    else:
        raise ValueError('Invalid command')

    # Format parameters into string
    motion_data = [general_utils.num_to_str(d, include_sign=False, precision=3)
                   for d in motion_data]

    # Structure and format data, command
    formatted_motion_data = postproc.fill_template(
        motion_data,
        STRUCTURES[motion_data_type],
        TEMPLATES[motion_data_type])
    formatted_motion = postproc.fill_template(
        formatted_motion_data,
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
    if opts.Include_digital_output:
        if command.digital_output is not None:
            io_type = BINARY_OUT
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
    a, b, c = transforms.euler_rpw_by_vectors(i_vector, j_vector, k_vector)
    return [pose.pose_x, pose.pose_y, pose.pose_z, a, b, c]


def _convert_configuration(configuration):
    """
    Convert a Configuration tuple to subclass conventions.
    :param configuration: Configuration tuple
    :return:
    """
    # TODO: Calculate S, T using configuration!
    s = configuration.configuration_1
    t = configuration.configuration_2
    return [s, t]
