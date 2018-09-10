#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic Analysis UI.
"""

# AXIS TOGGLES
# Default checked states for axis toggles
# You can add any axis numbers to the dictionary below that you use frequently
# e.g. 'Axis 7': True, 'Axis 9': True
AXIS_STATES = {'Axis 1': True,
               'Axis 2': True,
               'Axis 3': True,
               'Axis 4': True,
               'Axis 5': True,
               'Axis 6': True}

# Default checked state for external axis toggles
# These are handled all together so as not to bloat this congfig
# If 'True', all axes not included above will be checked
# If 'False', all axes not included above will be unchecked
EXTERNAL_AXIS_STATE = True

# Default checked state for isolate axis toggle
# If 'True', this toggle overrides multiple checked axes above and only the
# first axis set to 'True' above will be checked
ISOLATE_AXIS = False

# DERIVATIVE TOGGLES
# Default checked states for derivative toggles
DERIVATIVE_STATES = {'Position': True,
                     'Velocity': True,
                     'Accel': True,
                     'Jerk': True}

# Default checked state for isolate derivative toggle
# If 'True', this toggle overrides multiple checked derivatives above and only
# the first derivative set to 'True' above will be checked
ISOLATE_DERIVATIVE = True


# AUXILIARY TOGGLES
# Default checked state for legend display toggle
SHOW_LEGEND = True

# Default checked state for limit display toggle
SHOW_LIMITS = False