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
__x = 'X'
__y = 'Y'
__z = 'Z'
__r = 'R'
__p = 'P'
__y = 'Y'
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
        __a6,
    ]
)

FRAME = 'FRAME'
__frame_structure = namedtuple(
    FRAME, [
        __x,
        __y,
        __z,
        __r,
        __p,
        __y
    ]
)

MOVE = 'MOVE'
__move_structure = namedtuple(
    MOVE, [
        __params,
    ]
)

STRUCTURES = {
    JOINTS: __joints_structure,
    FRAME: __frame_structure,
    MOVE: __move_structure
}

# TEMPLATES
__joints_template = \
    '{}, {}, {}, {}, {}, {}'

__frame_template = \
    '{}, {}, {}, {}, {}, {}'

__move_template = \
    '{}'

TEMPLATES = {
    JOINTS: __joints_template,
    FRAME: __frame_template,
    MOVE: __move_template
}

# COMMANDS
MOTION_COMMAND = 'motion_command'
_motion_command_fields = [
    postproc.AXES,
    postproc.POSE
]
MotionCommand = namedtuple(
    MOTION_COMMAND, _motion_command_fields
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
        motion_type = MOVE
        if command.axes is not None:
            target_data_type = JOINTS
            axes = command.axes
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in axes]
            target_data.extend(params)

        elif command.pose is not None:
            target_data_type = FRAME
            pose = _convert_pose(command.pose)
            params = [general_utils.num_to_str(p, include_sign=False, precision=3)
                      for p in pose]
            target_data.extend(params)

        else:
            raise ValueError('Invalid command')

    else:  # User never supplied a motion type
        raise ValueError('Invalid motion type')

    # Structure and format the datatype
    formatted_target_data = postproc.fill_template(
        target_data,
        STRUCTURES[target_data_type],
        TEMPLATES[target_data_type])

    # Structure and format the motion command
    formatted_motion = postproc.fill_template(
        formatted_target_data,
        STRUCTURES[motion_type],
        TEMPLATES[motion_type])

    return formatted_motion


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
    r, p, y = transforms.euler_angles_by_matrix(m)
    return [pose.pose_x, pose.pose_y, pose.pose_z, r, p, y]
