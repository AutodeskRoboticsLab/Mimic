#!usr/bin/env python
# -*- coding: utf-8 -*-

import general_utils


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


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
