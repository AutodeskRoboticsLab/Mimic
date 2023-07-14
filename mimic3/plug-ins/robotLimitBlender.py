#!usr/bin/env python

"""
Dependency Graph plug-in that allows the physical rotational limits of the
robot rig to be taken into account when performing an Inverse Kinematic solve.
"""

import sys
import maya.api.OpenMaya as OpenMaya
import math


def maya_useNewAPI():
	"""
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
	"""
	pass


# Plug-in information:
kPluginNodeName = 'robotLimitBlender'  # The name of the node.
kPluginNodeClassify = 'utility/general'  # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId(0x87000) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class robotLimitBlender(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    value_in_attr = OpenMaya.MAngle()
    upper_limit_attr = OpenMaya.MAngle()
    lower_limit_attr = OpenMaya.MAngle()
    
    shader_range_attr = OpenMaya.MObject()

    # Outputs 
    blend_attr = OpenMaya.MAngle()


    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
    
    ##################################################
        
    def compute(self, pPlug, pDataBlock):
        
        if pPlug == robotLimitBlender.blend_attr:         
            ## Obtain the data handles for each attribute
            
            # Input Data Handles 
            value_in_data_handle = pDataBlock.inputValue(robotLimitBlender.value_in_attr)
            upper_limit_data_handle = pDataBlock.inputValue(robotLimitBlender.upper_limit_attr)
            lower_limit_data_handle = pDataBlock.inputValue(robotLimitBlender.lower_limit_attr)
            shader_range_data_handle = pDataBlock.inputValue(robotLimitBlender.shader_range_attr)
            
            # Output Data Handles 
            blend_data_handle = pDataBlock.outputValue( robotLimitBlender.blend_attr )


            ## Extract the actual value associated to our input attribute
            value_in = value_in_data_handle.asAngle().asDegrees()
            upper_limit = upper_limit_data_handle.asAngle().asDegrees()
            lower_limit = lower_limit_data_handle.asAngle().asDegrees()
            shader_range = shader_range_data_handle.asFloat()

            #==================================#
            #     Limit Blender Solve Code     #                 
            #==================================#
            upper_threshold = upper_limit - shader_range
            lower_threshold = lower_limit + shader_range

            if value_in >= upper_threshold:
                # If the value exceeds the upper limit,
                # clamp the value to the upper limit
                value = max(min(value_in, upper_limit), upper_threshold)

                # Remap the value between 0 and 1
                blend = (1.0 / (upper_limit - upper_threshold)) * (value - upper_threshold)

            elif value_in <= lower_threshold:
                # If the value exceeds the lower limit,
                # clamp the value to the lower limit
                value = min(max(value_in, lower_limit), lower_threshold)

                # Remap the value between 0 and 1
                blend = (1.0 / (lower_limit - lower_threshold)) * (value - lower_threshold)

            else:
                blend = 0


            # Set the Output Values
            blend_data_handle.setFloat(blend)

                
            # Mark the output data handle as being clean; it need not be computed given its input.
            blend_data_handle.setClean()



#========================================================#
#                 Plug-in initialization.                #
#========================================================#

def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a pointer.
    '''

    return  robotLimitBlender() 

def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our plug-in class.
    '''
    
    # The following function set will allow us to create our attributes.
    angleAttributeFn = OpenMaya.MFnUnitAttribute()
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#

    robotLimitBlender.value_in_attr = angleAttributeFn.create('value', 'value', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    robotLimitBlender.addAttribute(robotLimitBlender.value_in_attr)
    
    ## Limits ##
    robotLimitBlender.limits = compoundAttributeFn.create('axisLimits', 'axisLimits')
    
    robotLimitBlender.upper_limit_attr = angleAttributeFn.create('upperLimit','upperLimit', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotLimitBlender.upper_limit_attr) 

    robotLimitBlender.lower_limit_attr = angleAttributeFn.create('lowerLimit', 'lowerLimit', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotLimitBlender.lower_limit_attr) 

    robotLimitBlender.addAttribute(robotLimitBlender.limits) 
    #----------#
        
    robotLimitBlender.shader_range_attr = numericAttributeFn.create('shaderRange', 'shaderRange', OpenMaya.MFnNumericData.kFloat, 20.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    robotLimitBlender.addAttribute(robotLimitBlender.shader_range_attr)
    
    
    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#

    robotLimitBlender.blend_attr = numericAttributeFn.create('blend', 'blend', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False 
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True 
    numericAttributeFn.hidden = False 
    robotLimitBlender.addAttribute(robotLimitBlender.blend_attr) 


    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    robotLimitBlender.attributeAffects(robotLimitBlender.value_in_attr, robotLimitBlender.blend_attr)
    robotLimitBlender.attributeAffects(robotLimitBlender.upper_limit_attr, robotLimitBlender.blend_attr)
    robotLimitBlender.attributeAffects(robotLimitBlender.lower_limit_attr, robotLimitBlender.blend_attr)
    robotLimitBlender.attributeAffects(robotLimitBlender.shader_range_attr, robotLimitBlender.blend_attr)
    
           
def initializePlugin(mobject):
    '''
    Initialize the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kPluginNodeName, kPluginNodeId, nodeCreator,
                             nodeInitializer, OpenMaya.MPxNode.kDependNode, kPluginNodeClassify)
    except:
        sys.stderr.write('Failed to register node: ' + kPluginNodeName)
        raise
    
def uninitializePlugin(mobject):
    '''
    Uninitializes the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write('Failed to deregister node: ' + kPluginNodeName)
        raise