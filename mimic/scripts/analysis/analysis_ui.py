#!usr/bin/env python
# -*- coding: utf-8 -*-

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

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


class MimicAnalysisWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    def __init__(self, window_name, axis_numbers, parent=None):
        super(MimicAnalysisWindow, self).__init__(parent=parent)
        self.window_name = window_name
        self.axis_numbers = axis_numbers
        self.setWindowTitle('Mimic Analysis')
        self.setObjectName(self.window_name)
        self.setProperty('saveWindowPref', True)

        self.analysis_plot = None
        self.axis_toggle_widget = None
        self.deriv_toggle_widget = None
        self.aux_toggle_widget = None

        # Create and assign the central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        self.__build_ui()

        #print('# ' + mimic_analysis_window.showRepr())
        #mimic_analysis_window.show(dockable=True, height = 600, width=1165, floating=True)
        self.show()

        self.test_run()

        
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
                    axis_toggles=self.axis_toggle_widget.toggles,
                    derivative_toggles=self.deriv_toggle_widget.toggles)
        
        return data_control_frame


    def __build_axis_toggle_widget(self):
        """
        """
        # TO-DO: Get axis toggle names dynamically
        number_of_axes = 6
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
        axis_toggle_names = self.axis_toggle_widget.get_toggle_names()
        axis_toggles = self.axis_toggle_widget.get_toggles()

        # TO-DO: replace these settings with config settings
        axis_toggles[axis_toggle_names[0]].setChecked(True)
        self.axis_toggle_widget.set_isolate(True)

        deriv_toggle_names = self.deriv_toggle_widget.get_toggle_names()
        deriv_toggles = self.deriv_toggle_widget.get_toggles()

        # TO-DO: replace these settings with config settings
        for toggle in deriv_toggles:
            deriv_toggles[toggle].setChecked(True)


    def test_run(self):
        
        pens = analysis_ui_utils.Palette(6).pens
        
        deriv = 'Accel'
        plotitem_1 = pg.PlotDataItem(range(10), pen=pens['Axis 1']['Position'])
        plotitem_2 = pg.PlotDataItem(range(1, 11), pen=pens['Axis 2']['Velocity'])
        plotitem_3 = pg.PlotDataItem(range(2, 12), pen=pens['Axis 3']['Accel'])
        plotitem_4 = pg.PlotDataItem(range(3, 13), pen=pens['Axis 4']['Jerk'])
        plotitem_5 = pg.PlotDataItem(range(4, 14), pen=pens['Axis 5'][deriv])
        plotitem_6 = pg.PlotDataItem(range(5, 15), pen=pens['Axis 6'][deriv])
        
        self.analysis_plot.plot.addItem(plotitem_1)
        self.analysis_plot.plot.addItem(plotitem_2)
        self.analysis_plot.plot.addItem(plotitem_3)
        self.analysis_plot.plot.addItem(plotitem_4)
        self.analysis_plot.plot.addItem(plotitem_5)
        self.analysis_plot.plot.addItem(plotitem_6)
        
        legend = pg.LegendItem( offset=(50, 5))
        legend.addItem(plotitem_1, 'Axis 1 Postion')
        legend.addItem(plotitem_2, 'Axis 2 Velocity')
        legend.addItem(plotitem_3, 'Axis 3')
        legend.addItem(plotitem_4, 'Axis 4')
        legend.addItem(plotitem_5, 'Axis 5')
        legend.addItem(plotitem_6, 'Axis 6')
        
        legend.setParentItem(self.analysis_plot.plot)
        
        

