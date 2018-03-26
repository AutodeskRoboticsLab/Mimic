#!usr/bin/env python
"""
Generic post processor object.
"""

import os
from collections import namedtuple

import postproc_config
import general_utils

# PARAMS
__axis_1 = 'axis_1'
__axis_2 = 'axis_2'
__axis_3 = 'axis_3'
__axis_4 = 'axis_4'
__axis_5 = 'axis_5'
__axis_6 = 'axis_6'
__pose_x = 'pose_x'
__pose_y = 'pose_y'
__pose_z = 'pose_z'
__pose_ix = 'pose_ix'
__pose_iy = 'pose_iy'
__pose_iz = 'pose_iz'
__pose_jx = 'pose_jx'
__pose_jy = 'pose_jy'
__pose_jz = 'pose_jz'
__pose_kx = 'pose_kx'
__pose_ky = 'pose_ky'
__pose_kz = 'pose_kz'
__external_axis_1 = 'external_axis_1'
__external_axis_2 = 'external_axis_2'
__external_axis_3 = 'external_axis_3'
__external_axis_4 = 'external_axis_4'
__external_axis_5 = 'external_axis_5'
__external_axis_6 = 'external_axis_6'
__configuration_1 = 'configuration_1'
__configuration_2 = 'configuration_2'
__configuration_3 = 'configuration_3'
__identifier = 'identifier'
__value = 'value'

# STRUCTURES
AXES = 'axes'
Axes = namedtuple(
    AXES, [
        __axis_1,  # float
        __axis_2,  # float
        __axis_3,  # float
        __axis_4,  # float
        __axis_5,  # float
        __axis_6,  # float
    ]
)

POSE = 'pose'
Pose = namedtuple(
    POSE, [
        __pose_x,  # float
        __pose_y,  # float
        __pose_z,  # float
        __pose_ix,  # float
        __pose_iy,  # float
        __pose_iz,  # float
        __pose_jx,  # float
        __pose_jy,  # float
        __pose_jz,  # float
        __pose_kx,  # float
        __pose_ky,  # float
        __pose_kz,  # float
    ]
)

EXTERNAL_AXES = 'external_axes'
ExternalAxes = namedtuple(
    EXTERNAL_AXES, [
        __external_axis_1,  # float
        __external_axis_2,  # float
        __external_axis_3,  # float
        __external_axis_4,  # float
        __external_axis_5,  # float
        __external_axis_6,  # float
    ]
)

CONFIGURATION = 'configuration'
Configuration = namedtuple(
    CONFIGURATION, [
        __configuration_1,  # int
        __configuration_2,  # int
        __configuration_3,  # int
    ]
)

DIGITAL_OUTPUT = 'digital_output'
DigitalOutput = namedtuple(
    DIGITAL_OUTPUT, [
        __identifier,  # int, string
        __value  # int
    ]
)

DIGITAL_INPUT = 'digital_input'
DigitalInput = namedtuple(
    DIGITAL_INPUT, [
        __identifier,  # int, string
        __value  # int
    ]
)

ANALOG_OUTPUT = 'analog_output'
AnalogOutput = namedtuple(
    ANALOG_OUTPUT, [
        __identifier,  # int, string
        __value  # int
    ]
)

ANALOG_INPUT = 'analog_input'
AnalogInput = namedtuple(
    ANALOG_INPUT, [
        __identifier,  # int, string
        __value  # int
    ]
)


class PostProcessor(object):
    """
    Generic, superclass post-processor. This object is designed to provide
    generic functionality to all processor objects but should be altered at
    in subclass implementations.

    Note that this class contains protected functions that initialize (_init),
    process (_process), and get (_get) parameters. Only a few public functions
    are presented for the purpose of clarity. Once it has been configured, the
    function of the PostProcessor is to provide strong types, structures, and
    templates for minimally structured input.
    """

    def __init__(self,
                 type_robot,
                 type_processor,
                 output_file_extension,
                 def_program_template):
        """
        Initialize generic processor.
        :param type_robot: Type of robot supported by this processor
        :param type_processor: Type of this processor
        :param output_file_extension: Type of the output file
        """
        # Set processor parameters
        self.type_robot = type_robot
        self.type_processor = type_processor
        self.output_file_extension = output_file_extension
        self.default_program = def_program_template

    def _get_program_template_path(self):
        """
        Constructs and returns the expected template path. The type of robot,
        processor, and extension must coincide with those in the actual path.
        :return:
        """
        mimic_dir = general_utils.get_mimic_dir()  # dependent on Maya
        _template = '{}/scripts/postproc/{}/{}/{}.{}'
        return _template.format(mimic_dir,
                                self.type_robot,
                                self.type_processor,
                                postproc_config.DEFAULT_TEMPLATE_NAME,
                                self.output_file_extension)

    def _get_program_template(self):
        """
        Initialize program template. If there isn't one available, the provided
        default program template will be used instead.
        :return:
        """
        # TODO: Should this be type-case independent?
        try:
            # Get template from path
            program_template_path = self._get_program_template_path()
            with open(program_template_path, 'r') as f:
                return f.read()
        except IOError:  # file not found
            # Use default template instead
            return self.default_program

    def _get_program_output_path(self, output_directory, output_name, overwrite):
        """
        Constructs and returns the expected output path. Generated using the
        template path or output directory.
        :param output_directory: Optional directory for the output file.
        :param output_name: Optional name of the output file.
        :param overwrite: Optional bool to overwrite existing file. If False,
        a number will be appended to the name of the output file.
        :return:
        """
        if output_name == '' or output_name is None:
            output_name = postproc_config.DEFAULT_OUTPUT_NAME  # use default name
        elif not general_utils.str_is_simple(output_name):
            raise Exception('File name contains invalid characters')
        if output_directory == '' or output_directory is None:  # directory undefined
            template_path = self._get_program_template_path()
            template_name = postproc_config.DEFAULT_TEMPLATE_NAME
            path = template_path.replace(template_name, output_name)
        else:  # use the defined directory
            path = '{}/{}.{}'.format(output_directory, output_name, self.output_file_extension)
        if not overwrite:  # check to see if we need to a number to the output name
            if os.path.isfile(path):
                expand = 1
                extension = '.' + self.output_file_extension
                while True:
                    expand += 1
                    new_path = path.split(extension)[0] + str(expand) + extension
                    if os.path.isfile(new_path):
                        continue
                    else:
                        path = new_path
                        break
        return path

    def _process_command(self, command, opts):
        """
        Process a single command and user options.
        :param command: Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        raise NotImplementedError

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        raise NotImplementedError

    def process(self, commands, opts):
        """
        Process a list of commands and user options.
        :param commands: List of Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        processed_commands = []
        for command in commands:
            processed_command = self._process_command(command, opts)
            if processed_command is not None:
                processed_commands.append(processed_command)
        return self._process_program(processed_commands, opts)

    def write(self, content, output_directory='', output_name='', overwrite=True):
        """
        Write content to a file in the same directory and with the same file
        extension as the template file.
        :param content: The content to write.
        :param output_directory: Optional directory for the output file.
        :param output_name: Optional name of the output file.
        :param overwrite: Optional bool to overwrite existing file. If False,
        a number will be appended to the name of the output file.
        :return:
        """
        # Create an output file
        output_path = self._get_program_output_path(output_directory, output_name, overwrite)
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path

    def get_formatted_commands(self, params):
        """
        Using raw commands, get formatted commands.
        :param params:
        :return:
        """
        raise NotImplementedError


