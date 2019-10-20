#!usr/bin/env python
"""
Postprocessor subclass.
"""

from collections import namedtuple

import general_utils
import val3_config
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

MOVE_CPTP = 'CPTP'
__cptp_structure = namedtuple(
    MOVE_CPTP, [
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
    MOVE_CPTP: __cptp_structure,
    BINARY_OUT: __out_structure
}

# TEMPLATES
__axis_template = \
    '{},{},{},{},{},{}' \

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
    '  call MoveJoint({})'

__cptp_template = \
    '  PTP {} C_PTP'

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
    MOVE_CPTP: __cptp_template,
    BINARY_OUT: __out_template
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


class SimpleVAL3Processor(postproc.PostProcessor):
    """
    Postprocessor subclass.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleVAL3Processor, self).__init__(
            type_robot='Staubli',
            type_processor='VAL3',
            program_file_extension=val3_config.DEFAULT_FILE_EXTENSION,
            def_program_template=val3_config.DEFAULT_PROGRAM)

        # Initialize internal parameters
        self.supported_options = self._set_supported_options()

    def _process_program(self, processed_commands, opts):
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        if opts.Use_continuous_motion:
            initial_position = processed_commands[0].replace(' C_PTP', '')
            formatted_commands = '\n'.join(processed_commands)
            try:
                program_template = self._read_program_template()  # don't overwrite original
                if program_template.count('{}') != 2:
                    raise IndexError
                return program_template.format(initial_position, formatted_commands)
            except IndexError:
                message = 'To use continuous motion in VAL3, template requires ' \
                          '2 placeholders, one for the initial start position and ' \
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

        :param params_dict: Dictionary of namedtuple containing all command
        parameters (i.e. Axes, ExternalAxes, etc).
        :return:
        """
        # Try to get a MotionCommand
        params = []
        for field in _motion_command_fields:
            param = params_dict[field] if field in params_dict else None
            params.append(param)
        if params.count(None) != len(params):
            return MotionCommand(*params)
        else:
            # Try to get an IO command
            params = []
            for field in _io_command_fields:
                param = params_dict[field] if field in params_dict else None
                params.append(param)
            if params.count(None) != len(params):
                return IOCommand(*params)

    @staticmethod
    def _set_supported_options():
        """
        Set the supported options for this processor. Only set to True if the
        optional parameter is actually supported by this processor!
        :return:
        """
        return postproc_options.configure_user_options(
            ignore_motion=True,
            use_nonlinear_motion=True,
            use_linear_motion=False,
            use_continuous_motion=True,
            include_axes=True,
            include_external_axes=False,
            include_pose=False
        )


def _process_motion_command(command, opts):
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
                    external_axes = [axis if axis is not None else 0 for axis in command.external_axes]
                    motion_data.extend(external_axes)
                else:
                    motion_data_type = POS
                motion_data.extend(_convert_configuration(command.configuration))
            else:
                motion_data_type = FRAME
        else:
            raise ValueError('Invalid command')

    # Interpret nonlinear motion command
    elif opts.Use_nonlinear_motion:
        if opts.Use_continuous_motion:
            motion_type = MOVE_CPTP
        else:
            motion_type = MOVE_PTP
        if command.axes is not None:
            motion_data.extend(command.axes)
            if command.external_axes is not None:
                motion_data_type = E6AXIS
                external_axes = [axis if axis is not None else 0 for axis in command.external_axes]
                motion_data.extend(external_axes)
            else:
                motion_data_type = AXIS
        elif command.pose is not None:
            motion_data_type = FRAME
            motion_data.extend(_convert_pose(command.pose))
        else:
            raise ValueError('Invalid command')

    else:  # User never supplied a motion type
        raise ValueError('Invalid motion type')

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
    m = [i_vector, j_vector, k_vector]
    a, b, c = transforms.euler_angles_by_matrix(m)
    return [pose.pose_x, pose.pose_y, pose.pose_z, a, b, c]


def _convert_configuration(configuration):
    """
    Convert a Configuration tuple to subclass conventions.
    :param configuration: Configuration tuple
    :return:
    """
    # TODO: Calculate S, T using configuration!
    s = 0
    t = 0
    return [s, t]
