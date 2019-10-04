'''
//**************************************************************************/
// Copyright (c) 2016 Autodesk, Inc.
// All rights reserved.
// 
// These coded instructions, statements, and computer programs contain
// unpublished proprietary information written by Autodesk, Inc., and are
// protected by Federal copyright law. They may not be disclosed to third
// parties or copied or duplicated in any form, in whole or in part, without
// the prior written consent of Autodesk, Inc.
'''

import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.cmds as cmds

# Using the Maya Python API 2.0.
def maya_useNewAPI():
    pass

class RenderOverrideOptions(om.MPxNode):
    kTypeId = om.MTypeId(0x00080088)
    kTypeName = "RenderOverrideOptions"

    # Attributes

    reflectionTint = om.MObject()
    enableReflections = om.MObject()
    blurReflections = om.MObject()
    reflectionRange = om.MObject()
    saturation = om.MObject()

    # Selector node output.
    #out = om.MObject()

    @staticmethod
    def creator():
        return RenderOverrideOptions()

    @staticmethod
    def initializer():

        stringData = om.MFnStringData().create('')
        attrFn = om.MFnTypedAttribute()
        numAttrFn = om.MFnNumericAttribute()
        numericData = om.MFnNumericData()

        # Add typeFilter attribute
        RenderOverrideOptions.enableReflections = numAttrFn.create("enableReflections", "ef", om.MFnNumericData.kBoolean)
        numAttrFn.default = True
        numAttrFn.storable = True
        numAttrFn.keyable = True
        numAttrFn.readable = True
        numAttrFn.writable = True
        numAttrFn.hidden = False
        om.MPxNode.addAttribute(RenderOverrideOptions.enableReflections)

        # Add typeFilter attribute
        RenderOverrideOptions.reflectionTint = numAttrFn.createColor("reflectionTint", "rt")
        numAttrFn.default = (0.3, 0.3, 0.3)
        numAttrFn.storable = True
        numAttrFn.keyable = True
        numAttrFn.readable = True
        numAttrFn.writable = True
        numAttrFn.hidden = False
        om.MPxNode.addAttribute(RenderOverrideOptions.reflectionTint)

        RenderOverrideOptions.saturation = numAttrFn.create("saturation", "sat", om.MFnNumericData.kFloat)
        numAttrFn.default = 1.0
        numAttrFn.storable = True
        numAttrFn.keyable = True
        numAttrFn.readable = True
        numAttrFn.writable = True
        numAttrFn.hidden = False
        om.MPxNode.addAttribute(RenderOverrideOptions.saturation)

        RenderOverrideOptions.blurReflections = numAttrFn.create("blurReflections", "br", om.MFnNumericData.kBoolean)
        numAttrFn.default = True
        numAttrFn.storable = True
        numAttrFn.keyable = True
        numAttrFn.readable = True
        numAttrFn.writable = True
        numAttrFn.hidden = False
        om.MPxNode.addAttribute(RenderOverrideOptions.blurReflections)

        RenderOverrideOptions.reflectionRange = numAttrFn.create("reflectionRange", "rr", om.MFnNumericData.k2Float)
        numAttrFn.default = (0.0, 100.0)
        numAttrFn.storable = True
        numAttrFn.keyable = True
        numAttrFn.readable = True
        numAttrFn.writable = True
        numAttrFn.hidden = False
        om.MPxNode.addAttribute(RenderOverrideOptions.reflectionRange)

    def __init__(self):
        super(RenderOverrideOptions, self).__init__()

    def postConstructor(self):

        # Add the callback
        om.MNodeMessage.addAttributeChangedCallback(self.thisMObject(), RenderOverrideOptions.attrChangedCB, self)

    @staticmethod
    def attrChangedCB(msg, plg, otherPlug, self):
        cmds.refresh()

def _selectPlug(name):
    sl = om.MSelectionList()
    try:
        sl.add(name)
    except RuntimeError:
        # not found
        return None
    plg = sl.getPlug(0)

    if plg.isElement and name.find('[') == -1:
        # Hack because MSelectionList returns a plug over the first element of
        # a array of plug when no logical index is given
        return None
    return plg

def nameToNode(name):
    """Returns the MObject matching given name or None if not found.
       Raises RuntimeError if name is ambiguous."""
    plg = _selectPlug(name + ".message")
    return plg.node() if plg else None

def getFloat4PlugValue(plug):
    object = plug.asMObject()
    numDataFn = om.MFnNumericData( object )
    return numDataFn.getData( )

def getFloat3PlugValue(plug):
    object = plug.asMObject()
    numDataFn = om.MFnNumericData( object )
    return numDataFn.getData( )

