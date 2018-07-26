#!usr/bin/env python
# -*- coding: utf-8 -*-

import general_utils


import extern.pyqtgraph as pg

# Use Qt.py to provide for back-compatibility from PySide2 to PySide
from extern.Qt import QtWidgets
from extern.Qt import QtGui
from extern.Qt import QtCore
from extern.Qt import QtCompat

# create a font
FONT = QtGui.QFont()
FONT.setPointSize(12)
FONT.setBold = True

class ToggleButton(QtWidgets.QPushButton):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(ToggleButton, self).__init__(*args, **kwargs)

        icon_directory = general_utils.get_mimic_dir()
        self.toggle_off_path = icon_directory + '/icons/toggle_button_off.png'
        self.toggle_on_path = icon_directory + '/icons/toggle_button_on.png'
        
        self.setCheckable(True)
        self.setChecked(True)

        self.setFixedWidth(26)
        self.setFixedHeight(19)
        self.setStyleSheet('QPushButton {background-image: url('
        							   + self.toggle_off_path + '); ' \
        								'border: none; ' \
        								'background-repeat: no-repeat;}' 
						 + 'QPushButton:checked {background-image: url(' 
						 			   + self.toggle_on_path + '); ' \
						 				'border: none; '\
						 				'background-repeat: no-repeat;}')
        self.setFlat(False)
        

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
    
        robot_label = QtWidgets.QLabel('ROBOT') # just for testing

        main_layout.addWidget(robot_label, alignment = 4)
        main_layout.addWidget(toggle_button_widget)
        main_layout.addWidget(QtWidgets.QPushButton('RESET')) # just for testing


        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 2, 0, 2)

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

            axis_toggles[axis_key] = ToggleButton()
            toggle_buttons_group.addButton(axis_toggles[axis_key])

            axis_label = QtWidgets.QLabel('Axis {}'.format(axis_number))
            axis_label.setFont(FONT)

            toggle_grid_layout.addWidget(axis_label, i, 0)
            toggle_grid_layout.addWidget(axis_toggles[axis_key], i, 1)

        self.axis_toggles = axis_toggles
        self.toggle_buttons_group = toggle_buttons_group
        self.toggle_grid_layout = toggle_grid_layout

        return toggle_button_widget

from PySide.QtGui import QFrame


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Raised)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
