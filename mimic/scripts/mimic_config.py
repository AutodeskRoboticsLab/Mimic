#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic.
"""

# Mimic information!
MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 4  # Must coincide with version in mimic.mod
MIMIC_VERSION_PATCH = 0  # Must coincide with version in mimic.mod

# Robots
DEFAULT_ROBOT = ''  # E.G 'KUKA KR 60-3'

# Nominal Velocity, Acceleration, and Jerk limits
# In the where the above limits aren't specified on the robot rig,
# we can use these nominal values as defaults
NOMINAL_LIMIT = {'Velocity': 999.9,
				 'Accel': 9999.9,
				 'Jerk': 99999.9}
