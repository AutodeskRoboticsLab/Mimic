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

from extern import pyqtgraph as pg

# create a font
FONT = QtGui.QFont()
FONT.setPointSize(12)
FONT.setBold = True


class Toggle(QtWidgets.QPushButton):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(Toggle, self).__init__(*args, **kwargs)

        icon_directory = general_utils.get_mimic_dir()
        self.toggle_off_path = icon_directory + '/icons/toggle_button_off.png'
        self.toggle_on_path = icon_directory + '/icons/toggle_button_on.png'
        
        self.setCheckable(True)
        self.setChecked(False)

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


class DataToggle(Toggle):
    """
    """
    def __init__(self, data_type, plot_widget=None, data_control_widget=None, *args, **kwargs):
        """
        """
        super(DataToggle, self).__init__(*args, **kwargs)

        self.type = data_type  # 'Axis', 'Derivative', 'Isolate', 'Legend'

        self.plot_widget = plot_widget
        self.data_control_widget = data_control_widget

        self.toggled.connect(self.update)

    def update(self):
        """
        """
        if self.type == 'Axis':
            self.update_axis()
        elif self.type == 'Derivative':
            self.update_derivative()
        elif self.type == 'Isolate':
            self.update_isolate()
        elif self.type == 'Legend':
            self.update_legend()
        else:
            pm.warning('Unsupported DataToggle Type in analysis_ui_utils')


    def update_axis(self):
        """
        """
        self.plot_widget.update(self)
        if self.isChecked():
            print self.accessibleName() + ' is checked'
        else:
            print self.accessibleName() + ' is unchecked'


    def update_derivative(self):
        """
        """
        self.plot_widget.update(self)
        if self.isChecked():
            print self.accessibleName() + ' is checked'
        else:
            print self.accessibleName() + ' is unchecked'


    def update_isolate(self):
        """
        """
        isolate_toggle_state = self.isChecked()
        self.data_control_widget.set_isolate(isolate_toggle_state)


    def update_legend(self):
        """
        """
        self.plot_widget.update(self)
        if self.isChecked():
            print self.accessibleName() + ' is checked'
        else:
            print self.accessibleName() + ' is unchecked'


