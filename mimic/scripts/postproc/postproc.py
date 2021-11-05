#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generic post processor object.
"""

import os
from collections import namedtuple

import general_utils
import mimic_config

reload(general_utils)
reload(mimic_config)

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
TIME_INDEX = 'time_index'

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
    generic functionality to all processor objects (but should be altered
    in subclass implementations) and to interface the rest of Mimic.
    Note that this class contains protected functions that initialize,
    process, and get/set parameters and only a few unique public functions
    """

    def __init__(self,
                 type_robot,
                 type_processor,
                 program_file_extension,
                 def_program_template):
        """
        Initialize generic processor. This function sets PostProcessor types
        and a few default parameters. Subclasses should implement the following
        in their own initialization functions:
            super(*subclass, self).__init__(*args)
        :param type_robot: Type of robot supported by this processor
        :param type_processor: Type of this processor
        :param program_file_extension: Type of the output file
        """
        # Set processor parameters
        self.type_robot = type_robot
        self.type_processor = type_processor
        self.program_file_extension = program_file_extension
        self.program_directory = self._get_program_directory()
        self.program_template_name = self._get_program_name(
            default=mimic_config.Prefs.get('DEFAULT_TEMPLATE_NAME'))
        self.program_output_name = self._get_program_name(
            default=mimic_config.Prefs.get('DEFAULT_OUTPUT_NAME'))
        self.default_program = def_program_template

    def _get_program_directory(self, directory=None):
        """
        Constructs and returns the program template/output directory. If a directory
        is provided and is valid, this function passes it directly out, otherwise it
        uses the default directory instead, coinciding with the type of robot and type
        of processor being used.
        :param directory: Optional, user-defined directory.
        :return:
        """
        try:
            assert os.path.isdir(directory)
        except (TypeError, AssertionError):
            mimic_dir = general_utils.get_mimic_dir()  # dependent on Maya
            template = '{}/scripts/postproc/{}/{}'
            directory = template.format(mimic_dir, self.type_robot, self.type_processor)
        return directory

    @staticmethod
    def _get_program_name(name=None, default='default'):
        """
        Get program template name. If a name is provided, this function passes it right
        out, otherwise, it uses the default name instead. If the provided name contains
        invalid characters, raises an error.
        :param name:
        :return:
        """
        if name == '' or name is None:
            name = default
        if not general_utils.str_is_simple(name):
            raise ValueError('Warning! Name contains invalid characters: ' + name)
        return check_and_remove_file_extension(name)

    def _get_program_path(self, filename):
        """
        Get a path using a known directory and provided filename.
        :param filename: Program filename (without extension).
        :return:
        """
        return '{}/{}.{}'.format(self.program_directory, filename, self.program_file_extension)

    def get_program_template_path(self, template_filename=None):
        """
        Get the path to the program template file.
        :param template_filename: User defined filename.
        :return:
        """
        if template_filename == '' or template_filename is None:
            template_filename = self.program_template_name

        default_directory = self._get_program_directory(directory=None)
        program_template_path = '{}/{}.{}'.format(default_directory, template_filename, self.program_file_extension)
        
        return program_template_path

    def get_program_output_path(self, output_filename=None):
        """
        Get the path to the program template file.
        :param output_filename: User defined filename.
        :return:
        """
        if output_filename == '' or output_filename is None:
            output_filename = self.program_output_name
        return self._get_program_path(output_filename)

    def get_processor_type(self):
        """
        Get the type of this post processor in the form 'robot_type processor_type'
        :return:
        """
        return '{} {}'.format(self.type_robot, self.type_processor)

    def _read_program_template(self):
        """
        Initialize program template. If there isn't one available in the provided
        directory, the provided default program template will be used instead.
        :return:
        """
        try:  # Get template from path
            path = self.get_program_template_path()
            with open(path, 'r') as f:
                return f.read()
        except IOError:  # File not found
            # Use default template instead
            return self.default_program

    def _adjust_program_output_path(self, output_name, overwrite):
        """
        Constructs and returns the expected output path. Generated using the
        template path or output directory.
        :param output_name: Optional name of the output file.
        :param overwrite: Optional bool to overwrite existing file. If False,
        a number will be appended to the name of the output file.
        :return:
        """
        # Get the program output path itself
        program_output_path = self.get_program_output_path(output_name)
        # Add a number to the end of the path if overwrite if False
        if not overwrite:  # check to see if we need to a number to the output name
            if os.path.isfile(program_output_path):
                expand = 1
                extension = '.' + self.program_file_extension
                while True:
                    expand += 1
                    new_path = program_output_path.split(extension)[0] + str(expand) + extension
                    if os.path.isfile(new_path):
                        continue
                    else:
                        program_output_path = new_path
                        break
        return program_output_path

    def _process_command(self, command, opts):
        """
        Process a single command and user options.  This function should
        consider any options, format input commands, and fill a template.
        Subclass implementation may be static.
        :param command: Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        raise NotImplementedError

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and user options. This function should
        consider any options, format input instructions, and fill a program
        template. Subclass implementation may be static.
        :param processed_commands: List of processed commands.
        :return:
        """
        raise NotImplementedError

    def _format_command(self, params_dict):
        """
        Processor-specific function. Certain types of commands are very specific
        to the processor in use or application, such as EntertainTech, requiring
        in some cases both Motion and IO datatypes in a single line of code. This
        function allows PostProcessor (processor) subclasses to format the input
        params flexibly and as needed.
        :param params_dict: Dictionary of namedtuple containing all command
        parameters (i.e. Axes, ExternalAxes, etc).
        :return:
        """
        raise NotImplementedError

    def _set_supported_options(self):
        """
        Set the supported options for this processor. Only set to True if the
        optional parameter is actually supported by this processor!
        :return:
        """
        raise NotImplementedError

    def format_commands(self, params_dicts):
        """
        Processor-specific function. Calls _format_command for all params.
        :param params_dicts: List of dictionary of namedtuple containing all
        command parameters (i.e. Axes, ExternalAxes, etc).
        :return:
        """
        commands = []
        for params_dict in params_dicts:
            command = self._format_command(params_dict)
            commands.append(command)
        return commands

    def set_program_directory(self, directory):
        """
        Set the program directory, where template and output files can be found.
        :param directory:
        :return:
        """
        # Set program directory
        self.program_directory = self._get_program_directory(directory)

    def process(self, commands, opts, template_filename=None):
        """
        Process a list of commands and user options. This function should
        consider any options, format input commands, and fill a program template.
        :param commands: List of Command tuple
        :param opts: UserOptions tuple
        :param template_filename: Filename for template itself.
        :return:
        """
        self.program_template_name = self._get_program_name(
            template_filename, default=mimic_config.Prefs.get('DEFAULT_TEMPLATE_NAME'))
        processed_commands = []
        for command in commands:
            processed_command = self._process_command(command, opts)
            if processed_command is not None:
                processed_commands.append(processed_command)
        return self._process_program(processed_commands, opts)

    def write(self, content, output_filename=None, overwrite=True):
        """
        Write content to a file in the same directory and with the same file
        extension as the template file.
        :param content: The content to write.
        :param output_filename: Optional name of the output file.
        :param overwrite: Optional bool to overwrite existing file. If False,
        a number will be appended to the name of the output file.
        :return:
        """
        self.program_output_name = self._get_program_name(
            output_filename, default=mimic_config.Prefs.get('DEFAULT_OUTPUT_NAME'))
        output_path = self._adjust_program_output_path(output_filename, overwrite)
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path


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


def check_and_remove_file_extension(filename):
    """
    Remove file extension from filename.
    :param filename:
    :return:
    """
    dot = '.'
    if dot in filename:
        filename = filename.split(dot)[0]
    return filename


def confirm_path_exists(path):
    """
    Check that a file exists.
    :param path:
    :return:
    """
    if os.path.exists(path):
        return path
    else:
        return 'Warning! No file found in chosen directory. ' \
               'Using default instead.'
