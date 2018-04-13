#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic.
"""

# Mimic information!
MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 0  # Must coincide with version in mimic.mod

# Robots
DEFAULT_ROBOT = ''  # E.G 'KUKA KR 60-3'

# Plugin is dependent on the following scripts
REQUIRED_PLUGINS = [
    'robotAccumRot',
    'robotIK',
    'robotLimitRot',
    'snapTransforms'
]

# Reconcile rotation execution
# The reconcileRotation script job that ensures proper evaluation of the
# rotations about axes 4 and 6 can have a negative impact on the scene's
# performance, especially those that have large animation ranges.
# These parameters set the default evaluation state of the scriptJob

# If the Mimic UI is open, the checkbox in Prefs > Performance is used
# This parameter sets the default checkbox state. If the mimic UI is closed,
# this parameter is used
EXECUTE_RECONCILE_ROTATION_DEFAULT = True
