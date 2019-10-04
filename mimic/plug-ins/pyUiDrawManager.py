#-
# ===========================================================================
# Copyright 2015 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
#+

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

kText = 0
kLine = 1
kPoint = 2
kRect = 3
kQuad = 4
kSphere = 5
kCircle = 6
kArc = 7

class uiDrawManager(omui.MPxLocatorNode):
    id = om.MTypeId(0x0008002A)
    drawDbClassification = "drawdb/geometry/uiDrawManager"
    drawRegistrantId = "uiDrawManagerPlugin"

    ## ui type attribute
    aUIType = None
    aSelectability = None

    ## color
    aPrimitiveColor = None
    aPrimitiveTransparency = None

    ## line width and line style attributes
    aLineWidth = None
    aLineStyle = None

    ## fill attribute
    aIsFilled = None

    ## radius attribute
    aRadius = None

    ## 2D attributes
    aDraw2D = None
    aPosition = None

    ## Text attributes
    aTextAlignment = None
    eTextIncline = None
    aTextWeight = None
    aTextStretch = None
    aTextLine = None
    aTextBoxSize = None
    aText = None
    aTextBoxColor = None
    aTextBoxTransparency = None
    aTextFontSize = None
    aFontFaceName = None

    ## point attributes
    aPointSize = None

    ## line attributes
    aLineStartPoint = None
    aLineEndPoint = None

    ## rect attributes
    aRectUp = None
    aRectNormal = None
    aRectScale = None

    ## quad attributes
    aQuadVertex = [None, None, None, None]

    ## circle attributes
    aCircleNormal = None

    ## arc attributes
    aArcStart = None
    aArcEnd = None
    aArcNormal = None

    fFontList = None

    def __init__(self):
        omui.MPxLocatorNode.__init__(self)

    @staticmethod
    def creator():
        return uiDrawManager()

    @staticmethod
    def initialize():
        nAttr = om.MFnNumericAttribute()
        eAttr = om.MFnEnumAttribute()
        typedAttr = om.MFnTypedAttribute()

        ## Add ui type attribute
        uiDrawManager.aUIType = eAttr.create("uiType", "ut", kText)
        eAttr.addField("text", kText)
        eAttr.addField("line", kLine)
        eAttr.addField("point", kPoint)
        eAttr.addField("rect", kRect)
        eAttr.addField("quad", kQuad)
        eAttr.addField("sphere", kSphere)
        eAttr.addField("circle", kCircle)
        eAttr.addField("arc", kArc)
        om.MPxNode.addAttribute(uiDrawManager.aUIType)

        ## Add selectability
        uiDrawManager.aSelectability = eAttr.create("selectability", "st", omr.MUIDrawManager.kAutomatic)
        eAttr.addField("Unselectable", omr.MUIDrawManager.kNonSelectable)
        eAttr.addField("Selectable", omr.MUIDrawManager.kSelectable)
        eAttr.addField("Automatic", omr.MUIDrawManager.kAutomatic)
        om.MPxNode.addAttribute(uiDrawManager.aSelectability)

        ## Add color attribute
        uiDrawManager.aPrimitiveColor = nAttr.create("primitiveColor", "pc", om.MFnNumericData.k3Float)
        nAttr.default = (1.0, 0.0, 0.0)
        nAttr.usedAsColor = True
        om.MPxNode.addAttribute(uiDrawManager.aPrimitiveColor)

        ## Add transparency attribute
        uiDrawManager.aPrimitiveTransparency = nAttr.create("primitiveTransparency", "pt", om.MFnNumericData.kFloat, 0.0)
        nAttr.setSoftMin(0.0)
        nAttr.setSoftMax(1.0)
        om.MPxNode.addAttribute(uiDrawManager.aPrimitiveTransparency)

        ## add line width and line style attributes
        uiDrawManager.aLineWidth = nAttr.create("lineWidth", "lw", om.MFnNumericData.kFloat, 2.0)
        om.MPxNode.addAttribute(uiDrawManager.aLineWidth)

        uiDrawManager.aLineStyle = eAttr.create("lineStyle", "ls", omr.MUIDrawManager.kSolid)
        eAttr.addField("solid", omr.MUIDrawManager.kSolid)
        eAttr.addField("shortdotted", omr.MUIDrawManager.kShortDotted)
        eAttr.addField("shortdashed", omr.MUIDrawManager.kShortDashed)
        eAttr.addField("dashed", omr.MUIDrawManager.kDashed)
        eAttr.addField("dotted", omr.MUIDrawManager.kDotted)
        om.MPxNode.addAttribute(uiDrawManager.aLineStyle)

        ## Add filled attribute
        uiDrawManager.aIsFilled = nAttr.create("isFilled", "if", om.MFnNumericData.kBoolean, 0)
        om.MPxNode.addAttribute(uiDrawManager.aIsFilled)

        ## Add radius attribute
        uiDrawManager.aRadius = nAttr.create("radius", "ra", om.MFnNumericData.kDouble, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aRadius)

        ## add 2D attributes
        uiDrawManager.aDraw2D = nAttr.create("draw2D", "d2", om.MFnNumericData.kBoolean, 0)
        om.MPxNode.addAttribute(uiDrawManager.aDraw2D)

        uiDrawManager.aPosition = nAttr.create("position", "pos", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 0.0, 0.001)
        om.MPxNode.addAttribute(uiDrawManager.aPosition)

        ## Add text attributes.
        stringFn = om.MFnStringData()
        defaultText = stringFn.create("uiDrawManager-Text")
        uiDrawManager.aText = typedAttr.create("text", "t", om.MFnData.kString, defaultText)
        om.MPxNode.addAttribute(uiDrawManager.aText)

        uiDrawManager.aTextFontSize = nAttr.create("textFontSize", "tfs", om.MFnNumericData.kInt, omr.MUIDrawManager.kDefaultFontSize)
        nAttr.setMin(-1)
        nAttr.setMax(99)
        om.MPxNode.addAttribute(uiDrawManager.aTextFontSize)

        uiDrawManager.fFontList = omr.MUIDrawManager.getFontList()
        if len(uiDrawManager.fFontList) == 0:
            sys.stderr.write("No font available!\n")

        uiDrawManager.aFontFaceName = eAttr.create("fontFaceName", "ffn", 0)
        for i in range(len(uiDrawManager.fFontList)):
            faceName = uiDrawManager.fFontList[i]
            eAttr.addField(faceName, i)
        om.MPxNode.addAttribute(uiDrawManager.aFontFaceName)

        uiDrawManager.aTextAlignment = eAttr.create("textAlignment", "ta", omr.MUIDrawManager.kLeft)
        eAttr.addField("left", omr.MUIDrawManager.kLeft)
        eAttr.addField("center", omr.MUIDrawManager.kCenter)
        eAttr.addField("right", omr.MUIDrawManager.kRight)
        om.MPxNode.addAttribute(uiDrawManager.aTextAlignment)

        uiDrawManager.eTextIncline = eAttr.create("textIncline", "tic", omr.MUIDrawManager.kInclineNormal)
        eAttr.addField("normal", omr.MUIDrawManager.kInclineNormal)
        eAttr.addField("italic", omr.MUIDrawManager.kInclineItalic)
        om.MPxNode.addAttribute(uiDrawManager.eTextIncline)

        uiDrawManager.aTextWeight = eAttr.create("textWeight", "tw", omr.MUIDrawManager.kWeightBold)
        eAttr.addField("light", omr.MUIDrawManager.kWeightLight)
        eAttr.addField("bold", omr.MUIDrawManager.kWeightBold)
        om.MPxNode.addAttribute(uiDrawManager.aTextWeight)

        uiDrawManager.aTextStretch = nAttr.create("textStretch", "ts", om.MFnNumericData.kInt, omr.MUIDrawManager.kStretchUnstretched)
        nAttr.setMin(50)
        nAttr.setMax(200)
        om.MPxNode.addAttribute(uiDrawManager.aTextStretch)

        uiDrawManager.aTextLine = eAttr.create("textLine", "tl", 0)
        eAttr.addField("none", 0)
        eAttr.addField("overline", omr.MUIDrawManager.kLineOverline)
        eAttr.addField("underline", omr.MUIDrawManager.kLineUnderline)
        eAttr.addField("strikeout", omr.MUIDrawManager.kLineStrikeoutLine)
        om.MPxNode.addAttribute(uiDrawManager.aTextLine)

        uiDrawManager.aTextBoxSize = nAttr.create("textBoxSize", "tbs", om.MFnNumericData.k2Int)
        nAttr.default = (0, 0)
        om.MPxNode.addAttribute(uiDrawManager.aTextBoxSize)

        uiDrawManager.aTextBoxColor = nAttr.create("textBoxColor", "tbc", om.MFnNumericData.k3Float)
        nAttr.default = (0.0, 1.0, 1.0)
        nAttr.usedAsColor = True
        om.MPxNode.addAttribute(uiDrawManager.aTextBoxColor)

        uiDrawManager.aTextBoxTransparency = nAttr.create("textBoxTransparency", "tbt", om.MFnNumericData.kFloat, 0.0)
        nAttr.setSoftMin(0.0)
        nAttr.setSoftMax(1.0)
        om.MPxNode.addAttribute(uiDrawManager.aTextBoxTransparency)

        ## add point attributes
        uiDrawManager.aPointSize = nAttr.create("pointSize", "ps", om.MFnNumericData.kFloat, 2.0)
        om.MPxNode.addAttribute(uiDrawManager.aPointSize)

        ## add line attributes
        uiDrawManager.aLineStartPoint = nAttr.create("lineStartPoint", "lsp", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 0.0, 0.0)
        om.MPxNode.addAttribute(uiDrawManager.aLineStartPoint)

        uiDrawManager.aLineEndPoint = nAttr.create("lineEndPoint", "lep", om.MFnNumericData.k3Double)
        nAttr.default = (1.0, 1.0, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aLineEndPoint)

        ## add rect attributes
        uiDrawManager.aRectUp = nAttr.create("rectUp", "ru", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 1.0, 0.0)
        om.MPxNode.addAttribute(uiDrawManager.aRectUp)

        uiDrawManager.aRectNormal = nAttr.create("rectNormal", "rn", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 0.0, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aRectNormal)

        uiDrawManager.aRectScale = nAttr.create("rectScale", "rs", om.MFnNumericData.k2Double)
        nAttr.default = (1.0, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aRectScale)

        ## add quad attributes
        defaultPosition = [ (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0) ]
        for i in range(4):
            fullName = "quadVertex" + str(i)
            shortName = "qv" + str(i)
            uiDrawManager.aQuadVertex[i] = nAttr.create(fullName, shortName, om.MFnNumericData.k3Double)
            nAttr.default = defaultPosition[i]
            om.MPxNode.addAttribute(uiDrawManager.aQuadVertex[i])

        ## add circle attributes
        uiDrawManager.aCircleNormal = nAttr.create("circleNormal", "cn", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 0.0, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aCircleNormal)

        ## add arc attributes
        uiDrawManager.aArcStart = nAttr.create("arcStartVector", "asv", om.MFnNumericData.k3Double)
        nAttr.default = (1.0, 0.0, 0.0)
        om.MPxNode.addAttribute(uiDrawManager.aArcStart)

        uiDrawManager.aArcEnd = nAttr.create("arcEndVector", "aev", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 1.0, 0.0)
        om.MPxNode.addAttribute(uiDrawManager.aArcEnd)

        uiDrawManager.aArcNormal = nAttr.create("arcNormal", "an", om.MFnNumericData.k3Double)
        nAttr.default = (0.0, 0.0, 1.0)
        om.MPxNode.addAttribute(uiDrawManager.aArcNormal)


