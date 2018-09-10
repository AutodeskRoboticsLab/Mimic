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

import pyqtgraph as pg
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
    def __init__(self, window_name, axis_numbers, parent=None):
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


        self.__build_ui()

        #print('# ' + mimic_analysis_window.showRepr())
        #mimic_analysis_window.show(dockable=True, height = 600, width=1165, floating=True)
        self.show(dockable=True, height = 600, width=1165)


    def _delete_instance(self, window_name):
        """
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
        """
        # Create a layout
        main_layout = QtWidgets.QHBoxLayout(self.centralWidget())

        return main_layout


    def __build_data_output_frame(self):
        """
        """
        data_output_frame = QtWidgets.QFrame()
        data_output_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        
        return data_output_frame


    def __build_plot_frame(self):
        """
        """
        plot_frame = QtWidgets.QFrame()
        plot_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        plot_frame.setMinimumWidth(200)
    
        plot_frame_layout = QtWidgets.QVBoxLayout()
        
        # Create the main plot window and add it to the plot frame layout
        self.analysis_plot = analysis_ui_utils.AnalysisPlotWidget()
        self.analysis_plot.set_axis_numbers(self.axis_numbers)

        # Add a Legend to the plot
        legend = pg.LegendItem( offset=(60, 5))
        self.analysis_plot.add_legend(legend)      

        plot_frame_layout.addWidget(self.analysis_plot.plot_window)
        
        # Set the plot frames layout
        plot_frame.setLayout(plot_frame_layout)

        return plot_frame

    def __build_data_control_frame(self):
        """
        """
        data_control_frame = QtWidgets.QFrame()
        data_control_frame.setFrameStyle(
                            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        data_control_frame.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                         QtWidgets.QSizePolicy.Minimum)

        data_control_frame_layout = QtWidgets.QVBoxLayout()
        data_control_frame_layout.setAlignment(QtCore.Qt.AlignTop)
        data_control_frame_layout.setContentsMargins(3, 0, 3, 0)
        data_control_frame_layout.setSpacing(5)
        
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
        """
        deriv_toggles = ['Position', 'Velocity', 'Accel', 'Jerk']
        deriv_toggle_widget = analysis_ui_utils.DataControlWidget(
                                                toggle_names=deriv_toggles,
                                                plot_widget=self.analysis_plot,
                                                data_type='Derivative' )
        
        return deriv_toggle_widget


    def __build_aux_toggle_widget(self):
        """
        """
        aux_toggles = ['Limits', 'Legend']
        aux_toggle_widget = analysis_ui_utils.AuxToggleWidget(
                                              toggle_names=aux_toggles,
                                              plot_widget=self.analysis_plot)

        return aux_toggle_widget
    

    def initialize_toggle_states(self):
        """
        """
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

        self.deriv_toggle_widget.isolate_toggle.setChecked(isolate_derivative)

        # TO-DO: replace these settings with config settings
        for toggle in axis_toggles:
            try:
                axis_toggles[toggle].setChecked(axis_states[toggle])
            except KeyError:  # There's no default for the given axis
                axis_toggles[toggle].setChecked(external_axis_state)

        self.axis_toggle_widget.isolate_toggle.setChecked(isolate_axis)

        # Set auxiliary toggle states
        aux_toggles['Limits'].setChecked(show_limits)
        aux_toggles['Legend'].setChecked(show_legend)


