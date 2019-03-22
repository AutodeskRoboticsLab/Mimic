#!usr/bin/env python

"""
Dependency Graph plug-in and the heart of Mimic's robot rig. It performs the Inverse Kinematic solve, along with handling IK-FK switching
"""

import sys
import maya.api.OpenMaya as OpenMaya
import math
import maya.cmds as cmds

# Import inverse_kinematics module for mimic/scripts/robotmath
from robotmath import inverse_kinematics

reload(inverse_kinematics)  # For debugging

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass

#================================================#
#         Define custom utils for solver         #    
#================================================#
'''
def arrayMult(X,Y):
    result = [[0] * len(Y[0]) for i in range(len(X))]
    for i in range(len(X)):
        # iterate through columns of Y
        for j in range(len(Y[0])):
            # iterate through rows of Y
            for k in range(len(Y)):
                result[i][j] += X[i][k] * Y[k][j]
        
    return result

def tpose(lis):
    result = [list(x) for x in zip(*lis)]
    return result
'''

# Plug-in information:
kPluginNodeName = 'robotIKS'                # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId( 0x87001 ) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class robotIKS(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    
    tcpXAttr       = OpenMaya.MObject()
    tcpYAttr       = OpenMaya.MObject()
    tcpZAttr       = OpenMaya.MObject()
    tcpMatAttr     = OpenMaya.MMatrix()
    lcsXAttr       = OpenMaya.MObject()
    lcsYAttr       = OpenMaya.MObject()
    lcsZAttr       = OpenMaya.MObject()
    lcsMatAttr     = OpenMaya.MMatrix()
    targetXAttr    = OpenMaya.MObject()
    targetYAttr    = OpenMaya.MObject()
    targetZAttr    = OpenMaya.MObject()
    targetMatAttr  = OpenMaya.MMatrix()
    
    a1Attr = OpenMaya.MObject()
    a2Attr = OpenMaya.MObject()
    bAttr  = OpenMaya.MObject()
    c1Attr = OpenMaya.MObject()
    c2Attr = OpenMaya.MObject()
    c3Attr = OpenMaya.MObject()
    c4Attr = OpenMaya.MObject()
    
    axis2OffsetAttr = OpenMaya.MObject()
    axis3OffsetAttr = OpenMaya.MObject()
    axis5OffsetAttr = OpenMaya.MObject()
    
    flipA1Attr = OpenMaya.MObject()
    flipA2Attr = OpenMaya.MObject()
    flipA3Attr = OpenMaya.MObject()
    flipA4Attr = OpenMaya.MObject()
    flipA5Attr = OpenMaya.MObject()
    flipA6Attr = OpenMaya.MObject()
    
    soln1Attr = OpenMaya.MObject()
    soln2Attr = OpenMaya.MObject()
    soln3Attr = OpenMaya.MObject()
    
    ikAttr = OpenMaya.MObject()

    j1FKAttr = OpenMaya.MAngle()
    j2FKAttr = OpenMaya.MAngle()
    j3FKAttr = OpenMaya.MAngle()
    j4FKAttr = OpenMaya.MAngle()
    j5FKAttr = OpenMaya.MAngle()
    j6FKAttr = OpenMaya.MAngle()

    solverTypeAttr = OpenMaya.MObject()

    # Outputs 
    theta1Attr = OpenMaya.MAngle()
    theta2Attr = OpenMaya.MAngle()
    theta3Attr = OpenMaya.MAngle()
    theta4Attr = OpenMaya.MAngle()
    theta5Attr = OpenMaya.MAngle()
    theta6Attr = OpenMaya.MAngle()

    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
    
    ##################################################
        
    def compute(self, pPlug, pDataBlock):
                   
        # Obtain the data handles for each attribute
        
        ## Input Data Handles ##
        tcpXDataHandle      = pDataBlock.inputValue( robotIKS.tcpXAttr      )
        tcpYDataHandle      = pDataBlock.inputValue( robotIKS.tcpYAttr      )
        tcpZDataHandle      = pDataBlock.inputValue( robotIKS.tcpZAttr      )
        tcpMatDataHandle    = pDataBlock.inputValue( robotIKS.tcpMatAttr    )
        lcsXDataHandle      = pDataBlock.inputValue( robotIKS.lcsXAttr      )  
        lcsYDataHandle      = pDataBlock.inputValue( robotIKS.lcsYAttr      )
        lcsZDataHandle      = pDataBlock.inputValue( robotIKS.lcsZAttr      )
        lcsMatDataHandle    = pDataBlock.inputValue( robotIKS.lcsMatAttr    )                      
        targetXDataHandle   = pDataBlock.inputValue( robotIKS.targetXAttr   )
        targetYDataHandle   = pDataBlock.inputValue( robotIKS.targetYAttr   )
        targetZDataHandle   = pDataBlock.inputValue( robotIKS.targetZAttr   )
        targetMatDataHandle = pDataBlock.inputValue( robotIKS.targetMatAttr )
        
        a1DataHandle = pDataBlock.inputValue( robotIKS.a1Attr )
        a2DataHandle = pDataBlock.inputValue( robotIKS.a2Attr )
        bDataHandle  = pDataBlock.inputValue( robotIKS.bAttr  )
        c1DataHandle = pDataBlock.inputValue( robotIKS.c1Attr )
        c2DataHandle = pDataBlock.inputValue( robotIKS.c2Attr )
        c3DataHandle = pDataBlock.inputValue( robotIKS.c3Attr )
        c4DataHandle = pDataBlock.inputValue( robotIKS.c4Attr )

        axis2OffsetDataHandle = pDataBlock.inputValue( robotIKS.axis2OffsetAttr )
        axis3OffsetDataHandle = pDataBlock.inputValue( robotIKS.axis3OffsetAttr )
        axis5OffsetDataHandle = pDataBlock.inputValue( robotIKS.axis5OffsetAttr )
        
        flipA1DataHandle = pDataBlock.inputValue( robotIKS.flipA1Attr )
        flipA2DataHandle = pDataBlock.inputValue( robotIKS.flipA2Attr )
        flipA3DataHandle = pDataBlock.inputValue( robotIKS.flipA3Attr )
        flipA4DataHandle = pDataBlock.inputValue( robotIKS.flipA4Attr )
        flipA5DataHandle = pDataBlock.inputValue( robotIKS.flipA5Attr )
        flipA6DataHandle = pDataBlock.inputValue( robotIKS.flipA6Attr )
        
        soln1DataHandle = pDataBlock.inputValue( robotIKS.soln1Attr )
        soln2DataHandle = pDataBlock.inputValue( robotIKS.soln2Attr )
        soln3DataHandle = pDataBlock.inputValue( robotIKS.soln3Attr )

        ikDataHandle = pDataBlock.inputValue( robotIKS.ikAttr )

        j1FKDataHandle = pDataBlock.inputValue( robotIKS.j1FKAttr )
        j2FKDataHandle = pDataBlock.inputValue( robotIKS.j2FKAttr )
        j3FKDataHandle = pDataBlock.inputValue( robotIKS.j3FKAttr )
        j4FKDataHandle = pDataBlock.inputValue( robotIKS.j4FKAttr )
        j5FKDataHandle = pDataBlock.inputValue( robotIKS.j5FKAttr )
        j6FKDataHandle = pDataBlock.inputValue( robotIKS.j6FKAttr )

        solverTypeDataHandle = pDataBlock.inputValue( robotIKS.solverTypeAttr )

        # Extract the actual value associated to our input attribute
        tcp      = [tcpXDataHandle.asFloat(),
                    tcpYDataHandle.asFloat(),
                    tcpZDataHandle.asFloat()]
        tcpMat   = tcpMatDataHandle.asMatrix()

        lcs      = [lcsXDataHandle.asFloat(),
                    lcsYDataHandle.asFloat(),
                    lcsZDataHandle.asFloat()]
        lcsMat   = lcsMatDataHandle.asMatrix()

        target    = [targetXDataHandle.asFloat(),
                     targetYDataHandle.asFloat(),
                     targetZDataHandle.asFloat()]
        targetMat = targetMatDataHandle.asMatrix() 
        
        # Robot Definition
        robot_definition = [a1DataHandle.asFloat(),
                            a2DataHandle.asFloat(),
                            bDataHandle.asFloat(),
                            c1DataHandle.asFloat(),
                            c2DataHandle.asFloat(),
                            c3DataHandle.asFloat(),
                            c4DataHandle.asFloat()]

        # Axis Offset Values (robot's zero position in relation to IK solver zero position)
        axis2Offset = axis2OffsetDataHandle.asFloat()
        axis3Offset = axis3OffsetDataHandle.asFloat()
        axis5Offset = axis5OffsetDataHandle.asFloat()
        
        # Flip Axis Direction bools
        flipA1 = flipA1DataHandle.asBool()
        flipA2 = flipA2DataHandle.asBool()
        flipA3 = flipA3DataHandle.asBool()
        flipA4 = flipA4DataHandle.asBool()
        flipA5 = flipA5DataHandle.asBool()
        flipA6 = flipA6DataHandle.asBool()
        
        # Joint config bools
        sols = [soln1DataHandle.asBool(),
                soln2DataHandle.asBool(),
                soln3DataHandle.asBool()]
        
        ik = ikDataHandle.asBool()

        # FK Handle inputs
        j1FK = j1FKDataHandle.asAngle().asDegrees()
        j2FK = j2FKDataHandle.asAngle().asDegrees()
        j3FK = j3FKDataHandle.asAngle().asDegrees()
        j4FK = j4FKDataHandle.asAngle().asDegrees()
        j5FK = j5FKDataHandle.asAngle().asDegrees()
        j6FK = j6FKDataHandle.asAngle().asDegrees()

        # Solver Type
        solverType = solverTypeDataHandle.asInt()
        
        ## Output Data Handles ##
        theta1OutDataHandle = pDataBlock.outputValue( robotIKS.theta1Attr )
        theta2OutDataHandle = pDataBlock.outputValue( robotIKS.theta2Attr )
        theta3OutDataHandle = pDataBlock.outputValue( robotIKS.theta3Attr )
        theta4OutDataHandle = pDataBlock.outputValue( robotIKS.theta4Attr )
        theta5OutDataHandle = pDataBlock.outputValue( robotIKS.theta5Attr )
        theta6OutDataHandle = pDataBlock.outputValue( robotIKS.theta6Attr )
        


        if ik:
            if solverType == 1:  # Hawkins-Keating Solver (e.g. UR)
                jointVals = inverse_kinematics.solve_hawkins_keating(tcp,
                               tcpMat,
                               lcs, 
                               lcsMat, 
                               target,
                               targetMat,
                               robot_definition,
                               sols)

            else:
                jointVals = inverse_kinematics.solve_spherical_wrist(tcp,
                               tcpMat,
                               lcs, 
                               lcsMat, 
                               target,
                               targetMat,
                               robot_definition,
                               sols)


            if math.degrees(999) in jointVals:
                cmds.warning( "Not a valid configuration" )
                theta1OutDataHandle.setClean()
                theta2OutDataHandle.setClean()
                theta3OutDataHandle.setClean()
                theta4OutDataHandle.setClean()
                theta5OutDataHandle.setClean()
                theta6OutDataHandle.setClean()
            else:
                ##########################################################            
                
                # Offset J2/J3/J5 axes
                jointVals[1] = jointVals[1] - axis2Offset
                jointVals[2] = jointVals[2] - axis3Offset
                jointVals[4] = jointVals[4] - axis5Offset
                
                
                # Flip rotation directions if necessary 
                if flipA1:
                    jointVals[0] = jointVals[0] * (-1)
                if flipA2:
                    jointVals[1] = jointVals[1] * (-1)
                if flipA3:
                    jointVals[2] = jointVals[2] * (-1)
                if flipA4:
                    jointVals[3] = jointVals[3] * (-1)
                if flipA5:
                    jointVals[4] = jointVals[4] * (-1)
                if flipA6 :
                    jointVals[5] = jointVals[5] * (-1)
                
                # Convert to MAngle data type for output (the "2" is for data type degrees. 1 = radians)
                j1 = OpenMaya.MAngle( jointVals[0], 2 )
                j2 = OpenMaya.MAngle( jointVals[1], 2 )
                j3 = OpenMaya.MAngle( jointVals[2], 2 )
                j4 = OpenMaya.MAngle( jointVals[3], 2 )
                j5 = OpenMaya.MAngle( jointVals[4], 2 )
                j6 = OpenMaya.MAngle( jointVals[5], 2 )
                
                # Set the Output Values
                theta1 = theta1OutDataHandle.setMAngle( j1 )
                theta2 = theta2OutDataHandle.setMAngle( j2 )
                theta3 = theta3OutDataHandle.setMAngle( j3 )
                theta4 = theta4OutDataHandle.setMAngle( j4 )
                theta5 = theta5OutDataHandle.setMAngle( j5 )
                theta6 = theta6OutDataHandle.setMAngle( j6 ) 
                
                    
                # Mark the output data handle as being clean; it need not be computed given its input.
                theta1OutDataHandle.setClean()
                theta2OutDataHandle.setClean()
                theta3OutDataHandle.setClean()
                theta4OutDataHandle.setClean()
                theta5OutDataHandle.setClean()
                theta6OutDataHandle.setClean()

        else:
            # Set the Output Values
            theta1 = theta1OutDataHandle.setMAngle( OpenMaya.MAngle(j1FK, 2) )
            theta2 = theta2OutDataHandle.setMAngle( OpenMaya.MAngle(j2FK, 2) )
            theta3 = theta3OutDataHandle.setMAngle( OpenMaya.MAngle(j3FK, 2) )
            theta4 = theta4OutDataHandle.setMAngle( OpenMaya.MAngle(j4FK, 2) )
            theta5 = theta5OutDataHandle.setMAngle( OpenMaya.MAngle(j5FK, 2) )
            theta6 = theta6OutDataHandle.setMAngle( OpenMaya.MAngle(j6FK, 2) ) 
            
                
            # Mark the output data handle as being clean; it need not be computed given its input.
            theta1OutDataHandle.setClean()
            theta2OutDataHandle.setClean()
            theta3OutDataHandle.setClean()
            theta4OutDataHandle.setClean()
            theta5OutDataHandle.setClean()
            theta6OutDataHandle.setClean()



