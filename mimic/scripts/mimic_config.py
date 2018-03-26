#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic.
"""

# Mimic information!
MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 0  # Must coincide with version in mimic.mod

# Robots
DEFAULT_ROBOT = ''  # E.G 'KUKA KR60-3'

# Plugin is dependent on the following scripts
REQUIRED_PLUGINS = [
    'robotAccumRot',
    'robotIK',
    'robotLimitRot',
    'snapTransforms'
]