class UtilityButton(QtWidgets.QPushButton):
    """
    """
    def __init__(self, label, data_control_widget, *args, **kwargs):
        """
        """
        super(UtilityButton, self).__init__(label, *args, **kwargs)
        
        self.button_type = label
        self.data_control_widget = data_control_widget
        self.toggles = data_control_widget.toggles
        self.isolate_toggle = data_control_widget.isolate_toggle
        self.toggle_buttons = data_control_widget.toggle_group.buttons()
        self.toggle_group = data_control_widget.toggle_group

        self.clicked.connect(self.update)
    
    def update(self):
        """
        """
        if self.button_type == 'Show All':
            self.show_all()
        else:
            self.hide_all()

    def show_all(self):
        """
        """

        # Make sure the Isolate toggle is turned off to enable all of the
        # data toggles to be turned on
        self.isolate_toggle.setChecked(False)

        # Turn on all of the inactive data toggles
        inactive_toggles = [toggle for toggle in self.toggle_buttons if toggle.isChecked() == False]

        for toggle in inactive_toggles:
            toggle.setChecked(True)

    def hide_all(self):
        """
        """
        # Make a reference for the state of the isolate toggle so we can
        # maintain its state later
        initial_isolate_toggle_state = self.isolate_toggle.isChecked()

        # Turn off the Isolate toggle if necessary, which sets the toggle
        # group's state to inexclusive, which allows us to turn off all of
        # the toggles
        self.isolate_toggle.setChecked(False)

        # Turn off all of the active data toggles
        active_toggles = [toggle for toggle in self.toggle_buttons if toggle.isChecked() == True]

        for toggle in active_toggles:
            toggle.setChecked(False)

        # Set the state of the isolate toggle back to its initial state
        self.isolate_toggle.setChecked(initial_isolate_toggle_state)


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
    def __init__(self, toggle_names, plot_widget, data_type):
        super(DataControlWidget, self).__init__()

        self.main_layout = None
        self.toggle_grid_layout = None

        self.toggle_names = toggle_names
        self.plot_widget = plot_widget
        self.data_type = data_type

        self.toggles = {}
        self.toggle_group = QtWidgets.QButtonGroup()
        self.toggle_group.setExclusive(False)

        self.isolate_toggle = None

        self.__build_data_control_widget()

    def __build_data_control_widget(self):
        """
        """        
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Create and add the data control toggles
        toggle_widget = self.__build_toggle_widget()
        main_layout.addWidget(toggle_widget)

        # Add a spacing character
        main_layout.addWidget(QtWidgets.QLabel(unichr(0x2022)), alignment=4)

        # Create and add "isolate" toggle
        isolate_widget = self.__build_isolate_toggle_widget()
        main_layout.addWidget(isolate_widget)

        # Create and ddd "Show all" and "Hide all" buttons
        show_all_button = UtilityButton(label='Show All',
                                        data_control_widget=self)
        hide_all_button = UtilityButton(label='Hide All',
                                        data_control_widget=self)
        main_layout.addWidget(show_all_button) 
        main_layout.addWidget(hide_all_button) 

        # Set layout view preferences
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(0, 5, 0, 5)

        self.main_layout = main_layout


    def __build_toggle_widget(self):
        """
        """
        # Create a widget to hold the toggle button and label grid
        toggle_widget = QtWidgets.QWidget()

        # Create grid layout to be filled with toggle buttons and labels
        toggle_grid_layout = QtWidgets.QGridLayout(toggle_widget)

        for i, toggle_name in enumerate(self.toggle_names):
            # Create a toggle button and assign it a name            
            toggle_object = DataToggle(plot_widget=self.plot_widget,
                                       data_type=self.data_type)
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

    def __build_isolate_toggle_widget(self):
        """
        """
        isolate_widget = QtWidgets.QWidget()
        isolate_toggle = DataToggle(data_control_widget=self,
                                    data_type='Isolate')

        isolate_grid_layout = QtWidgets.QGridLayout(isolate_widget)

        label = QtWidgets.QLabel('Isolate')
        isolate_toggle.setAccessibleName('Isolate')
        label.setFont(FONT)

        isolate_grid_layout.addWidget(label, 0, 0)
        isolate_grid_layout.addWidget(isolate_toggle, 0, 1)

        # Add the isolate toggle button to the toggles dictionary
        self.isolate_toggle = isolate_toggle

        return isolate_widget


    def get_active_toggles(self):
        """
        """
        toggles = self.toggle_group.buttons()
        active_toggles = [toggle for toggle in toggles if toggle.isChecked() == True]

        return active_toggles


    def set_isolate(self, isolate_toggle_state):
        """
        """
        # If the toggle is turned on, turn off all of the toggles in the 
        # group, set the group to exclusive, then turn on a single toggle
        if isolate_toggle_state:
            # Turn off group exclusivity as this is the only way to uncheck
            # Every button
            self.toggle_group.setExclusive(False)

            # Break this out into a utility function?
            active_toggles = self.get_active_toggles()

            # Turn off all active toggles
            for toggle in active_toggles:
                toggle.setChecked(False)
            
            # Set the first active toggle back on
            try:
                active_toggles[0].setChecked(True)
            except IndexError:
                # No toggles were active
                pass

            # Set the toggle group back to exclusive
            self.toggle_group.setExclusive(True)
        else:
            # If toggle is turned off, set the toggle group to inexclusive
            self.toggle_group.setExclusive(False)


