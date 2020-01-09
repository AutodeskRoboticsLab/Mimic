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
from Qt import QtWidgets
from Qt import QtGui
from Qt import QtCore
from Qt import QtCompat

try:
    import pyqtgraph as pg
    PYQTGRAPH_LOADED = True
except ImportError:
    PYQTGRAPH_LOADED = False

# create a font
FONT = QtGui.QFont()
FONT.setPointSize(12)
FONT.setBold = True


class Toggle(QtWidgets.QPushButton):
    """
    Custom base class that inherits from QtWidgets.QPushButton and creates an
    ON/OFF toggle
    :type: QPushButton
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(Toggle, self).__init__(*args, **kwargs)

        # Get the custom button icons from Mimic
        # This is currently dependent on Mimic, but can changed if Analysis
        # module is decoupled from Mimic
        icon_directory = general_utils.get_mimic_dir()
        self.toggle_off_path = icon_directory + '/icons/toggle_button_off.png'
        self.toggle_on_path = icon_directory + '/icons/toggle_button_on.png'
        
        # Define QPushButton parameters
        self.setCheckable(True)
        self.setChecked(False)

        self.setFixedWidth(26)
        self.setFixedHeight(19)

        # Set styleSheet such that toggle_button_on.png is used if button is
        # checked, and toggle_button_off.png is used if button is unchecked
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
    Child of the Toggle class that creates more specific functionality.
    When toggled, an update method is called based on the toggle's data type
    :type: QPushButton
    """

    def __init__(self, data_type, plot_widget=None, data_control_widget=None, *args, **kwargs):
        """
        Instantiates a DataToggle with given data_type and assigns a
        plot_widget and/or data_control_widget if necessary, and connects the
        QButton's toggle signal to the update() method
        :param data_types: str
            supported: 'Axis', 'Derivative', 'Isolate', 'Limit' 'Legend'
        :param plot_widget: QWidget that the toggle is to operate on
        :param data_control_widget: QWidget that the toggle belongs to
        """
        super(DataToggle, self).__init__(*args, **kwargs)

        self.data_type = data_type  

        self.plot_widget = plot_widget
        self.data_control_widget = data_control_widget

        self.toggled.connect(self.update)


    def get_data_type(self):
        """
        Returns the DataToggle's assigned data type
        :return: str
        """
        return self.data_type


    def update(self):
        """
        Called when the instantiated button is toggled. Calls a more
        specific update function for each data type
        """
        data_type = self.get_data_type()

        if data_type == 'Axis':
            self.plot_widget.update_axis(self)
        elif data_type == 'Derivative':
            self.plot_widget.update_derivative(self)
        elif data_type == 'Isolate':
            self.update_isolate()        
        elif data_type == 'Limits':
            self.plot_widget.update_limits(self)
        elif data_type == 'Legend':
            self.plot_widget.update_legend_visibility(self)
        else:
            pm.warning('Unsupported DataToggle Type in analysis_ui_utils')


    def update_isolate(self):
        """
        Called when an Isolate Toggle is toggled
        """

        # Set the assigned data_control_widget's isolation state to 
        # the state of the toggle (i.e. True or False)
        isolate_toggle_state = self.isChecked()
        self.data_control_widget.set_isolate(isolate_toggle_state)