def getFloat2PlugValue(plug):
    object = plug.asMObject()
    numDataFn = om.MFnNumericData( object )
    return numDataFn.getData( )

def getBoolPlugValue(plug):
    return plug.asBool()

def getFloatPlugValue(plug):
    return plug.asFloat()

def getIntPlugValue(plug):
    return plug.asInt()

class FragmentSceneRender(omr.MSceneRender):
    def __init__(self, name):
        super(FragmentSceneRender, self).__init__(name, "GroundReflections")

    def preSceneRender(self, context):
        params = self.getParameters()
        if params is None:
            return

        # Find the options node
        optionsNodeName = 'groundReflectionOptions'
        optionObj = nameToNode(optionsNodeName)
        if optionObj is None:
            optionObj = nameToNode(cmds.createNode(RenderOverrideOptions.kTypeName, name=optionsNodeName, skipSelect=True))

        if optionObj is not None:
            # set the fragment's enabled input
            optionPlug = om.MPlug(optionObj, RenderOverrideOptions.enableReflections)
            if optionPlug is not None:
                enabled = getBoolPlugValue(optionPlug)
                params.setParameter('EnableReflection', enabled)

            # set the fragment's blur input
            optionPlug = om.MPlug(optionObj, RenderOverrideOptions.blurReflections)
            if optionPlug is not None:
                blur = getBoolPlugValue(optionPlug)
                if blur:
                    params.setParameter('BlurType', 3)
                else:
                    params.setParameter('BlurType', 0)
            
            # set the fragment composite color
            optionPlug = om.MPlug(optionObj, RenderOverrideOptions.reflectionTint)
            if optionPlug is not None:
                color = getFloat3PlugValue(optionPlug)
                params.setParameter('Color', color)

            # set the fragment saturation
            optionPlug = om.MPlug(optionObj, RenderOverrideOptions.saturation)
            if optionPlug is not None:
                val = getFloatPlugValue(optionPlug)
                params.setParameter('Saturation', val)

            # set the reflection range
            optionPlug = om.MPlug(optionObj, RenderOverrideOptions.reflectionRange)
            if optionPlug is not None:
                val = getFloat2PlugValue(optionPlug)
                params.setParameter('DistanceRange', val)

class FragmentRenderOverride(omr.MRenderOverride):

    def __init__(self, name):
        self.operatioIndex = 0
        self.operations =  [FragmentSceneRender("sceneAndGroundReflections"),
                           omr.MHUDRender(),
                           omr.MPresentTarget("present")]

        # set the clear op to use the settings from Maya and disable the clear op embeded in the scene render.
        self.operations[0].clearOperation().setOverridesColors(False)

        super(FragmentRenderOverride, self).__init__(name)

    def uiName(self):
        return 'Ground Reflections'

    def setup(self, destination):
        super(FragmentRenderOverride, self).setup(destination)

    def cleanup(self):
        super(FragmentRenderOverride, self).cleanup()

    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices

    def startOperationIterator(self):
        self.operationIndex = 0
        return True

    def renderOperation(self):
        return self.operations[self.operationIndex]

    def nextRenderOperation(self):
        self.operationIndex += 1
        return self.operationIndex < len(self.operations)

# global instance of this override.
fragmentRenderer = None

def initializePlugin(mobject):
    # NOTICE:  Please set the path to the plugin before running
    pathToPlugin = './'

    omr.MRenderer.getShaderManager().addShaderPath(pathToPlugin + "Shaders/OGSFX")
    omr.MRenderer.getShaderManager().addShaderPath(pathToPlugin + "Shaders/HLSL")
    omr.MRenderer.getShaderManager().addShaderPath(pathToPlugin + "Shaders/Cg")

    omr.MRenderer.getFragmentManager().addFragmentPath(pathToPlugin + "ScriptFragment")
    omr.MRenderer.getFragmentManager().addFragmentGraphFromFile("GroundReflections.xml")

    plugin = om.MFnPlugin(mobject, "Autodesk", "3.0", "Any")
    plugin.registerNode(RenderOverrideOptions.kTypeName, RenderOverrideOptions.kTypeId, RenderOverrideOptions.creator, RenderOverrideOptions.initializer)

    global fragmentRenderer
    fragmentRenderer = FragmentRenderOverride('GroundReflectionsOverride')
    omr.MRenderer.registerOverride(fragmentRenderer)

def uninitializePlugin(mobject):
    global fragmentRenderer
    plugin = om.MFnPlugin(mobject)
    try:
        plugin.deregisterNode(apiMeshCreator.id)
        omr.MRenderer.unregisterOverride(fragmentRenderer)
        fragmentRenderer = None
    except:
        sys.stderr.write("Failed to deregister node\n")
        pass



