#!usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaRender as omr

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

# Defaul Limits if none are passed
AXIS_POS_MIN_LIMIT = -360
AXIS_POS_MAX_LIMIT = 360

AXIS_VEL_LIMIT = 999.9
AXIS_ACCEL_LIMIT = 9999.9
AXIS_JERK_LIMIT = 99999.9


# Constants for HUD styling
kFontSize = 12
kFontWeight = omr.MUIDrawManager.kWeightLight
kHeaderTextWeight = omr.MUIDrawManager.kWeightBold
kBorderBuffer = 10  # Distance between edge of fiewport and HUD elements in pixels
kSectionBuffer = 5  # Distance between different hud sections in pixels
kLineWidth = 1
kAxisLabelColWidth = 25
kHUDWidth = 425  # Width of the HUD in pixels
kBarWidth = 320
kAlignLeft = omr.MUIDrawManager.kLeft
kAlignRight = omr.MUIDrawManager.kRight
kUp = om.MVector(0.0, 1, 0.0)
kRowHeight = kFontSize + 3
kBarHeight = 6


class mimicHUDManager(omui.MPxLocatorNode):
    id = om.MTypeId(0x87003)
    draw_db_classification = "drawdb/geometry/mimicHUDManager"
    draw_registrant_id = "mimicHUDManagerPlugin"

    ## General Design Attributes
    a_text_color = None
    a_text_transparency = None

    a_bar_color = None
    a_bar_transparency = None
    a_is_filled = None

    a_line_color = None
    a_line_transparency = None

    a_hud_position = None


    ## Robot Dynamics Attributes
    # Primary Axes Array
    a_axis_p = None
    a_axis_p_min_limit = None
    a_axis_p_max_limit = None

    a_axis_v = None
    a_axis_v_limit = None

    a_axis_a = None
    a_axis_a_limit = None

    a_axis_j = None
    a_axis_j_limit = None

    # External Axes Array
    a_external_axis_p = None
    a_external_axis_v = None
    a_external_axis_a = None
    a_external_axis_j = None   


    def __init__(self):
        omui.MPxLocatorNode.__init__(self)

    @staticmethod
    def creator():
        return mimicHUDManager()

    @staticmethod
    def initialize():
        nAttr = om.MFnNumericAttribute()
        eAttr = om.MFnEnumAttribute()
        typedAttr = om.MFnTypedAttribute()

        ## Add Text attributes
        # Color
        mimicHUDManager.a_text_color = nAttr.create("textColor", "tc", om.MFnNumericData.k3Float)
        nAttr.default = (0.0, 0.0, 0.0)
        nAttr.usedAsColor = True
        om.MPxNode.addAttribute(mimicHUDManager.a_text_color)

        # Transparency
        mimicHUDManager.a_text_transparency = nAttr.create("textTransparency", "tt", om.MFnNumericData.kFloat, 0.0)
        nAttr.setSoftMin(0.0)
        nAttr.setSoftMax(1.0)
        om.MPxNode.addAttribute(mimicHUDManager.a_text_transparency)


        ## Add Bar attributes
        # Color
        mimicHUDManager.a_bar_color = nAttr.create("barColor", "bc", om.MFnNumericData.k3Float)
        nAttr.default = (0.0, 0.0, 0.0)
        nAttr.usedAsColor = True
        om.MPxNode.addAttribute(mimicHUDManager.a_bar_color)

        # Transparency
        mimicHUDManager.a_bar_transparency = nAttr.create("barTransparency", "bt", om.MFnNumericData.kFloat, 0.3)
        nAttr.setSoftMin(0.0)
        nAttr.setSoftMax(1.0)
        om.MPxNode.addAttribute(mimicHUDManager.a_bar_transparency)

        # Filled 
        mimicHUDManager.a_is_filled = nAttr.create("isFilled", "if", om.MFnNumericData.kBoolean, True)
        om.MPxNode.addAttribute(mimicHUDManager.a_is_filled)


        ## Add Line attributes
        # Color
        mimicHUDManager.a_line_color = nAttr.create("lineColor", "lc", om.MFnNumericData.k3Float)
        nAttr.default = (0.0, 0.0, 0.0)
        nAttr.usedAsColor = True
        om.MPxNode.addAttribute(mimicHUDManager.a_line_color)

        # Transparency
        mimicHUDManager.a_line_transparency = nAttr.create("lineTransparency", "lt", om.MFnNumericData.kFloat, 0.0)
        nAttr.setSoftMin(0.0)
        nAttr.setSoftMax(1.0)
        om.MPxNode.addAttribute(mimicHUDManager.a_line_transparency)


        ## UI Position
        mimicHUDManager.a_hud_position = nAttr.create("hudPosition", "hudPos", om.MFnNumericData.k2Double)
        nAttr.default = (0.0, 0.0)
        om.MPxNode.addAttribute(mimicHUDManager.a_hud_position)


        ## Robot Dynamics Arrays
        # Primary Axes Positions
        mimicHUDManager.a_axis_p = nAttr.create("axisPosition", "ap", om.MFnNumericData.kFloat, 0.0)
        nAttr.array = True
        nAttr.usesArrayDataBuilder = True
        om.MPxNode.addAttribute(mimicHUDManager.a_axis_p)

        # Primary Axes Positions Min Limit
        mimicHUDManager.a_axis_p_min_limit = nAttr.create("axisPositionMinLimit", "apmin", om.MFnNumericData.kFloat, AXIS_POS_MIN_LIMIT)
        nAttr.array = True
        nAttr.usesArrayDataBuilder = True
        om.MPxNode.addAttribute(mimicHUDManager.a_axis_p_min_limit)

        # Primary Axes Positions Max Limit
        mimicHUDManager.a_axis_p_max_limit = nAttr.create("axisPositionMaxLimit", "apmax", om.MFnNumericData.kFloat, AXIS_POS_MIN_LIMIT)
        nAttr.array = True
        nAttr.usesArrayDataBuilder = True
        om.MPxNode.addAttribute(mimicHUDManager.a_axis_p_max_limit)


