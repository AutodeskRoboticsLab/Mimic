#!usr/bin/env python
"""
EntertainTech post processor
"""

import binascii
import string
from collections import namedtuple

import comma_separated_vals_config
import general_utils
from postproc import postproc
from postproc import postproc_options


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
RECORDS = 'RECORDS'
__records_structure = namedtuple(
    RECORDS, [
        __params
    ]
)

CHECKSUM = 'CHECKSUM'
__checksum_structure = namedtuple(
    CHECKSUM, [
        __params
    ]
)

STRUCTURES = {
    RECORDS: __records_structure,
    CHECKSUM: __checksum_structure
}

# TEMPLATES
__records_template = \
    '{}'

__checksum_template = \
    '  CRC = {}\n'

TEMPLATES = {
    RECORDS: __records_template,
    CHECKSUM: __checksum_template
}

# COMMANDS
RECORDS_COMMAND = 'RECORDS_COMMAND'
_records_command_fields = [
    postproc.TIME_INDEX,
    postproc.AXES,
    postproc.EXTERNAL_AXES,
    postproc.DIGITAL_OUTPUT,
    postproc.ANALOG_OUTPUT
]
RecordsCommand = namedtuple(
    RECORDS_COMMAND, _records_command_fields
)


class SimpleCSVProcessor(postproc.PostProcessor):
    """
    Processor data frame for KRL post processor.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleCSVProcessor, self).__init__(
            type_robot='GENERAL',
            type_processor='CSV',
            program_file_extension=comma_separated_vals_config.DEFAULT_FILE_EXTENSION,
            def_program_template=comma_separated_vals_config.DEFAULT_PROGRAM)

        # Initialize internal parameters
        self.supported_options = self._set_supported_options()

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        # Get program structure and template
        program_template = self._read_program_template()  # don't overwrite original
        formatted_commands = '\n'.join(processed_commands)
        program = program_template.format(formatted_commands)

        return program

    @staticmethod
    def _process_command(command, opts):
        """
        Process a single command and user options.
        :param command: Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        # Get command type
        command_type = postproc.get_structure_type(command)
        if not opts.Ignore_motion and command_type == RECORDS_COMMAND:
            return _process_records_command(command, opts)

    @staticmethod
    def _format_command(params_dict):
        """
        Processor-specific function. Certain types of commands are very specific
        to the processor in use or application, such as EntertainTech, requiring
        in some cases both Motion and IO datatypes in a single line of code. This
        function allows PostProcessor (processor) subclasses to format the input
        params flexibly and as needed.

        For this processor:
        Can create a RecordsCommand namedTuple from optional input parameters.

        :param params_dict: Dictionary of namedtuple containing all command
        parameters (i.e. Axes, ExternalAxes, etc).
        :return:
        """
        # Try to get a RecordCommand
        params = []
        for field in _records_command_fields:
            param = params_dict[field] if field in params_dict else None
            params.append(param)
        if params.count(None) != len(params):
            # params.insert(0, self.time_index)  # Include current time-index
            # self.time_index += self.time_step  # Increment to next time-index
            return RecordsCommand(*params)

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
            include_external_axes=True,
            include_digital_outputs=True,
        )


def _process_records_command(command, opts):
    """
    Process records command.
    :param command: Command tuple
    :opts opts: UserOptions tuple
    :return:
    """
    params = []

    # Add timestamp
    timestamp = general_utils.num_to_str(command.time_index)
    params.append(timestamp)

    # Add primary parameters
    if command.axes is not None:
        formatted_params = [general_utils.num_to_str(axis)
                            for axis in command.axes]
        params.extend(formatted_params)

    if command.external_axes is not None:
        external_axes = [axis for axis in command.external_axes if axis is not None]
        formatted_params = [general_utils.num_to_str(axis)
                            for axis in external_axes]
        params.extend(formatted_params)

    if command.digital_output is not None:
        digital_output = [io for io in command.digital_output if io is not None]

        formatted_params = [general_utils.num_to_str(io)
                            for io in digital_output]

        params.extend(formatted_params)

    # Structure and format data, command
    formatted_record = ', '.join(param for param in params)
    return formatted_record


def get_checksum(s):
    """
    Get the CRC32 checksum for a string.
    :param s: Input string
    :return:
    """
    # TODO: Couldn't reproduce CRC32 checksum in documentation?
    values = s.translate(None, string.whitespace)
    return binascii.crc32(values) & 0xffffffff
