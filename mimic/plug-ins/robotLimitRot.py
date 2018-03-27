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
kPluginNodeName = 'robotLimitRotation'    # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId( 0x87003 ) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class robotLimitRotation(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    JinAttr        = OpenMaya.MAngle()
    upperLimitAttr = OpenMaya.MAngle()
    lowerLimitAttr = OpenMaya.MAngle()
    ikAttr         = OpenMaya.MObject()

    # Outputs 
    JoutAttr = OpenMaya.MAngle()


    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
    
    ##################################################
        
    def compute(self, pPlug, pDataBlock):
                   
        ## Obtain the data handles for each attribute
        
        # Input Data Handles 
        JinDataHandle        = pDataBlock.inputValue( robotLimitRotation.JinAttr )
        upperLimitDataHandle = pDataBlock.inputValue( robotLimitRotation.upperLimitAttr )
        lowerLimitDataHandle = pDataBlock.inputValue( robotLimitRotation.lowerLimitAttr )
        ikDataHandle         = pDataBlock.inputValue( robotLimitRotation.ikAttr )
        
        # Output Data Handles 
        JoutDataHandle = pDataBlock.outputValue( robotLimitRotation.JoutAttr )


        ## Extract the actual value associated to our input attribute
        J_in       = JinDataHandle.asAngle().asDegrees()
        upperLimit = upperLimitDataHandle.asAngle().asDegrees()
        lowerLimit = lowerLimitDataHandle.asAngle().asDegrees()
        ik         = ikDataHandle.asBool()

        #===================================#
        #     Limit Rotation Solve Code     #                 
        #===================================#
        # If the input is greater than the robot's upper rotation limit, or
        # less than the robot's lower rotation limit, we flip the axis rotation
        # by 360 degrees to achieve a value that fits within the robots limits
        if ik:
            if J_in > upperLimit:
                J_out = J_in - 360
                if J_out < lowerLimit and ( abs(J_out - lowerLimit) > abs(J_in - upperLimit) ):
                    J_out = J_out + 360
            elif J_in < lowerLimit:
                J_out = J_in + 360
                if J_out > upperLimit and ( abs(J_out - upperLimit) > abs(J_in - lowerLimit) ):
                    J_out = J_out - 360
            else:
                J_out = J_in    
        
        else:
            J_out = J_in
           
                 

        # Set the Output Values
        Jout = JoutDataHandle.setMAngle( OpenMaya.MAngle( J_out , 2 ) )

            
        # Mark the output data handle as being clean; it need not be computed given its input.
        JoutDataHandle.setClean()

             

#========================================================#
#                 Plug-in initialization.                #
#========================================================#

def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a pointer.
    '''

    return  robotLimitRotation() 

def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our plug-in class.
    '''
    
    # The following function set will allow us to create our attributes.
    angleAttributeFn   = OpenMaya.MFnUnitAttribute()
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#

    robotLimitRotation.JinAttr = angleAttributeFn.create( 'jIn', 'jIn', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    robotLimitRotation.addAttribute( robotLimitRotation.JinAttr ) 
    
    ## Limits ##
    robotLimitRotation.limits = compoundAttributeFn.create( 'jointLimits', 'jointLimits' )
    
    robotLimitRotation.upperLimitAttr = angleAttributeFn.create( 'upperLimit', 'upperLimit', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotLimitRotation.upperLimitAttr ) 

    robotLimitRotation.lowerLimitAttr = angleAttributeFn.create( 'lowerLimit', 'lowerLimit', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotLimitRotation.lowerLimitAttr ) 

    robotLimitRotation.addAttribute( robotLimitRotation.limits ) 
    #----------#
        
    robotLimitRotation.ikAttr = numericAttributeFn.create( 'ik', 'ik', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    robotLimitRotation.addAttribute( robotLimitRotation.ikAttr )
    
    
    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#

    robotLimitRotation.JoutAttr = angleAttributeFn.create( 'jOut', 'jOut', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False 
    robotLimitRotation.addAttribute( robotLimitRotation.JoutAttr ) 



    
    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    robotLimitRotation.attributeAffects( robotLimitRotation.JinAttr, robotLimitRotation.JoutAttr   )
    robotLimitRotation.attributeAffects( robotLimitRotation.upperLimitAttr, robotLimitRotation.JoutAttr   )
    robotLimitRotation.attributeAffects( robotLimitRotation.lowerLimitAttr, robotLimitRotation.JoutAttr   )
    robotLimitRotation.attributeAffects( robotLimitRotation.ikAttr, robotLimitRotation.JoutAttr )
     


           
def initializePlugin( mobject ):
    '''
    Initialize the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin( mobject )
    try:
        mplugin.registerNode( kPluginNodeName, kPluginNodeId, nodeCreator,
                              nodeInitializer, OpenMaya.MPxNode.kDependNode, kPluginNodeClassify )
    except:
        sys.stderr.write( 'Failed to register node: ' + kPluginNodeName )
        raise
    
def uninitializePlugin( mobject ):
    '''
    Uninitializes the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin( mobject )
    try:
        mplugin.deregisterNode( kPluginNodeId )
    except:
        sys.stderr.write( 'Failed to deregister node: ' + kPluginNodeName )
        raise