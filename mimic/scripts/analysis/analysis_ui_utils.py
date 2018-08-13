#!usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import pymel.core as pm
    import maya.mel as mel
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    mel = None
    MAYA_IS_RUNNING = False

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
        Supported data_types: 'Axis', 'Derivative', 'Isolate', 'Limit' 'Legend'
        """
        super(DataToggle, self).__init__(*args, **kwargs)

        self.data_type = data_type  

        self.plot_widget = plot_widget
        self.data_control_widget = data_control_widget

        self.toggled.connect(self.update)


    def get_data_type(self):
        """
        """
        return self.data_type


    def update(self):
        """
        """
        data_type = self.get_data_type()

        if data_type == 'Axis':
            self.plot_widget.update_axis(self)
        elif data_type == 'Derivative':
            self.plot_widget.update_derivative(self)
        elif data_type == 'Isolate':
            self.update_isolate()        
        elif data_type == 'Limits':
            self.update_limits()
        elif data_type == 'Legend':
            self.plot_widget.update_legend_visibility(self)
        else:
            pm.warning('Unsupported DataToggle Type in analysis_ui_utils')


    def update_isolate(self):
        """
        """
        isolate_toggle_state = self.isChecked()
        self.data_control_widget.set_isolate(isolate_toggle_state)


    def update_limits(self):
        """
        """
        limits_toggle_state = self.isChecked()
        print 'Toggle Data Type: ', self.data_type


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


    def get_toggle_names(self):
        """
        """
        return self.toggle_names


    def get_toggles(self):
        """
        """
        return self.toggles       


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
                                       data_type=toggle_name)
            toggle_object.setAccessibleName(toggle_name)

            # Assign the button object to its appropriate dictionary key
            self.toggles[toggle_name] = toggle_object
            
            toggle_label = QtWidgets.QLabel(toggle_name)
            toggle_label.setFont(FONT)

            # Add the button and its label to the toggle grid UI
            aux_grid_layout.addWidget(toggle_label, i, 0)
            aux_grid_layout.addWidget(toggle_object, i, 1)

            self.toggles[toggle_name]  = toggle_object

    def get_toggles(self):
        """
        """
        return self.toggles


class AnalysisPlotWidget(QtWidgets.QWidget):
    """
    """
    def __init__(self):
        super(AnalysisPlotWidget, self).__init__()

        self.plot_window = pg.GraphicsLayoutWidget(show=True,
                                                   title='Mimic Analysis')
        self.legend = None
        self.data_controls = None
        self.axis_toggles = None
        self.derivative_toggles = None

        self.frames = None
        self.plot_data = None

        self.program_info = None

        self.axis_numbers = None
        self.axis_names = None
        self.derivative_names = ['Position', 'Velocity', 'Accel', 'Jerk']
        
        self.plot_window.setBackground((78, 78, 78))

        pg.setConfigOptions(antialias=True)

        self.plot = self.plot_window.addPlot()
        self.plot.showGrid(x=True, y=True)


    def set_axis_numbers(self, axis_numbers):
        """
        """
        self.axis_numbers = axis_numbers
        self.axis_names = ['Axis {}'.format(axis_num) for axis_num in self.axis_numbers]


    def get_axis_numbers(self):
        """
        """
        return self.axis_numbers


    def get_active_toggles(self, data_type):
        """
        """
        if data_type == 'Axis':
            toggle_buttons = self.data_controls['Axis'].buttons()
        else:
            toggle_buttons = self.data_controls['Derivative'].buttons()

        active_toggles = [toggle for toggle in toggle_buttons if toggle.isChecked() == True]

        return active_toggles


    def get_inactive_toggles(self, data_type):
        """
        """
        if data_type == 'Axis':
            toggle_buttons = self.data_controls['Axis'].buttons()
        else:
            toggle_buttons = self.data_controls['Derivative'].buttons()

        inactive_toggles = [toggle for toggle in toggle_buttons if toggle.isChecked() == False]
        
        return inactive_toggles


    def add_legend(self, legend):
        """
        """
        self.legend = legend


    def add_data_controls(self, axis_toggle_group, derivative_toggle_group):
        data_controls = {}
        data_controls['Axis'] = axis_toggle_group
        data_controls['Derivative'] = derivative_toggle_group

        self.data_controls = data_controls


    def add_toggles(self, axis_toggles, derivative_toggles):
        """
        """
        self.axis_toggles = axis_toggles
        self.derivative_toggles = derivative_toggles


    def add_plot_data(self, program_data, frames):
        """
        Converts input data to pyqtgraph plotItem objects for graphng
        """
        self.frames = frames

        self.plot_data = self._format_data_as_plotItems(program_data)


    def _format_data_as_plotItems(self, program_data):
        """
        """
        frames = self.frames
        num_axes = max(self.axis_numbers)
        pens = Palette(num_axes).pens

        plot_data = {}

        for axis in program_data:
            plot_data[axis] = {}
            for deriv in self.derivative_names:
                plot_data[axis][deriv] = {}

                axis_data = program_data[axis][deriv]
                pen = pens[axis][deriv]

                plot_item = pg.PlotDataItem(frames, axis_data, pen=pen)
                plot_data[axis][deriv] = plot_item

        return plot_data


    def add_program_info(self, program_info):
        """
        """
        self.program_info = program_info

    
    def hide_legend(self):
        """
        """
        self.legend.scene().removeItem(self.legend)


    def show_legend(self):
        """
        """
        self.legend.setParentItem(self.plot)


    def update(self, toggle):
        """
        """
        pass
    

    def update_axis(self, toggle):
        """
        """
        axis_name = toggle.accessibleName()

        # If the axis toggle is on, we check for all of the active derivative
        # toggles, and turn on their corresponding plots
        if toggle.isChecked():
            active_deriv_toggles = self.get_active_toggles('Derivative')

            for toggle in active_deriv_toggles:
                deriv_name = toggle.accessibleName()
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.addItem(axis_plot_item)

                # Add the item to the Legend
                #self.legend.addItem(axis_plot_item, '{} {}'.format(axis_name, deriv_name))
                self.update_legend_contents()


        # If the axis toggle is off, turn off all of it's visible plots
        else:
            for deriv_name in self.derivative_names:
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.removeItem(axis_plot_item)
                
                # Remove the item from the Legend
                # self.legend.removeItem(axis_plot_item)
                self.update_legend_contents()


    def update_legend_visibility(self, toggle):
        """
        """
        # If the legend toggle is on, turn the legend visibility on
        # Otherwise, hide the legend
        if toggle.isChecked():
            self.show_legend()
        else:
            self.hide_legend()


    def update_legend_contents(self):
        """
        Note: we essentially rebuild the legend each time a toggle is changed
        to maintain the order of the items in the legend
        """
        # Clear the previous legend
        for axis_name in self.axis_names:
            for deriv_name in self.derivative_names:
                plot_item = self.plot_data[axis_name][deriv_name]
                self.legend.removeItem(plot_item)

        for axis_name in self.axis_names:
            for deriv_name in self.derivative_names:
                plot_item = self.plot_data[axis_name][deriv_name]

                if self.axis_toggles[axis_name].isChecked() and self.derivative_toggles[deriv_name].isChecked():
                    self.legend.addItem(plot_item, '{} {}'.format(axis_name, deriv_name))
        

    def update_derivative(self, toggle):
        """
        """
        deriv_name = toggle.accessibleName()

        # If the derivativ toggle is on, we check for all of the active
        # axis toggles, and turn on their corresponding plots
        if toggle.isChecked():
            active_axis_toggles = self.get_active_toggles('Axis')

            for toggle in active_axis_toggles:
                axis_name = toggle.accessibleName()
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.addItem(axis_plot_item)

                # Add the item to the Legend
                self.update_legend_contents()

        # If the axis toggle is off, turn off all of it's visible plots
        else:
            for axis_name in self.axis_names:
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.removeItem(axis_plot_item)

                # Remove the item from the Legend
                self.update_legend_contents()

    def update_all(self):
        """
        """
        active_axis_toggles = self.get_active_toggles('Axis')
        active_deriv_toggles = self.get_active_toggles('Derivative')

        for axis_toggle in active_axis_toggles:
            axis_name = axis_toggle.accessibleName()

            for deriv_toggle in active_deriv_toggles:
                deriv_name = deriv_toggle.accessibleName()

                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.addItem(axis_plot_item)

        inactive_axis_toggles = self.get_inactive_toggles('Axis')
        inactive_deriv_toggles = self.get_inactive_toggles('Derivative')

        for axis_toggle in inactive_axis_toggles:
            axis_name = axis_toggle.accessibleName()

            for deriv_toggle in inactive_deriv_toggles:
                deriv_name = deriv_toggle.accessibleName()

                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.removeItem(axis_plot_item)


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
               (200, 100, 50),
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