class AuxToggleWidget(QtWidgets.QWidget):
    """
    """
    def __init__(self, toggle_names, plot_widget):
        super(AuxToggleWidget, self).__init__()
        
        self.plot_widget = plot_widget

        self.toggle_names = toggle_names
        self.toggles = {}
        self.__build_aux_toggle_widget()

    def __build_aux_toggle_widget(self):
        """
        """
        aux_grid_layout = QtWidgets.QGridLayout(self)

        for i, toggle_name in enumerate(self.toggle_names):
            # Create a toggle button and assign it a name            
            toggle_object = DataToggle(plot_widget=self.plot_widget,
                                       data_type='Legend')
            toggle_object.setAccessibleName(toggle_name)

            # Assign the button object to its appropriate dictionary key
            self.toggles[toggle_name] = toggle_object
            
            toggle_label = QtWidgets.QLabel(toggle_name)
            toggle_label.setFont(FONT)

            # Add the button and its label to the toggle grid UI
            aux_grid_layout.addWidget(toggle_label, i, 0)
            aux_grid_layout.addWidget(toggle_object, i, 1)

            self.toggles[toggle_name]  = toggle_object


class AnalysisPlotWidget(QtWidgets.QWidget):
    """
    """
    def __init__(self):
        super(AnalysisPlotWidget, self).__init__()

        self.plot_window = pg.GraphicsLayoutWidget(show=True,
                                                   title='Mimic Analysis')
        self.data_controls = None

        self.plot_window.setBackground((78, 78, 78))

        pg.setConfigOptions(antialias=True)

        self.plot = self.plot_window.addPlot()
        self.plot.showGrid(x=True, y=True)


    def update(self, toggle):
        if toggle.isChecked():
            self.update_axis_data(toggle)
        else:
            self.update_derivative_data(toggle)

        print toggle.type


    def update_axis_data(self, toggle):
        """
        """
        print 'hey'


    def update_derivative_data(self, toggle):
        print 'sup'


    def add_data_controls(self, axis_toggles, derivative_toggles):
        data_controls = {}
        data_controls['Axis'] = axis_toggles
        data_controls['Derivative'] = derivative_toggles

        self.data_controls = data_controls


class Palette(object):
    """
    """
    _COLORS = [(19, 234, 201),
               (255, 107, 107),
               (210, 200, 100),
               (150, 100, 190),
               (190, 20, 100),
               (250, 120, 5),
               (19, 234, 100),
               (55, 50, 100),
               (100, 100, 255),
               (75, 200, 190),
               (80, 20, 50),
               (250, 120, 255)
               ]
    _PEN_WIDTH = 2
    _PEN_OPACITY = 150  # 255-scale
    _PEN_STYLES = {'Position': QtCore.Qt.SolidLine,
                   'Velocity': QtCore.Qt.DashLine,
                   'Accel': QtCore.Qt.DashDotLine,
                   'Jerk': QtCore.Qt.DotLine
                   }

    _DERIVATIVES = ['Position', 'Velocity', 'Accel', 'Jerk']

    _BRUSH_OPACITY = 25




    def __init__(self, number_of_axes):
        super(Palette, self).__init__()

        self.number_of_axes = number_of_axes

        self.pens = self._create_pens()

    def _create_pens(self):
        """
        """
        pens = {}

        for i in range(self.number_of_axes):
            number_of_colors = len(Palette._COLORS)
            color_index = i % number_of_colors
            pen_color = Palette._COLORS[color_index]
            axis_number = i + 1  # Axis numbers are 1-indexed
            pen_key = 'Axis {}'.format(axis_number)

            pens[pen_key] = {}
            for deriv in Palette._DERIVATIVES:
                pen_style = Palette._PEN_STYLES[deriv]

                pens[pen_key][deriv] = pg.mkPen(pen_color + (Palette._PEN_OPACITY,), width=Palette._PEN_WIDTH)
                pens[pen_key][deriv].setStyle(pen_style)

        return pens

    def _create_brushes(self):
        """
        """
        brushes = {}

        for i in range(self.number_of_axes):
            number_of_colors = len(Palette._COLORS)
            color_index = i % number_of_colors
            pen_color = Palette._COLORS[color_index]
            axis_number = i + 1  # Axis numbers are 1-indexed
            brush_key = 'Axis {}'.format(axis_number)

            brushes[brush_key] = pg.mkPen(pen_color + (Palette._PEN_OPACITY,),
                                          width=Palette._PEN_WIDTH)
        return brushes

