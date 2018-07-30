#!usr/bin/env python
# -*- coding: utf-8 -*-

import general_utils

import extern.pyqtgraph as pg
import ui_utils
import analysis_ui_utils

reload(ui_utils)
reload(analysis_ui_utils)

# Use Qt.py to provide for back-compatibility from PySide2 to PySide
from extern.Qt import QtWidgets
from extern.Qt import QtGui
from extern.Qt import QtCore
from extern.Qt import QtCompat

# Create a default font
FONT = QtGui.QFont()
FONT.setPointSize(12)

# Create a title font
TITLE_FONT = QtGui.QFont()
TITLE_FONT.setPointSize(13)
TITLE_FONT.setCapitalization(QtGui.QFont.AllUppercase)

# Temporary dictionary for testing data
DATA = {'Axis 1 Position':range(10),
        'Axis 1 Velocity':range(10, 20),
        'Axis 1 Accel':range(20, 30),
        'Axis 1 Jerk':range(30, 40),
        'Axis 2 Position':[i/.9 for i in range(10)],
        'Axis 2 Velocity':[i/.9 for i in range(10, 20)],
        'Axis 2 Accel':[i/.9 for i in range(20, 30)],
        'Axis 2 Jerk':[i/.9 for i in range(30, 40)],
        'Axis 3 Position':[i/.8 for i in range(10)],
        'Axis 3 Velocity':[i/.8 for i in range(10, 20)],
        'Axis 3 Accel':[i/.8 for i in range(20, 30)],
        'Axis 3 Jerk':[i/.8 for i in range(30, 40)],
        'Axis 4 Position':[i/.8 for i in range(10)],
        'Axis 4 Velocity':[i/.8 for i in range(10, 20)],
        'Axis 4 Accel':[i/.8 for i in range(20, 30)],
        'Axis 4 Jerk':[i/.8 for i in range(30, 40)],
        'Axis 5 Position':[i/.7 for i in range(10)],
        'Axis 5 Velocity':[i/.7 for i in range(10, 20)],
        'Axis 5 Accel':[i/.7 for i in range(20, 30)],
        'Axis 5 Jerk':[i/.7 for i in range(30, 40)],
        'Axis 6 Position':[i/.5 for i in range(10)],
        'Axis 6 Velocity':[i/.5 for i in range(10, 20)],
        'Axis 6 Accel':[i/.5 for i in range(20, 30)],
        'Axis 6 Jerk':[i/.5 for i in range(30, 40)],

}


class MimicAnalysisUI(QtWidgets.QMainWindow):
    """
    """
    def __init__(self, *args, **kwargs):
        super(MimicAnalysisUI, self).__init__(*args, **kwargs)