##---------------------------------------------------------------------------
##---------------------------------------------------------------------------
## Viewport 2.0 override implementation
##---------------------------------------------------------------------------
##---------------------------------------------------------------------------
class uiDrawManagerData(om.MUserData):
    def __init__(self):
        om.MUserData.__init__(self, False)
        self.fUIType = kText
        self.fSelectability = omr.MUIDrawManager.kAutomatic
        self.fColor = om.MColor((1., 0., 0., 1.))
        self.fLineWidth = 2
        self.fLineStyle = omr.MUIDrawManager.kSolid
        self.fIsFilled = False
        self.fRadius = 1.
        self.fDraw2D = False
        self.fPosition = om.MPoint(0.0, 0.0, 0.001)
        # text
        self.fText = "uiDrawManager-Text"
        self.fTextFontSize = omr.MUIDrawManager.kDefaultFontSize
        self.fFontFaceIndex = 0
        self.fTextAlignment = omr.MUIDrawManager.kLeft
        self.fTextIncline = omr.MUIDrawManager.kInclineNormal
        self.fTextWeight = omr.MUIDrawManager.kWeightBold
        self.fTextStretch = omr.MUIDrawManager.kStretchUnstretched
        self.fTextLine = 0
        self.fTextBoxSize = [0, 0]
        self.fTextBoxColor = om.MColor((0., 1., 1., 1.))
        # point
        self.fPointSize = 2.
        # line
        self.fLineStartPoint = om.MPoint(0.0, 0.0, 0.0)
        self.fLineEndPoint = om.MPoint(1.0, 1.0, 1.0)
        # rect
        self.fRectUp = om.MVector(0.0, 1.0, 0.0)
        self.fRectNormal = om.MVector(0.0, 0.0, 1.0)
        self.fRectScale = [1., 1.]
        # quad
        self.fQuadVertex = [ om.MPoint(0.0, 0.0, 0.0), om.MPoint(1.0, 0.0, 0.0), om.MPoint(1.0, 1.0, 0.0), om.MPoint(0.0, 1.0, 0.0) ]
        # circle
        self.fCircleNormal = om.MVector(0.0, 0.0, 1.0)
        # arc
        self.fArcStart = om.MVector(1.0, 0.0, 0.0)
        self.fArcEnd = om.MVector(0.0, 1.0, 0.0)
        self.fArcNormal = om.MVector(0.0, 0.0, 1.0)


