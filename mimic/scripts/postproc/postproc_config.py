#!usr/bin/env python

"""
This module contains basic configuration parameters for postproc.
"""

# Default parameters
DEFAULT_POST_PROCESSOR = ''  # E.G. 'KUKA EntertainTech'
DEFAULT_TEMPLATE_NAME = 'template'
DEFAULT_OUTPUT_NAME = 'output'

# Pre-processor parameters
DEFAULT_SAMPLE_RATE_VALUE = 1
DEFAULT_SAMPLE_RATE_UNITS = 'frames'  # 'seconds' or 'frames'

# Output options
OPTS_IGNORE_WARNINGS = False
OPTS_OVERWRITE_EXISTING_FILE = True

# User options
OPTS_PREVIEW_IN_VIEWPORT = False
OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT = False