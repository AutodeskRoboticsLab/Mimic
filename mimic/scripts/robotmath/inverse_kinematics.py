#!usr/bin/env python
"""
Inverse kinematics solver
"""

import math

LARGE_NUMBER = 9e9

# To-do: Implement appraximation if no valid configuration exists for the given
# target pose (represented by ValueError math domain error)


def solver(robot_definition, pivot_point, tcp_rotation):
    """
    Fast inverse kinematic solver for most 6-axis industrial robots.
    Implementation based on 'An Analytical Solution of the Inverse Kinematics
    Problem of Industrial Serial Manipulators with an Orth-parallel Basis and
    a Spherical Wrist' by Brandstotter, Angerer, Hofbaur, 2014. Find reference
    provided at: references/IKSphericalWrist.pdf.
    :param robot_definition: List of seven essential geometrical parameters.
    :param pivot_point: Intersection (pivot) point of axes 4, 5, 6.
    :param tcp_rotation: Rotation matrix (3x3) for TCP.
    :return:
    """

    a1 = robot_definition[0]
    a2 = robot_definition[1]
    b = robot_definition[2]
    c1 = robot_definition[3]
    c2 = robot_definition[4]
    c3 = robot_definition[5]
    c4 = robot_definition[6]

    # Initialize arrays
    theta1_sol = [0 for i in range(2)]
    theta2_sol = [0 for i in range(4)]
    theta3_sol = [0 for i in range(4)]
    theta4_sol = [0 for i in range(8)]
    theta5_sol = [0 for i in range(8)]
    theta6_sol = [0 for i in range(8)]

    # SOLVE #
    nx1 = math.sqrt((math.pow(pivot_point[1], 2) + math.pow(pivot_point[0], 2) - math.pow(b, 2))) - a1
    s1_2 = math.pow(nx1, 2) + math.pow((pivot_point[2] - c1), 2)
    s2_2 = math.pow((nx1 + 2 * a1), 2) + math.pow((pivot_point[2] - c1), 2)
    k_2 = math.pow(a2, 2) + math.pow(c3, 2)
    s1 = math.sqrt(s1_2)
    s2 = math.sqrt(s2_2)
    k = math.sqrt(k_2)

    # Theta 1
    theta1_1 = math.atan2(pivot_point[1], pivot_point[0]) - math.atan2(b, (nx1 + a1))
    theta1_2 = math.atan2(pivot_point[1], pivot_point[0]) + math.atan2(b, (nx1 + a1)) - math.pi

    # Theta 2
    try:
        theta2_1 = -math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) +\
                   math.atan2(nx1, (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_1 = LARGE_NUMBER

    try:
        theta2_2 = math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) +\
                   math.atan2(nx1, (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_2 = LARGE_NUMBER

    try:
        theta2_3 = math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) -\
                   math.atan2((nx1 + 2 * a1), (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_3 = LARGE_NUMBER

    try:
        theta2_4 = -(math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) +\
                     math.atan2((nx1 + 2 * a1), (pivot_point[2] - c1)))
    except ValueError:  # math domain error
        theta2_4 = LARGE_NUMBER

    # Theta 3
    try:
        theta3_1 = math.pi - (math.acos((math.pow(c2, 2) + k_2 - s1_2) / (2 * c2 * k)) - math.atan2(a2, c3))
    except ValueError:  # math domain error
        theta3_1 = LARGE_NUMBER
    try:
        theta3_2 = math.pi - (-math.acos((math.pow(c2, 2) + k_2 - s1_2) / (2 * c2 * k)) - math.atan2(a2, c3))
    except ValueError:  # math domain error
        theta3_2 = LARGE_NUMBER
    try:
        theta3_3 = -(math.pi - (math.acos((math.pow(c2, 2) + k_2 - s2_2) / (2 * c2 * k)) + math.atan2(a2, c3)))
    except ValueError:  # math domain error
        theta3_3 = LARGE_NUMBER
    try:
        theta3_4 = -(math.pi - (-math.acos((math.pow(c2, 2) + k_2 - s2_2) / (2 * c2 * k)) + math.atan2(a2, c3)))
    except ValueError:  # math domain error
        theta3_4 = LARGE_NUMBER

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

    m11 = tcp_rotation[0][2] * sin231 * cos11 + tcp_rotation[1][2] * sin231 * sin11 + tcp_rotation[2][2] * cos231
    m12 = tcp_rotation[0][2] * sin232 * cos12 + tcp_rotation[1][2] * sin232 * sin12 + tcp_rotation[2][2] * cos232
    m13 = tcp_rotation[0][2] * sin233 * cos13 + tcp_rotation[1][2] * sin233 * sin13 + tcp_rotation[2][2] * cos233
    m14 = tcp_rotation[0][2] * sin234 * cos14 + tcp_rotation[1][2] * sin234 * sin14 + tcp_rotation[2][2] * cos234

    # Theta 4
    try:
        theta4_1 = math.atan2((tcp_rotation[1][2] * cos11 - tcp_rotation[0][2] * sin11),
                              tcp_rotation[0][2] * cos231 * cos11 + tcp_rotation[1][2] * cos231 * sin11 -
                              tcp_rotation[2][2] * sin231)
        theta4_5 = theta4_1 + math.pi
    except ValueError:  # math domain error
        theta4_1 = LARGE_NUMBER
        theta4_5 = LARGE_NUMBER
    try:
        theta4_2 = math.atan2((tcp_rotation[1][2] * cos12 - tcp_rotation[0][2] * sin12),
                              tcp_rotation[0][2] * cos232 * cos12 + tcp_rotation[1][2] * cos232 * sin12 -
                              tcp_rotation[2][2] * sin232)
        theta4_6 = theta4_2 + math.pi
    except ValueError:  # math domain error
        theta4_2 = LARGE_NUMBER
        theta4_6 = LARGE_NUMBER
    try:
        theta4_3 = math.atan2((tcp_rotation[1][2] * cos13 - tcp_rotation[0][2] * sin13),
                              tcp_rotation[0][2] * cos233 * cos13 + tcp_rotation[1][2] * cos233 * sin13 -
                              tcp_rotation[2][2] * sin233)
        theta4_7 = theta4_3 + math.pi
    except ValueError:  # math domain error
        theta4_3 = LARGE_NUMBER
        theta4_7 = LARGE_NUMBER
    try:
        theta4_4 = math.atan2((tcp_rotation[1][2] * cos14 - tcp_rotation[0][2] * sin14),
                              tcp_rotation[0][2] * cos234 * cos14 + tcp_rotation[1][2] * cos234 * sin14 -
                              tcp_rotation[2][2] * sin234)
        theta4_8 = theta4_4 + math.pi
    except ValueError:  # math domain error
        theta4_4 = LARGE_NUMBER
        theta4_8 = LARGE_NUMBER

    # Theta 5
    try:
        theta5_1 = math.atan2((math.sqrt(1 - math.pow(m11, 2))), m11)
        theta5_5 = -theta5_1
    except ValueError:  # math domain error
        theta5_1 = LARGE_NUMBER
        theta5_5 = LARGE_NUMBER
    try:
        theta5_2 = math.atan2((math.sqrt(1 - math.pow(m12, 2))), m12)
        theta5_6 = -theta5_2
    except ValueError:  # math domain error
        theta5_2 = LARGE_NUMBER
        theta5_6 = LARGE_NUMBER
    try:
        theta5_3 = math.atan2((math.sqrt(1 - math.pow(m13, 2))), m13)
        theta5_7 = -theta5_3
    except ValueError:  # math domain error
        theta5_3 = LARGE_NUMBER
        theta5_7 = LARGE_NUMBER
    try:
        theta5_4 = math.atan2((math.sqrt(1 - math.pow(m14, 2))), m14)
        theta5_8 = -theta5_4
    except ValueError:  # math domain error
        theta5_4 = LARGE_NUMBER
        theta5_8 = LARGE_NUMBER

    # Theta 6
    try:
        theta6_1 = math.atan2(
            (tcp_rotation[0][1] * sin231 * cos11 + tcp_rotation[1][1] * sin231 * sin11 + tcp_rotation[2][1] * cos231),
            (-tcp_rotation[0][0] * sin231 * cos11 - tcp_rotation[1][0] * sin231 * sin11 - tcp_rotation[2][0] * cos231))
        theta6_5 = theta6_1 - math.pi
    except ValueError:  # math domain error
        theta6_1 = LARGE_NUMBER
        theta6_5 = LARGE_NUMBER
    try:
        theta6_2 = math.atan2(
            (tcp_rotation[0][1] * sin232 * cos12 + tcp_rotation[1][1] * sin232 * sin12 + tcp_rotation[2][1] * cos232),
            (-tcp_rotation[0][0] * sin232 * cos12 - tcp_rotation[1][0] * sin232 * sin12 - tcp_rotation[2][0] * cos232))
        theta6_6 = theta6_2 - math.pi
    except ValueError:  # math domain error
        theta6_2 = LARGE_NUMBER
        theta6_6 = LARGE_NUMBER
    try:
        theta6_3 = math.atan2(
            (tcp_rotation[0][1] * sin233 * cos13 + tcp_rotation[1][1] * sin233 * sin13 + tcp_rotation[2][1] * cos233),
            (-tcp_rotation[0][0] * sin233 * cos13 - tcp_rotation[1][0] * sin233 * sin13 - tcp_rotation[2][0] * cos233))
        theta6_7 = theta6_3 - math.pi
    except ValueError:  # math domain error
        theta6_3 = LARGE_NUMBER
        theta6_7 = LARGE_NUMBER
    try:
        theta6_4 = math.atan2(
            (tcp_rotation[0][1] * sin234 * cos14 + tcp_rotation[1][1] * sin234 * sin14 + tcp_rotation[2][1] * cos234),
            (-tcp_rotation[0][0] * sin234 * cos14 - tcp_rotation[1][0] * sin234 * sin14 - tcp_rotation[2][0] * cos234))
        theta6_8 = theta6_4 - math.pi
    except ValueError:  # math domain error
        theta6_4 = LARGE_NUMBER
        theta6_8 = LARGE_NUMBER

    theta1_sol[0] = math.degrees(theta1_1)
    theta1_sol[1] = math.degrees(theta1_2)

    theta2_sol[0] = math.degrees(theta2_1)
    theta2_sol[1] = math.degrees(theta2_2)
    theta2_sol[2] = math.degrees(theta2_3)
    theta2_sol[3] = math.degrees(theta2_4)

    theta3_sol[0] = math.degrees(theta3_1)
    theta3_sol[1] = math.degrees(theta3_2)
    theta3_sol[2] = math.degrees(theta3_3)
    theta3_sol[3] = math.degrees(theta3_4)

    theta4_sol[0] = math.degrees(theta4_1)
    theta4_sol[1] = math.degrees(theta4_2)
    theta4_sol[2] = math.degrees(theta4_3)
    theta4_sol[3] = math.degrees(theta4_4)
    theta4_sol[4] = math.degrees(theta4_5)
    theta4_sol[5] = math.degrees(theta4_6)
    theta4_sol[6] = math.degrees(theta4_7)
    theta4_sol[7] = math.degrees(theta4_8)

    theta5_sol[0] = math.degrees(theta5_1)
    theta5_sol[1] = math.degrees(theta5_2)
    theta5_sol[2] = math.degrees(theta5_3)
    theta5_sol[3] = math.degrees(theta5_4)
    theta5_sol[4] = math.degrees(theta5_5)
    theta5_sol[5] = math.degrees(theta5_6)
    theta5_sol[6] = math.degrees(theta5_7)
    theta5_sol[7] = math.degrees(theta5_8)

    theta6_sol[0] = math.degrees(theta6_1)
    theta6_sol[1] = math.degrees(theta6_2)
    theta6_sol[2] = math.degrees(theta6_3)
    theta6_sol[3] = math.degrees(theta6_4)
    theta6_sol[4] = math.degrees(theta6_5)
    theta6_sol[5] = math.degrees(theta6_6)
    theta6_sol[6] = math.degrees(theta6_7)
    theta6_sol[7] = math.degrees(theta6_8)

    all_solutions = [
        theta1_sol,
        theta2_sol,
        theta3_sol,
        theta4_sol,
        theta5_sol,
        theta6_sol
    ]

    return all_solutions


def solve_spherical_wrist(tcp, tcp_mat, lcs, lcs_mat, target, target_mat, robot_definition, sols=[1, 1, 1]):
    """
    Fast inverse kinematic solver for most 6-axis industrial robots.
    Implementation based on 'An Analytical Solution of the Inverse Kinematics
    Problem of Industrial Serial Manipulators with an Orth-parallel Basis and
    a Spherical Wrist' by Brandstotter, Angerer, Hofbaur, 2014. Find reference
    provided at: references/IKSphericalWrist.pdf.

    This is primarilly called by the robotIK.py plugin node from Maya's DG
    :param : 
    :param :
    :param :
    :return:
    """
    tcpX = tcp[0]
    tcpY = tcp[1]
    tcpZ = tcp[2]

    lcsX = lcs[0]
    lcsY = lcs[1]
    lcsZ = lcs[2]

    targetX = target[0]
    targetY = target[1]
    targetZ = target[2]

    a1 = robot_definition[0]
    a2 = robot_definition[1]
    b = robot_definition[2]
    c1 = robot_definition[3]
    c2 = robot_definition[4]
    c3 = robot_definition[5]
    c4 = robot_definition[6]

    soln1 = sols[0]
    soln2 = sols[1]
    soln3 = sols[2]

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
    tcpTrans       = _array_mult(Rtm, tcpTrans) # Convert tcp translation from Maya frame to robot tool frame
    
    lcsTrans[0][0] = lcsX                     # Get translation of local base frame w.r.t robot world frame (Square controller)
    lcsTrans[1][0] = lcsY                     #
    lcsTrans[2][0] = lcsZ                     #
    lcsTrans       = _array_mult(Ram, lcsTrans) # Convert lcs translation to robot world frame        

    targetPt[0][0] = targetX                  # Get translation of target in maya frame w.r.t robot world frame (Square controller)
    targetPt[1][0] = targetY                  #
    targetPt[2][0] = targetZ                  #
    targetPt       = _array_mult(Ram, targetPt) # Convert target translation translation to robot world frame        

    # Convert Maya format rotation matrices to truncated format
    tcpRotXAxis = [[tcp_mat[0]],[tcp_mat[1]],[tcp_mat[2]]]
    tcpRotYAxis = [[tcp_mat[4]],[tcp_mat[5]],[tcp_mat[6]]]
    tcpRotZAxis = [[tcp_mat[8]],[tcp_mat[9]],[tcp_mat[10]]]
    tcp_matTrunc = tpose([tpose(tcpRotXAxis)[0], tpose(tcpRotYAxis)[0], tpose(tcpRotZAxis)[0]])
    
    tcpRot      = tpose(_array_mult(Rtm, tcp_matTrunc)) # Convert tcp rotation matrix to robot tool frame
    
    lcsRotXAxis = [[lcs_mat[0]],[lcs_mat[1]],[lcs_mat[2]]]
    lcsRotYAxis = [[lcs_mat[4]],[lcs_mat[5]],[lcs_mat[6]]]
    lcsRotZAxis = [[lcs_mat[8]],[lcs_mat[9]],[lcs_mat[10]]]
    lcs_matTrunc = tpose([tpose(lcsRotXAxis)[0], tpose(lcsRotYAxis)[0], tpose(lcsRotZAxis)[0]])
    
    lcsRot      = tpose(_array_mult(Ram, lcs_matTrunc)) # Convert local base frame rotation matrix to robot world frame
    
    targetRotXAxis = [[target_mat[0]],[target_mat[1]],[target_mat[2]]]
    targetRotYAxis = [[target_mat[4]],[target_mat[5]],[target_mat[6]]]
    targetRotZAxis = [[target_mat[8]],[target_mat[9]],[target_mat[10]]]
    target_matTrunc = tpose([tpose(targetRotXAxis)[0], tpose(targetRotYAxis)[0], tpose(targetRotZAxis)[0]])
    
    targetRot      = tpose(_array_mult(Ram, target_matTrunc)) # Convert target rotation matrix to robot world frame        
    
    
    # Find Flange and Pivot locations in local robot frame
    Re = _array_mult(tpose(targetRot), tcpRot)                                             # Rotation of the tcp w.r.t the target in robot world frame (square controller)
    Rlm = _array_mult(Ram, lcsRot)                                                         # Transformation of local coordinate system in Maya frame (still not sure why)
    
    targetPt = [i - j for i,j in zip(tpose(targetPt)[0], tpose(lcsTrans)[0])]            # Find distance from local base frame (circle controller)
                                                                                         # to target point in robot world frame
                                                                              
    flangePt = [i - j for i,j in zip(targetPt, tpose(_array_mult(Re,tcpTrans))[0])]        # Find the flange point in robot world frame 
    pivotPt  = [i - j for i,j in zip(flangePt, tpose(_array_mult(Re, T))[0])]              # Find the pivot point in robot world frame
    
    flangePt  = tpose(_array_mult(Rlm, [[flangePt[0]], [flangePt[1]], [flangePt[2]]]))[0]  # Convert flange point to local frame (circle controller)
    pivotPt  = tpose(_array_mult(Rlm, [[pivotPt[0]], [pivotPt[1]], [pivotPt[2]]]))[0]      # Convert pivot point to local frame (circle controller)
    
    Re = _array_mult(Rlm, Re)                                                              # Rotation of the tcp w.r.t the target in robot local frame (cirlce controller) 
    
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
        jointVals[0] = theta1_Sol[0]
    
        if soln2: 
            jointVals[1] = theta2_Sol[0]
            jointVals[2] = theta3_Sol[0]
    
            if soln3: 
                jointVals[3] = theta4_Sol[0]
                jointVals[4] = theta5_Sol[0]
                jointVals[5] = theta6_Sol[0]
            else:
                jointVals[3] = theta4_Sol[4]
                jointVals[4] = theta5_Sol[4]
                jointVals[5] = theta6_Sol[4]
                        
        else:
            jointVals[1] = theta2_Sol[1]
            jointVals[2] = theta3_Sol[1]
    
            if soln3:
                jointVals[3] = theta4_Sol[1]
                jointVals[4] = theta5_Sol[1]
                jointVals[5] = theta6_Sol[1]
            else:
                jointVals[3] = theta4_Sol[5]
                jointVals[4] = theta5_Sol[5]
                jointVals[5] = theta6_Sol[5]
               
    else:
        jointVals[0] = theta1_Sol[1]
    
        if soln2:
            jointVals[1] = theta2_Sol[2]
            jointVals[2] = theta3_Sol[2]
    
            if soln3:
                jointVals[3] = theta4_Sol[2]
                jointVals[4] = theta5_Sol[2]
                jointVals[5] = theta6_Sol[2]
            else:
                jointVals[3] = theta4_Sol[6]
                jointVals[4] = theta5_Sol[6]
                jointVals[5] = theta6_Sol[6]
                      
        else:
            jointVals[1] = theta2_Sol[3]
            jointVals[2] = theta3_Sol[3]
    
            if soln3:
                jointVals[3] = theta4_Sol[3]
                jointVals[4] = theta5_Sol[3]
                jointVals[5] = theta6_Sol[3]
            else:
                jointVals[3] = theta4_Sol[7]
                jointVals[4] = theta5_Sol[7]
                jointVals[5] = theta6_Sol[7] 
    
    return jointVals


def solve_hawkins_keating(tcp, tcp_mat, lcs, lcs_mat, target, target_mat, robot_definition, sols=[1, 1, 1]):
    """
    Fast inverse kinematic solver for most 6-axis "co-bots" 
    (e.g. Universal Robots).
    Implementation based on 'Analytic Inverse Kinematics for the Universal Robots' 
    by Hawkins, 2013 and 'UR5 Inverse Kinematics' by Keating. Find reference
    provided at: references/IKHawkins.pdf and references/IKKeating.pdf.
    :param :
    :param :
    :param :
    :return:
    """
    sol_1 = sols[0]
    sol_2 = sols[1]
    sol_3 = sols[2]

    # If the sol_1 boolean is 0, the other solutions invert
    # To solve this, we check to see if sol_1 is 0, then flip the others if so
    if not sol_1:
        sol_2 = not sol_2
        sol_3 = not sol_3

    tcpX = tcp[0]
    tcpY = tcp[1]
    tcpZ = tcp[2]

    lcsX = lcs[0]
    lcsY = lcs[1]
    lcsZ = lcs[2]

    targetX = target[0]
    targetY = target[1]
    targetZ = target[2]

    # Get D-H Parameters from robot_definition
    d_1 = robot_definition[0]
    d_4 = robot_definition[1]
    d_5 = robot_definition[2]
    d_6 = robot_definition[3]
    a_2 = robot_definition[4]
    a_3 = robot_definition[5]     
     
    # Initialized lists
    tcp_rot = [[0] * 3 for _ in range(3)]
    target_rot = [[0] * 3 for _ in range(3)]
    lcs_trans = [[0] * 1 for _ in range(3)]
    tcp_trans = [[0] * 1 for _ in range(3)]
    target_point = [[0] * 1 for _ in range(3)]
     
    # Define translation vector from the tool flange to the wrist frame.
    _t = [[0], [0], [-d_6], [1]]
     
    # ====================#
    #  Frame Definitions  #
    # ====================#
    
    # The following are Maya specific.
    # These can be substituted with your own frame definititions 
    target_ctrl_path = 'target_CTRL'

    # Tool Center Point (TCP) locator
    tcp_path = 'tcp_HDL'
    tcp = pm.ls(tcp_path)[0]
    # Local Base Frame controller (circle control at base of the robot in Maya).
    lcs = pm.ls('local_CTRL')[0]
    # Target Frame controller (square control at the robot's tool flange in Maya).
    target_path = 'target_HDL'
    target = pm.ls(target_path)[0]
     
    # Maya uses a different coordinate system than our IK solver, so we have
    # to convert from Maya's frame to the solver's frame.
    # If your base frame is different, you can substitute the transformation here.
     
    # Solver's tool frame (X,Y,Z) = Maya's tool frame (X, Y, Z)
    # UR solver tool and maya tool are the same
    # Rotation matrix from Maya tool frame to solver's tool frame.
    r_tool_frame = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  
     
    # Solver world frame (X,Y,Z) = Maya world frame (-Z, -X, Y)
    # Rotation matrix from Maya's world frame to solver world frame.
    r_world_frame = [[0, 0, -1], [-1, 0, 0], [0, 1, 0]]
     
    # Get local translation of the TCP w.r.t. tool flange.
    tcp_trans[0][0] = tcpX
    tcp_trans[1][0] = tcpY
    tcp_trans[2][0] = tcpZ
     
     
    # Convert TCP translation from Maya's tool frame to solver tool frame.
    tcp_trans = _array_mult(r_tool_frame, tcp_trans)
     
    # Get translation of local base frame (Circle controller) w.r.t robot's
    # world frame (Square controller).
    lcs_trans[0][0] = lcs.getTranslation()[0]
    lcs_trans[1][0] = lcs.getTranslation()[1]
    lcs_trans[2][0] = lcs.getTranslation()[2]
         
    # Convert lcs translation from Maya's world frame to solver world frame.
    lcs_trans = _array_mult(r_world_frame, lcs_trans)
     
    # Get translation of target in Maya's world frame w.r.t robot world frame
    # (Square controller).
    target_point[0][0] = target.getTranslation()[0]
    target_point[1][0] = target.getTranslation()[1]
    target_point[2][0] = target.getTranslation()[2]
         
    # Convert target translation from Maya's world frame to solver world frame.
    target_point = _array_mult(r_world_frame, target_point)
     
    # Get lcs, tcp, and target rotation matrices in Maya's world frame
    lcs_matrix = pm.xform(lcs, query=True, os=True, m=True)
    tcp_matrix = pm.xform(tcp, query=True, os=True, m=True)
    target_matrix = pm.xform(target, query=True, os=True, m=True)
     
    # Convert Maya formatted rotation matrices to truncated format
    # Tool center point (TCP) matrix
    tcp_x_axis = [[tcp_matrix[0]], [tcp_matrix[1]], [tcp_matrix[2]]]
    tcp_y_axis = [[tcp_matrix[4]], [tcp_matrix[5]], [tcp_matrix[6]]]
    tcp_z_axis = [[tcp_matrix[8]], [tcp_matrix[9]], [tcp_matrix[10]]]
    tcp_matrix_truncated = general_utils.transpose_list(
        [general_utils.transpose_list(tcp_x_axis)[0],
         general_utils.transpose_list(tcp_y_axis)[0],
         general_utils.transpose_list(tcp_z_axis)[0]])
              
    # Convert truncated tcp rotation matrix to solver tool frame
    tcp_rot = general_utils.transpose_list(
        _array_mult(r_tool_frame, tcp_matrix_truncated))
     
    # Local coordinate system matrix (circle controller)
    lcs_x_axis = [[lcs_matrix[0]], [lcs_matrix[1]], [lcs_matrix[2]]]
    lcs_y_axis = [[lcs_matrix[4]], [lcs_matrix[5]], [lcs_matrix[6]]]
    lcs_z_axis = [[lcs_matrix[8]], [lcs_matrix[9]], [lcs_matrix[10]]]
    lcs_matrix_truncated = general_utils.transpose_list(
        [general_utils.transpose_list(lcs_x_axis)[0],
         general_utils.transpose_list(lcs_y_axis)[0],
         general_utils.transpose_list(lcs_z_axis)[0]])
              
    # Convert local base frame rotation matrix to solver world frame
    lcs_rot = general_utils.transpose_list(
        _array_mult(r_world_frame,
                                                  lcs_matrix_truncated))
     
    # Target rotation matrix
    target_x_axis = [[target_matrix[0]], [target_matrix[1]], [target_matrix[2]]]
    target_y_axis = [[target_matrix[4]], [target_matrix[5]], [target_matrix[6]]]
    target_z_axis = [[target_matrix[8]], [target_matrix[9]], [target_matrix[10]]]
    target_matrix_truncated = general_utils.transpose_list(
        [general_utils.transpose_list(target_x_axis)[0],
         general_utils.transpose_list(target_y_axis)[0],
         general_utils.transpose_list(target_z_axis)[0]])
          
    # Convert target rotation matrix to solver world frame
    target_rot = general_utils.transpose_list(
        _array_mult(r_world_frame,
                                              target_matrix_truncated))
     
    # Find Flange Point location in solver world frame
    #
    # Rotation of the tcp w.r.t to the target in solver world frame
    _re = _array_mult(
        general_utils.transpose_list(target_rot), tcp_rot)
     
    # Rotation of the robot's local coordinate system (circle
    # controller) w.r.t the solver world frame
    _rlm = _array_mult(r_world_frame, lcs_rot)
     
    # Find distance from the robot's local coordinate system (circle
    # controller) to target point in solver world frame
    target_point = [i - j for i, j in zip(
        general_utils.transpose_list(target_point)[0],
        general_utils.transpose_list(lcs_trans)[0])]
     
    # Find the flange point in the solver's world frame
    flange_point = [i - j for i, j in zip(target_point,
                                          general_utils.transpose_list(
                                              _array_mult(_re, tcp_trans))[0])]
     
     
    # Find the flange point in solver's world frame
    flange_point = general_utils.transpose_list(
        _array_mult(_rlm,
                                              [[flange_point[0]],
                                               [flange_point[1]],
                                               [flange_point[2]]]))[0]
     
    # Define the Rotation of the tcp w.r.t the target in robot's local frame
    # (cirlce controller)
    _re = _array_mult(_rlm, _re)
     
     
    #########
    # SOLVE #
    #########
    # The solve is only dependent on the DH-Params, _re, and flange_point
     
    # Construct T0_6, the transformation matric of the Frame 6 WRT the Base frame 0
    T0_6 = _re
    T0_6[0].append(flange_point[0])
    T0_6[1].append(flange_point[1])
    T0_6[2].append(flange_point[2])
     
    # Define Position of Frame 6, P, WRT the base frame 0. This is == flange_point
    P0_6 = flange_point
     
    # Assign x, y, and z-components of T0_6 to variables for ease of callback
    T06_XX = T0_6[0][0]
    T06_XY = T0_6[0][1]
    T06_XZ = T0_6[0][2]
    T06_YX = T0_6[1][0]
    T06_YY = T0_6[1][1]
    T06_YZ = T0_6[1][2]
    T06_ZX = T0_6[2][0]
    T06_ZY = T0_6[2][1]
    T06_ZZ = T0_6[2][2]
    T06_X = P0_6[0]
    T06_Y = P0_6[1]
    T06_Z = P0_6[2]
     
     
    #--------------#
    # Find Theta 1 #
    #--------------#
    # To we first determine the location of frame 5 (the wrist frame)
    # in relation to the base frame 0: P0_5
    # P0_5 can be found by translating backwards from frame 6 to frame 5 along z_6
    P0_5 = _array_mult(T0_6, _t)
    P0_5 = general_utils.transpose_list(P0_5)[0]
     
    nx1 = math.sqrt(math.pow(P0_5[0], 2) + math.pow(P0_5[1], 2))
     
    if sol_1:
        theta_1 = math.atan2(P0_5[1], P0_5[0]) + math.acos(d_4/nx1) + math.pi/2.0
    else:
        theta_1 = math.atan2(P0_5[1], P0_5[0]) - math.acos(d_4/nx1) + math.pi/2.0
     
    # Bound Theta between +/- 180 degrees
    if abs(theta_1) > math.pi:
        sign = abs(theta_1)/theta_1
        theta_1 += -(sign * 2*math.pi)
         
     
    #--------------#
    # Find Theta 5 #
    #--------------#
    if sol_3:
        theta_5 = -math.acos((T06_X*math.sin(theta_1) - T06_Y*math.cos(theta_1) - d_4) / d_6)
    else:
        theta_5 = math.acos((T06_X*math.sin(theta_1) - T06_Y*math.cos(theta_1) - d_4) / d_6)
     
     
    #--------------#
    # Find Theta 6 #
    #--------------#
    s1 = math.sin(theta_1)
    c1 = math.cos(theta_1)
    s5 = math.sin(theta_5)
    c5 = math.cos(theta_5)

    n1 = -T06_XY*s1 + T06_YY*c1
    n2 = T06_XX*s1 - T06_YX*c1
     
    theta_6 = math.atan2(n1/s5, n2/s5)
         
 
    #--------------#
    # Find Theta 3 #
    #--------------#
    s6 = math.sin(theta_6)
    c6 = math.cos(theta_6)
    
    # Find the X- and Y- components of the position of Frame 4 WRT Frame 1:
    # P14_X and P14_Y 
    P14_X = d_5*(s6*(T06_XX*c1 + T06_YX*s1) + c6*(T06_XY*c1 + T06_YY*s1)) - d_6*(T06_XZ*c1 + T06_YZ*s1) + T06_X*c1 + T06_Y*s1
    P14_Y = T06_Z - d_1 - d_6*T06_ZZ + d_5*(T06_ZY*c6 + T06_ZX*s6)
    
    P14_XY_2 = P14_X*P14_X + P14_Y*P14_Y

    c3 = (P14_XY_2 - a_2*a_2 - a_3*a_3) / (2.0*a_2*a_3)
     
    if sol_2:
        theta_3 = math.acos(c3)
    else:
        theta_3 = 2*math.pi - math.acos(c3)  
     
     
    #--------------#
    # Find Theta 2 #
    #--------------#
    s3 = math.sin(theta_3)
     
    denom = a_2*a_2 + a_3*a_3 + 2*a_2*a_3*c3
    nc_1 = (a_2 + a_3*c3)
    nc_2 = a_3*s3
     
    theta_2 = math.atan2((nc_1*P14_Y - nc_2*P14_X) / denom, (nc_1*P14_X + nc_2*P14_Y) / denom) - math.pi
     
     
    #--------------#
    # Find Theta 4 #
    #--------------#
    c23 = math.cos(theta_2 + theta_3);
    s23 = math.sin(theta_2 + theta_3);
    
    T04_XX = -s5*(T06_XZ*c1 + T06_YZ*s1) - c5*(s6*(T06_XY*c1 + T06_YY*s1) - c6*(T06_XX*c1 + T06_YX*s1))
    T04_XY = c5*(T06_ZX*c6 - T06_ZY*s6) - T06_ZZ*s5

    if sol_3:
        theta_4 = math.atan2(c23*T04_XY - s23*T04_XX, T04_XX*c23 + T04_XY*s23)
    else:
        theta_4 = math.atan2(c23*T04_XY - s23*T04_XX, T04_XX*c23 + T04_XY*s23)
    
    # Theta 6 is off by 180 degrees (haven't gotten to the bottom of this yet)
    # So we adjust Theta 6 by 180, then make sure it is bound between +/- 180
    theta_6 = theta_6 - math.pi
    
    if abs(theta_6) > math.pi:
        sign = abs(theta_6)/theta_6
        theta_6 += -(sign * 2*math.pi)
        
    # Convert all angles to degrees and assign to a dictionary
    theta_1 = math.degrees(theta_1)
    theta_2 = math.degrees(theta_2)
    theta_3 = math.degrees(theta_3)
    theta_4 = math.degrees(theta_4)
    theta_5 = math.degrees(theta_5)
    theta_6 = math.degrees(theta_6)


# Utility Functions
def _array_mult(X,Y):
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

def select_solution(all_solutions, sol_1=False, sol_2=False, sol_3=False):
    """
    Select an inverse kinematic solution given all solutions.
    :param all_solutions: All solutions from inverse kinematic solver
    :param sol_1: Solution 1 parameter
    :param sol_2: Solution 2 parameter
    :param sol_3: Solution 3 parameter
    :return: 
    """
    axes = [0 for i in range(6)]
    theta1_sol = all_solutions[0]
    theta2_sol = all_solutions[1]
    theta3_sol = all_solutions[2]
    theta4_sol = all_solutions[3]
    theta5_sol = all_solutions[4]
    theta6_sol = all_solutions[5]

    if sol_1:
        axes[0] = theta1_sol[0]

        if sol_2:
            axes[1] = theta2_sol[0]
            axes[2] = theta3_sol[0]

            if sol_3:
                axes[3] = theta4_sol[0]
                axes[4] = theta5_sol[0]
                axes[5] = theta6_sol[0]
            else:  # not sol_3
                axes[3] = theta4_sol[4]
                axes[4] = theta5_sol[4]
                axes[5] = theta6_sol[4]

        else:  # not sol_2
            axes[1] = theta2_sol[1]
            axes[2] = theta3_sol[1]

            if sol_3:
                axes[3] = theta4_sol[1]
                axes[4] = theta5_sol[1]
                axes[5] = theta6_sol[1]
            else:  # not sol_3
                axes[3] = theta4_sol[5]
                axes[4] = theta5_sol[5]
                axes[5] = theta6_sol[5]

    else:  # not sol_1
        axes[0] = theta1_sol[1]

        if sol_2:
            axes[1] = theta2_sol[2]
            axes[2] = theta3_sol[2]

            if sol_3:
                axes[3] = theta4_sol[2]
                axes[4] = theta5_sol[2]
                axes[5] = theta6_sol[2]
            else:  # not sol_3
                axes[3] = theta4_sol[6]
                axes[4] = theta5_sol[6]
                axes[5] = theta6_sol[6]

        else:  # not sol_2
            axes[1] = theta2_sol[3]
            axes[2] = theta3_sol[3]

            if sol_3:
                axes[3] = theta4_sol[3]
                axes[4] = theta5_sol[3]
                axes[5] = theta6_sol[3]
            else:  # not sol_3
                axes[3] = theta4_sol[7]
                axes[4] = theta5_sol[7]
                axes[5] = theta6_sol[7]

    return axes
