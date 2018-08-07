#!usr/bin/env python
# -*- coding: utf-8 -*-

import maya.OpenMayaUI as omui

# Use Qt.py to provide for back-compatibility from PySide2 to PySide
from extern.Qt import QtWidgets
from extern.Qt import QtGui
from extern.Qt import QtCore
from extern.Qt import QtCompat


def getMayaWindow():
    """
    """
    mayaMainWindowPtr = omui.MQtUtil.mainWindow() 
    mayaMainWindow = QtCompat.wrapInstance(long(mayaMainWindowPtr), QtWidgets.QWidget) 

    return mayaMainWindow

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
