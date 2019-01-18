#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic.
"""

# Mimic information!
MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 2  # Must coincide with version in mimic.mod
MIMIC_VERSION_PATCH = 1  # Must coincide with version in mimic.mod

# Robots
DEFAULT_ROBOT = ''  # E.G 'KUKA KR 60-3'

# Reconcile rotation execution
# The reconcileRotation script job that ensures proper evaluation of the
# rotations about axes 4 and 6 can have a negative impact on the scene's
# performance, especially those that have large animation ranges.
# These parameters set the default evaluation state of the scriptJob

# If the Mimic UI is open, the checkbox in Prefs > Performance is used
# This parameter sets the default checkbox state. If the mimic UI is closed,
# this parameter is used
EXECUTE_RECONCILE_ROTATION_DEFAULT = True


# Nominal Velocity, Acceleration, and Jerk limits
# In the where the above limits aren't specified on the robot rig,
# we can use these nominal values as defaults
NOMINAL_LIMIT = {'Velocity': 999.9,
				 'Accel': 9999.9,
				 'Jerk': 99999.9}
