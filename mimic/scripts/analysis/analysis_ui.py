#!usr/bin/env python
# -*- coding: utf-8 -*-

import general_utils


import extern.pyqtgraph as pg
import ui_utils
reload(ui_utils)

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

class AxisToggleWidget(QtWidgets.QWidget):
    """
     -------------------------------
    |   -------------------------   |
    |  |   -------------------   |  |
    W  C  |  Axis 1 | Toggle  |  |  |
    I  O  G  Axis 2 | Toggle  |  |  |
    D  L  R  Axis 3 | Toggle  |  |  |
    G  U  I        ...        |  |  |
    E  M  D        ...        |  |  |
    T  N  |  Axis n | Toggle  |  |  |
    |  |   -------------------   |  |
    |  |                         |  |
    |  |    Isolate | Toggle     |  |
    |  |                         |  |
    |  |    ---- Button ----     |  |
    |  |   |    Show All    |    |  |
    |  |    ----------------     |  |
    |  |    ---- Button ----     |  |
    |  |   |    Hide All    |    |  |
    |  |    ----------------     |  |
    |   -------------------------   |
     -------------------------------
    """
    def __init__(self, number_of_axes = 6, *args, **kwargs):
        """
        """
        super(AxisToggleWidget, self).__init__(*args, **kwargs)

        self.num_axes = number_of_axes

        self.main_layout = None
        self.toggle_grid_layout = None
        self.toggle_buttons_group = None

        self.axis_toggles = {}

        self.__build_axis_toggle_widget()


    def __build_axis_toggle_widget(self):
        """
        """        
        main_layout = QtWidgets.QVBoxLayout(self)
        toggle_button_widget = self.__build_toggle_group(self.num_axes)
    
        widget_label = QtWidgets.QLabel('Axes') 
        widget_label.setFont(TITLE_FONT)

        #main_layout.addWidget(widget_label, alignment = 4)
        main_layout.addWidget(toggle_button_widget)

        main_layout.addSpacerItem(QtWidgets.QSpacerItem(5, 20))

        main_layout.addWidget(QtWidgets.QPushButton('RESET')) # just for testing


        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(0, 5, 0, 5)

        self.main_layout = main_layout


    def __build_toggle_group(self, number_of_axes):
        """
        """
        axis_toggles = {}
        # Create a widget to hold the toggle button group
        toggle_button_widget = QtWidgets.QWidget()

        # Create grid layout to be filled with axis labels and toggle buttons
        toggle_grid_layout = QtWidgets.QGridLayout(toggle_button_widget)

        # Create button group
        toggle_buttons_group = QtWidgets.QButtonGroup()

        for i in range(number_of_axes):
            axis_number = i + 1  # Axes are 1-indexed

            axis_key = 'Axis {}'.format(axis_number)

            axis_toggles[axis_key] = ui_utils.ToggleButton()
            toggle_buttons_group.addButton(axis_toggles[axis_key])

            axis_label = QtWidgets.QLabel('Axis {}'.format(axis_number))
            axis_label.setFont(FONT)

            toggle_grid_layout.addWidget(axis_label, i, 0)
            toggle_grid_layout.addWidget(axis_toggles[axis_key], i, 1)

        # toggle_grid_layout.setSpacing(3)

        self.axis_toggles = axis_toggles
        self.toggle_buttons_group = toggle_buttons_group
        self.toggle_grid_layout = toggle_grid_layout

        return toggle_button_widget


class DerivativeToggleWidget(QtWidgets.QWidget):
    """
     ---------------------------------
    |   ---------------------------   |
    |  |   ---------------------   |  |
    W  C  |                     |  |  |
    I  O  G  Position | Toggle  |  |  |
    D  L  R  Velocity | Toggle  |  |  |
    G  U  I  Accel    | Toggle  |  |  |
    E  M  D  Jerk     | Toggle  |  |  |
    T  N  |                     |  |  |
    |  |   ---------------------   |  |
    |  |                           |  |
    |  |    Isolate | Toggle       |  |
    |  |                           |  |
    |  |    ---- Button ----       |  |
    |  |   |    Show All    |      |  |
    |  |    ----------------       |  |
    |  |    ---- Button ----       |  |
    |  |   |    Hide All    |      |  |
    |  |    ----------------       |  |
    |   ---------------------------   |
     ---------------------------------
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(DerivativeToggleWidget, self).__init__(*args, **kwargs)

        self.main_layout = None
        self.toggle_grid_layout = None
        self.toggle_buttons_group = None

        self.derivative_toggles = {}

        self.__build_derivative_toggle_widget()


    def __build_derivative_toggle_widget(self):
        """
        """        
        main_layout = QtWidgets.QVBoxLayout(self)
        toggle_button_widget = self.__build_toggle_group()
    
        widget_label = QtWidgets.QLabel('Attributes')
        widget_label.setFont(TITLE_FONT)

        #main_layout.addWidget(widget_label, alignment = 4)
        main_layout.addWidget(toggle_button_widget)

        main_layout.addSpacerItem(QtWidgets.QSpacerItem(5, 20))

        main_layout.addWidget(QtWidgets.QPushButton('RESET')) # just for testing


        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(0, 5, 0, 5)

        self.main_layout = main_layout


    def __build_toggle_group(self):
        """
        """
        derivative_toggles = {}
        # Create a widget to hold the toggle button group
        toggle_button_widget = QtWidgets.QWidget()

        # Create grid layout to be filled with derivative labels and toggle buttons
        toggle_grid_layout = QtWidgets.QGridLayout(toggle_button_widget)

        # Create button group
        toggle_buttons_group = QtWidgets.QButtonGroup()

        derivative_keys = ['Position', 'Velocity', 'Accel', 'Jerk']

        for i, derivative_key in enumerate(derivative_keys):

            derivative_toggles[derivative_key] = ui_utils.ToggleButton()
            toggle_buttons_group.addButton(derivative_toggles[derivative_key])

            derivative_label = QtWidgets.QLabel(derivative_key)
            derivative_label.setFont(FONT)

            toggle_grid_layout.addWidget(derivative_label, i, 0)
            toggle_grid_layout.addWidget(derivative_toggles[derivative_key], i, 1)

        self.derivative_toggles = derivative_toggles
        self.toggle_buttons_group = toggle_buttons_group
        self.toggle_grid_layout = toggle_grid_layout

        return toggle_button_widget


