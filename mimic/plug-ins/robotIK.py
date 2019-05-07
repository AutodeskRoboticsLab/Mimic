#!usr/bin/env python

"""
Dependency Graph plug-in and the heart of Mimic's robot rig.
It performs the Inverse Kinematic solve, along with handling IK-FK switching
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


# Plug-in information:
kPluginNodeName = 'robotIKS'                # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId(0x87001) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class robotIKS(OpenMaya.MPxNode):
    """
    """
    # Define Node Input Attributes
    tcp_x_attr = OpenMaya.MObject()
    tcp_y_attr = OpenMaya.MObject()
    tcp_z_attr = OpenMaya.MObject()
    tcp_mat_attr = OpenMaya.MMatrix()
    lcs_x_attr = OpenMaya.MObject()
    lcs_y_attr = OpenMaya.MObject()
    lcs_z_attr = OpenMaya.MObject()
    lcs_mat_attr = OpenMaya.MMatrix()
    target_x_attr = OpenMaya.MObject()
    target_y_attr = OpenMaya.MObject()
    target_z_attr = OpenMaya.MObject()
    target_mat_attr = OpenMaya.MMatrix()
    
    a1_attr = OpenMaya.MObject()
    a2_attr = OpenMaya.MObject()
    b_attr = OpenMaya.MObject()
    c1_attr = OpenMaya.MObject()
    c2_attr = OpenMaya.MObject()
    c3_attr = OpenMaya.MObject()
    c4_attr = OpenMaya.MObject()
    
    axis1_offset_attr = OpenMaya.MObject()
    axis2_offset_attr = OpenMaya.MObject()
    axis3_offset_attr = OpenMaya.MObject()
    axis4_offset_attr = OpenMaya.MObject()
    axis5_offset_attr = OpenMaya.MObject()
    axis6_offset_attr = OpenMaya.MObject()
    
    flip_a1_attr = OpenMaya.MObject()
    flip_a2_attr = OpenMaya.MObject()
    flip_a3_attr = OpenMaya.MObject()
    flip_a4_attr = OpenMaya.MObject()
    flip_a5_attr = OpenMaya.MObject()
    flip_a6_attr = OpenMaya.MObject()
    
    sol_1_attr = OpenMaya.MObject()
    sol_2_attr = OpenMaya.MObject()
    sol_3_attr = OpenMaya.MObject()
    
    ik_attr = OpenMaya.MObject()

    a1_fk_attr = OpenMaya.MAngle()
    a2_fk_attr = OpenMaya.MAngle()
    a3_fk_attr = OpenMaya.MAngle()
    a4_fk_attr = OpenMaya.MAngle()
    a5_fk_attr = OpenMaya.MAngle()
    a6_fk_attr = OpenMaya.MAngle()

    solver_type_attr = OpenMaya.MObject()

    # Outputs 
    theta1_attr = OpenMaya.MAngle()
    theta2_attr = OpenMaya.MAngle()
    theta3_attr = OpenMaya.MAngle()
    theta4_attr = OpenMaya.MAngle()
    theta5_attr = OpenMaya.MAngle()
    theta6_attr = OpenMaya.MAngle()

    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
    
    ##################################################
        
    def compute(self, pPlug, pDataBlock):
                   
        # Obtain the data handles for each attribute
        
        ## Input Data Handles ##
        tcp_x_data_handle = pDataBlock.inputValue(robotIKS.tcp_x_attr)
        tcp_y_data_handle = pDataBlock.inputValue(robotIKS.tcp_y_attr)
        tcp_z_data_handle = pDataBlock.inputValue(robotIKS.tcp_z_attr)
        tcp_mat_data_handle = pDataBlock.inputValue(robotIKS.tcp_mat_attr)
        lcs_x_data_handle = pDataBlock.inputValue(robotIKS.lcs_x_attr)  
        lcs_y_data_handle = pDataBlock.inputValue(robotIKS.lcs_y_attr)
        lcs_z_data_handle = pDataBlock.inputValue(robotIKS.lcs_z_attr)
        lcs_mat_data_handle = pDataBlock.inputValue(robotIKS.lcs_mat_attr)                      
        target_x_data_handle = pDataBlock.inputValue(robotIKS.target_x_attr)
        target_y_data_handle = pDataBlock.inputValue(robotIKS.target_y_attr)
        target_z_data_handle = pDataBlock.inputValue(robotIKS.target_z_attr)
        target_mat_data_handle = pDataBlock.inputValue(robotIKS.target_mat_attr)
        
        a1_data_handle = pDataBlock.inputValue(robotIKS.a1_attr)
        a2_data_handle = pDataBlock.inputValue(robotIKS.a2_attr)
        b_data_handle = pDataBlock.inputValue(robotIKS.b_attr)
        c1_data_handle = pDataBlock.inputValue(robotIKS.c1_attr)
        c2_data_handle = pDataBlock.inputValue(robotIKS.c2_attr)
        c3_data_handle = pDataBlock.inputValue(robotIKS.c3_attr)
        c4_data_handle = pDataBlock.inputValue(robotIKS.c4_attr)

        axis1_offset_data_handle = pDataBlock.inputValue(robotIKS.axis1_offset_attr)
        axis2_offset_data_handle = pDataBlock.inputValue(robotIKS.axis2_offset_attr)
        axis3_offset_data_handle = pDataBlock.inputValue(robotIKS.axis3_offset_attr)
        axis4_offset_data_handle = pDataBlock.inputValue(robotIKS.axis4_offset_attr)
        axis5_offset_data_handle = pDataBlock.inputValue(robotIKS.axis5_offset_attr)
        axis6_offset_data_handle = pDataBlock.inputValue(robotIKS.axis6_offset_attr)
        
        flip_a1_data_handle = pDataBlock.inputValue(robotIKS.flip_a1_attr)
        flip_a2_data_handle = pDataBlock.inputValue(robotIKS.flip_a2_attr)
        flip_a3_data_handle = pDataBlock.inputValue(robotIKS.flip_a3_attr)
        flip_a4_data_handle = pDataBlock.inputValue(robotIKS.flip_a4_attr)
        flip_a5_data_handle = pDataBlock.inputValue(robotIKS.flip_a5_attr)
        flip_a6_data_handle = pDataBlock.inputValue(robotIKS.flip_a6_attr)
        
        sol_1_data_handle = pDataBlock.inputValue(robotIKS.sol_1_attr)
        sol_2_data_handle = pDataBlock.inputValue(robotIKS.sol_2_attr)
        sol_3_data_handle = pDataBlock.inputValue(robotIKS.sol_3_attr)

        ik_data_handle = pDataBlock.inputValue(robotIKS.ik_attr)

        a1_fk_data_handle = pDataBlock.inputValue(robotIKS.a1_fk_attr)
        a2_fk_data_handle = pDataBlock.inputValue(robotIKS.a2_fk_attr)
        a3_fk_data_handle = pDataBlock.inputValue(robotIKS.a3_fk_attr)
        a4_fk_data_handle = pDataBlock.inputValue(robotIKS.a4_fk_attr)
        a5_fk_data_handle = pDataBlock.inputValue(robotIKS.a5_fk_attr)
        a6_fk_data_handle = pDataBlock.inputValue(robotIKS.a6_fk_attr)

        solver_type_data_handle = pDataBlock.inputValue(robotIKS.solver_type_attr)

        # Extract the actual value associated to our input attribute
        tcp = [tcp_x_data_handle.asFloat(),
               tcp_y_data_handle.asFloat(),
               tcp_z_data_handle.asFloat()]

        tcp_mat = tcp_mat_data_handle.asMatrix()

        lcs = [lcs_x_data_handle.asFloat(),
               lcs_y_data_handle.asFloat(),
               lcs_z_data_handle.asFloat()]

        lcs_mat = lcs_mat_data_handle.asMatrix()

        target = [target_x_data_handle.asFloat(),
                  target_y_data_handle.asFloat(),
                  target_z_data_handle.asFloat()]

        target_mat = target_mat_data_handle.asMatrix() 
        
        # Robot Definition
        robot_definition = [a1_data_handle.asFloat(),
                            a2_data_handle.asFloat(),
                            b_data_handle.asFloat(),
                            c1_data_handle.asFloat(),
                            c2_data_handle.asFloat(),
                            c3_data_handle.asFloat(),
                            c4_data_handle.asFloat()]

        # Axis Offset Values (robot's zero position in relation to IK solver zero position)
        axis1_offset = axis1_offset_data_handle.asFloat()
        axis2_offset = axis2_offset_data_handle.asFloat()
        axis3_offset = axis3_offset_data_handle.asFloat()
        axis4_offset = axis4_offset_data_handle.asFloat()
        axis5_offset = axis5_offset_data_handle.asFloat()
        axis6_offset = axis6_offset_data_handle.asFloat()
        
        angle_offsets = [axis1_offset,
                         axis2_offset,
                         axis3_offset,
                         axis4_offset,
                         axis5_offset,
                         axis6_offset]

        # Flip Axis Direction bools
        flip_a1 = flip_a1_data_handle.asBool()
        flip_a2 = flip_a2_data_handle.asBool()
        flip_a3 = flip_a3_data_handle.asBool()
        flip_a4 = flip_a4_data_handle.asBool()
        flip_a5 = flip_a5_data_handle.asBool()
        flip_a6 = flip_a6_data_handle.asBool()

        flip_rot_directions = [flip_a1, flip_a2, flip_a3, flip_a4, flip_a5, flip_a6]
        
        # Joint config solution bools
        sol = [sol_1_data_handle.asBool(),
               sol_2_data_handle.asBool(),
               sol_3_data_handle.asBool()]
        
        ik = ik_data_handle.asBool()

        # FK Handle inputs
        a1_fk = a1_fk_data_handle.asAngle().asDegrees()
        a2_fk = a2_fk_data_handle.asAngle().asDegrees()
        a3_fk = a3_fk_data_handle.asAngle().asDegrees()
        a4_fk = a4_fk_data_handle.asAngle().asDegrees()
        a5_fk = a5_fk_data_handle.asAngle().asDegrees()
        a6_fk = a6_fk_data_handle.asAngle().asDegrees()

        # Solver Type
        solver_type = solver_type_data_handle.asInt()
        
        ## Output Data Handles ##
        theta1_out_data_handle = pDataBlock.outputValue(robotIKS.theta1_attr)
        theta2_out_data_handle = pDataBlock.outputValue(robotIKS.theta2_attr)
        theta3_out_data_handle = pDataBlock.outputValue(robotIKS.theta3_attr)
        theta4_out_data_handle = pDataBlock.outputValue(robotIKS.theta4_attr)
        theta5_out_data_handle = pDataBlock.outputValue(robotIKS.theta5_attr)
        theta6_out_data_handle = pDataBlock.outputValue(robotIKS.theta6_attr)
        


        if ik:
            thetas = inverse_kinematics.solve(
                            tcp,
                            tcp_mat,
                            lcs,
                            lcs_mat,
                            target,
                            target_mat,
                            robot_definition,
                            solver_type,
                            sol)
           
            # Apply axis offsets
            thetas = inverse_kinematics.apply_offsets(thetas,
                                            angle_offsets,
                                            flip_rot_directions)
            
            # Convert to MAngle data type for output
            # (the "2" is for data type degrees. 1 = radians)
            a1 = OpenMaya.MAngle(thetas[0], 2)
            a2 = OpenMaya.MAngle(thetas[1], 2)
            a3 = OpenMaya.MAngle(thetas[2], 2)
            a4 = OpenMaya.MAngle(thetas[3], 2)
            a5 = OpenMaya.MAngle(thetas[4], 2)
            a6 = OpenMaya.MAngle(thetas[5], 2)
            
            # Set the Output Values
            theta1 = theta1_out_data_handle.setMAngle(a1)
            theta2 = theta2_out_data_handle.setMAngle(a2)
            theta3 = theta3_out_data_handle.setMAngle(a3)
            theta4 = theta4_out_data_handle.setMAngle(a4)
            theta5 = theta5_out_data_handle.setMAngle(a5)
            theta6 = theta6_out_data_handle.setMAngle(a6) 
            
                
            # Mark the output data handle as being clean; it need not be computed given its input.
            theta1_out_data_handle.setClean()
            theta2_out_data_handle.setClean()
            theta3_out_data_handle.setClean()
            theta4_out_data_handle.setClean()
            theta5_out_data_handle.setClean()
            theta6_out_data_handle.setClean()

        else:
            # Set the Output Values
            theta1 = theta1_out_data_handle.setMAngle(OpenMaya.MAngle(a1_fk, 2))
            theta2 = theta2_out_data_handle.setMAngle(OpenMaya.MAngle(a2_fk, 2))
            theta3 = theta3_out_data_handle.setMAngle(OpenMaya.MAngle(a3_fk, 2))
            theta4 = theta4_out_data_handle.setMAngle(OpenMaya.MAngle(a4_fk, 2))
            theta5 = theta5_out_data_handle.setMAngle(OpenMaya.MAngle(a5_fk, 2))
            theta6 = theta6_out_data_handle.setMAngle(OpenMaya.MAngle(a6_fk, 2)) 
            
                
            # Mark the output data handle as being clean; it need not be computed given its input.
            theta1_out_data_handle.setClean()
            theta2_out_data_handle.setClean()
            theta3_out_data_handle.setClean()
            theta4_out_data_handle.setClean()
            theta5_out_data_handle.setClean()
            theta6_out_data_handle.setClean()



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
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    angleAttributeFn = OpenMaya.MFnUnitAttribute()
    matrixAttributeFn = OpenMaya.MFnMatrixAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#

    #--------------------#
    #  Robot Definition  #
    #--------------------#
    
    # Robot Definition Parent Attr
    robotIKS.robotDef = compoundAttributeFn.create('robotDefinition', 'robotDef')
    
    # a1 # 
    robotIKS.a1_attr = numericAttributeFn.create('a1', 'a1', OpenMaya.MFnNumericData.kFloat, 32.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a1_attr) 

    # a2 # 
    robotIKS.a2_attr = numericAttributeFn.create('a2', 'a2', OpenMaya.MFnNumericData.kFloat, 20.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a2_attr)     

    # b # 
    robotIKS.b_attr = numericAttributeFn.create('b', 'b', OpenMaya.MFnNumericData.kFloat, 0.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.b_attr)     

    # c1 # 
    robotIKS.c1_attr = numericAttributeFn.create('c1', 'c1', OpenMaya.MFnNumericData.kFloat, 78.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.c1_attr) 
  
    # c2 # 
    robotIKS.c2_attr = numericAttributeFn.create('c2', 'c2', OpenMaya.MFnNumericData.kFloat, 128.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.c2_attr) 

    # c3 # 
    robotIKS.c3_attr = numericAttributeFn.create('c3', 'c3', OpenMaya.MFnNumericData.kFloat, 118.25)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.c3_attr) 

    # c4 # 
    robotIKS.c4_attr = numericAttributeFn.create('c4', 'c4', OpenMaya.MFnNumericData.kFloat, 20.0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.c4_attr) 
    
    robotIKS.addAttribute(robotIKS.robotDef)  # Add Parent Attr 


    #----------------#
    #  Axis Offsets  #
    #----------------#
    robotIKS.axisOffsets = compoundAttributeFn.create('axisOffsets', 'aOffsets')

    # Axis 1 Offset #
    robotIKS.axis1_offset_attr = numericAttributeFn.create('axis1Offset', 'a1Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis1_offset_attr) 
    
    # Axis 2 Offset #
    robotIKS.axis2_offset_attr = numericAttributeFn.create('axis2Offset', 'a2Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis2_offset_attr) 
    
    # Axis 3 Offset #
    robotIKS.axis3_offset_attr = numericAttributeFn.create('axis3Offset', 'a3Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis3_offset_attr)  

    # Axis 4 Offset #
    robotIKS.axis4_offset_attr = numericAttributeFn.create('axis4Offset', 'a4Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis4_offset_attr)  

    # Axis 5 Offset #
    robotIKS.axis5_offset_attr = numericAttributeFn.create('axis5Offset', 'a5Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis5_offset_attr)

    # Axis 6 Offset #
    robotIKS.axis6_offset_attr = numericAttributeFn.create('axis6Offset', 'a6Offset', OpenMaya.MFnNumericData.kFloat, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.axis6_offset_attr)  

    robotIKS.addAttribute(robotIKS.axisOffsets)  # Add Parent Attr 
  

    #------------------------#
    #  Flip Axis Directions  # 
    #------------------------#
    robotIKS.axisDirections = compoundAttributeFn.create('axisDirections', 'axisDirs')
    
    # Flip Axis 1 Direction #
    robotIKS.flip_a1_attr = numericAttributeFn.create('flipA1', 'flipA1', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a1_attr) 

    # Flip Axis 2 Direction #
    robotIKS.flip_a2_attr = numericAttributeFn.create('flipA2', 'flipA2', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a2_attr) 

    # Flip Axis 3 Direction #
    robotIKS.flip_a3_attr = numericAttributeFn.create('flipA3', 'flipA3', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a3_attr) 

    # Flip Axis 4 Direction #
    robotIKS.flip_a4_attr = numericAttributeFn.create('flipA4', 'flipA4', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a4_attr) 

    # Flip Axis 5 Direction #
    robotIKS.flip_a5_attr = numericAttributeFn.create('flipA5', 'flipA5', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a5_attr) 

    # Flip Axis 6 Direction #
    robotIKS.flip_a6_attr = numericAttributeFn.create('flipA6', 'flipA6', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.flip_a6_attr) 

    robotIKS.addAttribute(robotIKS.axisDirections)  # Add Parent Attr 


    #----------------------#
    #  Joint Config Bools  # 
    #----------------------#
    
    # Robot Definition Parent Attr
    robotIKS.jointConfig = compoundAttributeFn.create('jointConfiguration', 'config')
    
    # soln1 # 
    robotIKS.sol_1_attr = numericAttributeFn.create('soln1', 'soln1', OpenMaya.MFnNumericData.kBoolean, 1)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.sol_1_attr) 

    # soln2 # 
    robotIKS.sol_2_attr = numericAttributeFn.create('soln2', 'soln2', OpenMaya.MFnNumericData.kBoolean, 1)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.sol_2_attr)     

    # soln3 # 
    robotIKS.sol_3_attr = numericAttributeFn.create('soln3', 'soln3', OpenMaya.MFnNumericData.kBoolean, 1)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.sol_3_attr)     

    # ik #
    robotIKS.ik_attr = numericAttributeFn.create('ik', 'ik', OpenMaya.MFnNumericData.kBoolean, 1)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.ik_attr)     
    
    robotIKS.addAttribute(robotIKS.jointConfig)  # Add Parent Attr 

    #-------------------#
    #    FK Controls    # 
    #-------------------#  
    robotIKS.fkControls = compoundAttributeFn.create('fkControls', 'fkCtrls')
    
    # J1 FK #  
    robotIKS.a1_fk_attr = angleAttributeFn.create('j1_FK', 'j1_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a1_fk_attr)     

    # J2 FK #  
    robotIKS.a2_fk_attr = angleAttributeFn.create('j2_FK', 'j2_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a2_fk_attr)     

    # J3 FK #  
    robotIKS.a3_fk_attr = angleAttributeFn.create('j3_FK', 'j3_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a3_fk_attr)     

    # J4 FK #  
    robotIKS.a4_fk_attr = angleAttributeFn.create('j4_FK', 'j4_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a4_fk_attr)     

    # J5 FK #  
    robotIKS.a5_fk_attr = angleAttributeFn.create('j5_FK', 'j5_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a5_fk_attr)     

    # J6 FK #  
    robotIKS.a6_fk_attr = angleAttributeFn.create('j6_FK', 'j6_FK', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True 
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.a6_fk_attr)     


    robotIKS.addAttribute(robotIKS.fkControls) 
    
                    
    #---------------------------------#
    #  TCP Translation - Local Space  #
    #---------------------------------#
    
    # TCP Parent Attr
    robotIKS.tcp = compoundAttributeFn.create('tcpFrame', 'tcp') 
    
    # tcpX #
    robotIKS.tcp_x_attr = numericAttributeFn.create('tcpX', 'tcpX', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.tcp_x_attr) 

    # tcpY #
    robotIKS.tcp_y_attr = numericAttributeFn.create('tcpY', 'tcpY', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.tcp_y_attr)

    # tcpZ #
    robotIKS.tcp_z_attr = numericAttributeFn.create('tcpZ', 'tcpZ', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    compoundAttributeFn.addChild(robotIKS.tcp_z_attr)  
    
    # TCP Matrix - Local Space ##
    robotIKS.tcp_mat_attr = matrixAttributeFn.create('tcpMatrix', 'tcpMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.tcp_mat_attr) 
    
    robotIKS.addAttribute(robotIKS.tcp)  # Add parent Attr
    
   

    #---------------------------------#
    #  LCS Translation - Local Space  #
    #---------------------------------#
    
    # LCS Parent Attr
    robotIKS.lcs = compoundAttributeFn.create('localFrame', 'lcs') 
    
    # lcsX #
    robotIKS.lcs_x_attr = numericAttributeFn.create('lcsX', 'lcsX', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.lcs_x_attr) 

    # lcsY #
    robotIKS.lcs_y_attr = numericAttributeFn.create('lcsY', 'lcsY', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.lcs_y_attr) 

    # lcsZ #
    robotIKS.lcs_z_attr = numericAttributeFn.create('lcsZ', 'lcsZ', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.lcs_z_attr) 

    ## LCS Matrix - Local Space ##
    robotIKS.lcs_mat_attr = matrixAttributeFn.create('lcsMatrix', 'lcsMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.lcs_mat_attr)  

    robotIKS.addAttribute(robotIKS.lcs)  # Add parent Attr
    
    
    #-----------------------------------------#      
    #  Target Translation - Maya World Space  #
    #-----------------------------------------#      
    
    # Target Parent Attr
    robotIKS.target = compoundAttributeFn.create('targetFrame', 'target') 
    
    # targetX #
    robotIKS.target_x_attr = numericAttributeFn.create('targetX', 'targetX', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.target_x_attr) 

    # targetY #
    robotIKS.target_y_attr = numericAttributeFn.create('targetY', 'targetY', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.target_y_attr) 

    # targetZ #
    robotIKS.target_z_attr = numericAttributeFn.create('targetZ', 'targetZ', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.target_z_attr)
    
    ## Target Matrix - World Space ##
    robotIKS.target_mat_attr = matrixAttributeFn.create('targetMatrix', 'targetMat', OpenMaya.MFnMatrixAttribute.kDouble)
    matrixAttributeFn.writable = True 
    matrixAttributeFn.storable = True 
    matrixAttributeFn.hidden = False 
    compoundAttributeFn.addChild(robotIKS.target_mat_attr)    

    robotIKS.addAttribute(robotIKS.target)  # Add parent Attr

    #-----------------------------------------#      
    #                Solver Type              #
    #-----------------------------------------#  
    robotIKS.solver_type_attr= numericAttributeFn.create('solverType', 'solverType', OpenMaya.MFnNumericData.kInt, 0)
    numericAttributeFn.storable = True 
    numericAttributeFn.writable = True
    numericAttributeFn.hidden = False
    robotIKS.addAttribute(robotIKS.solver_type_attr)     
    
    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#
    
    # Final Joint Values Parent Attr
    robotIKS.theta = compoundAttributeFn.create('JointVals', 'theta') 

    robotIKS.theta1_attr = angleAttributeFn.create('theta1', 'J1', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False
    #robotIKS.addAttribute(robotIKS.theta1_attr) 
    compoundAttributeFn.addChild(robotIKS.theta1_attr)

    robotIKS.theta2_attr = angleAttributeFn.create('theta2', 'J2', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False 
    #robotIKS.addAttribute(robotIKS.theta2_attr) 
    compoundAttributeFn.addChild(robotIKS.theta2_attr)

    robotIKS.theta3_attr = angleAttributeFn.create('theta3', 'J3', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False
    #robotIKS.addAttribute(robotIKS.theta3_attr)  
    compoundAttributeFn.addChild(robotIKS.theta3_attr)

    robotIKS.theta4_attr = angleAttributeFn.create('theta4', 'J4', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False
    #robotIKS.addAttribute(robotIKS.theta4_attr)  
    compoundAttributeFn.addChild(robotIKS.theta4_attr)

    robotIKS.theta5_attr = angleAttributeFn.create('theta5', 'J5', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False
    #robotIKS.addAttribute(robotIKS.theta5_attr)  
    compoundAttributeFn.addChild(robotIKS.theta5_attr)

    robotIKS.theta6_attr = angleAttributeFn.create('theta6', 'J6', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = False 
    angleAttributeFn.writable = False
    angleAttributeFn.readable = True 
    angleAttributeFn.hidden = False
    #robotIKS.addAttribute(robotIKS.theta6_attr)  
    compoundAttributeFn.addChild(robotIKS.theta6_attr)
    
    robotIKS.addAttribute(robotIKS.theta)  # Add parent Attr


    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    input_attrs = [robotIKS.a1_attr,
                   robotIKS.a2_attr,
                   robotIKS.b_attr,
                   robotIKS.c1_attr,
                   robotIKS.c2_attr,
                   robotIKS.c3_attr,
                   robotIKS.c4_attr,
                   robotIKS.axis1_offset_attr,
                   robotIKS.axis2_offset_attr,
                   robotIKS.axis3_offset_attr,
                   robotIKS.axis4_offset_attr,
                   robotIKS.axis5_offset_attr,
                   robotIKS.axis6_offset_attr,
                   robotIKS.flip_a1_attr,
                   robotIKS.flip_a2_attr,
                   robotIKS.flip_a3_attr,
                   robotIKS.flip_a4_attr,
                   robotIKS.flip_a5_attr,
                   robotIKS.flip_a6_attr,
                   robotIKS.sol_1_attr,
                   robotIKS.sol_2_attr,
                   robotIKS.sol_3_attr,
                   robotIKS.ik_attr,
                   robotIKS.a1_fk_attr,
                   robotIKS.a2_fk_attr,
                   robotIKS.a3_fk_attr,
                   robotIKS.a4_fk_attr,
                   robotIKS.a5_fk_attr,
                   robotIKS.a6_fk_attr,
                   robotIKS.tcp_x_attr,
                   robotIKS.tcp_y_attr,
                   robotIKS.tcp_z_attr,
                   robotIKS.tcp_mat_attr,
                   robotIKS.lcs_x_attr,
                   robotIKS.lcs_y_attr,
                   robotIKS.lcs_z_attr,
                   robotIKS.lcs_mat_attr,
                   robotIKS.target_x_attr,
                   robotIKS.target_y_attr,
                   robotIKS.target_z_attr,
                   robotIKS.target_mat_attr,
                   robotIKS.solver_type_attr
                  ]

    output_attrs = [robotIKS.theta1_attr,
                   robotIKS.theta2_attr,
                   robotIKS.theta3_attr,
                   robotIKS.theta4_attr,
                   robotIKS.theta5_attr,
                   robotIKS.theta6_attr,
                   robotIKS.theta]

    for input_attr in input_attrs:
        for output_attr in output_attrs:
            robotIKS.attributeAffects(input_attr, output_attr)
     

           
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