class UtilityButton(QtWidgets.QPushButton):
    """
    Custom base class that inherits from QtWidgets.QPushButton with more 
    specific functionality
    :type: QPushButton
    """
    def __init__(self, label, data_control_widget, *args, **kwargs):
        """
        Instantiates a QPushButton with the text label on it and connects
        it's clicked signal to the update() method
        :param label: str, Name to appear on button in the UI
            supported: 'Show All' or 'Hide All'
        :param data_control_widget: QWidget that the toggle belongs to
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
        Handles button functionality based on label name
        """
        if self.button_type == 'Show All':
            self.show_all()
        else:
            self.hide_all()


    def show_all(self):
        """
        Called if the button is a "Show All" button, and is clicked.
        Turns all toggles ON in the assigned data_control_widget
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
        Called if the button is a "Hide All" button, and is clicked.
        Turns all toggles OFF in the assigned data_control_widget
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
    Creates a collection of data controls (DataToggles) and utility buttons
    for interracting with the Analysis UI
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
    :type: QWidget 
    """
    def __init__(self, toggle_names, plot_widget, data_type):
        """
        Builds the data control widget with the supplied toggle names and
        data types
        :param toggle_names: list of toggle names to add to the widget
        :param plot_widget: QWidget that the toggle is to operate on
        :param data_type: str, type of toggles to create
            supported: 'Axis', 'Derivative'
        """ 
        super(DataControlWidget, self).__init__()

        self.main_layout = None  # QVBoxLayout

        self.toggle_names = toggle_names
        self.plot_widget = plot_widget
        self.data_type = data_type

        self.toggles = {}
        self.toggle_group = QtWidgets.QButtonGroup()
        self.toggle_group.setExclusive(False)

        self.isolate_toggle = None  # DataToggle object reference

        self.__build_data_control_widget()


    def __build_data_control_widget(self):
        """
        Adds all of the data control UI elements to a QVBoxLayout
        :return main_layout: QVBoxLayout
        """

        # Create the main layout and parent it to the DataControlWidget        
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Create and add the data control toggles
        toggle_widget = self.__build_toggle_widget()
        main_layout.addWidget(toggle_widget)

        # Add a spacing character
        main_layout.addWidget(QtWidgets.QLabel(unichr(0x2022)), alignment=QtCore.Qt.AlignCenter)

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
        Creates a QWidget and adds all of the DataToggles for the data
        control widget
        :return toggle_widget: QWidget
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

        return toggle_widget


    def __build_isolate_toggle_widget(self):
        """
        Creates a QWidget and adds the "Isolate" toggle
        :return isolate_widget: QWidget
        """
        isolate_widget = QtWidgets.QWidget()

        # Create a DataToggle of type 'Isolate'
        isolate_toggle = DataToggle(data_control_widget=self,
                                    data_type='Isolate')

        # Create a grid layout for the label and toggle
        isolate_grid_layout = QtWidgets.QGridLayout(isolate_widget)

        # Create a label for the toggle
        label = QtWidgets.QLabel('Isolate')
        isolate_toggle.setAccessibleName('Isolate')
        label.setFont(FONT)

        # Add the label and the toggle to the grid layout
        isolate_grid_layout.addWidget(label, 0, 0)
        isolate_grid_layout.addWidget(isolate_toggle, 0, 1)

        # Add the isolate toggle button to the toggles dictionary
        self.isolate_toggle = isolate_toggle

        return isolate_widget


    def get_active_toggles(self):
        """
        Gets a list of object references for all active toggles
        :return active_toggles: list 
        """
        toggles = self.toggle_group.buttons()
        active_toggles = [toggle for toggle in toggles if toggle.isChecked() == True]

        return active_toggles


    def get_toggle_names(self):
        """
        Returns a list of toggle names for the data control widget
        :return: list
        """
        return self.toggle_names


    def get_toggles(self):
        """
        Returns a dictionary of toggles assigned to the data control widget
            {'Toggle Name': Object Reference}
        :return: dict
        """
        return self.toggles       


    def set_isolate(self, isolate_toggle_state):
        """
        Sets the isolation state of the data control widget
        If True, only a single data control toggle can be active at a time
        If False, multiple toggles can be active simultaneously
        :param isolate_toggle_state: bool
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
    Creates a collection of auxiliary toggles
    :type: QWidget
    """
    def __init__(self, toggle_names, plot_widget):
        """
        Creates DataToggles and adds them to the Widget
        :param toggle_names: list of toggle names to add to the widget
        :param plot_widget: QWidget that the toggle is to operate on
        """
        super(AuxToggleWidget, self).__init__()
        
        self.plot_widget = plot_widget

        self.toggle_names = toggle_names
        self.toggles = {}
        self.__build_aux_toggle_widget()


    def __build_aux_toggle_widget(self):
        """
        Adds all of the DataToggle UI elements to a QGridLayout that is
        parented to the instantiated QWidget object
        """ 

        # Create the main layout and parent it to the AuxToggleWidget        
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
        Returns a dictionary of toggles assigned to the data control widget
            {'Toggle Name': Object Reference}
        :return: dict
        """
        return self.toggles


class AnalysisPlotWidget(QtWidgets.QWidget):
    """
    Main Analysis plot Class that handles all of the plot graphics
    :type: QWidget
    """
    def __init__(self):
        super(AnalysisPlotWidget, self).__init__()

        self.plot_window = pg.GraphicsLayoutWidget(show=True,
                                                   title='Mimic Analysis')
        self.legend = None  # pg.LegendItem
        self.data_controls = None  # dict of QtWidgets.QButtonGroup()s
        self.axis_toggles = None  # dict: {'Axis n': Object Reference}
        self.derivative_toggles = None  # dict: {'Deriv': Object Reference}
        self.limit_toggle = None  # DataToggle object reference

        self.frames = None  # List of frames for program being analyzed
                            # This becomes the x-axis data
        self.plot_data = None  # dict of pg.plotItems
        self.limit_data = None  # dict of pg.linearRegionItems

        self.program_info = None  # Not implemented yet

        self.axis_numbers = None  # List of axis numbers for current program
        self.axis_names = None  # list of axis names ['Axis 1', 'Axis 2'...]
        self.derivative_names = ['Position', 'Velocity', 'Accel', 'Jerk']
        
        self.plot_window.setBackground((78, 78, 78))

        pg.setConfigOptions(antialias=True)

        self.plot = self.plot_window.addPlot()
        self.plot.showGrid(x=True, y=True)


    def set_axis_numbers(self, axis_numbers):
        """
        Assigns input axis_numbers to the instance attribute axis_numbers.
        Generates and assigns axis names to instance attribute axis_names
        :param axis numbers: List of axis numbers for current program
        """
        self.axis_numbers = axis_numbers
        self.axis_names = ['Axis {}'.format(axis_num) for axis_num in self.axis_numbers]


    def get_axis_numbers(self):
        """
        Gets list of axis numbers from current program
        :return: list
        """
        return self.axis_numbers


    def get_active_toggles(self, data_type):
        """
        Gets a list of object references for all active toggles for input
        data_type
        :param data_type: str, 'Axis' or 'Derivative'
        :return active_toggles: list of object references
        """
        if data_type == 'Axis':
            toggle_buttons = self.data_controls['Axis'].buttons()
        else:
            toggle_buttons = self.data_controls['Derivative'].buttons()

        active_toggles = [toggle for toggle in toggle_buttons if toggle.isChecked() == True]

        return active_toggles


    def get_inactive_toggles(self, data_type):
        """
        Gets a list of object references for all inactive toggles for input
        data_type        
        :param data_type: str, 'Axis' or 'Derivative'
        :return inactive_toggles: list of object references
        """
        if data_type == 'Axis':
            toggle_buttons = self.data_controls['Axis'].buttons()
        else:
            toggle_buttons = self.data_controls['Derivative'].buttons()

        inactive_toggles = [toggle for toggle in toggle_buttons if toggle.isChecked() == False]
        
        return inactive_toggles


    def add_legend(self, legend):
        """
        Assigns input legend to the instance attribute legend.
        """
        self.legend = legend


    def add_data_controls(self, axis_toggle_group, derivative_toggle_group):
        """
        Assigns input data controls to instance attribute dict data_controls
        :paran axis_toggle_group: QtWidgets.QButtonGroup()
        :param derivative_toggle_group: QtWidgets.QButtonGroup()
        """
        data_controls = {}
        data_controls['Axis'] = axis_toggle_group
        data_controls['Derivative'] = derivative_toggle_group

        self.data_controls = data_controls


    def add_toggles(self, axis_toggles, derivative_toggles, limit_toggle):
        """
        Assigns input toggles to instance attributes
        :param axis_toggles: dict, {'Axis n': Toggle Object Reference}
        :param derivative_toggles: dict, {'Deriv': Toggle Object Reference}
        :param limit_toggle: DataToggle object reference
        """
        self.axis_toggles = axis_toggles
        self.derivative_toggles = derivative_toggles
        self.limit_toggle = limit_toggle


    def add_plot_data(self, program_data, frames):
        """
        Converts input data to pyqtgraph plotItem objects for graphng
        :param program_data: dict of position, velocity, accel, jerk data
        :param frames: list of frames that correspond with program data
        """
        self.frames = frames

        self.plot_data = self._format_data_as_plotItems(program_data)


    def add_limit_data(self, limit_data):
        """
        Converts input data to pyqtgraph linearRegionItem objects for graphng
        :param limit_data: dict containing min/max axis limits
        """
        self.limit_data = self._format_data_as_LinearRegionItems(limit_data)
        

    def _format_data_as_plotItems(self, program_data):
        """
        Takes input program_data and reformats it as pg.PlotDataItems for
        plotting
        :param program_data: dict of position, velocity, accel, jerk data
        :return plot_data: dict of position, velocity, accel, jerk pg.PlotDataItems
        """
        frames = self.frames
        num_axes = max(self.axis_numbers)
        pens = Palette(num_axes).pens

        plot_data = {}

        for axis in program_data:
            plot_data[axis] = {}
            for deriv in self.derivative_names:
                axis_data = program_data[axis][deriv]
                pen = pens[axis][deriv]

                plot_item = pg.PlotDataItem(frames, axis_data, pen=pen)
                plot_data[axis][deriv] = plot_item

        return plot_data


    def _format_data_as_LinearRegionItems(self, limit_data):
        """
        Takes input limit_data and reformats it as pg.LinearRegionItems for
        plotting
        :param limit_data: dict of position, velocity, accel, jerk limits
        :return plot_limit_data: dict of position, velocity, accel, jerk
            limits as pg.LinearRegionItems
        """
        num_axes = max(self.axis_numbers)
        pens = Palette(num_axes).pens
        brushes = Palette(num_axes).brushes

        region_buffer = 100

        plot_limit_data = {}

        for deriv in self.derivative_names:
            plot_limit_data[deriv] = {}
            for axis in limit_data[deriv]:
                plot_limit_data[deriv][axis] = {}

                limit_max = limit_data[deriv][axis]['Max Limit']
                limit_min = limit_data[deriv][axis]['Min Limit']

                # Find the maximum and minumum values in the data
                max_data = self.plot_data[axis][deriv].dataBounds(1)[1]
                min_data = self.plot_data[axis][deriv].dataBounds(1)[0]

                pen = pens[axis][deriv]
                # Adjust pen alpha to make it more transparent
                pen_color = pen.color()
                pen_color.setAlpha(100)
                pen.setColor(pen_color)

                brush = brushes[axis]

                if limit_max is not None:
                    linear_region_max = pg.LinearRegionItem(orientation='horizontal', pen=pen, brush=brush, movable=False)

                    # If the data exceeds the maximum limit, set the limit
                    # buffer region above the max data
                    if max_data > limit_max:
                        linear_region_max.setRegion([limit_max, max_data + region_buffer])
                    # Otherwise use the default region buffer
                    else:
                        linear_region_max.setRegion([limit_max, limit_max + region_buffer])
                else:
                    linear_region_max = None


                if limit_min is not None:
                    linear_region_min = pg.LinearRegionItem(orientation='horizontal', pen=pen, brush=brush, movable=False)
                    
                    # If the data exceeds the minimum limit, set the limit
                    # buffer region below the min data
                    if min_data < limit_min:
                        linear_region_min.setRegion([limit_min, min_data - region_buffer])
                    # Otherwise use the default region buffer
                    else:
                        linear_region_min.setRegion([limit_min, limit_min - region_buffer])
                else:
                    linear_region_min = None

                plot_limit_data[deriv][axis]['Max Limit'] = linear_region_max
                plot_limit_data[deriv][axis]['Min Limit'] = linear_region_min

        return plot_limit_data


    def add_program_info(self, program_info):
        """
        """
        self.program_info = program_info


    def show_limits(self):
        """
        Makes axis limit pg.LinearRegionItems visible on the plot for all
        active toggles
        """
        active_axis_toggles = self.get_active_toggles('Axis')
        active_deriv_toggles = self.get_active_toggles('Derivative')

        for axis_toggle in active_axis_toggles:
            for deriv_toggle in active_deriv_toggles:
                axis = axis_toggle.accessibleName()
                deriv = deriv_toggle.accessibleName()

                try: 
                    limit_max_item = self.limit_data[deriv][axis]['Max Limit']
                    limit_min_item = self.limit_data[deriv][axis]['Min Limit']

                    # If there is limit data for the current axis derivative,
                    # Add it to the plot
                    if limit_max_item is not None:
                        self.plot.addItem(limit_max_item)
                    if limit_min_item is not None:
                        self.plot.addItem(limit_min_item)
                except KeyError:  # External Axis limits not implemented yet
                    pass


    def hide_limits(self):
        """
        Removes all axis limit pg.LinearRegionItems from the plot
        """
        for axis in self.axis_names:
            for deriv in self.derivative_names:
                try:
                    limit_max_item = self.limit_data[deriv][axis]['Max Limit']
                    limit_min_item = self.limit_data[deriv][axis]['Min Limit']
                    
                    # If there is limit data for the current axis derivative,
                    # Remove it from the plot
                    if limit_max_item is not None:
                        self.plot.removeItem(limit_max_item)
                    if limit_min_item is not None:
                        self.plot.removeItem(limit_min_item)
                except KeyError:  # External Axis limits not implemented yet
                    pass


    def hide_legend(self):
        """
        Hides the plot legend
        """
        self.legend.scene().removeItem(self.legend)


    def show_legend(self):
        """
        Shows the plot legend
        """
        self.legend.setParentItem(self.plot)
    

    def update_axis(self, toggle):
        """
        Shows/hides plot data assigned to input toggle depending on toggle state
        :param toggle: Axis DataToggle object
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

        # If the axis toggle is off, turn off all of it's visible plots
        else:
            for deriv_name in self.derivative_names:
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.removeItem(axis_plot_item)
                
        # Update the legend and limits
        self.update_legend_contents()
        self.update_limits()


    def update_legend_visibility(self, toggle):
        """
        Shows/hides legend based on input toggle state
        :param toggle: Legend DataToggle object
        """
        # If the legend toggle is on, turn the legend visibility on
        # Otherwise, hide the legend
        if toggle.isChecked():
            self.show_legend()
        else:
            self.hide_legend()


    def update_legend_contents(self):
        """
        Rebuilds the legend each time a toggle is changed to maintain the
        order of the items in the legend
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
        Shows/hides plot data assigned to input toggle depending on toggle state
        :param toggle: Derivative DataToggle object
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

        # If the axis toggle is off, turn off all of it's visible plots
        else:
            for axis_name in self.axis_names:
                axis_plot_item = self.plot_data[axis_name][deriv_name]
                self.plot.removeItem(axis_plot_item)

        # Update the legend and limits
        self.update_legend_contents()
        self.update_limits()


    def update_limits(self, toggle=None):
        """
        Shows/hides limits assigned to input toggle depending on toggle state
        :param toggle: Limit DataToggle object
        """
        if not toggle:
            toggle = self.limit_toggle

        # If the toggle is on, check all active axis and derivative toggles
        # and show their corresponding limits
        if toggle.isChecked():
            self.hide_limits()  # Clear the plot of limits first
            self.show_limits()
        else:
            self.hide_limits()


    def update_all(self):
        """
        Updates all items on the plot based on current toggle states
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
    Custom class used to generate line colors and styles dynamically, based on
    the needs of the plot
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
        self.brushes = self._create_brushes()

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
            brush_color = Palette._COLORS[color_index]
            axis_number = i + 1  # Axis numbers are 1-indexed
            brush_key = 'Axis {}'.format(axis_number)

            brushes[brush_key] = {}
            
            brushes[brush_key] = pg.mkBrush(brush_color + (Palette._BRUSH_OPACITY,))

        return brushes

