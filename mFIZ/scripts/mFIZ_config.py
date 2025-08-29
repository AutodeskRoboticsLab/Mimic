#!usr/bin/env python

"""
This module contains basic configuration parameters for mFIZ Serial tools.
"""


# Default FIZ attributes
FIZ_ATTRS = ['focus', 'iris', 'zoom']

# Default animCurve colors
ANIM_CURVE_COLORS = {'focus': [.8, .35, .15],
                     'iris': [.15, .7, .8],
                     'zoom': [.8, .15, .8]}

CONNECTION_INDICATOR_COLORS = [[.75, .25, .25],  # Not connected
                               [.4, .8, .4]]  # Connected


# Set UI checkBox default for the "Stop Playback on Disconnect" option
DEFAULT_STOP_PLAYBACK_ON_DISCONNECT = True


# List of required plugins
REQUIRED_PLUGINS = ['mFIZ', 'mFIZ_remap']


# Suppoerted Motor APIs
SUPPORTED_MOTOR_APIS = ['redrockmicroEclipse', 'debug']  # The first entry is set to the default option