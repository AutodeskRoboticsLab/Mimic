#!usr/bin/env python

"""
This module contains basic configuration parameters for SimpleURScriptServoProcessor.
"""

# System parameters
DEFAULT_FILE_EXTENSION = 'script'

DEFAULT_JOINT_SPEED = '0.25'
DEFAULT_JOINT_ACCELERATION = '0.25'
DEFAULT_BLOCKING_TIME = '0.04'
DEFAULT_LOOKAHEAD = '0.1'
DEFAULT_GAIN = '300'

# Default program
DEFAULT_PROGRAM = \
    'popup("go to start?", title="Go To Start",blocking=True)\n' \
    '{}\n' \
    'popup("play path?", title="Play Path",blocking=True)\n' \
    '{}\n'