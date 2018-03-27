#!usr/bin/env python

"""
Dependency Graph plug-in that enables the IK solver to evaluate axis angles
beyond +/- 180 degrees

This function creates a cycle in the Dependency Graph, which is not best
practice; however, it is the best way to ensure accurate rotation in robot
axis beyond the limits of the Inverse Kinematic solver
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
kPluginNodeName = 'robotAccumulateRotation'    # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId( 0x87002 ) # A unique ID associated to this node type.    

# This class name must match kPluginNodeName above
class robotAccumRotation(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    J0Attr    = OpenMaya.MAngle()
    JinAttr   = OpenMaya.MAngle()
    JflipAttr = OpenMaya.MObject()
    ikAttr    = OpenMaya.MObject()

    # Outputs 
    JoutAttr = OpenMaya.MAngle()
    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
    
    # Main compute method
    def compute(self, pPlug, pDataBlock):
                   
        ## Obtain the data handles for each attribute
        
        # Input Data Handles 
        J0DataHandle    = pDataBlock.inputValue( robotAccumRotation.J0Attr )
        JinDataHandle   = pDataBlock.inputValue( robotAccumRotation.JinAttr )
        JflipDataHandle = pDataBlock.inputValue( robotAccumRotation.JflipAttr )
        ikDataHandle    = pDataBlock.inputValue( robotAccumRotation.ikAttr )
        
        # Output Data Handles 
        JoutDataHandle = pDataBlock.outputValue( robotAccumRotation.JoutAttr )


        ## Extract the actual value associated to our input attribute
        J_0   = J0DataHandle.asAngle().asDegrees()
        J_in  = JinDataHandle.asAngle().asDegrees()
        Jflip = JflipDataHandle.asBool() 
        ik    = ikDataHandle.asBool()

        # Accumulate Rotation Solve Code 
        # If we're in IK mode, check to see if the current rotation value and 
        # the previous value differ by a large amount (e.g. 300 degrees)
        if ik:
            try:
                if abs(J_in - J_0) > 300: 
                    # If so, we assume that the inverse kinematic solver has
                    # flipped, so we manually flip the value back
                    # E.G. if J_0 = 179 and J_in = -179, we assume the output,
                    # J_out, should actually be +181
                    J_out = J_in - (abs(J_in)/J_in) * 360
                else:
                    J_out = J_in
            except:
                J_out = J_in
                
            # If the flipAxis boolean on the robot rig is set to True, we 
            # invert the output by +/- 360 degrees. So +235 becomes -125    
            if Jflip:
                try:
                    J_out = J_out - (abs(J_out)/J_out) * 360
                except:
                    pass
        # If ik is flase, we are in forward kinematic mode; in which case, we
        # pass the input straight through
        else:
            J_out = J_in
           
         
        # Set the Output Values
        Jout = JoutDataHandle.setMAngle( OpenMaya.MAngle( J_out , 2 ) )

            
        # Mark the output data handle as being clean; it need not be computed
        # given its input.
        JoutDataHandle.setClean()

             

# Plug-in initialization:
def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a
    pointer. 
    '''
    return  robotAccumRotation() 

def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our
    plug-in class.
    '''
    
    # The following function set will allow us to create our attributes.
    angleAttributeFn   = OpenMaya.MFnUnitAttribute()
    numericAttributeFn = OpenMaya.MFnNumericAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#
    robotAccumRotation.J0Attr = angleAttributeFn.create( 'j0', 'j0', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    robotAccumRotation.addAttribute( robotAccumRotation.J0Attr ) 

    robotAccumRotation.JinAttr = angleAttributeFn.create( 'jIn', 'jIn', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    robotAccumRotation.addAttribute( robotAccumRotation.JinAttr ) 
   
    robotAccumRotation.JflipAttr = numericAttributeFn.create( 'jFlip', 'jFlip', OpenMaya.MFnNumericData.kBoolean, 0 )
    numericAttributeFn.storable = True 
    numericAttributeFn.writable = True
    numericAttributeFn.hidden   = False
    robotAccumRotation.addAttribute( robotAccumRotation.JflipAttr ) 
    
    robotAccumRotation.ikAttr = numericAttributeFn.create( 'ik', 'ik', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    robotAccumRotation.addAttribute( robotAccumRotation.ikAttr )
    
    
    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#

    robotAccumRotation.JoutAttr = angleAttributeFn.create( 'jOut', 'jOut', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False 
    robotAccumRotation.addAttribute( robotAccumRotation.JoutAttr ) 

    
    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    robotAccumRotation.attributeAffects( robotAccumRotation.JinAttr, robotAccumRotation.JoutAttr   )
    robotAccumRotation.attributeAffects( robotAccumRotation.JflipAttr, robotAccumRotation.JoutAttr )
    robotAccumRotation.attributeAffects( robotAccumRotation.ikAttr, robotAccumRotation.JoutAttr )
     
           
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