#!usr/bin/env python
# -*- coding: utf-8 -*-


import general_utils
import ui_utils

reload(general_utils)
reload(ui_utils)

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


class DataToggleButton(ToggleButton):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(DataToggleButton, self).__init__(*args, **kwargs)

        self.toggled.connect(self.update_plot)

    def update_plot(self):
        if self.isChecked():
            print self.accessibleName() + ' is checked'
        else:
            print self.accessibleName() + ' is unchecked'


class IsolateToggleButton(ToggleButton):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(IsolateToggleButton, self).__init__(*args, **kwargs)

        self.toggled.connect(self.toggle_isolation)

    def toggle_isolation(self):
        if self.isChecked():
            print self.accessibleName() + ' is checked'
        else:
            print self.accessibleName() + ' is unchecked'


class DataControlWidget(QtWidgets.QWidget):
    """
     --------------------------------
    |   --------------------------   |
    |  |   --------------------   |  |
    W  C  |  Label 1 | Toggle  |  |  |
    I  O  G  Label 2 | Toggle  |  |  |
    D  L  R  Label 3 | Toggle  |  |  |
    G  U  I        ...         |  |  |
    E  M  D        ...         |  |  |
    T  N  |  Label n | Toggle  |  |  |
    |  |   --------------------   |  |
    |  |                          |  |
    |  |     Isolate | Toggle     |  |
    |  |                          |  |
    |  |     ---- Button ----     |  |
    |  |    |    Show All    |    |  |
    |  |     ----------------     |  |
    |  |     ---- Button ----     |  |
    |  |    |    Hide All    |    |  |
    |  |     ----------------     |  |
    |   --------------------------   |
     --------------------------------
    """
    def __init__(self, toggle_names, *args, **kwargs):
        super(DataControlWidget, self).__init__(*args, **kwargs)

        self.main_layout = None
        self.toggle_grid_layout = None

        self.toggle_names = toggle_names

        self.toggles = {}
        self.toggle_group = QtWidgets.QButtonGroup()

        self.__build_data_control_widget()


    def __build_data_control_widget(self):
        """
        """        
        main_layout = QtWidgets.QVBoxLayout(self)
        toggle_widget = self.__build_toggle_widget(self.toggle_names)
    

        main_layout.addWidget(toggle_widget)

        # main_layout.addSpacerItem(QtWidgets.QSpacerItem(5, 20))


        main_layout.addWidget(QtWidgets.QLabel(unichr(0x2022)), alignment = 4)

        # Add "isolate" toggle
        isolate_widget = QtWidgets.QWidget()
        isolate_grid_layout = QtWidgets.QGridLayout(isolate_widget)

        label = QtWidgets.QLabel('Isolate')
        label.setFont(FONT)

        isolate_grid_layout.addWidget(label, 0, 0)
        isolate_grid_layout.addWidget(IsolateToggleButton(), 0, 1)

        main_layout.addWidget(isolate_widget)

        # Add "Show all" and "Hide all" buttons
        main_layout.addWidget(QtWidgets.QPushButton('Show All')) # just for testing
        main_layout.addWidget(QtWidgets.QPushButton('Hide All')) # just for testing

        # Set layout view attributes
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(0, 5, 0, 5)

        self.main_layout = main_layout


    def __build_toggle_widget(self, toggle_names):
        """
        """
        # Create a widget to hold the toggle button and label grid
        toggle_widget = QtWidgets.QWidget()

        # Create grid layout to be filled with toggle buttons and labels
        toggle_grid_layout = QtWidgets.QGridLayout(toggle_widget)

        for i, toggle_name in enumerate(toggle_names):
            # Create a toggle button and assign it a name            
            toggle_object = DataToggleButton()
            toggle_object.setAccessibleName(toggle_name)

            # Assign the button object to its appropriate dictionary key
            self.toggles[toggle_name] = toggle_object
            
            self.toggle_group.addButton(toggle_object)

            toggle_label = QtWidgets.QLabel(toggle_name)
            toggle_label.setFont(FONT)

            # Add the button and its label to the toggle grid UI
            toggle_grid_layout.addWidget(toggle_label, i, 0)
            toggle_grid_layout.addWidget(toggle_object, i, 1)

        self.toggle_grid_layout = toggle_grid_layout

        return toggle_widget