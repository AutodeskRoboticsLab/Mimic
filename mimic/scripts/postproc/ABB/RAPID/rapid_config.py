#!usr/bin/env python

"""
This module contains basic configuration parameters for SimpleRAPIDProcessor.
"""

# Default system parameters
DEFAULT_FILE_EXTENSION = 'prg'

# Default parameters
DEFAULT_TOOL = 'tool0'
DEFAULT_WOBJ = 'wobj0'
DEFAULT_SPEED = 'v100'
DEFAULT_ZONE = 'z0'
DEFAULT_EXAX = [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]
DEFAULT_CONF = [0, 0, 0, 0]

# Default program
DEFAULT_PROGRAM = \
    'MODULE MainModule\n' \
    '	!Main routine\n' \
    '	PROC main()\n' \
    '		ConfL\Off;\n' \
    '		SingArea\Wrist;\n' \
    '		! Go to start position\n' \
    '        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;\n' \
    '        ! Go to programmed positions\n' \
    '{}\n' \
    '		! Go to end position\n' \
    '	    MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;\n' \
    '		Stop;\n' \
    '	ENDPROC\n' \
    'ENDMODULE\n'
