#!usr/bin/env python
# -*- coding: utf-8 -*-

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
try:
    import pymel.core as pm
    from pymel import versions
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    mel = None
    MAYA_IS_RUNNING = False

try:
    import pyqtgraph as pg
    PYQTGRAPH_LOADED = True
except ImportError:
    PYQTGRAPH_LOADED = False

import ui_utils
import analysis_ui_utils
import analysis_ui_config

reload(ui_utils)
reload(analysis_ui_utils)
reload(analysis_ui_config)

# Use Qt.py to provide for back-compatibility from PySide2 to PySide
from Qt import QtWidgets
from Qt import QtGui
from Qt import QtCore
from Qt import QtCompat


class MimicAnalysisWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    """
    Custom UI class that constructs the Mimic Analysis UI using PySide2
    Inherits from MayaQWidgetDockableMixin to enable docking
    Inherits from QtWidgets.QMainWindow
    """
    def __init__(self, window_name, axis_numbers, parent=None):
        # If a Mimic Analysis window already exists, delete it before
        # instantiating a new one
        self._delete_instance(window_name)

        super(MimicAnalysisWindow, self).__init__(parent=parent)

        self.window_name = window_name
        self.axis_numbers = axis_numbers

        # Create and assign the central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        self.setWindowTitle('Mimic Analysis')
        self.setObjectName(self.window_name)
        self.setProperty('saveWindowPref', True)

        self.analysis_plot = None
        self.axis_toggle_widget = None
        self.deriv_toggle_widget = None
        self.aux_toggle_widget = None

        # Main utility function that constructs the UI
        self.__build_ui()

        # Make the window visible in Maya
        self.show(dockable=True, height = 600, width=1165)


    def _delete_instance(self, window_name):
        """
        Deletes any instances of the window that already exist
        This is handles slightly differently from Maya 2016 and Maya 2017+
        """
        if versions.current() <201700:
            if pm.window(window_name, exists = True):
                pm.deleteUI(window_name, wnd = True)
        
        if versions.current() >= 201700:
            control = window_name + 'WorkspaceControl'
            if pm.workspaceControl(control, q=True, exists=True):
                pm.workspaceControl(control, e=True, close=True)
                pm.deleteUI(control, control=True)
        

    def __build_ui(self):
        """
        Main utility function that constructs the UI
        The UI is made up of three frames:
        - At the time of this writing, the "Data Output Frame" is not
          implemented, so it just an empty frame hidden on the left side of the
          Mimic Analysis UI. In the future, it will show numerical data that
          corresponds with the graphical data on the plot
        - The "Plot Frame" is the frame that holds the actual graph
        - The "Data Control Frame" is the panel on the left that holds the
          toggles and options for interracting with the data on the plot
        """
        main_layout = self.__build_main_layout()

        data_output_frame = self.__build_data_output_frame()
        plot_frame = self.__build_plot_frame()
        data_control_frame = self.__build_data_control_frame()

        main_layout.addWidget(data_output_frame)
        main_layout.addWidget(plot_frame)
        main_layout.addWidget(data_control_frame)

        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(2)


    def __build_main_layout(self):
        """
        Creates a Qt Horizontal Box Layout object to hold the main UI
        frames
        :return main_layout: QHBoxLayout
        """
        # Create a layout
        main_layout = QtWidgets.QHBoxLayout(self.centralWidget())

        return main_layout


    def __build_data_output_frame(self):
        """
        Creates a Qt Frame object to hold the data output UI elemets
        Currently, this is just an empty frame used as a placeholder for
        future UI plans
        :return data_output_frame: QFrame
        """
        data_output_frame = QtWidgets.QFrame()
        data_output_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        
        return data_output_frame


    def __build_plot_frame(self):
        """
        Creates a Qt Frame object to hold the plot UI elemets
        |-- QFrame
            |-- QVBoxLayout
                |-- Analysis Plot (PyQtGraph Graphics Layout Widget)
        :return plot_frame: QFrame
        """

        # Create a QFrame object
        plot_frame = QtWidgets.QFrame()
        plot_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        plot_frame.setMinimumWidth(200)
    
        # Create a QVBoxLayout to populate with UI elements
        plot_frame_layout = QtWidgets.QVBoxLayout()
        
        # Create the main plot window
        self.analysis_plot = analysis_ui_utils.AnalysisPlotWidget()
        self.analysis_plot.set_axis_numbers(self.axis_numbers)

        # Add a Legend to the plot
        legend = pg.LegendItem(offset=(60, 5))
        self.analysis_plot.add_legend(legend)      

        # Add the plot window to the QVBoxLayout
        plot_frame_layout.addWidget(self.analysis_plot.plot_window)
        
        # Add the QVBoxLayout to the QFrame
        plot_frame.setLayout(plot_frame_layout)

        return plot_frame


    def __build_data_control_frame(self):
        """
        Creates a Qt Frame object to hold the data control UI elemets
        |-- QFrame
            |-- QVBoxLayout
                |-- Axis Toggle Widget
                |-- Derivative Toggle Widget
                |-- Auxiliary Toggle Widget
        :return data_control_frame: QFrame
        """
        
        # Create a QFrame object
        data_control_frame = QtWidgets.QFrame()
        data_control_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        data_control_frame.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                         QtWidgets.QSizePolicy.Minimum)

        # Create a QVBoxLayout to populate with UI elements
        data_control_frame_layout = QtWidgets.QVBoxLayout()
        data_control_frame_layout.setAlignment(QtCore.Qt.AlignTop)
        data_control_frame_layout.setContentsMargins(3, 0, 3, 0)
        data_control_frame_layout.setSpacing(5)

        # Add the QVBoxLayout to the QFrame        
        data_control_frame.setLayout(data_control_frame_layout)        
        
        # Build and add the axis toggle widget
        self.axis_toggle_widget = self.__build_axis_toggle_widget()
        data_control_frame_layout.addWidget(self.axis_toggle_widget)
        
        # Add a horizontal line spacer
        data_control_frame_layout.addWidget(ui_utils.QHLine())

        # Build and add the derivative toggle widget
        self.deriv_toggle_widget = self.__build_derivative_toggle_widget()
        data_control_frame_layout.addWidget(self.deriv_toggle_widget)
        
        # Add a horizontal line and blank spacer
        data_control_frame_layout.addWidget(ui_utils.QHLine())
        data_control_frame_layout.addSpacerItem(QtWidgets.QSpacerItem(3, 0))

        # Build and add the auxilary toggle widget
        self.aux_toggle_widget = self.__build_aux_toggle_widget()
        data_control_frame_layout.addWidget(self.aux_toggle_widget)


        # Assign data toggles to plot
        self.analysis_plot.add_data_controls(
                    axis_toggle_group=self.axis_toggle_widget.toggle_group,
                    derivative_toggle_group=self.deriv_toggle_widget.toggle_group)

        self.analysis_plot.add_toggles(
                    axis_toggles=self.axis_toggle_widget.toggles,
                    derivative_toggles=self.deriv_toggle_widget.toggles,
                    limit_toggle=self.aux_toggle_widget.toggles['Limits'])
        
        return data_control_frame


    def __build_axis_toggle_widget(self):
        """
        Instantiates anlysis utility class 'DataControlWidget' using axis names
        incuded in the program being analyzed.
         --------------------------------
        |   --------------------------   |
        |  |   --------------------   |  |
        W  C  |   Axis 1 | Toggle  |  |  |
        I  O  G   Axis 2 | Toggle  |  |  |
        D  L  R   Axis 3 | Toggle  |  |  |
        G  U  I         ...        |  |  |
        E  M  D         ...        |  |  |
        T  N  |   Axis n | Toggle  |  |  |
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
        :return axis_toggle_widget: QWidget 
        """
        axis_toggle_names = []

        for axis_number in self.axis_numbers:
            axis_toggle_names.append('Axis {}'.format(axis_number))
        
        
        axis_toggle_widget = analysis_ui_utils.DataControlWidget(
                                               toggle_names=axis_toggle_names,
                                               plot_widget=self.analysis_plot,
                                               data_type='Axis')

        return axis_toggle_widget


    def __build_derivative_toggle_widget(self):
        """
        Instantiates anlysis utility class 'DataControlWidget' using
        derivatives types being
         ----------------------------------
        |   ----------------------------   |
        |  |   ----------------------   |  |
        W  C  |                      |  |  |
        I  O  G   Position | Toggle  |  |  |
        D  L  R   Velocity | Toggle  |  |  |
        G  U  I   Accel    | Toggle  |  |  |
        E  M  D   Jerk     | Toggle  |  |  |
        T  N  |                      |  |  |
        |  |   ----------------------   |  |
        |  |                            |  |
        |  |       Isolate | Toggle     |  |
        |  |                            |  |
        |  |       ---- Button ----     |  |
        |  |      |    Show All    |    |  |
        |  |       ----------------     |  |
        |  |       ---- Button ----     |  |
        |  |      |    Hide All    |    |  |
        |  |       ----------------     |  |
        |   ----------------------------   |
         ----------------------------------
        :return deriv_toggle_widget: QWidget 
        """
        deriv_toggles = ['Position', 'Velocity', 'Accel', 'Jerk']
        deriv_toggle_widget = analysis_ui_utils.DataControlWidget(
                                                toggle_names=deriv_toggles,
                                                plot_widget=self.analysis_plot,
                                                data_type='Derivative' )
        
        return deriv_toggle_widget


    def __build_aux_toggle_widget(self):
        """
        Instantiates anlysis utility class 'AuxToggleWidget' for toggling axis
        limits and plotlegend visibility
         -------------------------------
        |   -------------------------   |
        |  |   -------------------   |  |
        W  C  |                   |  |  |
        I  O  G                   |  |  |
        D  L  R  Limits | Toggle  |  |  |
        G  U  I  Legend | Toggle  |  |  |
        E  M  D                   |  |  |
        T  N  |                   |  |  |
        |  |   -------------------   |  |
        |   -------------------------   |
         -------------------------------
        :return aux_toggle_widget: QWidget
        """
        aux_toggles = ['Limits', 'Legend']
        aux_toggle_widget = analysis_ui_utils.AuxToggleWidget(
                                              toggle_names=aux_toggles,
                                              plot_widget=self.analysis_plot)

        return aux_toggle_widget
    

    def initialize_toggle_states(self):
        """
        Takes input from user config file 'analysis_ui_config.py' and
        sets Mimic Analysis UI toggles accordingly
        """

        # Get dicts of toggles assigned to each toggle widgets
        axis_toggles = self.axis_toggle_widget.get_toggles()
        deriv_toggles = self.deriv_toggle_widget.get_toggles()
        aux_toggles = self.aux_toggle_widget.get_toggles()

        # Get default toggle states from analysis_ui_config
        axis_states = analysis_ui_config.AXIS_STATES
        external_axis_state = analysis_ui_config.EXTERNAL_AXIS_STATE
        isolate_axis = analysis_ui_config.ISOLATE_AXIS
        derivative_states = analysis_ui_config.DERIVATIVE_STATES
        isolate_derivative = analysis_ui_config.ISOLATE_DERIVATIVE
        show_limits = analysis_ui_config.SHOW_LIMITS
        show_legend = analysis_ui_config.SHOW_LEGEND

        # Set derivative toggle states
        for toggle in deriv_toggles:
            deriv_toggles[toggle].setChecked(derivative_states[toggle])

        # Set isolate derivative toggle state
        self.deriv_toggle_widget.isolate_toggle.setChecked(isolate_derivative)

        # Set axis toggle states
        for toggle in axis_toggles:
            try:
                axis_toggles[toggle].setChecked(axis_states[toggle])
            except KeyError:  # There's no default for the given axis
                axis_toggles[toggle].setChecked(external_axis_state)

        # Set isolate axis toggle state
        self.axis_toggle_widget.isolate_toggle.setChecked(isolate_axis)

        # Set auxiliary toggle states
        aux_toggles['Limits'].setChecked(show_limits)
        aux_toggles['Legend'].setChecked(show_legend)


