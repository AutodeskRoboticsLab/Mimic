#!usr/bin/env python
"""
Postprocessor subclass.
"""

from collections import namedtuple

import general_utils
import karel_config
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
__params = 'params'

# STRUCTURES
JOINTS = 'JOINTS'
__joints_structure = namedtuple(
    JOINTS, [
        __a1,
        __a2,
        __a3,
        __a4,
        __a5,
        __a6
    ]
)

MOVE_JOINTS = 'PTP'
__move_joints_structure = namedtuple(
    MOVE_JOINTS, [
        __params
    ]
)

STRUCTURES = {
    JOINTS: __joints_structure,
    MOVE_JOINTS: __move_joints_structure
}

# TEMPLATES
__joints_template = \
    '[' \
    '[{}, {}, {}, {}, {}, {}]' \
    ']'

__move_joints_template = \
    '  MOVE JOINTS? {}'

TEMPLATES = {
    JOINTS: __joints_template,
    MOVE_JOINTS: __move_joints_template
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


class SimpleKARELProcessor(postproc.PostProcessor):
    """
    Postprocessor subclass.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleKARELProcessor, self).__init__(
            type_robot='FANUC',
            type_processor='KAREL',
            program_file_extension=karel_config.DEFAULT_FILE_EXTENSION,
            def_program_template=karel_config.DEFAULT_PROGRAM)

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
        formatted_commands = '\n'.join(processed_commands)
        program_template = self._read_program_template()  # don't overwrite original
        return program_template.format(formatted_commands)

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
            include_axes=True,
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

    # Interpret nonlinear motion command
    if opts.Use_nonlinear_motion:
        if command.axes is not None:
            motion_type = MOVE_JOINTS
            target_data_type = JOINTS
            target_data.extend(command.axes)
        else:
            raise ValueError('Invalid command')

    else:  # User never supplied a motion type
        raise ValueError('Invalid motion type')

    # Format parameters into string
    target_data = [general_utils.num_to_str(d, include_sign=False, precision=3)
                   for d in target_data]

    # Structure and format datatype
    formatted_target_data = postproc.fill_template(
        target_data,
        STRUCTURES[target_data_type],
        TEMPLATES[target_data_type])

    # Structure and format motion command
    formatted_motion = postproc.fill_template(
        formatted_target_data,
        STRUCTURES[motion_type],
        TEMPLATES[motion_type])
    return formatted_motion