def fill_template(params, structure, template):
    """
    Fill template using structured params.
    :param params:
    :param structure:
    :param template:
    :return:
    """
    try:
        structured_params = structure(*params)
    except TypeError:  # params may be a single value
        structured_params = structure(params)
    return template.format(*structured_params)


def get_structure_type(structure):
    """
    Get the name of a post-processor structure.
    :param structure: Structure of type: namedtuple
    :return:
    """
    return type(structure).__name__


# USER OPTIONS
USER_OPTIONS = 'USER_OPTIONS'
__user_options = namedtuple(
    USER_OPTIONS, [
        'ignore_motion',
        'use_motion_as_variables',
        'use_linear_motion',
        'use_nonlinear_motion',
        'include_axes',
        'include_pose',
        'include_external_axes',
        'include_configuration',
        'ignore_ios',
        'process_ios_first',
        'include_digital_output',
        'include_checksum'
    ]
)


def configure_user_options(
        ignore_motion=postproc_config.OPTS_IGNORE_MOTION_COMMANDS,
        use_motion_as_variables=postproc_config.OPTS_USE_MOTION_AS_VARIABLES,
        use_linear_motion=True if postproc_config.OPTS_USE_LINEAR_MOTION
        else not postproc_config.OPTS_USE_NONLINEAR_MOTION,
        use_nonlinear_motion=True if postproc_config.OPTS_USE_NONLINEAR_MOTION
        else not postproc_config.OPTS_USE_LINEAR_MOTION,
        include_axes=postproc_config.OPTS_INCLUDE_AXES,
        include_pose=postproc_config.OPTS_INCLUDE_AXES,
        include_external_axes=postproc_config.OPTS_INCLUDE_EXTERNAL_AXES,
        include_configuration=postproc_config.OPTS_INCLUDE_CONFIGURATION,
        ignore_ios=postproc_config.OPTS_IGNORE_IO_COMMANDS,
        process_ios_first=postproc_config.OPTS_PROCESS_IOS_FIRST,
        include_digital_output=postproc_config.OPTS_INCLUDE_DIGITAL_OUTPUT,
        include_checksum=postproc_config.OPTS_INCLUDE_CHECKSUM):
    """
    Configure user options. Defaults every parameter to False unless specified
    by user.
    :param ignore_motion: Ignore all motion commands.
    :param use_motion_as_variables: Use motion as variables.
    :param use_linear_motion: Move linearly.
    :param use_nonlinear_motion: Move non-linearly.
    :param include_axes: Include axes in command.
    :param include_pose: Include pose in command.
    :param include_external_axes: Include external axes in command.
    :param include_configuration: Include configuration in command.
    :param ignore_ios: Ignore all IO commands.
    :param process_ios_first: Process IOs and append to output before motion.
    :param include_digital_output: Include digital output in command.
    :param include_checksum: Include a CRC32 checksum in output.
    :return:
    """
    return __user_options(
        ignore_motion=ignore_motion,
        use_motion_as_variables=use_motion_as_variables,
        use_linear_motion=use_linear_motion,
        use_nonlinear_motion=use_nonlinear_motion,
        include_axes=include_axes,
        include_pose=include_pose,
        include_external_axes=include_external_axes,
        include_configuration=include_configuration,
        ignore_ios=ignore_ios,
        process_ios_first=process_ios_first,
        include_digital_output=include_digital_output,
        include_checksum=include_checksum
    )