class mimicHUDManagerData(om.MUserData):
    def __init__(self):
        om.MUserData.__init__(self, False)
        # self.fUIType = kText
        # self.fSelectability = omr.MUIDrawManager.kAutomatic
        self.f_text_color = om.MColor((0.0, 0.0, 0.0, 1.))

        self.f_bar_color = om.MColor((0.0, 0.0, 0.0, 0.7))
        self.f_is_filled = True

        self.f_line_color = om.MColor((0.0, 0.0, 0.0, 1.))

        self.f_hud_position = om.MPoint(0.0, 0.0)

        self.f_robot_name = ''
        self.f_primary_axis_data = {}

        self.f_axis_position_connections = None
        


################################################################################################
class mimicHUDManagerDrawOverride(omr.MPxDrawOverride):
    def __init__(self, obj):
        omr.MPxDrawOverride.__init__(self, obj, None)

    @staticmethod
    def creator(obj):
        return mimicHUDManagerDrawOverride(obj)

    def supportedDrawAPIs(self):
        return (omr.MRenderer.kOpenGL | omr.MRenderer.kDirectX11 | omr.MRenderer.kOpenGLCoreProfile)

    def isBounded(self, objPath, cameraPath):
        return False

    def boundingBox(self, objPath, cameraPath):
        return om.MBoundingBox()

    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        data = oldData
        if not isinstance(data, mimicHUDManagerData):
            data = mimicHUDManagerData()

        mimicHUDManagerNode = objPath.node()
        if mimicHUDManagerNode.isNull():
            return

        ## Retrieve Text attributes
        # Color
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_text_color)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.f_text_color = om.MColor(nData.getData())

        # Transparency
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_text_transparency)
        data.f_text_color.a = 1.0 - plug.asFloat()


        ## Retrieve Bar attributes
        # Color
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_bar_color)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.f_bar_color = om.MColor(nData.getData())

        # Transparency
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_bar_transparency)
        data.f_bar_color.a = 1.0 - plug.asFloat()

        ## retrieve filled flag
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_is_filled)
        data.f_is_filled = plug.asBool()


        ## Retrieve Line attributes
        # Color
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_line_color)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.f_line_color = om.MColor(nData.getData())

        # Transparency
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_line_transparency)
        data.f_line_color.a = 1.0 - plug.asFloat()


        ## retrieve screen position
        plug = om.MPlug(mimicHUDManagerNode, mimicHUDManager.a_hud_position)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.f_hud_position = om.MPoint(nData.getData())
        # data.f_hud_position.w = 1.0


        # Get robot name
        data.f_robot_name = 'KUKA_KR60_3_0'
        

        # Get Primary Axis Data
        self._get_primary_axis_data(mimicHUDManagerNode, data)


        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        if not isinstance(data, mimicHUDManagerData):
            return

        # debugStr =  'Axes Positions: {} {}'.format(data.f_axes_positions, data.f_axis_position_connections)
        # debugStr =  'Port Height: {} Port Width {}'.format(data.f_viewport_height, data.f_viewport_width)
        # debugStr =  'Viewport Dims {}'.format(frameContext.getViewportDimensions())

        viewport_width = frameContext.getViewportDimensions()[2]
        viewport_height = frameContext.getViewportDimensions()[3]

        p_hud_origin = om.MPoint(kBorderBuffer, viewport_height - kBorderBuffer)

        ## All drawing operations must take place between calls to beginDrawable()
        ## and endDrawable().
        drawManager.beginDrawable(isPickable=False)

        # Set common style parameters
        drawManager.setFontSize(kFontSize)
        drawManager.setLineWidth(kLineWidth)

        # All draw loacations are going to be offset from the previous draw item
        # so we define a "cursor" position to keep track and update the desired 
        # draw position, starting at the origin
        cursor_point = om.MPoint(p_hud_origin)

        # Draw the header
        cursor_point = self._draw_header(drawManager, cursor_point, data)

        # Draw position HUD
        cursor_point = self._draw_position_hud(drawManager, cursor_point, data)

    
    def _draw_header(self, drawManager, cursor_point, data):
        """
        """
        robot_name = data.f_robot_name

        cursor_point.y -= kFontSize

        drawManager.setFontWeight(kHeaderTextWeight)
        drawManager.setColor(data.f_text_color)
        #drawManager.text2d(cursor_point, robot_name + ' {}'.format(data.f_axis_position_connections) , kAlignLeft)
        drawManager.text2d(cursor_point, '{}'.format(data.f_primary_axis_data['A1']) , kAlignLeft)

        cursor_point.y -= 3

        line_start_x = cursor_point.x
        line_start_y = cursor_point.y

        line_length = kHUDWidth

        line_start_point = om.MPoint(line_start_x, line_start_y)
        line_end_point = om.MPoint(line_start_x + line_length, line_start_y)

        drawManager.setColor(data.f_line_color)
        drawManager.line2d(line_start_point, line_end_point)


        return cursor_point

    def _draw_position_hud(self, drawManager, cursor_point, data):
        """
        """

        cursor_point.y -= kSectionBuffer
        cursor_point.x += kAxisLabelColWidth  # Shift to accomodate for right text alignment

        for i in data.f_axis_position_connections:
            axis_number = i + 1  # Robot axes are 1-indexed
            axis_key = 'A{}'.format(axis_number)

            cursor_point.y -= kRowHeight

            # Draw Axis Label
            drawManager.setFontWeight(kFontWeight)
            drawManager.setColor(data.f_text_color)            
            drawManager.text2d(cursor_point, axis_key, kAlignRight)

            # Draw limit markers
            axis_position_min = data.f_primary_axis_data[axis_key]['Min Position Limit']
            axis_position_max = data.f_primary_axis_data[axis_key]['Max Position Limit']

            pos_min_coeff = self._map_value(-360.0, 360.0, 0.0, 1.0, axis_position_min)
            pos_max_coeff = self._map_value(-360.0, 360.0, 0.0, 1.0, axis_position_max)
            
            min_marker_x = (cursor_point.x + kSectionBuffer) + (pos_min_coeff * kBarWidth)
            min_marker_y = cursor_point.y + 7

            min_marker_point = om.MPoint(min_marker_x, min_marker_y)

            drawManager.setColor(data.f_bar_color)
            drawManager.rect2d(min_marker_point, kUp, 2, 4, filled=data.f_is_filled)

            # Draw Position Bar
            axis_position = data.f_primary_axis_data[axis_key]['Position']
            scale = self._map_value(-360.0, 360.0, -kBarWidth/4., kBarWidth/4., axis_position)

            bar_pos_x = (cursor_point.x + kSectionBuffer + scale) + kBarWidth/2.0
            bar_pos_y = cursor_point.y + 7
            bar_pos_point = om.MPoint(bar_pos_x, bar_pos_y)

            drawManager.setColor(data.f_bar_color)
            drawManager.rect2d(bar_pos_point, kUp, scale, kBarHeight, filled=data.f_is_filled)


            # Draw axis position number readout
            cursor_point.x += kAxisLabelColWidth + kBarWidth - kBorderBuffer
            drawManager.setColor(data.f_text_color)
            drawManager.text2d(cursor_point, '{}'.format(axis_position), kAlignLeft)
            cursor_point.x -= kAxisLabelColWidth + kBarWidth - kBorderBuffer


        return cursor_point

    def _get_primary_axis_data(self, node, data):
        """
        """
        primary_axis_data = {}

        # Get primary axes positions and limits
        pos_plugs = om.MPlug(node, mimicHUDManager.a_axis_p)
        axis_position_indeces = pos_plugs.getExistingArrayAttributeIndices()

        min_pos_limits_plug = om.MPlug(node, mimicHUDManager.a_axis_p_min_limit)
        max_pos_limits_plug = om.MPlug(node, mimicHUDManager.a_axis_p_max_limit)

        if axis_position_indeces:
            axis_position_connections = []

            for i in axis_position_indeces:

                axis_i_plug = pos_plugs.elementByLogicalIndex(i)

                # Check if the plug still has a connection; if not, continue to the next one
                if not axis_i_plug.isConnected:
                    continue

                # If the plug has a connection, add its index to the list of axes
                axis_position_connections.append(i)

                # Initialize Axis-i data dict
                axis_number = i + 1  # Axes are 1-indexed
                axis_key = 'A{}'.format(axis_number)
                primary_axis_data[axis_key] = {}

                axis_i_position = round(axis_i_plug.asFloat(), 2)
                min_pos_limit = round(min_pos_limits_plug.elementByLogicalIndex(i).asFloat(), 2)
                max_pos_limit = round(max_pos_limits_plug.elementByLogicalIndex(i).asFloat(), 2)
                
                primary_axis_data[axis_key]['Position'] = axis_i_position
                primary_axis_data[axis_key]['Min Position Limit'] = min_pos_limit
                primary_axis_data[axis_key]['Max Position Limit'] = max_pos_limit


            data.f_primary_axis_data = primary_axis_data
            data.f_axis_position_connections = axis_position_connections

    def _map_value(self, input_min, input_max, output_min, output_max, raw_value):
        """
        """

        # If the value is outside the input range, clamp it to the input range
        val = self._clamp_value(raw_value, input_min, input_max)

        mapped_val = output_min + ((output_max - output_min) / (input_max - input_min)) * (val - input_min)

        return mapped_val

    def _clamp_value(self, value, min_value, max_value):
        """
        """
        return max(min(value, max_value), min_value)


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    try:
        plugin.registerNode("mimicHUDManager", mimicHUDManager.id, mimicHUDManager.creator, mimicHUDManager.initialize, om.MPxNode.kLocatorNode, mimicHUDManager.draw_db_classification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(mimicHUDManager.draw_db_classification, mimicHUDManager.draw_registrant_id, mimicHUDManagerDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise

def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.deregisterNode(mimicHUDManager.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise

    try:
        omr.MDrawRegistry.deregisterGeometryOverrideCreator(mimicHUDManager.draw_db_classification, mimicHUDManager.draw_registrant_id)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise

