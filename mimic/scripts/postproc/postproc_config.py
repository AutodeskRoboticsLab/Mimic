#!usr/bin/env python

"""
This module contains basic configuration parameters for postproc.
"""

# Default parameters
DEFAULT_POST_PROCESSOR = ''  # E.G. 'KUKA EntertainTech'
DEFAULT_TEMPLATE_NAME = 'template'
DEFAULT_OUTPUT_NAME = 'output'

# Pre-processor parameters
DEFAULT_SAMPLE_RATE_VALUE = 0.012
DEFAULT_SAMPLE_RATE_UNITS = 'seconds'

# Motion options
OPTS_IGNORE_MOTION_COMMANDS = False
OPTS_USE_MOTION_AS_VARIABLES = False
OPTS_USE_LINEAR_MOTION = False
OPTS_USE_NONLINEAR_MOTION = True
OPTS_INCLUDE_AXES = True
OPTS_INCLUDE_POSE = False
OPTS_INCLUDE_EXTERNAL_AXES = False
OPTS_INCLUDE_CONFIGURATION = False

# IO options
OPTS_IGNORE_IO_COMMANDS = True
OPTS_INCLUDE_DIGITAL_OUTPUT = False
OPTS_PROCESS_IOS_FIRST = False

# Misc options
OPTS_INCLUDE_CHECKSUM = False

# Output options
OPTS_IGNORE_WARNINGS = False
OPTS_OVERWRITE_EXISTING_FILE = True
