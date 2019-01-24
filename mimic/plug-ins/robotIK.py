#!usr/bin/env python

"""
Dependency Graph plug-in and the heart of Mimic's robot rig. It performs the Inverse Kinematic solve, along with handling IK-FK switching
"""

import sys
import maya.api.OpenMaya as OpenMaya
import math
import maya.cmds as cmds

def maya_useNewAPI():
	"""
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
	"""
	pass

#================================================#
#         Define custom utils for solver         #    
#================================================#

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

        
        # Extract the actual value associated to our input attribute
        tcpX      = tcpXDataHandle.asFloat()
        tcpY      = tcpYDataHandle.asFloat()
        tcpZ      = tcpZDataHandle.asFloat()
        tcpMat    = tcpMatDataHandle.asMatrix()           
        lcsX      = lcsXDataHandle.asFloat()
        lcsY      = lcsYDataHandle.asFloat()
        lcsZ      = lcsZDataHandle.asFloat()
        lcsMat    = lcsMatDataHandle.asMatrix()
        tcpX      = tcpXDataHandle.asFloat()
        tcpY      = tcpYDataHandle.asFloat()
        tcpZ      = tcpZDataHandle.asFloat()
        tcpMat    = tcpMatDataHandle.asMatrix()
        targetX   = targetXDataHandle.asFloat()
        targetY   = targetYDataHandle.asFloat()
        targetZ   = targetZDataHandle.asFloat()
        targetMat = targetMatDataHandle.asMatrix() 
        
        # Robot Definition
        a1 = a1DataHandle.asFloat()
        a2 = a2DataHandle.asFloat()
        b  = bDataHandle.asFloat()
        c1 = c1DataHandle.asFloat()
        c2 = c2DataHandle.asFloat()
        c3 = c3DataHandle.asFloat()
        c4 = c4DataHandle.asFloat()

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
        soln1 = soln1DataHandle.asBool()
        soln2 = soln2DataHandle.asBool()
        soln3 = soln3DataHandle.asBool()
        
        ik = ikDataHandle.asBool()

        # FK Handle inputs
        j1FK = j1FKDataHandle.asAngle().asDegrees()
        j2FK = j2FKDataHandle.asAngle().asDegrees()
        j3FK = j3FKDataHandle.asAngle().asDegrees()
        j4FK = j4FKDataHandle.asAngle().asDegrees()
        j5FK = j5FKDataHandle.asAngle().asDegrees()
        j6FK = j6FKDataHandle.asAngle().asDegrees()
        
        ## Output Data Handles ##
        theta1OutDataHandle = pDataBlock.outputValue( robotIKS.theta1Attr )
        theta2OutDataHandle = pDataBlock.outputValue( robotIKS.theta2Attr )
        theta3OutDataHandle = pDataBlock.outputValue( robotIKS.theta3Attr )
        theta4OutDataHandle = pDataBlock.outputValue( robotIKS.theta4Attr )
        theta5OutDataHandle = pDataBlock.outputValue( robotIKS.theta5Attr )
        theta6OutDataHandle = pDataBlock.outputValue( robotIKS.theta6Attr )
        
        if ik:
            #========================================================#
            #                     IK Solve Code                      #
            #========================================================#
            
            # Initialize Variables
            tcpRot    = [[0] * 3 for i in range(3)]
            targetRot = [[0] * 3 for i in range(3)]
            tcpTrans  = [[0] * 1 for i in range(3)]
            lcsTrans  = [[0] * 1 for i in range(3)]
            targetPt  = [[0] * 1 for i in range(3)]
            flangePt  = [[0] * 3 for i in range(1)]
            pivotPt   = [[0] * 3 for i in range(1)]
            
            theta1_Sol = [[0] * 2 for i in range(1)][0]
            theta2_Sol = [[0] * 4 for i in range(1)][0] 
            theta3_Sol = [[0] * 4 for i in range(1)][0]
            theta4_Sol = [[0] * 8 for i in range(1)][0]
            theta5_Sol = [[0] * 8 for i in range(1)][0]
            theta6_Sol = [[0] * 8 for i in range(1)][0]
    
            jointVals  = [[0] * 6 for i in range(1)][0]
            
            T = [[0], [0], [c4]]
            
            #=====================#
            #  Frame Definitions  #
            #=====================#
            # Maya to robot tcp coordinate change. robot (X,Y,Z) = Maya (-Y, X, Z) 
            Rtm = [[0,-1,0],[1,0,0],[0,0,1]]          # Rotation matrix from Maya frame to robot tool frame
            Ram = [[0,0,1],[1,0,0],[0,1,0]]           # Rotation matrix from Maya frame to robot world frame    
            
            tcpTrans[0][0] = tcpX                     # Get local Translation of tcp w.r.t. tool flange
            tcpTrans[1][0] = tcpY                     #   
            tcpTrans[2][0] = tcpZ                     # 
            tcpTrans       = arrayMult(Rtm, tcpTrans) # Convert tcp translation from Maya frame to robot tool frame
            
            lcsTrans[0][0] = lcsX                     # Get translation of local base frame w.r.t robot world frame (Square controller)
            lcsTrans[1][0] = lcsY                     #
            lcsTrans[2][0] = lcsZ                     #
            lcsTrans       = arrayMult(Ram, lcsTrans) # Convert lcs translation to robot world frame        
    
            targetPt[0][0] = targetX                  # Get translation of target in maya frame w.r.t robot world frame (Square controller)
            targetPt[1][0] = targetY                  #
            targetPt[2][0] = targetZ                  #
            targetPt       = arrayMult(Ram, targetPt) # Convert target translation translation to robot world frame        
    
            # Convert Maya format rotation matrices to truncated format
            tcpRotXAxis = [[tcpMat[0]],[tcpMat[1]],[tcpMat[2]]]
            tcpRotYAxis = [[tcpMat[4]],[tcpMat[5]],[tcpMat[6]]]
            tcpRotZAxis = [[tcpMat[8]],[tcpMat[9]],[tcpMat[10]]]
            tcpMatTrunc = tpose([tpose(tcpRotXAxis)[0], tpose(tcpRotYAxis)[0], tpose(tcpRotZAxis)[0]])
            
            tcpRot      = tpose(arrayMult(Rtm, tcpMatTrunc)) # Convert tcp rotation matrix to robot tool frame
            
            lcsRotXAxis = [[lcsMat[0]],[lcsMat[1]],[lcsMat[2]]]
            lcsRotYAxis = [[lcsMat[4]],[lcsMat[5]],[lcsMat[6]]]
            lcsRotZAxis = [[lcsMat[8]],[lcsMat[9]],[lcsMat[10]]]
            lcsMatTrunc = tpose([tpose(lcsRotXAxis)[0], tpose(lcsRotYAxis)[0], tpose(lcsRotZAxis)[0]])
            
            lcsRot      = tpose(arrayMult(Ram, lcsMatTrunc)) # Convert local base frame rotation matrix to robot world frame
            
            targetRotXAxis = [[targetMat[0]],[targetMat[1]],[targetMat[2]]]
            targetRotYAxis = [[targetMat[4]],[targetMat[5]],[targetMat[6]]]
            targetRotZAxis = [[targetMat[8]],[targetMat[9]],[targetMat[10]]]
            targetMatTrunc = tpose([tpose(targetRotXAxis)[0], tpose(targetRotYAxis)[0], tpose(targetRotZAxis)[0]])
            
            targetRot      = tpose(arrayMult(Ram, targetMatTrunc)) # Convert target rotation matrix to robot world frame        
            
            
            # Find Flange and Pivot locations in local robot frame
            Re = arrayMult(tpose(targetRot), tcpRot)                                             # Rotation of the tcp w.r.t the target in robot world frame (square controller)
            Rlm = arrayMult(Ram, lcsRot)                                                         # Transformation of local coordinate system in Maya frame (still not sure why)
            
            targetPt = [i - j for i,j in zip(tpose(targetPt)[0], tpose(lcsTrans)[0])]            # Find distance from local base frame (circle controller)
                                                                                                 # to target point in robot world frame
                                                                                      
            flangePt = [i - j for i,j in zip(targetPt, tpose(arrayMult(Re,tcpTrans))[0])]        # Find the flange point in robot world frame 
            pivotPt  = [i - j for i,j in zip(flangePt, tpose(arrayMult(Re, T))[0])]              # Find the pivot point in robot world frame
            
            flangePt  = tpose(arrayMult(Rlm, [[flangePt[0]], [flangePt[1]], [flangePt[2]]]))[0]  # Convert flange point to local frame (circle controller)
            pivotPt  = tpose(arrayMult(Rlm, [[pivotPt[0]], [pivotPt[1]], [pivotPt[2]]]))[0]      # Convert pivot point to local frame (circle controller)
            
            Re = arrayMult(Rlm, Re)                                                              # Rotation of the tcp w.r.t the target in robot local frame (cirlce controller) 
            
            #=========#
            #  SOLVE  #
            #=========#
            nx1  = math.sqrt((math.pow(pivotPt[1], 2) + math.pow(pivotPt[0], 2) - math.pow(b, 2))) - a1
            s1_2 = math.pow(nx1, 2) + math.pow((pivotPt[2] - c1), 2)
            s2_2 = math.pow((nx1 + 2 * a1), 2) + math.pow((pivotPt[2] - c1), 2)
            k_2  = math.pow(a2, 2) + math.pow(c3, 2)
            s1   = math.sqrt(s1_2)
            s2   = math.sqrt(s2_2)
            k    = math.sqrt(k_2)
            
            valid_solition = 1


            # Theta 1
            theta1_1     = math.atan2(pivotPt[1], pivotPt[0]) - math.atan2(b, (nx1 + a1))
            theta1_2     = math.atan2(pivotPt[1], pivotPt[0]) + math.atan2(b, (nx1 + a1)) - math.pi
            
            
            # Theta 2
            if abs((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) <= 1:
                theta2_1 = -math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) + math.atan2(nx1, (pivotPt[2] - c1))
                theta2_2 = math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) + math.atan2(nx1, (pivotPt[2] - c1))
            else:
                valid_solition = 0
                theta2_1 = math.atan2(nx1, (pivotPt[2] - c1))
                theta2_2 = math.atan2(nx1, (pivotPt[2] - c1))

            if abs((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) <= 1:
                theta2_3 = math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) - math.atan2((nx1 + 2 * a1), (pivotPt[2] - c1))
                theta2_4 = -(math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) + math.atan2((nx1 + 2 * a1), (pivotPt[2] - c1)))
            else:
                valid_solition = 0
                theta2_3 = - math.atan2((nx1 + 2 * a1), (pivotPt[2] - c1)) 
                theta2_4 = - math.atan2((nx1 + 2 * a1), (pivotPt[2] - c1)) 
            

            # Theta 3
            if abs((math.pow(c2, 2) + k_2 - s1_2) / (2 * c2 * k)) <= 1:
                theta3_1 = math.pi - (math.acos((math.pow(c2, 2) + k_2 - s1_2) / (2 * c2 * k)) - math.atan2(a2, c3))
                theta3_2 = math.pi - (-math.acos((math.pow(c2, 2) + k_2 - s1_2) / (2 * c2 * k)) - math.atan2(a2, c3))
            else:
                valid_solition = 0
                theta3_1 = math.pi - (math.pi - math.atan2(a2, c3))
                theta3_2 = math.pi - (-math.pi - math.atan2(a2, c3))

            if abs((math.pow(c2, 2) + k_2 - s2_2) / (2 * c2 * k)) <= 1:
                theta3_3 = -(math.pi - (math.acos((math.pow(c2, 2) + k_2 - s2_2) / (2 * c2 * k)) + math.atan2(a2, c3)))
                theta3_4 = -(math.pi - (-math.acos((math.pow(c2, 2) + k_2 - s2_2) / (2 * c2 * k)) + math.atan2(a2, c3)))
            else:
                valid_solition = 0
                theta3_3 = -(math.pi - (math.pi - math.atan2(a2, c3)))
                theta3_4 = -(math.pi - (-math.pi - math.atan2(a2, c3)))

            
            sin11 = math.sin(theta1_1)
            sin12 = math.sin(theta1_1)
            sin13 = math.sin(theta1_2)
            sin14 = math.sin(theta1_2)
            
            cos11 = math.cos(theta1_1)
            cos12 = math.cos(theta1_1)
            cos13 = math.cos(theta1_2)
            cos14 = math.cos(theta1_2)
            
            sin231 = math.sin(theta2_1 + theta3_1)
            sin232 = math.sin(theta2_2 + theta3_2)
            sin233 = math.sin(theta2_3 + theta3_3)
            sin234 = math.sin(theta2_4 + theta3_4)
            
            cos231 = math.cos(theta2_1 + theta3_1)
            cos232 = math.cos(theta2_2 + theta3_2)
            cos233 = math.cos(theta2_3 + theta3_3)
            cos234 = math.cos(theta2_4 + theta3_4)
            
            m11 = Re[0][2] * sin231 * cos11 + Re[1][2] * sin231 * sin11 + Re[2][2] * cos231
            m12 = Re[0][2] * sin232 * cos12 + Re[1][2] * sin232 * sin12 + Re[2][2] * cos232
            m13 = Re[0][2] * sin233 * cos13 + Re[1][2] * sin233 * sin13 + Re[2][2] * cos233
            m14 = Re[0][2] * sin234 * cos14 + Re[1][2] * sin234 * sin14 + Re[2][2] * cos234
            
            # Theta 4
            theta4_1 = math.atan2((Re[1][2] * cos11 - Re[0][2] * sin11), Re[0][2] * cos231 * cos11 + Re[1][2] * cos231 * sin11 - Re[2][2] * sin231)
            theta4_5 = theta4_1 + math.pi

            theta4_2 = math.atan2((Re[1][2] * cos12 - Re[0][2] * sin12), Re[0][2] * cos232 * cos12 + Re[1][2] * cos232 * sin12 - Re[2][2] * sin232)
            theta4_6 = theta4_2 + math.pi

            theta4_3 = math.atan2((Re[1][2] * cos13 - Re[0][2] * sin13), Re[0][2] * cos233 * cos13 + Re[1][2] * cos233 * sin13 - Re[2][2] * sin233)
            theta4_7 = theta4_3 + math.pi

            theta4_4 = math.atan2((Re[1][2] * cos14 - Re[0][2] * sin14), Re[0][2] * cos234 * cos14 + Re[1][2] * cos234 * sin14 - Re[2][2] * sin234)
            theta4_8 = theta4_4 + math.pi

            
            # Theta 5
            theta5_1 = math.atan2((math.sqrt(1 - math.pow(m11, 2))), m11)
            theta5_5 = -theta5_1

            theta5_2 = math.atan2((math.sqrt(1 - math.pow(m12, 2))), m12)
            theta5_6 = -theta5_2

            theta5_3 = math.atan2((math.sqrt(1 - math.pow(m13, 2))), m13)
            theta5_7 = -theta5_3

            theta5_4 = math.atan2((math.sqrt(1 - math.pow(m14, 2))), m14)
            theta5_8 = -theta5_4
            
            
            # Theta 6
            theta6_1 = math.atan2((Re[0][1] * sin231 * cos11 + Re[1][1] * sin231 * sin11 + Re[2][1] * cos231), (-Re[0][0] * sin231 * cos11 - Re[1][0] * sin231 * sin11 - Re[2][0] * cos231))
            theta6_5 = theta6_1 - math.pi

            theta6_2 = math.atan2((Re[0][1] * sin232 * cos12 + Re[1][1] * sin232 * sin12 + Re[2][1] * cos232), (-Re[0][0] * sin232 * cos12 - Re[1][0] * sin232 * sin12 - Re[2][0] * cos232))
            theta6_6 = theta6_2 - math.pi

            theta6_3 = math.atan2((Re[0][1] * sin233 * cos13 + Re[1][1] * sin233 * sin13 + Re[2][1] * cos233), (-Re[0][0] * sin233 * cos13 - Re[1][0] * sin233 * sin13 - Re[2][0] * cos233))
            theta6_7 = theta6_3 - math.pi

            theta6_4 = math.atan2((Re[0][1] * sin234 * cos14 + Re[1][1] * sin234 * sin14 + Re[2][1] * cos234), (-Re[0][0] * sin234 * cos14 - Re[1][0] * sin234 * sin14 - Re[2][0] * cos234))
            theta6_8 = theta6_4 - math.pi

                    
            theta1_Sol[0] = math.degrees(theta1_1)
            theta1_Sol[1] = math.degrees(theta1_2)
            
            theta2_Sol[0] = math.degrees(theta2_1)
            theta2_Sol[1] = math.degrees(theta2_2)
            theta2_Sol[2] = math.degrees(theta2_3)
            theta2_Sol[3] = math.degrees(theta2_4)
            
            theta3_Sol[0] = math.degrees(theta3_1)
            theta3_Sol[1] = math.degrees(theta3_2)
            theta3_Sol[2] = math.degrees(theta3_3)
            theta3_Sol[3] = math.degrees(theta3_4)
            
            theta4_Sol[0] = math.degrees(theta4_1)
            theta4_Sol[1] = math.degrees(theta4_2)
            theta4_Sol[2] = math.degrees(theta4_3)
            theta4_Sol[3] = math.degrees(theta4_4)
            theta4_Sol[4] = math.degrees(theta4_5)
            theta4_Sol[5] = math.degrees(theta4_6)
            theta4_Sol[6] = math.degrees(theta4_7)
            theta4_Sol[7] = math.degrees(theta4_8)
            
            theta5_Sol[0] = math.degrees(theta5_1)
            theta5_Sol[1] = math.degrees(theta5_2)
            theta5_Sol[2] = math.degrees(theta5_3)
            theta5_Sol[3] = math.degrees(theta5_4)
            theta5_Sol[4] = math.degrees(theta5_5)
            theta5_Sol[5] = math.degrees(theta5_6)
            theta5_Sol[6] = math.degrees(theta5_7)
            theta5_Sol[7] = math.degrees(theta5_8)
            
            theta6_Sol[0] = math.degrees(theta6_1)
            theta6_Sol[1] = math.degrees(theta6_2)
            theta6_Sol[2] = math.degrees(theta6_3)
            theta6_Sol[3] = math.degrees(theta6_4)
            theta6_Sol[4] = math.degrees(theta6_5)
            theta6_Sol[5] = math.degrees(theta6_6)
            theta6_Sol[6] = math.degrees(theta6_7)
            theta6_Sol[7] = math.degrees(theta6_8)        
            
            
            # select one of the 8 solutions        
    
            if soln1:
                jointVals[0] = theta1_Sol[0];
            
                if soln2: 
                    jointVals[1] = theta2_Sol[0];
                    jointVals[2] = theta3_Sol[0];
            
                    if soln3: 
                        jointVals[3] = theta4_Sol[0];
                        jointVals[4] = theta5_Sol[0];
                        jointVals[5] = theta6_Sol[0];
                    else:
                        jointVals[3] = theta4_Sol[4];
                        jointVals[4] = theta5_Sol[4];
                        jointVals[5] = theta6_Sol[4];
                                
                else:
                    jointVals[1] = theta2_Sol[1];
                    jointVals[2] = theta3_Sol[1];
            
                    if soln3:
                        jointVals[3] = theta4_Sol[1];
                        jointVals[4] = theta5_Sol[1];
                        jointVals[5] = theta6_Sol[1];
                    else:
                        jointVals[3] = theta4_Sol[5];
                        jointVals[4] = theta5_Sol[5];
                        jointVals[5] = theta6_Sol[5];
                       
            else:
                jointVals[0] = theta1_Sol[1];
            
                if soln2:
                    jointVals[1] = theta2_Sol[2];
                    jointVals[2] = theta3_Sol[2];
            
                    if soln3:
                        jointVals[3] = theta4_Sol[2];
                        jointVals[4] = theta5_Sol[2];
                        jointVals[5] = theta6_Sol[2];
                    else:
                        jointVals[3] = theta4_Sol[6];
                        jointVals[4] = theta5_Sol[6];
                        jointVals[5] = theta6_Sol[6];
                              
                else:
                    jointVals[1] = theta2_Sol[3];
                    jointVals[2] = theta3_Sol[3];
            
                    if soln3:
                        jointVals[3] = theta4_Sol[3];
                        jointVals[4] = theta5_Sol[3];
                        jointVals[5] = theta6_Sol[3];
                    else:
                        jointVals[3] = theta4_Sol[7];
                        jointVals[4] = theta5_Sol[7];
                        jointVals[5] = theta6_Sol[7];            
            
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
                
                # Offset J2/J3 axes
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