#========================================================#
#                 Plug-in initialization.                #
#========================================================#

def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a pointer.
    '''

    return  robotIKS() 

def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our plug-in class.
    '''
    
    # The following function set will allow us to create our attributes.
    numericAttributeFn  = OpenMaya.MFnNumericAttribute()
    angleAttributeFn    = OpenMaya.MFnUnitAttribute()
    matrixAttributeFn   = OpenMaya.MFnMatrixAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#

    #--------------------#
    #  Robot Definition  #
    #--------------------#
    
    # Robot Definition Parent Attr
    robotIKS.robotDef = compoundAttributeFn.create( 'robotDefinition', 'robotDef' )
    
    # a1 # 
    robotIKS.a1Attr = numericAttributeFn.create( 'a1', 'a1', OpenMaya.MFnNumericData.kFloat, 32.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.a1Attr ) 

    # a2 # 
    robotIKS.a2Attr = numericAttributeFn.create( 'a2', 'a2', OpenMaya.MFnNumericData.kFloat, 20.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.a2Attr )     

    # b # 
    robotIKS.bAttr = numericAttributeFn.create( 'b', 'b', OpenMaya.MFnNumericData.kFloat, 0.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.bAttr )     

    # c1 # 
    robotIKS.c1Attr = numericAttributeFn.create( 'c1', 'c1', OpenMaya.MFnNumericData.kFloat, 78.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.c1Attr ) 
  
    # c2 # 
    robotIKS.c2Attr = numericAttributeFn.create( 'c2', 'c2', OpenMaya.MFnNumericData.kFloat, 128.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.c2Attr ) 

    # c3 # 
    robotIKS.c3Attr = numericAttributeFn.create( 'c3', 'c3', OpenMaya.MFnNumericData.kFloat, 118.25 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.c3Attr ) 

    # c4 # 
    robotIKS.c4Attr = numericAttributeFn.create( 'c4', 'c4', OpenMaya.MFnNumericData.kFloat, 20.0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.c4Attr ) 
    
    robotIKS.addAttribute( robotIKS.robotDef )  # Add Parent Attr 


    #----------------#
    #  Axis Offsets  #
    #----------------#
    robotIKS.axisOffsets = compoundAttributeFn.create( 'axisOffsets', 'aOffsets' )
    
    # Axis 2 Offset #
    robotIKS.axis2OffsetAttr = numericAttributeFn.create( 'axis2Offset', 'a2Offset', OpenMaya.MFnNumericData.kFloat, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.axis2OffsetAttr ) 
    
    # Axis 3 Offset #
    robotIKS.axis3OffsetAttr = numericAttributeFn.create( 'axis3Offset', 'a3Offset', OpenMaya.MFnNumericData.kFloat, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.axis3OffsetAttr )  

    # Axis 5 Offset #
    robotIKS.axis5OffsetAttr = numericAttributeFn.create( 'axis5Offset', 'a5Offset', OpenMaya.MFnNumericData.kFloat, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.axis5OffsetAttr )  

    robotIKS.addAttribute( robotIKS.axisOffsets )  # Add Parent Attr 
  

    #------------------------#
    #  Flip Axis Directions  # 
    #------------------------#
    robotIKS.axisDirections = compoundAttributeFn.create( 'axisDirections', 'axisDirs' )
    
    # Flip Axis 1 Direction #
    robotIKS.flipA1Attr = numericAttributeFn.create( 'flipA1', 'flipA1', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA1Attr ) 

    # Flip Axis 2 Direction #
    robotIKS.flipA2Attr = numericAttributeFn.create( 'flipA2', 'flipA2', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA2Attr ) 

    # Flip Axis 3 Direction #
    robotIKS.flipA3Attr = numericAttributeFn.create( 'flipA3', 'flipA3', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA3Attr ) 

    # Flip Axis 4 Direction #
    robotIKS.flipA4Attr = numericAttributeFn.create( 'flipA4', 'flipA4', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA4Attr ) 

    # Flip Axis 5 Direction #
    robotIKS.flipA5Attr = numericAttributeFn.create( 'flipA5', 'flipA5', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA5Attr ) 

    # Flip Axis 6 Direction #
    robotIKS.flipA6Attr = numericAttributeFn.create( 'flipA6', 'flipA6', OpenMaya.MFnNumericData.kBoolean, 0 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.flipA6Attr ) 

    robotIKS.addAttribute( robotIKS.axisDirections )  # Add Parent Attr 


    #----------------------#
    #  Joint Config Bools  # 
    #----------------------#
    
    # Robot Definition Parent Attr
    robotIKS.jointConfig = compoundAttributeFn.create( 'jointConfiguration', 'config' )
    
    # soln1 # 
    robotIKS.soln1Attr = numericAttributeFn.create( 'soln1', 'soln1', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.soln1Attr ) 

    # soln2 # 
    robotIKS.soln2Attr = numericAttributeFn.create( 'soln2', 'soln2', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.soln2Attr )     

    # soln3 # 
    robotIKS.soln3Attr = numericAttributeFn.create( 'soln3', 'soln3', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.soln3Attr )     

    # ik #
    robotIKS.ikAttr = numericAttributeFn.create( 'ik', 'ik', OpenMaya.MFnNumericData.kBoolean, 1 )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.ikAttr )     
    
    robotIKS.addAttribute( robotIKS.jointConfig )  # Add Parent Attr 

    #-------------------#
    #    FK Controls    # 
    #-------------------#  
    robotIKS.fkControls = compoundAttributeFn.create( 'fkControls', 'fkCtrls' )
    
    # J1 FK #  
    robotIKS.j1FKAttr = angleAttributeFn.create( 'j1_FK', 'j1_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j1FKAttr )     

    # J2 FK #  
    robotIKS.j2FKAttr = angleAttributeFn.create( 'j2_FK', 'j2_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j2FKAttr )     

    # J3 FK #  
    robotIKS.j3FKAttr = angleAttributeFn.create( 'j3_FK', 'j3_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j3FKAttr )     

    # J4 FK #  
    robotIKS.j4FKAttr = angleAttributeFn.create( 'j4_FK', 'j4_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j4FKAttr )     

    # J5 FK #  
    robotIKS.j5FKAttr = angleAttributeFn.create( 'j5_FK', 'j5_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j5FKAttr )     

    # J6 FK #  
    robotIKS.j6FKAttr = angleAttributeFn.create( 'j6_FK', 'j6_FK', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.j6FKAttr )     


    robotIKS.addAttribute( robotIKS.fkControls ) 
    
                    
    #---------------------------------#
    #  TCP Translation - Local Space  #
    #---------------------------------#
    
    # TCP Parent Attr
    robotIKS.tcp = compoundAttributeFn.create( 'tcpFrame', 'tcp' ) 
    
    # tcpX #
    robotIKS.tcpXAttr = numericAttributeFn.create( 'tcpX', 'tcpX', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.tcpXAttr ) 

    # tcpY #
    robotIKS.tcpYAttr = numericAttributeFn.create( 'tcpY', 'tcpY', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.tcpYAttr )

    # tcpZ #
    robotIKS.tcpZAttr = numericAttributeFn.create( 'tcpZ', 'tcpZ', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False
    compoundAttributeFn.addChild( robotIKS.tcpZAttr )  
    
    # TCP Matrix - Local Space ##
    robotIKS.tcpMatAttr = matrixAttributeFn.create( 'tcpMatrix', 'tcpMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.tcpMatAttr ) 
    
    robotIKS.addAttribute( robotIKS.tcp )  # Add parent Attr
    
   

    #---------------------------------#
    #  LCS Translation - Local Space  #
    #---------------------------------#
    
    # LCS Parent Attr
    robotIKS.lcs = compoundAttributeFn.create( 'localFrame', 'lcs' ) 
    
    # lcsX #
    robotIKS.lcsXAttr = numericAttributeFn.create( 'lcsX', 'lcsX', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.lcsXAttr ) 

    # lcsY #
    robotIKS.lcsYAttr = numericAttributeFn.create( 'lcsY', 'lcsY', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.lcsYAttr ) 

    # lcsZ #
    robotIKS.lcsZAttr = numericAttributeFn.create( 'lcsZ', 'lcsZ', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.lcsZAttr ) 

    ## LCS Matrix - Local Space ##
    robotIKS.lcsMatAttr = matrixAttributeFn.create( 'lcsMatrix', 'lcsMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.lcsMatAttr )  

    robotIKS.addAttribute( robotIKS.lcs )  # Add parent Attr
    
    
    #-----------------------------------------#      
    #  Target Translation - Maya World Space  #
    #-----------------------------------------#      
    
    # Target Parent Attr
    robotIKS.target = compoundAttributeFn.create( 'targetFrame', 'target' ) 
    
    # targetX #
    robotIKS.targetXAttr = numericAttributeFn.create( 'targetX', 'targetX', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.targetXAttr ) 

    # targetY #
    robotIKS.targetYAttr = numericAttributeFn.create( 'targetY', 'targetY', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.targetYAttr ) 

    # targetZ #
    robotIKS.targetZAttr = numericAttributeFn.create( 'targetZ', 'targetZ', OpenMaya.MFnNumericData.kFloat )                                                            
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.targetZAttr )
    
    ## Target Matrix - World Space ##
    robotIKS.targetMatAttr = matrixAttributeFn.create( 'targetMatrix', 'targetMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden   = False 
    compoundAttributeFn.addChild( robotIKS.targetMatAttr )    

    robotIKS.addAttribute( robotIKS.target )  # Add parent Attr

    #-----------------------------------------#      
    #                Solver Type              #
    #-----------------------------------------#  
    robotIKS.solverTypeAttr= numericAttributeFn.create( 'solverType', 'solverType', OpenMaya.MFnNumericData.kInt, 0 )
    numericAttributeFn.storable = True 
    numericAttributeFn.writable = True
    numericAttributeFn.hidden   = False
    robotIKS.addAttribute( robotIKS.solverTypeAttr )     
    
    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#
    
    # Final Joint Values Parent Attr
    robotIKS.theta = compoundAttributeFn.create( 'JointVals', 'theta' ) 

    robotIKS.theta1Attr = angleAttributeFn.create( 'theta1', 'J1', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False
    #robotIKS.addAttribute( robotIKS.theta1Attr ) 
    compoundAttributeFn.addChild( robotIKS.theta1Attr )

    robotIKS.theta2Attr = angleAttributeFn.create( 'theta2', 'J2', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False 
    #robotIKS.addAttribute( robotIKS.theta2Attr ) 
    compoundAttributeFn.addChild( robotIKS.theta2Attr )

    robotIKS.theta3Attr = angleAttributeFn.create( 'theta3', 'J3', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False
    #robotIKS.addAttribute( robotIKS.theta3Attr )  
    compoundAttributeFn.addChild( robotIKS.theta3Attr )

    robotIKS.theta4Attr = angleAttributeFn.create( 'theta4', 'J4', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False
    #robotIKS.addAttribute( robotIKS.theta4Attr )  
    compoundAttributeFn.addChild( robotIKS.theta4Attr )

    robotIKS.theta5Attr = angleAttributeFn.create( 'theta5', 'J5', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False
    #robotIKS.addAttribute( robotIKS.theta5Attr )  
    compoundAttributeFn.addChild( robotIKS.theta5Attr )

    robotIKS.theta6Attr = angleAttributeFn.create( 'theta6', 'J6', OpenMaya.MFnUnitAttribute.kAngle )
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden   = False
    #robotIKS.addAttribute( robotIKS.theta6Attr )  
    compoundAttributeFn.addChild( robotIKS.theta6Attr )
    
    robotIKS.addAttribute( robotIKS.theta )  # Add parent Attr


    
    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    #-------------#
    #  Robot Def  #
    #-------------#
    
    # a1 #
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.a1Attr, robotIKS.theta      )        

    # a2 #
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.a2Attr, robotIKS.theta      )        
     

    # b #
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta6Attr )      
    robotIKS.attributeAffects( robotIKS.bAttr, robotIKS.theta      )      

    # c1 #
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta6Attr ) 
    robotIKS.attributeAffects( robotIKS.c1Attr, robotIKS.theta      ) 

    # c2 #
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta6Attr ) 
    robotIKS.attributeAffects( robotIKS.c2Attr, robotIKS.theta      ) 

    # c3 #
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta6Attr ) 
    robotIKS.attributeAffects( robotIKS.c3Attr, robotIKS.theta      ) 

    # c4 #
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.c4Attr, robotIKS.theta      )

    #----------------#
    #  Axis Offsets  #
    #----------------#

    # axis 2 #
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.axis2OffsetAttr, robotIKS.theta      )

    # axis 3 #
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.axis3OffsetAttr, robotIKS.theta      )

    # axis 5 #
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.axis5OffsetAttr, robotIKS.theta      )


    #------------------------#
    #  Flip Axis Directions  # 
    #------------------------#
    
    # axis 1 #
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA1Attr, robotIKS.theta      )
 
    # axis 2 #
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA2Attr, robotIKS.theta      )
    
    # axis 3 #
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA3Attr, robotIKS.theta      )

    # axis 4 #
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA4Attr, robotIKS.theta      )


    # axis 5 #
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA5Attr, robotIKS.theta      )

    # axis 6 #
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.flipA6Attr, robotIKS.theta      )
    
    #----------------------#
    #  Joint Congig Bools  #
    #----------------------#
    
    # soln1 #
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.soln1Attr, robotIKS.theta      )
    
    # soln2 #
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.soln2Attr, robotIKS.theta      )
    
    # soln3 #
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.soln3Attr, robotIKS.theta      )
    
    # ik #
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.ikAttr, robotIKS.theta      )


    #-------------------#
    #    FK Controls    #
    #-------------------#
    
    # J1 FK #
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j1FKAttr, robotIKS.theta      )

    # J2 FK #
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j2FKAttr, robotIKS.theta      )

    # J3 FK #
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j3FKAttr, robotIKS.theta      )

    # J4 FK #
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j4FKAttr, robotIKS.theta      )

    # J5 FK #
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j5FKAttr, robotIKS.theta      )

    # J6 FK #
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.j6FKAttr, robotIKS.theta      )

                 
    #-------#
    #  TCP  #
    #-------#

    # TCP X #
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.tcpXAttr, robotIKS.theta      )

    
    # TCP Y #
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.tcpYAttr, robotIKS.theta      )
    
    # TCP Z #
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.tcpZAttr, robotIKS.theta      )
 
    # Tcp Matrix #
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta1Attr )    
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta2Attr )    
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta3Attr )    
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta4Attr )    
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta5Attr )    
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta6Attr )       
    robotIKS.attributeAffects( robotIKS.tcpMatAttr, robotIKS.theta      )       

    #-------#
    #  LCS  #
    #-------#

    # LCS X #
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.lcsXAttr, robotIKS.theta      )
    
    # LCS Y #
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.lcsYAttr, robotIKS.theta      )
    
    # LCS Z #
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.lcsZAttr, robotIKS.theta      )
 
    # LCS Matrix #
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta1Attr )    
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta2Attr )    
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta3Attr )    
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta4Attr )    
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta5Attr )    
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta6Attr ) 
    robotIKS.attributeAffects( robotIKS.lcsMatAttr, robotIKS.theta      ) 

    #----------#
    #  Target  #
    #----------#

    # Target X #
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.targetXAttr, robotIKS.theta      )
    
    # Target Y #
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.targetYAttr, robotIKS.theta      )
    
    # Target Z #
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta6Attr )
    robotIKS.attributeAffects( robotIKS.targetZAttr, robotIKS.theta      )
  

    # Target Matrix #
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta1Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta2Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta3Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta4Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta5Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta6Attr )    
    robotIKS.attributeAffects( robotIKS.targetMatAttr, robotIKS.theta      ) 


    #---------------#
    #  Solver Type  #
    #---------------#
    
    # a1 #
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta1Attr )
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta2Attr )
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta3Attr )
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta4Attr )
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta5Attr )
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta6Attr )        
    robotIKS.attributeAffects( robotIKS.solverTypeAttr, robotIKS.theta      ) 

           
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