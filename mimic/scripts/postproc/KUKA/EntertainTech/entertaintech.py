#!usr/bin/env python
"""
EntertainTech post processor
"""

import binascii
import string
from collections import namedtuple

import entertaintech_config
import general_utils
from postproc import postproc

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
__time_index = 'time_index'
RecordsCommand = namedtuple(
    RECORDS_COMMAND, [
        __time_index,
        postproc.AXES,
        postproc.EXTERNAL_AXES,
        postproc.DIGITAL_OUTPUT
    ]
)


class SimpleEntertainTechProcessor(postproc.PostProcessor):
    """
    Processor data frame for KRL post processor.
    """

    def __init__(self):
        """
        Initialize specific processor.
        """
        # Initialize superclass (generic processor)
        super(SimpleEntertainTechProcessor, self).__init__(
            type_robot='KUKA',
            type_processor='EntertainTech',
            output_file_extension='emily',
            def_program_template=entertaintech_config.DEFAULT_PROGRAM)

        self.time_step = entertaintech_config.DEFAULT_TIME_STEP
        self.time_index = entertaintech_config.DEFAULT_START_TIME

    def _process_program(self, processed_commands, opts):  # Implement in base class!
        """
        Process a list of instructions and fill a program template.
        :param processed_commands: List of processed commands.
        :return:
        """
        # Get program structure and template
        program_template = self._get_program_template()  # don't overwrite original
        formatted_commands = '\n'.join(processed_commands)
        program = program_template.format(formatted_commands)
        if opts.include_checksum:
            checksum = get_checksum(formatted_commands)
            checksum_string = TEMPLATES[CHECKSUM].format(checksum)
            search_string = '[HEADER]\n'
            index = program.find(search_string) + len(search_string)
            program = program[:index] + checksum_string + program[index:]
        return program

    def _process_command(self, command, opts):
        """
        Process a single command and user options.
        :param command: Command tuple
        :param opts: UserOptions tuple
        :return:
        """
        # Get command type
        command_type = postproc.get_structure_type(command)
        if not opts.ignore_motion and command_type == RECORDS_COMMAND:
            return _process_records_command(command, opts)

    def get_formatted_commands(self, params):
        """
        Get formatted commands from raw axes.
        :param params:
        :return:
        """
        commands = []
        for axes in params:
            command = RecordsCommand(
                time_index=self.time_index,
                axes=postproc.Axes(*axes),
                external_axes=None,
                digital_output=None)
            commands.append(command)
            self.time_index += self.time_step
        return commands


def _process_records_command(command, opts):
    """
    Process records command.
    :param command: Command tuple
    :opts opts: UserOptions tuple
    :return:
    """
    params = []
    padding = 12

    # Add timestamp
    timestamp = general_utils.num_to_str(command.time_index, include_sign=True, padding=padding)
    params.append(timestamp)

    # Add primary parameters
    if command.axes is not None:
        formatted_params = [general_utils.num_to_str(axis, include_sign=True, padding=padding)
                            for axis in command.axes]
        params.extend(formatted_params)

    if command.external_axes is not None:
        formatted_params = [general_utils.num_to_str(axis, include_sign=True, padding=padding)
                            for axis in command.external_axes]
        params.extend(formatted_params)

    if command.digital_output is not None:
        formatted_params = [general_utils.num_to_str(digital_output.value, include_sign=True, padding=padding)
                            for digital_output in command.digital_output]
        params.extend(formatted_params)

    template = ''.join([TEMPLATES[RECORDS] for param in params])

    # Structure and format data, command
    formatted_record = template.format(*params)

    return formatted_record


def get_checksum(s):
    """
    Get the CRC32 checksum for a string.
    :param s: Input string
    :return:
    """
    values = s.translate(None, string.whitespace)
    return binascii.crc32(values) & 0xffffffff
