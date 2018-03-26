#!usr/bin/env python
"""
Inverse kinematics solver
"""

import math


LARGE_NUMBER = 9e9 


def solver(robot_definition, pivot_point, tcp_rotation):
    """
    Fast inverse kinematic solver for most 6-axis industrial robots.
    Implementation based on 'An Analytical Solution of the Inverse Kinematics
    Problem of Industrial Serial Manipulators with an Orth-parallel Basis and
    a Spherical Wrist' by Brandstotter, Angerer, Hofbaur, 2014. Find reference
    provided at: mimic/docs/references/IKSphericalWrist.pdf
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
        theta2_1 = -math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) + math.atan2(nx1, (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_1 = LARGE_NUMBER

    try:
        theta2_2 = math.acos((s1_2 + math.pow(c2, 2) - k_2) / (2 * s1 * c2)) + math.atan2(nx1, (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_2 = LARGE_NUMBER

    try:
        theta2_3 = math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) - math.atan2((nx1 + 2 * a1), (pivot_point[2] - c1))
    except ValueError:  # math domain error
        theta2_3 = LARGE_NUMBER

    try:
        theta2_4 = -(math.acos((s2_2 + math.pow(c2, 2) - k_2) / (2 * s2 * c2)) + math.atan2((nx1 + 2 * a1), (pivot_point[2] - c1)))
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
        theta4_1 = math.atan2((tcp_rotation[1][2] * cos11 - tcp_rotation[0][2] * sin11), tcp_rotation[0][2] * cos231 * cos11 + tcp_rotation[1][2] * cos231 * sin11 - tcp_rotation[2][2] * sin231)
        theta4_5 = theta4_1 + math.pi
    except ValueError:  # math domain error
        theta4_1 = LARGE_NUMBER
        theta4_5 = LARGE_NUMBER
    try:
        theta4_2 = math.atan2((tcp_rotation[1][2] * cos12 - tcp_rotation[0][2] * sin12), tcp_rotation[0][2] * cos232 * cos12 + tcp_rotation[1][2] * cos232 * sin12 - tcp_rotation[2][2] * sin232)
        theta4_6 = theta4_2 + math.pi
    except ValueError:  # math domain error
        theta4_2 = LARGE_NUMBER
        theta4_6 = LARGE_NUMBER
    try:
        theta4_3 = math.atan2((tcp_rotation[1][2] * cos13 - tcp_rotation[0][2] * sin13), tcp_rotation[0][2] * cos233 * cos13 + tcp_rotation[1][2] * cos233 * sin13 - tcp_rotation[2][2] * sin233)
        theta4_7 = theta4_3 + math.pi
    except ValueError:  # math domain error
        theta4_3 = LARGE_NUMBER
        theta4_7 = LARGE_NUMBER
    try:
        theta4_4 = math.atan2((tcp_rotation[1][2] * cos14 - tcp_rotation[0][2] * sin14), tcp_rotation[0][2] * cos234 * cos14 + tcp_rotation[1][2] * cos234 * sin14 - tcp_rotation[2][2] * sin234)
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
        theta6_1 = math.atan2((tcp_rotation[0][1] * sin231 * cos11 + tcp_rotation[1][1] * sin231 * sin11 + tcp_rotation[2][1] * cos231), (-tcp_rotation[0][0] * sin231 * cos11 - tcp_rotation[1][0] * sin231 * sin11 - tcp_rotation[2][0] * cos231))
        theta6_5 = theta6_1 - math.pi
    except ValueError:  # math domain error
        theta6_1 = LARGE_NUMBER
        theta6_5 = LARGE_NUMBER
    try:
        theta6_2 = math.atan2((tcp_rotation[0][1] * sin232 * cos12 + tcp_rotation[1][1] * sin232 * sin12 + tcp_rotation[2][1] * cos232), (-tcp_rotation[0][0] * sin232 * cos12 - tcp_rotation[1][0] * sin232 * sin12 - tcp_rotation[2][0] * cos232))
        theta6_6 = theta6_2 - math.pi
    except ValueError:  # math domain error
        theta6_2 = LARGE_NUMBER
        theta6_6 = LARGE_NUMBER
    try:
        theta6_3 = math.atan2((tcp_rotation[0][1] * sin233 * cos13 + tcp_rotation[1][1] * sin233 * sin13 + tcp_rotation[2][1] * cos233), (-tcp_rotation[0][0] * sin233 * cos13 - tcp_rotation[1][0] * sin233 * sin13 - tcp_rotation[2][0] * cos233))
        theta6_7 = theta6_3 - math.pi
    except ValueError:  # math domain error
        theta6_3 = LARGE_NUMBER
        theta6_7 = LARGE_NUMBER
    try:
        theta6_4 = math.atan2((tcp_rotation[0][1] * sin234 * cos14 + tcp_rotation[1][1] * sin234 * sin14 + tcp_rotation[2][1] * cos234), (-tcp_rotation[0][0] * sin234 * cos14 - tcp_rotation[1][0] * sin234 * sin14 - tcp_rotation[2][0] * cos234))
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
