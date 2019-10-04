# -*- coding: utf-8 -*-
"""Custom Render Override for drawnig Manipulator even during playback."""
###############################################################################
import sys
import math

import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaAnim as omani
import maya.api.OpenMayaRender as omr
import maya.mel as mel

if False:
    # For mypy type annotation
    from typing import (  # NOQA
        Dict,
        List,
        Tuple,
        Pattern,
        Callable,
        Any,
        Text,
        Union
    )

###############################################################################

__author__ = 'yamahigashi'
__version__ = '0.1.0'

maya_useNewAPI = True
renderOverrideInstance = None  # type: DrawMimicHUDOverride

###############################################################################


class MimicHUDRender(omr.MHUDRender):
    """Render Manipulator object on current selection position."""

    def __init__(self):
        # type: (Text) -> None
        super(MimicHUDRender, self).__init__()

    # ------------------------------------------------------------------------

    def hasUIDrawables(self):
        # type: () -> bool
        return True

    def requiresLightData(self):
        # type: () -> bool
        return False

    def execute(self, context):
        # type: (omr.MDrawContext) -> None
        pass

    def addUIDrawables(self, drawManager, frameContext):
        # type: (omui.MUIDrawManager, omr.MFrameContext) -> bool
        selList = om.MSelectionList()
        selList.add('pCube1')
        obj = selList.getDependNode(0)

        print "selList: ", selList
 
        # Now get the MPlug for the attribute Visibility.
        depFn = om.MFnDependencyNode(om.MObject(obj))
        tx = depFn.findPlug('translateX', False).asFloat()
        ty = depFn.findPlug('translateY', False).asFloat()

        drawManager.beginDrawable()

        ## Draw a text "Foot"
        pos = om.MPoint(tx, 0.0)  ## Position of the text
        textColor = om.MColor( (0.1, 0.8, 0.8, 1.0) )  ## Text color

        drawManager.setColor( textColor )
        drawManager.setFontSize( omr.MUIDrawManager.kSmallFontSize )
        drawManager.text(pos, "Footprint", omr.MUIDrawManager.kCenter )

        scale = ty
        pos = om.MPoint(tx + 50. + scale, 0.0)  ## Position of the text
        up = om.MVector(0.0, 1, 0.0)  ## Position of the text
        drawManager.rect2d(pos, up, scale, 10, filled=True)

        drawManager.endDrawable()
        return True

    # ------------------------------------------------------------------------


class DrawMimicHUDOverride(omr.MRenderOverride):
    """Pass."""

    def __init__(self, name):
        # type: (Text) -> None
        self.operatioIndex = 0
        self.operations = [
            omr.MSceneRender("scene"),
            MimicHUDRender(),
            omr.MHUDRender(),
            omr.MPresentTarget("present")
        ]

        self.operations[0].clearOperation().setOverridesColors(False)
        super(DrawMimicHUDOverride, self).__init__(name)

    def uiName(self):
        # type: () -> Text
        return "Mimic HUD"

    def setup(self, destination):
        # type: (Text) -> None
        super(DrawMimicHUDOverride, self).setup(destination)

    def cleanup(self):
        # type: () -> None
        super(DrawMimicHUDOverride, self).cleanup()

    def supportedDrawAPIs(self):
        # type: () -> int
        return omr.MRenderer.kAllDevices

    def startOperationIterator(self):
        # type: () -> bool
        self.operationIndex = 0
        return True

    def renderOperation(self):
        # type: () -> omr.MRenderOperation
        return self.operations[self.operationIndex]

    def nextRenderOperation(self):
        # type: () -> bool
        self.operationIndex += 1
        return self.operationIndex < len(self.operations)


def initializePlugin(mobj):
    om.MFnPlugin(mobj, __author__, __version__, 'Any')

    try:
        global renderOverrideInstance
        renderOverrideInstance = DrawMimicHUDOverride("DrawMimicHUD")
        omr.MRenderer.registerOverride(renderOverrideInstance)

    except Exception:
        sys.stderr.write("registerOverride\n")
        om.MGlobal.displayError("registerOverride")
        raise


def uninitializePlugin(mobj):
    # plugin = om.MFnPlugin(mobj)
    # print(plugin)

    try:
        global renderOverrideInstance
        if renderOverrideInstance is not None:
            omr.MRenderer.deregisterOverride(renderOverrideInstance)
            renderOverrideInstance = None

    except Exception:
        sys.stderr.write("deregisterOverride\n")
        om.MGlobal.displayError("deregisterOverride")
        raise