################################################################################################
class uiDrawManagerDrawOverride(omr.MPxDrawOverride):
    def __init__(self, obj):
        omr.MPxDrawOverride.__init__(self, obj, None)

    @staticmethod
    def creator(obj):
        return uiDrawManagerDrawOverride(obj)

    def supportedDrawAPIs(self):
        return (omr.MRenderer.kOpenGL | omr.MRenderer.kDirectX11 | omr.MRenderer.kOpenGLCoreProfile)

    def isBounded(self, objPath, cameraPath):
        return False

    def boundingBox(self, objPath, cameraPath):
        return om.MBoundingBox()

    def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
        data = oldData
        if not isinstance(data, uiDrawManagerData):
            data = uiDrawManagerData()

        uiDrawManagerNode = objPath.node()
        if uiDrawManagerNode.isNull():
            return

        ## retrieve uiType
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aUIType)
        data.fUIType = plug.asShort()

        ## common attributes
        ## retrieve selectability
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aSelectability)
        data.fSelectability = plug.asShort()

        ## retrieve color
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aPrimitiveColor)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.fColor = om.MColor(nData.getData())

        ## retrieve transparency
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aPrimitiveTransparency)
        data.fColor.a = 1.0 - plug.asFloat()

        ## retrieve line width
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aLineWidth)
        data.fLineWidth = plug.asFloat()

        ## retrieve line style
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aLineStyle)
        data.fLineStyle = plug.asShort()

        ## retrieve filled flag
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aIsFilled)
        data.fIsFilled = plug.asBool()

        ## retrieve radius
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aRadius)
        data.fRadius = plug.asDouble()

        ## retrieve 2D flag
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aDraw2D)
        data.fDraw2D = plug.asBool()

        ## retrieve screen position
        plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aPosition)
        o = plug.asMObject()
        nData = om.MFnNumericData(o)
        data.fPosition = om.MPoint(nData.getData())
        data.fPosition.w = 1.0

        if data.fUIType == kText:
            ## retrieve text
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aText)
            data.fText = plug.asString()

            ## retrieve text font size
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextFontSize)
            data.fTextFontSize = max(plug.asInt(), 0)

            ## retrieve font face index
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aFontFaceName)
            data.fFontFaceIndex = plug.asInt()

            ## retrieve text alignment
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextAlignment)
            data.fTextAlignment = plug.asShort()

            ## retrieve text incline
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.eTextIncline)
            data.fTextIncline = plug.asInt()

            ## retrieve text weight
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextWeight)
            data.fTextWeight = plug.asInt()

            ## retrieve text stretch
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextStretch)
            data.fTextStretch = plug.asInt()

            ## retrieve text line
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextLine)
            data.fTextLine = plug.asInt()

            ## retrieve text box size
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextBoxSize)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fTextBoxSize = nData.getData()

            ## retrieve text box color
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextBoxColor)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fTextBoxColor = om.MColor(nData.getData())

            ## retrieve text box transparency
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aTextBoxTransparency)
            data.fTextBoxColor.a = 1.0 - plug.asFloat()

        elif data.fUIType == kPoint:
            ## retrieve point size
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aPointSize)
            data.fPointSize = plug.asFloat()

        elif data.fUIType == kLine:
            ## retrieve line start point
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aLineStartPoint)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fLineStartPoint = om.MPoint(nData.getData())
            data.fLineStartPoint.w = 1.0

            ## retrieve line end point
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aLineEndPoint)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fLineEndPoint = om.MPoint(nData.getData())
            data.fLineEndPoint.w = 1.0

        elif data.fUIType == kRect:
            ## retrieve rect up vector
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aRectUp)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fRectUp = om.MVector(nData.getData())

            ## retrieve rect normal vector
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aRectNormal)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fRectNormal = om.MVector(nData.getData())

            ## retrieve rect scale
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aRectScale)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fRectScale = nData.getData()

        elif data.fUIType == kQuad:
            ## retrieve quad vertices
            for i in range(4):
                plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aQuadVertex[i])
                o = plug.asMObject()
                nData = om.MFnNumericData(o)
                data.fQuadVertex[i] = om.MPoint(nData.getData())

        elif data.fUIType == kCircle:
            ## retrieve circle normal
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aCircleNormal)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fCircleNormal = om.MVector(nData.getData())

        elif data.fUIType == kArc:
            ## retrieve arc start vector
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aArcStart)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fArcStart = om.MVector(nData.getData())

            ## retrieve arc end vector
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aArcEnd)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fArcEnd = om.MVector(nData.getData())

            ## retrieve arc normal
            plug = om.MPlug(uiDrawManagerNode, uiDrawManager.aArcNormal)
            o = plug.asMObject()
            nData = om.MFnNumericData(o)
            data.fArcNormal = om.MVector(nData.getData())

        elif data.fUIType == kSphere:
            pass

        else:
            sys.stderr.write("unhandled ui type.\n")

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        if not isinstance(data, uiDrawManagerData):
            return

        if data.fUIType == kText:
            ## Draw a text "uiDrawManager"
            ## All drawing operations must take place between calls to beginDrawable()
            ## and endDrawable().
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setFontSize(data.fTextFontSize)
            drawManager.setFontIncline(data.fTextIncline)
            drawManager.setFontWeight(data.fTextWeight)
            drawManager.setFontStretch(data.fTextStretch)
            drawManager.setFontLine(data.fTextLine)

            faceName = uiDrawManager.fFontList[data.fFontFaceIndex]
            drawManager.setFontName(faceName)

            boxSize = data.fTextBoxSize
            if boxSize[0] + boxSize[1] == 0:
                boxSize = None

            if data.fDraw2D:
                ## uiDrawManagerData::fPosition gives a screen space position
                ## where 2D UI item is located.
                drawManager.text2d(data.fPosition, data.fText, data.fTextAlignment, boxSize, data.fTextBoxColor, False)
                scale = 100
                pos = om.MPoint(50., 0.0)  ## Position of the text
                up = om.MVector(0.0, 1, 0.0)  ## Position of the text
                drawManager.rect2d(pos, up, scale, 10, filled=True)         
            else:
                ## for 3D items, place it at the origin of the world space.
                drawManager.text(data.fPosition, data.fText, data.fTextAlignment, boxSize, data.fTextBoxColor, False)

            drawManager.endDrawable()

        elif data.fUIType == kLine:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            if data.fDraw2D:
                drawManager.line2d(data.fLineStartPoint, data.fLineEndPoint)

            else:
                drawManager.line(data.fLineStartPoint, data.fLineEndPoint)

            drawManager.endDrawable()

        elif data.fUIType == kPoint:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setPointSize(data.fPointSize)

            if data.fDraw2D:
                drawManager.point2d(data.fPosition)

            else:
                drawManager.point(data.fPosition)

            drawManager.endDrawable()

        elif data.fUIType == kRect:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            if data.fDraw2D:
                ## For 2d rectangle, an up vector in screen space is used to determine its X
                ## and Y directions. In addition, "fRectScale" (in pixels)
                ## specify the half-lengths of the 2d rectangle.
                drawManager.rect2d(data.fPosition, data.fRectUp, data.fRectScale[0], data.fRectScale[1], data.fIsFilled)

            else:
                ## For 3d rectangle, the up vector should not be parallel with the normal vector.
                drawManager.rect(data.fPosition, data.fRectUp, data.fRectNormal, data.fRectScale[0], data.fRectScale[1], data.fIsFilled)

            drawManager.endDrawable()

        elif data.fUIType == kQuad:
            pass
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            ## prepare primitive type
            mode = omr.MUIDrawManager.kClosedLine
            if data.fIsFilled:
                mode = omr.MUIDrawManager.kTriStrip

            ## prepare position list and index
            position = om.MPointArray()
            index = om.MUintArray()
            for i in range(4):
                position.append(data.fQuadVertex[i])
                index.append(i)

            if not data.fIsFilled:
                index = None

            ## draw mesh
            if data.fDraw2D:
                drawManager.mesh2d(mode, position, None, index)

            else:
                drawManager.mesh(mode, position, None, None, index)

            drawManager.endDrawable()

        elif data.fUIType == kSphere:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            drawManager.sphere(data.fPosition, data.fRadius, data.fIsFilled)

            drawManager.endDrawable()

        elif data.fUIType == kCircle:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            if data.fDraw2D:
                ## The radius in specified as pixel unit for 2d items.
                drawManager.circle2d(data.fPosition, data.fRadius, data.fIsFilled)

            else:
                drawManager.circle(data.fPosition, data.fCircleNormal, data.fRadius, data.fIsFilled)

            drawManager.endDrawable()

        elif data.fUIType == kArc:
            drawManager.beginDrawable(data.fSelectability)

            drawManager.setColor(data.fColor)
            drawManager.setLineWidth(data.fLineWidth)
            drawManager.setLineStyle(data.fLineStyle)

            if data.fDraw2D:
                ## If 2d, the range of the arc is defined by the start and end vectors
                ## specified in screen space.
                drawManager.arc2d(data.fPosition, data.fArcStart, data.fArcEnd, data.fRadius, data.fIsFilled)

            else:
                ## For 3d arc, the projections of the start and end vectors onto the arc plane(
                ## determined by the normal vector) determine the range of the arc.
                drawManager.arc(data.fPosition, data.fArcStart, data.fArcEnd, data.fArcNormal, data.fRadius, data.fIsFilled)

            drawManager.endDrawable()

        else:
            sys.stderr.write("unhandled ui type.\n")


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    try:
        plugin.registerNode("uiDrawManager", uiDrawManager.id, uiDrawManager.creator, uiDrawManager.initialize, om.MPxNode.kLocatorNode, uiDrawManager.drawDbClassification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(uiDrawManager.drawDbClassification, uiDrawManager.drawRegistrantId, uiDrawManagerDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise

def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.deregisterNode(uiDrawManager.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise

    try:
        omr.MDrawRegistry.deregisterGeometryOverrideCreator(uiDrawManager.drawDbClassification, uiDrawManager.drawRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise

