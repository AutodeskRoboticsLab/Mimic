#!usr/bin/env python

"""
Functions that actually make Mimic run.
"""

try:
    import pymel.core as pm
    import maya.mel as mel

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    mel = None
    MAYA_IS_RUNNING = False
import math
import re

import general_utils
import mimic_config
from postproc import postproc
from postproc import postproc_setup
from postproc import postproc_options
from robotmath import inverse_kinematics

reload(mimic_config)
reload(postproc)
reload(postproc_setup)
reload(postproc_options)
reload(general_utils)
reload(inverse_kinematics)


def get_robot_roots(all_robots=0, sel=[]):
    """
    Gets the root node name of the robot(s) in the scene (e.g. 'KUKA_KR60_0')
    - If all_robots = 1, get_robot_roots returns the robot name(s) for all
      robots in the scene, regardless of selection
    - If all_robots = 0, get_robot_roots returns the robot name(s) for 
      selected objects, if the object is a child of the robot 
      (e.g. 'target_CTRL')
    :param all_robots: boolean; flag to specify which robot names to return:
     all robots or just the selected ones
    :param sel: list; list of all of the object selected in the Maya viewport
    :return robot_roots: list
    """

    robot_roots = []

    # If no robots exist, return empty array.
    if not pm.objExists('*|robot_GRP|target_CTRL'):
        return robot_roots

    if all_robots:
        # All valid robot rigs will have this hierarchy
        sel = pm.ls('*|robot_GRP|target_CTRL')
    else:
        # If no selection is passed, manually check for selections in Maya's
        # viewport.
        if not sel:
            sel = pm.ls(selection=True, type='transform')
            # If there is nothing is selected in Maya's viewport,
            # return an empty
        if not sel:
            return robot_roots

    for selection in sel:
        # For current selected object, traverse up its hierarchy to find the
        # root robot transform node, if one exists.
        loop = 1
        while loop:
            # Check if the selected object is the root robot transform.
            # e.g. 'KUKA_KR60_0'
            # If so, append it to the list of robots.
            if pm.objExists('{}|robot_GRP|target_CTRL'.format(selection)):
                robot_roots.append(selection)
                loop = 0  # Continue to next selected object
            else:
                try:

                    # Climb up the heirarchy one level to the selections
                    # parent.
                    selection = pm.listRelatives(selection, allParents=True,
                                                 type='transform')[0]
                except:
                    # If selection has no parents, and is not a child of a
                    # robot, omit it from the return array and skip to the next
                    # selected object.
                    loop = 0

    robot_roots = list(set(robot_roots))  # Eliminate duplicates

    # if not robot_roots:
    #     raise ValueError('No robots selected or No robots in scene')

    return robot_roots


def check_robot_selection(number_of_robots=None):
    """
    Confirm that robots have been selected; if a number of robots is provided,
    confirm that the number of robots selected matches it.
    :param number_of_robots:
    :return:
    """
    # Check if any robots are selected
    robots = get_robot_roots()
    if not robots:
        return False
    # Check against number of robots
    if number_of_robots:
        if len(robots) > number_of_robots:
            return False
    return True


def clear_limits_ui(*args):
    """
    Clears the axis limit fields in the Mimic UI.
    :param args: Required for Maya to pass command from the UI
    :return:
    """
    for i in range(6):
        pm.textField('t_A{}Min'.format(i + 1), edit=True, text='')
        pm.textField('t_A{}Max'.format(i + 1), edit=True, text='')
        pm.textField('t_E{}Min'.format(i + 1), edit=True, text='')
        pm.textField('t_E{}Max'.format(i + 1), edit=True, text='')


def clear_fk_pose_ui(*args):
    """
    Clears the FK pose fields in the Mimic UI.
    :param args: Required for Maya to pass command from the UI
    :return:
    """
    for i in range(6):
        pm.textField('t_a{}'.format(i + 1), edit=True, text='')


def set_program_dir(*args):
    """
    Creates a file dialog box that allows the user to select a directory to
    save program files.
    :param args: Required for Maya to pass command from the UI.
    :return:
    """

    # Propt user with file dialog box.
    # If they don't provide any input, exit the function.
    directory = pm.fileDialog2(fileMode=2, dialogStyle=2)
    if not directory:
        return

    # Assign user input to the Program Directory Text field in the Mimic UI.
    pm.textField('t_programDirectoryText', edit=True, text=directory[0])


def _get_closest_ik_keyframe(robot, current_frame):
    """
    Finds the keyframe on the input Robot's IK attribute that is closest
    to the frame that is being evaluated. We only consider there to ba an
    a true IK keyframe if there is a keyframe set for ~both~ the tool_CTRLS
    ik attribute, as well as the FK_CTRLS rotate attributes
    :param robot: name string of the selected robot
    :param current_frame: int; frame that is currently being evaluated
    :return closest_ik_key: int; 
    :return count_direction: int; 
    """
    # Get a list of all keyframes on robots IK attribute.
    ik_keys = pm.keyframe('{}|robot_GRP|target_CTRL'.format(robot),
                          attribute='ik',
                          query=True,
                          time='-10:')

    # Verify that there is also a keyframe set on the FK controls' rotate
    # attributes. If there's not, we remove it from the list
    # Note: we only need to check on controller as they are al keyframed
    # together
    ik_keys_filtered = [key for key in ik_keys if pm.keyframe('{}|robot_GRP|FK_CTRLS|a1FK_CTRL.rotateY'.format(robot),
                                                              query=True,
                                                              time=key)]

    # If there are no IK attribute keyframes on the current robot,
    # return an empty array.
    if not ik_keys_filtered:
        return None, None

    # Find the IK attribute keyframe that's closest to current time,
    # above or below the current frame.
    closest_ik_key = min(ik_keys_filtered, key=lambda x: abs(x - current_frame))

    # Figure out which side of the current keyframe the closest frame is to
    # use as a for loop range step size. Represented by +1 or -1
    # i.e. range(*, *, count_direction)
    sign = lambda x: (1, -1)[x < 0]
    count_direction = sign(current_frame - closest_ik_key)

    return closest_ik_key, count_direction


def _accumulate_rotation(a_in, a_0):
    """
    Compares current Axis value with its previous value to determine if there
    has been a 360 degree flip in the Axis' evaluation.
    e.g.:If a_0 = 94 and a_in = -265 instead of -266, this function would
    output a_out = 95
    :param a_in: float; current evaluation of axis rotation
    :param a_0: float; previous evaluation of axis rotation
    :return a_out: float
    """
    # If the input value and previous value differ by a large amount, we assume
    # the evaluation has been flipped, so we manually flip it back. Otherwise,
    # we output the input value unchanged
    if abs(a_in - a_0) > 300:
        a_out = a_in - (abs(a_in) / a_in) * 360
    else:
        a_out = a_in

    return a_out


def _get_reconciled_rotation_value(robot, axis, rotation_axis, current_frame):
    """
    Determines the proper rotation value of an axis at the desired frame by
    comparing the evaluation to the closest keyframed value.
    :param robot: name string of the selected robot
    :param axis: int; number of the axis being evaluated
    :param rotation_axis: string; axis that specified axis rotates about
    :param current_frame: int; frame that is currently being evaluated
    :return keyed_val: float; correct value of the axis in question
    :return flip: bool; boolean signaling whether or not the axis evaluation
     needs to be flipped
    """
    # Initialize variables
    keyed_val = None
    flip = False

    # Find the closest keyframe on the robot's IK attribute 
    closest_ik_key, count_direction = _get_closest_ik_keyframe(robot,
                                                               current_frame)

    # If there are no IK attribute keyframes on the current robot,
    # exit the function.
    if not type(closest_ik_key) == float:
        return keyed_val, flip

    # If the current frame has an ik attribute keyframe,
    # assign that value as the keyed value.
    if closest_ik_key == current_frame:
        # Axis rotation value as given by the Dependency Graph
        DG_val = pm.getAttr('{}|robot_GRP|target_CTRL.axis{}' \
                            .format(robot, axis),
                            time=current_frame)
        # Axis rotation as approximated by an IK keyframe
        keyed_val = pm.getAttr('{}|robot_GRP|FK_CTRLS|a{}FK_CTRL.rotate{}' \
                               .format(robot, axis, rotation_axis),
                               time=current_frame)
        keyed_val = _accumulate_rotation(DG_val, keyed_val)

        if abs(DG_val - keyed_val) > 300:
            flip = True

    # If the current frame doesn't have an IK attribute keyframe, 
    # find the closest one and traverse the timeline to determine the correct
    # evaluation.
    else:
        # Initialize axis value as keyframed value.
        keyed_val = pm.getAttr('{}|robot_GRP|FK_CTRLS|a{}FK_CTRL.rotate{}' \
                               .format(robot, axis, rotation_axis),
                               time=closest_ik_key)

        # Traverse the timeline from the closest IK attribute keyframe to the
        # current frame. Determine desired rotation angle at each frame
        for frame in range(int(closest_ik_key),
                           int(current_frame + count_direction),
                           count_direction):
            # Find the axis value at the current frame as given by the
            # Dependency Graph.
            DG_val = pm.getAttr('{}|robot_GRP|target_CTRL.axis{}' \
                                .format(robot, axis),
                                time=frame)

            # Compare Dependency Graph evaluation with keyframed value
            keyed_val = _accumulate_rotation(DG_val, keyed_val)

        if abs(DG_val - keyed_val) > 300:
            flip = True

    return keyed_val, flip


def reconcile_rotation():
    """
    The robot's inverse kinematic solver can only solve rotation values theta, 
    such that 180 deg > theta > -180 deg, even though some axes are capable 
    of rotating beyond that. We account for this by manually accumulating the 
    rotation beyond +/- 180 deg, which can cause Maya's dependency graph to 
    evaluate improperly in some cases. To account for these scenarios, we can 
    keyframe rotation values.

    This function determines the proper rotation value of an axis at the
    desired frame by comparing the evaluation to the closest keyframed value
    and flips the axis value manually if necessary.  
    :return:
    """
    robots = get_robot_roots(1)  # Get the names of all robots in the scene
    if not robots:
        print 'No Robots in Scene'
        return

    # Define which axes this function will operate on, along with their
    # corresponding axis of rotation. These are typically axes that have 
    # rotation limits > 180 and/or < -180. Currently only axes 4 and 6 are 
    # supported by attributes on target_CTRL (e.g. invertAxis4).
    axes = [4, 6]
    rotation_axes = ['Z', 'Z']

    current_frame = pm.currentTime()

    for robot in robots:
        in_ik_mode = pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot))

        # If the scene is in FK mode, do nothing.
        if not in_ik_mode:
            continue

        # For each axis, determine if the value needs to be manually flipped
        # +/- 360 degrees. If so, flip the axis value
        for i, axis in enumerate(axes):
            keyed_val, flip = _get_reconciled_rotation_value(robot,
                                                             axis,
                                                             rotation_axes[i],
                                                             current_frame)
            if flip:
                # Manually flip value of the axis by 360 degrees.
                invert_axis(axis, [robot])
                print '{}: Axis {} rotation reconciled'.format(robot, axis)
            else:
                continue


def mimic_script_jobs():
    """
    Adds a Maya script job to the scene that executes reconcile_rotation() when
    the time is changed in the animation timeline.
    :return:
    """
    pm.cycleCheck(evaluation=0)

    pm.scriptJob(event=['timeChanged', reconcile_rotation], killWithScene=True)
    print "Robot scriptJobs Initialized"
    print 'Reconcile Rotation script job running'
    print 'cycleCheck OFF'


def add_mimic_script_node(*args):
    """
    Adds a script node to the scene that executes when the scene is open and
    adds a reconcile_rotation script job to the scene
    :param args: Required for Maya to pass command from the UI.
    :return:
    """
    if pm.objExists('mimicScriptNode'):
        print('Script Node Already Exists')
        return

    # Define the command to be executed when the scriptNode is triggered
    script_str = 'import pymel.core as pm; ' \
                 'import mimic_utils; ' \
                 'mimic_utils.mimic_script_jobs()'

    pm.scriptNode(sourceType="Python",
                  scriptType=2,
                  beforeScript=script_str,
                  name='mimicScriptNode')

    pm.cycleCheck(evaluation=0)

    # The scriptNode only works after the scene has been saved, closed, and
    # reopened. So we have to run the scriptJobs manually for the initial 
    # scene session.
    mimic_script_jobs()

    print 'Robot Script Node Added'


def add_hud_script_node(*args):
    """
    Adds a script node to the scene that executes when the scene is closed that
    runs close_hud(). This ensures that the HUD closes when the scene is closed.
    :param args: Required for Maya to pass command from the UI.
    :return:
    """
    if pm.objExists('mimicHudScriptNode'):
        print('Script Node Already Exists')
        return

    # Define the command to be executed when the scriptNode is triggered
    script_str = 'import pymel.core as pm; ' \
                 'import mimic_utils; ' \
                 'mimic_utils.close_hud()'

    pm.scriptNode(sourceType="Python",
                  scriptType=2,
                  afterScript=script_str,
                  name='mimicHudScriptNode')

    print 'HUD Script Node Added'


def find_ik_solutions(robot):
    """
    Fids all possible IK configuration solutions for the input robot, given the
    current position of the tool center point, local base frame, and target frame.

    This function is used to determine which IK configuration is necessary to
    match a given FK pose. To do this, we only need to inspect and compare
    axes 1, 2, and 5.
    :param robot: name string of the selected robot
    :return ik_sols: list of possible axis configurations
    """

    # Get the robot geometry from robot definition attributes on the rig.
    a1 = pm.getAttr('{}|robot_GRP|target_CTRL.a1'.format(robot))
    a2 = pm.getAttr('{}|robot_GRP|target_CTRL.a2'.format(robot))
    b = pm.getAttr('{}|robot_GRP|target_CTRL.b'.format(robot))
    c1 = pm.getAttr('{}|robot_GRP|target_CTRL.c1'.format(robot))
    c2 = pm.getAttr('{}|robot_GRP|target_CTRL.c2'.format(robot))
    c3 = pm.getAttr('{}|robot_GRP|target_CTRL.c3'.format(robot))
    c4 = pm.getAttr('{}|robot_GRP|target_CTRL.c4'.format(robot))

    robot_definition = [a1, a2, b, c1, c2, c3, c4]

    # Each robot manufacturer has a pose in which all axis values are zero.
    # Determine the offset of Axis 2 between the zero pose of the
    # manufacturer and the zero pose of the IK solver (see documentation).
    a2_offset = pm.getAttr('{}|robot_GRP|target_CTRL.axis2Offset' \
                           .format(robot))

    # Each robot manufacturer defines positive and negative axis rotation
    # differently in relation our IK solver implementation.
    # This is defined on each robot rig by the axis* attribute
    flip_a1 = pm.getAttr('{}|robot_GRP|target_CTRL.flipAxis1direction' \
                         .format(robot))
    flip_a2 = pm.getAttr('{}|robot_GRP|target_CTRL.flipAxis2direction' \
                         .format(robot))
    flip_a5 = pm.getAttr('{}|robot_GRP|target_CTRL.flipAxis5direction' \
                         .format(robot))

    # Initialized lists
    tcp_rot = [[0] * 3 for i in range(3)]
    target_rot = [[0] * 3 for i in range(3)]
    lcs_trans = [[0] * 1 for i in range(3)]
    tcp_trans = [[0] * 1 for i in range(3)]
    target_point = [[0] * 1 for i in range(3)]
    flange_point = [[0] * 3 for i in range(1)]
    pivot_point = [[0] * 3 for i in range(1)]

    # Define translation vector from wrist pivot point to tool flange.
    T = [[0], [0], [c4]]

    # =====================#
    #  Frame Definitions  #
    # =====================#

    # Tool Center Point (TCP) locater
    tcp = pm.ls('{}|robot_GRP|robot_GEOM|Base|' \
                'axis1|axis2|axis3|axis4|axis5|axis6|tcp_GRP|tcp_HDL' \
                .format(robot))[0]
    # Local Base Frame controller (circle control at base of the robot).
    lcs = pm.ls('{}|robot_GRP|local_CTRL'.format(robot))[0]
    # Target Frame controller (square control at the robot's tool flange).
    target = pm.ls('{}|robot_GRP|target_HDL'.format(robot))[0]

    # Maya uses a different coordinate system than our IK solver, so we have
    # to convert from Maya's frame to the solver's frame. 

    # Solver's tool frame (X,Y,Z) = Maya's tool frame (Z, X, Y)
    # Rotation matrix from Maya tool frame to solver's tool frame. 
    R_tool_frame = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    # Solver world frame (X,Y,Z) = Maya world frame (-Y, X, Z)
    # Rotation matrix from Maya's world frame to solver world frame.
    R_world_frame = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]

    # Get local translation of the TCP w.r.t. tool flange.
    tcp_trans[0][0] = tcp.getTranslation()[0]
    tcp_trans[1][0] = tcp.getTranslation()[1]
    tcp_trans[2][0] = tcp.getTranslation()[2]
    # Convert TCP translation from Maya's tool frame to solver tool frame.
    tcp_trans = general_utils.array_multiply(R_tool_frame, tcp_trans)

    # Get translation of local base frame (Circle controller) w.r.t robot's
    # world frame (Square controller).
    lcs_trans[0][0] = lcs.getTranslation()[0]
    lcs_trans[1][0] = lcs.getTranslation()[1]
    lcs_trans[2][0] = lcs.getTranslation()[2]
    # Convert lcs translation from Maya's world frame to solver world frame.
    lcs_trans = general_utils.array_multiply(R_world_frame, lcs_trans)

    # Get translation of target in Maya's world frame w.r.t robot world frame
    # (Square controller).
    target_point[0][0] = target.getTranslation()[0]
    target_point[1][0] = target.getTranslation()[1]
    target_point[2][0] = target.getTranslation()[2]
    # Convert target translation from Maya's world frame to solver world frame.
    target_point = general_utils.array_multiply(R_world_frame, target_point)

    # Get lcs, tcp, and target matrices in Maya's world frame
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
        general_utils.array_multiply(R_tool_frame, tcp_matrix_truncated))

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
        general_utils.array_multiply(R_world_frame,
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
        general_utils.array_multiply(R_world_frame,
                                     target_matrix_truncated))

    # Find Flange and Pivot locations in local solver world frame
    # Rotation of the tcp w.r.t to the target in solver world frame
    Re = general_utils.array_multiply(
        general_utils.transpose_list(target_rot), tcp_rot)

    # Rotation of the robot's local coordinate system (circle
    # controller) w.r.t the solver world frame
    Rlm = general_utils.array_multiply(R_world_frame, lcs_rot)

    # Find distance from the robot's local coordinate system (circle
    # controller) to target point in solver world frame
    target_point = [i - j for i, j in zip(
        general_utils.transpose_list(target_point)[0],
        general_utils.transpose_list(lcs_trans)[0])]

    # Find the flange point in the solver's world frame
    flange_point = [i - j for i, j in zip(target_point,
                                          general_utils.transpose_list(
                                              general_utils.array_multiply(Re, tcp_trans))[0])]

    # Find the pivot point in the solver's world frame
    pivot_point = [i - j for i, j in zip(flange_point,
                                         general_utils.transpose_list(
                                             general_utils.array_multiply(Re, T))[0])]

    # Find the flange point w.r.t the robot's local frame (circle controller) 
    # in solver's world frame
    flange_point = general_utils.transpose_list(
        general_utils.array_multiply(Rlm,
                                     [[flange_point[0]],
                                      [flange_point[1]],
                                      [flange_point[2]]]))[0]

    # Find the pivot point w.r.t the robot's local frame (circle controller) 
    # in solver's world frame
    pivot_point = general_utils.transpose_list(
        general_utils.array_multiply(Rlm,
                                     [[pivot_point[0]],
                                      [pivot_point[1]],
                                      [pivot_point[2]]]))[0]

    # Define the Rotation of the tcp w.r.t the target in robot's local frame
    # (cirlce controller)
    Re = general_utils.array_multiply(Rlm, Re)

    # Find all IK solutions for the given configuration
    all_ik_sols = inverse_kinematics.solver(robot_definition, pivot_point, Re)

    # We only need to compare axes 1, 2, and 5 when switching between
    # IK and FK
    theta1_sol = all_ik_sols[0]
    theta2_sol = all_ik_sols[1]
    theta5_sol = all_ik_sols[4]

    # Account for robot manufacturer's Axis 2 offset from solver
    theta2_sol[:] = [x - a2_offset for x in theta2_sol]

    # Account for robot manufacturer's inverted rotation directions
    flip = 1
    if flip_a1:
        flip = -1
    if flip_a2:
        theta2_sol[:] = [-1 * x for x in theta2_sol]
    if flip_a5:
        theta5_sol[:] = [-1 * x for x in theta5_sol]

    # Assemble all combinations of solutions for axes 1, 2, and 5 for
    # IK/FK switching
    ik_sols = [[flip * theta1_sol[0], theta2_sol[0], theta5_sol[0]],
               [flip * theta1_sol[0], theta2_sol[0], theta5_sol[4]],
               [flip * theta1_sol[0], theta2_sol[1], theta5_sol[1]],
               [flip * theta1_sol[0], theta2_sol[1], theta5_sol[5]],
               [flip * theta1_sol[1], theta2_sol[2], theta5_sol[2]],
               [flip * theta1_sol[1], theta2_sol[2], theta5_sol[6]],
               [flip * theta1_sol[1], theta2_sol[3], theta5_sol[3]],
               [flip * theta1_sol[1], theta2_sol[3], theta5_sol[7]],
               [flip * (theta1_sol[0] + 360), theta2_sol[0], theta5_sol[0]],
               [flip * (theta1_sol[0] + 360), theta2_sol[0], theta5_sol[4]],
               [flip * (theta1_sol[0] + 360), theta2_sol[1], theta5_sol[1]],
               [flip * (theta1_sol[0] + 360), theta2_sol[1], theta5_sol[5]],
               [flip * (theta1_sol[1] + 360), theta2_sol[2], theta5_sol[2]],
               [flip * (theta1_sol[1] + 360), theta2_sol[2], theta5_sol[6]],
               [flip * (theta1_sol[1] + 360), theta2_sol[3], theta5_sol[3]],
               [flip * (theta1_sol[1] + 360), theta2_sol[3], theta5_sol[7]]]

    return ik_sols


def find_fk_config(robot):
    """
    Get the six axes from the selected robot.
    :param robot: name string of the selected robot
    :return:
    """
    a1 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1.rotateY'.format(robot))
    a2 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1|axis2.rotateX'.format(robot))
    a3 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1|axis2|axis3.rotateX'.format(robot))
    a4 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1|axis2|axis3|axis4.rotateZ'.format(robot))
    a5 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1|axis2|axis3|axis4|axis5.rotateX'.format(robot))
    a6 = pm.getAttr('{}|robot_GRP|robot_GEOM|Base|'
                    'axis1|axis2|axis3|axis4|axis5|axis6.rotateZ'.format(robot))
    fk_config = [a1, a2, a3, a4, a5, a6]
    return fk_config


__FK_CONFIGS = [[1, 1, 1],
                [1, 1, 0],
                [1, 0, 1],
                [1, 0, 0],
                [0, 1, 1],
                [0, 1, 0],
                [0, 0, 1],
                [0, 0, 0],
                [1, 1, 1],
                [1, 1, 0],
                [1, 0, 1],
                [1, 0, 0],
                [0, 1, 1],
                [0, 1, 0],
                [0, 0, 1],
                [0, 0, 0]]


def find_closest_config(fk_configuration, ik_solutions):
    """
    Finds the index of the closest Inverse Kinematic solution to the input
    Forward Kinematic axis configuration
    :param fk_configuration: list; 1 x m array that represents the
     initial axis configuration
    :param ik_solutions: list; n x m array representing all possible
     axis configurations
    :return:
    """
    C = [zip(fk_configuration, row) for row in ik_solutions]
    D = [[] for i in range(len(ik_solutions))]
    # Find the difference between the initial configuration and each possible
    # configuration. The row with the smallest difference represents the
    # closest solution to to the initial configuration
    for i, row in enumerate(C):
        D[i] = [abs(a - b) for a, b in row]
        D[i] = sum(D[i])

    solution_index = D.index(min(D))
    # Get three booleans corresponding with a valid IK configuration using index
    config = __FK_CONFIGS[solution_index]
    return config


def flip_robot_base(*args):
    """
    Toggles Inverse Kinematic Solution 1 Boolean
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    for robot in robots:
        target_ctrl_attr = '{}|robot_GRP|target_CTRL.ikSolution1' \
            .format(robot)
        ik_sol = pm.getAttr(target_ctrl_attr)
        pm.setAttr(target_ctrl_attr, not ik_sol)


def flip_robot_elbow(*args):
    """
    Toggles Inverse Kinematic Solution 2 Boolean
    :param args:
    :return:
    """

    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    for robot in robots:
        target_ctrl_attr = '{}|robot_GRP|target_CTRL.ikSolution2' \
            .format(robot)
        ik_sol = pm.getAttr(target_ctrl_attr)
        pm.setAttr(target_ctrl_attr, not ik_sol)


def flip_robot_wrist(*args):
    """
    Toggles Inverse Kinematic Solution 3 Boolean
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    for robot in robots:
        target_ctrl_attr = '{}|robot_GRP|target_CTRL.ikSolution3' \
            .format(robot)
        ik_sol = pm.getAttr(target_ctrl_attr)
        pm.setAttr(target_ctrl_attr, not ik_sol)


def invert_axis(axis_number, robots=[]):
    """
    Invert a robot's axis.
    :param axis_number: Index of axis to invert (1 indexed)
    :param robots: name strings of the selected robots
    :return:
    """
    if not robots:
        robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    sel = pm.ls(selection=True, type='transform')

    try:
        for robot in robots:
            target_ctrl_attr = '{}|robot_GRP|target_CTRL.invertAxis{}' \
                .format(robot, axis_number)
            pm.setAttr(target_ctrl_attr, 1)
            pm.select(sel)
            eval_str = 'import pymel.core as pm; ' \
                       'pm.setAttr(\'' + target_ctrl_attr + '\', 0)'
            pm.evalDeferred(eval_str)
    except:
        pm.warning('Error Inverting Axis')


def zero_target(*args):
    """
    Set translation and rotation of a robot object in channel box to zero, 0.
    If in IK mode effect tool controller. If in FK mode effect all axes.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        for robot in robots:

            ik_mode = pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot))

            if ik_mode:
                if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
                    pm.setAttr('{}|robot_GRP|tool_CTRL.translate' \
                               .format(robot), 0, 0, 0)
                    pm.setAttr('{}|robot_GRP|tool_CTRL.rotate' \
                               .format(robot), 0, 0, 0)
                else:
                    pm.setAttr('{}|robot_GRP|target_CTRL.translate' \
                               .format(robot), 0, 0, 0)
                    pm.setAttr('{}|robot_GRP|target_CTRL.rotate' \
                               .format(robot), 0, 0, 0)
            else:
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a1FK_CTRL.rotateY' \
                           .format(robot), 0)
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a2FK_CTRL.rotateX' \
                           .format(robot), 0)
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a3FK_CTRL.rotateX' \
                           .format(robot), 0)
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a4FK_CTRL.rotateZ' \
                           .format(robot), 0)
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a5FK_CTRL.rotateX' \
                           .format(robot), 0)
                pm.setAttr('{}|robot_GRP|FK_CTRLS|a6FK_CTRL.rotateZ' \
                           .format(robot), 0)
    except:
        pm.warning('Cannot zero target')


def zero_base_world(*args):
    """
    Set translation and rotation of robot base in world space (square controller)
    in channel box to zero, 0.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        for robot in robots:
            pm.setAttr('{}|world_CTRL.translate'.format(robot),
                       0, 0, 0)
            pm.setAttr('{}|world_CTRL.rotate'.format(robot),
                       0, 0, 0)
    except:
        pm.warning('Cannot zero base (world)')


def zero_base_local(*args):
    """
    Set translation and rotation of robot base in local space (circular controller)
    in channel box to zero, 0.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        for robot in robots:
            pm.setAttr('{}|robot_GRP|local_CTRL.translate'.format(robot),
                       0, 0, 0)
            pm.setAttr('{}|robot_GRP|local_CTRL.rotate'.format(robot),
                       0, 0, 0)
    except:
        pm.warning('Cannot zero base (local)')


def zero_all(*args):
    """
    Set translation and rotation of robot object, robot base in world space
    (square controller), local space (circular controller) in channel box to
    zero, 0.
    :param args:
    :return:
    """
    zero_target()
    zero_base_world()
    zero_base_local()


def get_axis_val(axis_number, round_val=True):
    """
    Get the rotation value (degrees) of an axis.
    :param axis_number: Index of axis to effect (1 indexed)
    :param round_val: Round the output value.
    :return:
    """
    axis_val = []
    robots = get_robot_roots(1)

    for robot in robots:
        if round_val:
            axis_val.append(round(pm.getAttr('{}|robot_GRP|target_CTRL' \
                                             '.axis{}' \
                                             .format(robot, axis_number))))
        else:
            axis_val.append(pm.getAttr('{}|robot_GRP|target_CTRL.axis{}' \
                                       .format(robot, axis_number)))

    return axis_val


def axis_val_hud(*args):
    """
    Toggle the presence of a heads-up-display (HUD) for viewing axes in Maya.
    :param args:
    :return:
    """
    robots = get_robot_roots(1)

    if not robots:
        print 'No Robots in Scene'
        if pm.headsUpDisplay('a1_hud', exists=True):
            for i in range(6):
                pm.headsUpDisplay('a{}_hud'.format(i + 1), remove=True)
        return

    # Check if the HUD exists already
    if pm.headsUpDisplay('a1_hud', exists=True):
        # If so, remove it
        for i in range(6):
            pm.headsUpDisplay('a{}_hud'.format(i + 1), remove=True)
        # Turn Limit Meter off
        for robot in robots:
            pm.setAttr('{}|robot_GRP|limitMeter_CTRL.v'.format(robot), 0)
            pm.setAttr('{}|robot_GRP|limitMeter_GRP.v'.format(robot), 0)
        return
    else: # If not, create it
        for i in range(6):
            pm.headsUpDisplay('a{}_hud'.format(i + 1),
                              section=5,
                              block=7 - i,
                              blockSize='small',
                              label='A{}'.format(i + 1),
                              labelFontSize='large',
                              dataWidth=30,
                              command=pm.Callback(get_axis_val, i + 1),
                              event='timeChanged')
        # Turn Limit Meter on
        for robot in robots:
            pm.setAttr('{}|robot_GRP|limitMeter_CTRL.v'.format(robot), 1)
            pm.setAttr('{}|robot_GRP|limitMeter_GRP.v'.format(robot), 1)


def close_hud():
    """
    Close the heads-up-display (HUD) in Maya; runs in a script node that executes
    when the Maya scene is closed.
    :return:
    """
    if pm.headsUpDisplay('a1_hud', exists=True):
        for i in range(6):
            pm.headsUpDisplay('a{}_hud'.format(i + 1), remove=True)


def attach_tool_controller(*args):
    """
    Attaches tool controller to robot and adds parent constraint with
    target_CTRL
    :param args:
    :return:
    """

    sel = pm.ls(selection=True, type='transform')
    robot = get_robot_roots()

    # Exception handling
    if not sel:
        pm.warning('Nothing selected; ' \
                   'select a valid robot control and tool controller')
    if not robot:
        pm.warning('No robot selected; ' \
                   'select a valid robot')
        return
    if len(robot) > 1:
        pm.warning('Too many robots selected; ' \
                   'select a single robot')
        return
    if len(sel) > 2:
        pm.warning('Too many selections; ' \
                   'select a single robot control, and single tool controller')
        return
    if len(sel) == 1:
        pm.warning('Not enough selections; ' \
                   'select a single robot control, and single tool control')
        return
    if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot[0])):
        pm.warning('Robot already has an assigned tool controller')
        return

    robot_grp = '{}|robot_GRP'.format(robot[0])

    # find which selected object is the tool controller
    if not get_robot_roots(0, [sel[0]]):
        tool_ctrl = sel[0]
    else:
        tool_ctrl = sel[1]

    try:
        pm.parent(tool_ctrl, robot_grp, absolute=True)

        try:
            pm.rename(robot_grp + '|' + tool_ctrl, 'tool_CTRL')
        except:
            pass

        pm.parentConstraint('{}|robot_GRP|tool_CTRL'.format(robot[0]),
                            '{}|robot_GRP|target_CTRL'.format(robot[0]),
                            name='targetToToolCtrl_pCnst',
                            maintainOffset=True)
        # Duplicate and add to FK parent chain
        tool_ctrl_dup = pm.duplicate('{}|robot_GRP|tool_CTRL'.format(robot[0]))
        pm.rename(tool_ctrl_dup, 'tool_CTRL_FK')
        pm.parent('{}|robot_GRP|tool_CTRL_FK'.format(robot[0]),
                  '{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                  'axis4|axis5|axis6|tcp_GRP|tcp_HDL'.format(robot[0]),
                  absolute=True)
        pm.setAttr('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                   'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_CTRL_FK.v' \
                   .format(robot[0]), 0)

        # Lock rotation/translation of IK/FK CTRL (only works if prefs | file
        # references | edits on references is checked)
        try:
            pm.setAttr('{}|robot_GRP|target_CTRL.translate' \
                       .format(robot[0]),
                       lock=True)
            pm.setAttr('{}|robot_GRP|target_CTRL.rotate' \
                       .format(robot[0]),
                       lock=True)

            pm.setAttr('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                       'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_CTRL_FK.' \
                       'translate'.format(robot[0]),
                       lock=True)
            pm.setAttr('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                       'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_CTRL_FK.' \
                       'rotate'.format(robot[0]),
                       lock=True)
        except:
            pass

        pm.select('{}|robot_GRP|tool_CTRL'.format(robot[0]))

    except:
        pm.warning('Error attaching tool controller')


def attach_tool_model(*args):
    """
    Attaches model to the selected robot by placing it the the robots forward
    kinematic hierarchy
    :param args:
    :return:
    """
    sel = pm.ls(selection=True, type='transform')
    robot = get_robot_roots()

    # Exception handling
    if not sel:
        pm.warning('Nothing selected; ' \
                   'select a valid robot control and tool controller')
        return
    if not robot:
        pm.warning('No tool controller selected; ' \
                   'select a valid tool controller')
        return
    if len(robot) > 1:
        pm.warning('Too many robot controllers selected; ' \
                   'select a single controller')
        return
    if len(sel) == 1:
        pm.warning('Not enough selections; ' \
                   'select a single robot control, and single tool model')
        return

    # find which selected object is the tool model
    tools = []
    for each in sel:
        if not get_robot_roots(0, [each]):
            tools.append(each)
        else:
            pass

    for tool_model in tools:
        try:
            pm.parent(tool_model,
                      '{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                      'axis4|axis5|axis6|tcp_GRP|tcp_HDL'.format(robot[0]),
                      absolute=True)
            try:
                pm.rename('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|' \
                          'axis3|axis4|axis5|axis6|tcp_GRP|tcp_HDL|{}' \
                          .format(robot[0], tool_model),
                          'tool_MDL')
            except:
                pass
            # Lock rotation/translation of Tool Model
            pm.setAttr('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                       'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_MDL*.' \
                       'translate'.format(robot[0]),
                       lock=True)
            pm.setAttr('{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                       'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_MDL*.' \
                       'rotate'.format(robot[0]),
                       lock=True)

            if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot[0])):
                pm.select('{}|robot_GRP|tool_CTRL'.format(robot[0]))
            else:
                pm.select('{}|robot_GRP|target_CTRL'.format(robot[0]))

        except:
            pm.warning('Error attaching tool model {}'.format(tool_model))


def detach_tool_controller(*args):
    """
    Detaches tool controller to robot, removes parent constraint with
    target_CTRL, and then parents previous tool controller to the world (i.e.
    the root node in the Maya scene).
    :param args:
    :return
    """
    selection = pm.ls(selection=True)

    tools = 0  # Keep track of whether or not we have any tools
    for sel in selection:
        # Check if the selection is part of a valid robot
        if get_robot_roots(sel=[sel]):
            # Check if the selection is a valid tool controller
            if 'tool_CTRL' in str(sel):
                # If so unlock the robot's target_CTRL translate and
                # rotate attributes and parent the tool_CTRL to the world 
                robot = get_robot_roots(sel=[sel])[0]

                pm.delete('{}|robot_GRP|target_CTRL|targetToToolCtrl_pCnst' \
                          .format(robot))
                pm.delete('{}|robot_GRP|robot_GEOM|Base|' \
                          'axis1|axis2|axis3|axis4|axis5|axis6|' \
                          'tcp_GRP|tcp_HDL|tool_CTRL_FK' \
                          .format(robot))
                pm.setAttr('{}|robot_GRP|target_CTRL.translate' \
                           .format(robot),
                           lock=False)
                pm.setAttr('{}|robot_GRP|target_CTRL.rotate' \
                           .format(robot),
                           lock=False)
                pm.parent(sel, world=True, absolute=True)
                tools = 1  # Our selection is a tool controller

    # If there were no tools in our selection, alert the user
    if not tools:
        pm.warning('No tool controllers selected')
        return


def detach_tool_model(*args):
    """
    Detaches model to the selected robot by placing it the the robots forward
    kinematic hierarchy.
    :param args:
    :return
    """
    selection = pm.ls(selection=True)

    tools = 0  # Keep track of whether or not we have any tools
    for sel in selection:
        # Check if the selection is part of a valid robot
        if get_robot_roots(all_robots=0, sel=[sel]):
            # Check if the selection is a valid tool model
            if 'tool_MDL' in str(sel):
                # If so unlock the model's translate and rotate attributes
                # and parent the object to the world 
                try:
                    pm.setAttr(sel.translate, lock=False)
                    pm.setAttr(sel.rotate, lock=False)
                    pm.parent(sel, world=True, absolute=True)
                except:
                    pm.warning('Couldn\'t remove tool model from robot')
                tools = 1  # Our selection is a tool controller

    # If there were no tools in our selection, alert the user
    if not tools:
        pm.warning('No tool models selected')
        return


def get_axis_limits(*args):
    """
    Gets the current axis limits and updates UI with those values.
    :param args:
    :return:
    """
    robot = get_robot_roots()
    if not robot:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    # TODO: HARD CODED - Number of robot axes; should include external axes
    num_axes = 6

    if len(robot) > 1:
        pm.warning('Too many selections: Select a single robot')
        return

    for i in range(num_axes):
        val_min = int(pm.getAttr('{}|robot_GRP|target_CTRL.axis{}Min' \
                                 .format(robot[0], i + 1)))
        val_max = int(pm.getAttr('{}|robot_GRP|target_CTRL.axis{}Max' \
                                 .format(robot[0], i + 1)))

        pm.textField('t_A{}Min'.format(i + 1), edit=True, text=val_min)
        pm.textField('t_A{}Max'.format(i + 1), edit=True, text=val_max)


def set_axis_limit(axis_number, min_max):
    """
    Gets user-input value from UI and sets corresponding axis limits on the robot
    :param axis_number: Index of axis to effect (1 indexed)
    :param min_max: string, either 'Min' or 'Max'
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        val = float(pm.textField('t_A{}{}'.format(axis_number, min_max),
                                 query=True,
                                 text=True))
        for robot in robots:
            pm.setAttr('{}|robot_GRP|target_CTRL.axis{}{}' \
                       .format(robot, axis_number, min_max),
                       val)
    except:
        pass


def get_velocity_limits(robot):
    """
    Gets the current velocity limits and updates UI with those values.
    :param robot: name string of the selected robot
    :return:
    """
    velocity_limits = []

    # HARD CODED - Number of robot axes; should include external axes
    num_axes = 6
    # Create a list of robot's velocity limits
    for i in range(num_axes):
        velocity_limits.append(pm.getAttr('{}|robot_GRP|target_CTRL.axis{}' \
                                          'VelocityLimit'.format(robot, i + 1)))
    return velocity_limits


def set_axis_limits(*args):
    """
    Gets user-input value from UI and sets all axis limits at once
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    # number of robot axes; could include external axes potentially
    num_axes = 6

    try:
        for i in range(num_axes):
            set_axis_limit(i + 1, 'Min')
            set_axis_limit(i + 1, 'Max')
    except:
        pass


def get_fk_pose(*args):
    """
    Get the Forward Kinematic pose for a selected robot in the Maya scene.
    :param args:
    :return:
    """
    robot = get_robot_roots()
    if not robot:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    if len(robot) > 1:
        pm.warning('Too many selections; Select a single robot')
        return

    axes = find_fk_config(robot[0])

    for i in range(len(axes)):
        pm.textField('t_a{}'.format(i + 1),
                     edit=True,
                     text=round(axes[i], 2))


def select_fk_axis_handle(axis_number):
    """
    Selects FK Axis Control
    :param axis_number:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    selection = []
    for robot in robots:
        selection.append('{}|robot_GRP|FK_CTRLS|a{}FK_CTRL' \
                         .format(robot, axis_number))

    pm.select(selection)
    pm.setToolTo('RotateSuperContext')


def set_axis(axis_number):
    """
    Set the rotation value (degrees) of a selected robot and axis using
    Mimic UI fields.
    :param axis_number: Index of axis to effect (1 indexed)
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    # These are specific to how the robots are rigged in relation to Maya's
    # coordinate system
    rotation_axes = ['Y', 'X', 'X', 'Z', 'X', 'Z']

    try:  # if the text field is empty, or not a float value, skip it
        rotation_axis = rotation_axes[axis_number - 1]
        val = float(pm.textField('t_a{}'.format(axis_number),
                                 query=True,
                                 text=True))

        for robot in robots:
            pm.setAttr('{}|robot_GRP|FK_CTRLS|a{}FK_CTRL.rotate{}' \
                       .format(robot, axis_number, rotation_axis),
                       val)
    except:
        pass


def set_fk_pose(*args):
    """
    Set the Forward Kinematic pose of a selected robot.
    :param args:
    :return:
    """
    # Number of robot axes; could include external axes potentially.
    num_axes = 6

    try:
        for i in range(num_axes):
            set_axis(i + 1)
    except:
        pm.warning('Error setting FK pose')


def _snap_IK_target_to_FK(robot):
    """
    Snaps the IK control handle to the end of the FK heirarchy
    Used for IK/FK switching and keyframing.
    :param robot: name string of the selected robot
    :return:
    """
    # Snap IK Ctrl to FK location
    # If robot has tool controller, use that
    if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
        ctrl_ik = '{}|robot_GRP|tool_CTRL'.format(robot)
        ctrl_fk = '{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                  'axis4|axis5|axis6|tcp_GRP|tcp_HDL|tool_CTRL_FK' \
            .format(robot)

        # Snap tool_CTRL to tool_CTRL_FK.
        try:
            pm.snapTransforms(s=ctrl_fk, d=ctrl_ik)
        except:
            pm.warning('Coundn\'t snap {} tool_CTRL handle to FK' \
                       .format(robot))

    # If robot doesn't have a tool controller, use target_CTRL.
    else:
        ctrl_ik = '{}|robot_GRP|target_CTRL'.format(robot)
        ctrl_fk = '{}|robot_GRP|robot_GEOM|Base|axis1|axis2|axis3|' \
                  'axis4|axis5|axis6|tcp_GRP|tcp_HDL' \
            .format(robot)

        try:
            pm.snapTransforms(s=ctrl_fk, d=ctrl_ik)
        except:
            pm.warning('Coundn\'t snap {} target_CTRL handle to FK' \
                       .format(robot))


def switch_to_ik(robot):
    """
    Switches all robots in scene to IK mode
    :param robot: name string of the selected robot
    :return:
    """

    try:
        # Turn FK control visibility off
        pm.setAttr('{}|robot_GRP|FK_CTRLS.v'.format(robot), 0)

        # Turn IK control visibility on
        pm.setAttr('{}|robot_GRP|target_CTRL.v'.format(robot), 1)
        pm.setAttr('{}|robot_GRP|target_CTRL|target_CTRLShape.visibility' \
                   .format(robot), 1)

        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            pm.setAttr('{}|robot_GRP|tool_CTRL.v'.format(robot), 1)

        # Snap IK Ctrl to FK location
        _snap_IK_target_to_FK(robot)

        # Find closest IK configuration to current FK pose
        ik_sols = find_ik_solutions(robot)
        fk_config = find_fk_config(robot)

        # Only use a1, a2, and a5 to determing closest config.
        fk_config_trunc = [fk_config[i] for i in [0, 1, 4]]
        ik_config = find_closest_config(fk_config_trunc, ik_sols)

        # Match IK config to FK pose
        pm.setAttr('{}|robot_GRP|target_CTRL.ikSolution1' \
                   .format(robot), ik_config[0])
        pm.setAttr('{}|robot_GRP|target_CTRL.ikSolution2' \
                   .format(robot), ik_config[1])
        pm.setAttr('{}|robot_GRP|target_CTRL.ikSolution3' \
                   .format(robot), ik_config[2])

        # turn ik solve back on
        pm.setAttr('{}|robot_GRP|target_CTRL.ik'.format(robot), 1)

    except:
        pm.warning('Error swithching to IK')


def switch_to_fk(robot):
    """
    Switches all robots in the scene to IK mode.
    :param robot: name string of the selected robot
    :return:
    """
    try:
        # Turn IK control visibility off
        pm.setAttr('{}|robot_GRP|target_CTRL.v'.format(robot), 0)

        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            pm.setAttr('{}|robot_GRP|tool_CTRL.v'.format(robot), 0)

            # Turn FK control visibility on
        pm.setAttr('{}|robot_GRP|FK_CTRLS.v'.format(robot), 1)

        # Find axis angles from IK pose, and match FK control handles    
        fk_config = find_fk_config(robot)

        pm.setAttr('{}|robot_GRP|FK_CTRLS|a1FK_CTRL.rotateY'.format(robot),
                   fk_config[0])
        pm.setAttr('{}|robot_GRP|FK_CTRLS|a2FK_CTRL.rotateX'.format(robot),
                   fk_config[1])
        pm.setAttr('{}|robot_GRP|FK_CTRLS|a3FK_CTRL.rotateX'.format(robot),
                   fk_config[2])
        pm.setAttr('{}|robot_GRP|FK_CTRLS|a4FK_CTRL.rotateZ'.format(robot),
                   fk_config[3])
        pm.setAttr('{}|robot_GRP|FK_CTRLS|a5FK_CTRL.rotateX'.format(robot),
                   fk_config[4])
        pm.setAttr('{}|robot_GRP|FK_CTRLS|a6FK_CTRL.rotateZ'.format(robot),
                   fk_config[5])

        pm.setAttr('{}|robot_GRP|target_CTRL.ik'.format(robot), 0)

    except:
        pm.warning('Error switching to FK')


def toggle_ik_fk(*args):
    """
    Toggles all robots in scene between IK and FK modes
    :param args:
    :return:
    """
    current_tab = pm.tabLayout('switcher_tab_layout', query=True, selectTab=True)

    if current_tab == 'ikTab':
        ik_tab = 1
    else:
        ik_tab = 0

    robots = get_robot_roots(1)
    if not robots:
        return

    for robot in robots:
        try:
            if ik_tab:
                if pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot)):
                    continue

                switch_to_ik(robot)

            else:
                if not pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot)):
                    continue

                switch_to_fk(robot)
        except:
            pm.warning('Error during IK/FK switch')

    # Maintain appropriate selections on each robot
    try:
        selection = []
        active_robots = get_robot_roots()
        if active_robots:
            if ik_tab:
                for robot in active_robots:
                    if pm.objExists('{}|robot_GRP|target_CTRL'.format(robot)):
                        if pm.objExists('{}|robot_GRP|tool_CTRL' \
                                                .format(robot)):
                            selection.append('{}|robot_GRP|tool_CTRL' \
                                             .format(robot))
                        else:
                            selection.append('{}|robot_GRP|target_CTRL' \
                                             .format(robot))
            else:
                for robot in active_robots:
                    if pm.objExists('{}|robot_GRP|target_CTRL'.format(robot)):
                        selection.append('{}|robot_GRP|FK_CTRLS|a6FK_CTRL' \
                                         .format(robot))
            pm.select(selection)
        else:
            pass

    except:
        pm.warning('Error selecting after IK/FK switch')


def key_ik(*args):
    """
    Keyframe the robot's Inverse Kinematic pose.
    :param args:
    :return:
    """

    robots = get_robot_roots()
    if not robots:
        pm.warning('No robots selected')
        return

    for robot in robots:
        if not pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot)):
            switch_to_ik(robot)

        ik_attributes = ['ik',
                         'v',
                         'ikSolution1',
                         'ikSolution2',
                         'ikSolution3']

        # Key all IK elements
        target_ctrl = '{}|robot_GRP|target_CTRL'.format(robot)

        for attr in ik_attributes:
            pm.setKeyframe(target_ctrl, attribute=attr)

        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                           attribute='v')

        fk_pose = find_fk_config(robot)

        # Key all FK elements
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a1FK_CTRL'.format(robot),
                       attribute='rotateY',
                       value=fk_pose[0])
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a2FK_CTRL'.format(robot),
                       attribute='rotateX',
                       value=fk_pose[1])
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a3FK_CTRL'.format(robot),
                       attribute='rotateX',
                       value=fk_pose[2])
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a4FK_CTRL'.format(robot),
                       attribute='rotateZ',
                       value=fk_pose[3])
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a5FK_CTRL'.format(robot),
                       attribute='rotateX',
                       value=fk_pose[4])
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a6FK_CTRL'.format(robot),
                       attribute='rotateZ',
                       value=fk_pose[5])

        # Key visibility of FK controllers
        pm.setKeyframe('{}|robot_GRP|FK_CTRLS' \
                       .format(robot),
                       attribute='visibility')

        # Key tool controllers
        if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
            if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
                pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                               attribute='translate')
                pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                               attribute='rotate')
            else:
                pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                               attribute='translate')
                pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                               attribute='rotate')


def key_fk(*args):
    """
    Keyframe the robot's Forward Kinematic pose.
    :param args:
    :return:
    """

    robots = get_robot_roots()
    if not robots:
        pm.warning('No robots selected')
        return

    for robot in robots:
        # If the robot's IK attribute is on, switch the robot to
        # FK mode before proceeding 
        if pm.getAttr('{}|robot_GRP|target_CTRL.ik'.format(robot)):
            switch_to_fk(robot)

        # Snap IK control to the FK hierarchy
        _snap_IK_target_to_FK(robot)

        # Key all FK elements
        try:
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a1FK_CTRL'.format(robot),
                           attribute='rotateY')
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a2FK_CTRL'.format(robot),
                           attribute='rotateX')
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a3FK_CTRL'.format(robot),
                           attribute='rotateX')
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a4FK_CTRL'.format(robot),
                           attribute='rotateZ')
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a5FK_CTRL'.format(robot),
                           attribute='rotateX')
            pm.setKeyframe('{}|robot_GRP|FK_CTRLS|a6FK_CTRL'.format(robot),
                           attribute='rotateZ')

            # Key visibility of FK controllers
            for i in range(6):
                pm.setKeyframe('{}|robot_GRP|FK_CTRLS' \
                               .format(robot),
                               attribute='visibility')
        except:
            pm.warning('Error setting FK keys in FK mode')

        # Key all IK elements
        try:
            pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                           attribute='ik')
            pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                           attribute='v',
                           value=0)

            if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
                pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                               attribute='v')

            # Key tool controllers
            if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
                if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
                    pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                                   attribute='translate')
                    pm.setKeyframe('{}|robot_GRP|tool_CTRL'.format(robot),
                                   attribute='rotate')
                else:
                    pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                                   attribute='translate')
                    pm.setKeyframe('{}|robot_GRP|target_CTRL'.format(robot),
                                   attribute='rotate')

        except:
            pm.warning('Error setting IK keys in FK mode')


def select_keyframe_hierarchy(*args):
    """
    Select IK-FK keyframe hierarchy
    :param args:
    :return:
    """
    if not check_robot_selection():
        pm.warning('No robot\'s selected; ' \
                   'select at least one robot')
        return

    object_list = ['{}|robot_GRP|target_CTRL',
                   '{}|robot_GRP|FK_CTRLS',
                   '{}|robot_GRP|FK_CTRLS|a1FK_CTRL',
                   '{}|robot_GRP|FK_CTRLS|a2FK_CTRL',
                   '{}|robot_GRP|FK_CTRLS|a3FK_CTRL',
                   '{}|robot_GRP|FK_CTRLS|a4FK_CTRL',
                   '{}|robot_GRP|FK_CTRLS|a5FK_CTRL',
                   '{}|robot_GRP|FK_CTRLS|a6FK_CTRL']

    keyable_robot_objects = []
    robots = get_robot_roots()

    for robot in robots:
        for obj in object_list:
            keyable_robot_objects.append(obj.format(robot))

        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            keyable_robot_objects.append('{}|robot_GRP|tool_CTRL'.format(robot))
    pm.select(keyable_robot_objects)


def delete_ik_fk_keys(*args):
    """
    Delete an Inverse Kinematic or Forward Kinematic keyframe.
    :param args:
    :return:
    """
    if not check_robot_selection():
        pm.warning('No robots selected; ' \
                   'Select at least one robot.')

    keyed_attrs = {'{}|robot_GRP|target_CTRL': ['ik',
                                                'visibility',
                                                'ikSolution1',
                                                'ikSolution2',
                                                'ikSolution3'],
                   '{}|robot_GRP|FK_CTRLS': ['visibility'],
                   '{}|robot_GRP|FK_CTRLS|a1FK_CTRL': ['rotateY'],
                   '{}|robot_GRP|FK_CTRLS|a2FK_CTRL': ['rotateX'],
                   '{}|robot_GRP|FK_CTRLS|a3FK_CTRL': ['rotateX'],
                   '{}|robot_GRP|FK_CTRLS|a4FK_CTRL': ['rotateZ'],
                   '{}|robot_GRP|FK_CTRLS|a5FK_CTRL': ['rotateX'],
                   '{}|robot_GRP|FK_CTRLS|a6FK_CTRL': ['rotateZ']}

    robots = get_robot_roots()

    current_frame = pm.currentTime()
    for robot in robots:
        # Check if there's an keyframe set on the target_CTRL.ik attribute
        key = pm.keyframe('{}|robot_GRP|target_CTRL'.format(robot),
                          attribute='ik',
                          query=True,
                          time=current_frame)

        # If there is no keyframe set on the IK attribute, continue to the
        # next robot
        if not key:
            pm.warning('{} has no IK|FK keyframe at frame {}' \
                       .format(robot, current_frame))
            continue

        for obj in keyed_attrs:
            for attr in keyed_attrs[obj]:
                pm.cutKey(obj.format(robot),
                          time=current_frame,
                          attribute=attr,
                          option="keys")

        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            pm.cutKey('{}|robot_GRP|tool_CTRL'.format(robot),
                      time=current_frame,
                      attribute='visibility',
                      option="keys")

        if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
            if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
                pm.cutKey('{}|robot_GRP|tool_CTRL'.format(robot),
                          time=current_frame,
                          attribute='translate',
                          option="keys")
                pm.cutKey('{}|robot_GRP|tool_CTRL'.format(robot),
                          time=current_frame,
                          attribute='rotate',
                          option="keys")
            else:
                pm.cutKey('{}|robot_GRP|target_CTRL'.format(robot),
                          time=current_frame,
                          attribute='translate',
                          option="keys")
                pm.cutKey('{}|robot_GRP|target_CTRL'.format(robot),
                          time=current_frame,
                          attribute='rotate',
                          option="keys")


def toggle_ik_fk_ui(*args):
    """
    Toggle control mode of Inverse Kinematics or Forward Kinematics in the Mimic UI.
    :param args:
    :return:
    """
    if not pm.window("mimic_win", exists=True):
        return

    current_tab = pm.tabLayout('switcher_tab_layout', query=True, selectTabIndex=True)

    if current_tab == 1:
        pm.tabLayout('switcher_tab_layout', edit=True, selectTabIndex=2)
    elif current_tab == 2:
        pm.tabLayout('switcher_tab_layout', edit=True, selectTabIndex=1)
    else:
        pm.warning('Error toggling IK/FK tabs')


def key_ik_fk(*args):
    """
    Key the Inverse Kinematic or Forward Kinematic pose of a robot in the Maya
    scene, depending on control mode selected in the Mimic UI.
    :param args:
    :return:
    """
    if not pm.window("mimic_win", exists=True):
        return

    current_tab = pm.tabLayout('switcher_tab_layout', query=True, selectTabIndex=True)

    try:
        if current_tab == 1:
            key_ik()
        elif current_tab == 2:
            key_fk()
    except:
        pm.warning('Error keying IK/FK')


def _filter_hotkey_set_name(hotkey_set_name):
    """
    Force input hotkey-set name to exclude special characters.
    :param hotkey_set_name: Named of hotkey-set for use in Maya.
    :return:
    """
    # Replace spaces with underscores
    hotkey_set_name = hotkey_set_name.replace(' ', '_')
    # Remove special characters
    hotkey_set_name = ''.join(re.findall(r"[_a-zA-Z0-9]+", hotkey_set_name))
    return hotkey_set_name


def _create_hotkey_set():
    """
    Create a hotkey-set associated with Mimic.
    :return:
    """
    message_str = 'You must use a custom hotkey profile.\n\n' \
                  'To continue adding Mimic hotkeys, switch \n' \
                  'to a custom hotkey set in the Hotkey Editor\n' \
                  'or create a new profile below. \n'

    user_input = pm.promptDialog(
        title='New Hotkey Profile',
        message=message_str,
        messageAlign='center',
        button=['Cancel', 'Create'],
        defaultButton='Create',
        text='Mimic_Hotkeys',
        style='text',
        cancelButton='Cancel',
        dismissString='Cancel')

    if user_input == 'Create':
        hotkey_set_name = pm.promptDialog(query=True, text=True)
        hotkey_set_name_filtered = _filter_hotkey_set_name(hotkey_set_name)
        pm.hotkeySet(hotkey_set_name_filtered, current=True)
        print 'New Hotkey Set created: {}'.format(hotkey_set_name_filtered)
        return True


def assign_hotkey(command_name, annotation_str, command_string):
    """
    Assigns hotkeys using a user's character input and a command.
    :param command_name: Name of the Mimic command for hotkey (acquired from Mimic)
    :param annotation_str: Comment or description of hotkey
    :param command_string: String-form of the actual command to execute
    :return:
    """

    if command_name == 'mimic_toggleIkFkMode':
        key_str = pm.textField('t_toggleIkFk', query=True, text=True)
    elif command_name == 'mimic_keyIkFk':
        key_str = pm.textField('t_keyIkFk', query=True, text=True)

    if len(key_str) > 1:
        pm.warning('Hotkey must be a single character; no hotkey set')
        return

    # Check if the user is in Maya's locked default hotkey set.
    if pm.hotkeySet(query=True, current=True) == 'Maya_Default':
        # If so, try switching to the default Mimic Hotkey Set
        if pm.hotkeySet('Mimic_Hotkeys', exists=True):
            pm.hotkeySet('Mimic_Hotkeys', current=True, edit=True)
            print 'Hotkey Set changed to Mimic Hotkeys'
        # If Mimic Hotkey set doesn't exist, propt the user to create a custom
        # Hotkey set and switch to it. 
        else:
            hotkey_set_created = _create_hotkey_set()
            # If the user does not create a new hotkey set, exit the function
            if not hotkey_set_created:
                pm.warning('No custom hotkey profile created; ' \
                           'No Mimic Hotkey set')
                return

    if key_str:
        if pm.runTimeCommand(command_name, exists=True):
            pass
        else:
            pm.runTimeCommand(command_name,
                              category='Custom Scripts',
                              annotation=annotation_str,
                              command=command_string,
                              commandLanguage='python')

        hotkey_name = command_name + 'Hotkey'

        if pm.hotkey(key_str, query=True):
            if pm.hotkey(key_str, query=True, name=True) == hotkey_name:
                print 'Hotkey ' \
                      '\'{}\' ' \
                      'already set to ' \
                      '\'{}\''.format(key_str, hotkey_name)

            else:
                pm.warning('Hotkey ' \
                           '\'{}\' ' \
                           'already in use by another function' \
                           .format(key_str))
        else:
            pm.nameCommand(hotkey_name,
                           command=command_name,
                           annotation=annotation_str)

            pm.hotkey(keyShortcut=key_str,
                      name=hotkey_name)

            print '{} hotkey set to \'{}\' key'.format(command_name, key_str)
    else:
        pm.warning('No key string input; ' \
                   'input a key string in Mimic UI')

    pm.setFocus('prefs_tab_layout')


def remove_hotkey(command_name):
    """
    Removes hotkey from the user hotkey-set.
    :param command_name: Name of the Mimic command for hotkey (acquired from Mimic)
    :return:
    """
    if command_name == 'mimic_toggleIkFkMode':
        key_str = pm.textField('t_toggleIkFk', query=True, text=True)
    elif command_name == 'mimic_keyIkFk':
        key_str = pm.textField('t_keyIkFk', query=True, text=True)

    if len(key_str) > 1:
        pm.warning('Hotkey must be a single character')
        return

    # Check if key_str is assigned as a hotkey to cmd_name runtimeCommand
    if key_str:
        if pm.hotkey(key_str, query=True, name=True) == command_name + 'Hotkey':
            pm.runTimeCommand(command_name, edit=True, delete=True)
            pm.hotkey(keyShortcut=key_str, name=None)
            print 'Hotkey {} removed from \'{}\' key'.format(command_name, key_str)
        else:
            pm.warning('\'{}\' key is not assigned to the {} function in ' \
                       'the current Hotkey Set; no hotkey was removed' \
                       .format(key_str, command_name))
    else:
        pm.warning('No key input; ' \
                   'input the key you\'d like to remove in Mimic UI')


def find_hotkey(hotkey_name):
    """
    If a hotkey is assigned, this function finds and adds it to the Mimic UI
    at runtime.
    :param hotkey_name:
    :return:
    """
    # Check if the user is in Maya's locked default hotkey set.
    if pm.hotkeySet(query=True, current=True) == 'Maya_Default':
        # If so, try switching to the default Mimic Hotkey Set
        if pm.hotkeySet('Mimic_Hotkeys', exists=True):
            pm.hotkeySet('Mimic_Hotkeys', current=True, edit=True)
            print 'Hotkey Set changed to Mimic Hotkeys'

    count = pm.assignCommand(query=True, numElements=True)

    key = ''
    for index in range(1, count + 1):
        if pm.assignCommand(index, query=True, name=True) == hotkey_name:
            key = pm.assignCommand(index, query=True, keyString=True)[0]

    if key == 'NONE':
        return None
    else:
        return key


def set_shader_range(*args):
    """
    Sets the range of angles within which the limit-shader will show up.
    :param args:
    :return:
    """
    shader_range = pm.floatField("f_shaderRange", value=True, query=True)

    robots = get_robot_roots()
    if not robots:
        pm.warning('No robots selected')
        return

    for robot in robots:
        pm.setAttr('{}|robot_GRP|target_CTRL.shaderRange'.format(robot),
                   shader_range)


def import_robot(rigs_dir):
    """
    Imports selected robot from Mimic UI dropdown menu into the scene
    :param rigs_dir: string; directory where robot rig files are located
    :return:
    """

    # If the scene is in IK mode, switch to FK before importing the robot
    current_tab = pm.tabLayout('switcher_tab_layout', query=True, selectTabIndex=True)
    if current_tab == 2:
        pm.tabLayout('switcher_tab_layout', edit=True, selectTabIndex=1)

    rigs = general_utils.get_rigs_dict()
    rig_names = general_utils.get_rigs_names(rigs)
    for rig_name in rig_names:
        try:
            if pm.optionMenu('robotImportList',
                             query=True,
                             value=True) == rig_name:
                try:
                    rig_path = rigs[rig_name]
                    pm.importFile(rig_path,
                                  defaultNamespace=True,
                                  returnNewNodes=True)
                except:
                    pm.warning('Error Loading ' + rig_name)
        except:
            pm.warning('No robots found; check rig directory')


def save_pose_to_shelf(*args):
    """
    Save a robot pose as a button on the Mimic shelf. Saves both IK and FK poses.
    :param args:
    :return:
    """
    target_shelf = mel.eval('tabLayout -q -selectTab $gShelfTopLevel;')
    store_cmds = 'import pymel.core as pm \n' \
                 'import mimic_utils \n' \
                 'reload(mimic_utils) \n\n' \
        # 'if not check_robot_selection(1): \n' \
    # '    robot = \'\' \n\n'

    startLineCode = "["
    endLineCode = "],\n"

    if not check_robot_selection(1):
        pm.warning("Must select exactly one robot")
        return

    robot = get_robot_roots()[0]
    # Check which mode we're in
    current_tab = pm.tabLayout('switcher_tab_layout', query=True, st=True)

    # IK MODE
    if current_tab == 'ikTab':
        store_cmds += 'tab = 1 \n'
        store_cmds += 'attrs = ['

        target_ctrl = '{}|robot_GRP|target_CTRL'.format(robot)
        target_ctrl_str = '{}|robot_GRP|target_CTRL'

        config_attrs = ['ik', 'v', 'ikSolution1', 'ikSolution2', 'ikSolution3']
        for each in config_attrs:
            find_val = pm.getAttr(target_ctrl + "." + each)
            save_to_shelf = (startLineCode
                             + "'"
                             + (target_ctrl_str + "." + each)
                             + "', " + " %f" + endLineCode) % find_val

            store_cmds += save_to_shelf

        # If a tool controller exists, use that to keyframe transformation
        # attributes
        if pm.objExists('{}|robot_GRP|tool_CTRL'.format(robot)):
            target_ctrl = '{}|robot_GRP|tool_CTRL'.format(robot)
            target_ctrl_str = '{}|robot_GRP|tool_CTRL'
        else:
            target_ctrl = '{}|robot_GRP|target_CTRL'.format(robot)
            target_ctrl_str = '{}|robot_GRP|target_CTRL'

        keyable = pm.listAttr(target_ctrl,
                              k=True,
                              r=True,
                              w=True,
                              c=True,
                              u=True)

        # Remove robotSubtype from list
        # In future rigs, this shouldn't be keyable
        if 'robotSubtype' in keyable:
            keyable.remove('robotSubtype')

        print keyable
        for each in keyable:
            find_val = pm.getAttr(target_ctrl + "." + each)
            save_to_shelf = (startLineCode + "'" + (
                target_ctrl_str + "." + each) + "', " + " {}".format(find_val) + endLineCode)
            store_cmds += save_to_shelf

    # FK MODE
    else:

        store_cmds += 'tab = 2 \n'
        store_cmds += 'attrs = ['

        target_ctrl = '{}|robot_GRP|target_CTRL'.format(robot)
        target_ctrl_str = '{}|robot_GRP|target_CTRL'

        config_attrs = ['ik', 'v']
        for each in config_attrs:
            find_val = pm.getAttr(target_ctrl + "." + each)
            save_to_shelf = (startLineCode + "'" + (
                target_ctrl_str + "." + each) + "', " + " %f" + endLineCode) % find_val
            store_cmds += save_to_shelf

        fk_ctrl = "{}|robot_GRP|FK_CTRLS|".format(robot)
        fk_ctrl_str = "{}|robot_GRP|FK_CTRLS|"
        joint_vals = ['a1FK_CTRL', 'a2FK_CTRL', 'a3FK_CTRL', 'a4FK_CTRL', 'a5FK_CTRL', 'a6FK_CTRL']
        joint_val_attr = ['rotateY', 'rotateX', 'rotateX', 'rotateZ', 'rotateX', 'rotateZ']

        for i, each in enumerate(joint_vals):
            attrs = fk_ctrl + each + "." + joint_val_attr[i]
            attr_str = fk_ctrl_str + each + "." + joint_val_attr[i]
            find_val = pm.getAttr(attrs)
            save_to_shelf = (startLineCode + "'" + attr_str + "', " + " %f" + endLineCode) % find_val
            store_cmds += save_to_shelf

    store_cmds += '] \n\n' \
                  'mimic_utils.assign_saved_pose(attrs, tab) \n'

    prompt_dialog = pm.promptDialog(t="Robot Pose", m="Pose Name:", b="Save")

    # Condition statement that checks if our button gets clicked.  If this condition is met, then run the following commands
    if prompt_dialog == "Save":
        # This variable stores the Name we add to our Prompt Dialog
        prompt_dialog_name = pm.promptDialog(query=True, text=True)
        # This line creates our Shelf Button that uses MEL as the source type for the commands stored in "store_cmds", and adds the Shelf Button under our custom tab named "Body Poses"
        pm.shelfButton(l=prompt_dialog_name, annotation=prompt_dialog_name, imageOverlayLabel=prompt_dialog_name,
                       i='commandButton.png', command=store_cmds, p=target_shelf, sourceType="python")


def assign_saved_pose(attributes, tab):
    """
    Takes a saved pose from a shelf button (created with 'save_pose_to_shelf')
    and assigns that pose to the selected robot.
    :param attributes: Robot attributes saved in pose button.
    :param tab: IK or FK mode, derived from tab being controlled by user
    :return:
    """
    if not check_robot_selection(1):
        pm.warning('Must have single robot selected')
        return
    pm.tabLayout('switcher_tab_layout', edit=True, sti=tab)
    robot = get_robot_roots()[0]
    for attr in attributes:
        pm.setAttr(attr[0].format(robot), attr[1])
    return


def get_maya_framerate():
    """
    Get the animation framerate setting used in the Maya scene.
    :return:
    """
    if pm.currentUnit(time=True, query=True) == 'game':
        framerate = 15.
    elif pm.currentUnit(time=True, query=True) == 'film':
        framerate = 24.
    elif pm.currentUnit(time=True, query=True) == 'pal':
        framerate = 25.
    elif pm.currentUnit(time=True, query=True) == 'ntsc':
        framerate = 30.
    elif pm.currentUnit(time=True, query=True) == 'show':
        framerate = 48.
    elif pm.currentUnit(time=True, query=True) == 'palf':
        framerate = 50.
    elif pm.currentUnit(time=True, query=True) == 'ntscf':
        framerate = 60.
    else:
        pm.currentUnit(time='film')
        framerate = 24.

    return framerate


def _get_animation_parameters():
    """
    Get the animation parameters start frame, end frame, framerate, and total time
    in seconds from Maya.
    :return:
    """
    start_frame = pm.intField("i_programStartFrame", query=True, value=True)
    end_frame = pm.intField("i_programEndFrame", query=True, value=True)
    framerate = get_maya_framerate()

    # Define the animation time in seconds.
    animation_time_sec = ((end_frame + 1) - start_frame) / framerate

    animation_params = {'Start Frame': start_frame,
                        'End Frame': end_frame,
                        'Framerate': framerate,
                        'Animation Time (sec)': animation_time_sec}

    return animation_params


def _check_command_parameters(robot, animation_params):
    """
    Checks that the user input for animation paramters is valid.
    :param robot: name string of the selected robot
    :param animation_params: dict of animation parameters
    :return:
    """
    start_frame = animation_params['Start Frame']
    end_frame = animation_params['End Frame']

    if end_frame <= start_frame:
        pm.warning('End Frame must be larger than Start Frame')
        return

    # If no keyframes are set, exit the function.
    closest_ik_key = _get_closest_ik_keyframe(robot, start_frame)[0]

    if not type(closest_ik_key) == float:
        pm.warning('You must set an IK or FK keyframe to ensure ' \
                   'proper evaluation when saving a program; ' \
                   'no program written')
        return
    return True


def _get_commands_from_animation(robot, animation_params, time_interval_value, time_interval_units):
    """
    Get key-framed commands from the animation slider.
    :param robot: name string of the selected robot
    :param animation_params: dict of animation parameters
    :param time_interval_value: Sample rate
    :param time_interval_units: Sample rate units
    :return commands: list of list of robot configurations at each step
    """
    # Get relevant animation parameters.
    start_frame = animation_params['Start Frame']
    end_frame = animation_params['End Frame']
    framerate = animation_params['Framerate']
    animation_time_sec = animation_params['Animation Time (sec)']

    # Convert time interval from frames to seconds if necessary
    if time_interval_units == 'seconds':
        step_sec = time_interval_value
    else:  # time_interval_units == 'frames'
        step_sec = float(time_interval_value) / framerate

    # Find the closest multiple of the number of steps in our animation 
    # num_steps = int((step_sec * math.ceil(animation_time_sec / step_sec) + step_sec) / step_sec)
    num_steps = int(math.ceil(animation_time_sec / step_sec) + 1)

    # Create array of timesteps in milliseconds.
    time_array_sec = [round(i * step_sec, 5) for i in range(0, num_steps)]

    # Create array of timesteps in frames.
    time_array_frame = [round(start_frame + (framerate * t_sec), 3) for t_sec in time_array_sec]

    # Initialize output array.
    commands = [[0] * 6 for i in range(len(time_array_frame))]

    # Get the robot's axis configuration at each time step and write it to the
    # output array
    for i, frame in enumerate(time_array_frame):
        for j in range(6):
            commands[i][j] = pm.getAttr('{}|robot_GRP|target_CTRL.axis{}'
                                        .format(robot, j + 1), time=frame)

    # We have to manually inspect axes to ensure proper, continuous
    # evaluation with rotations +/- 180 degrees. 

    # Define which axes to inspect, along with their corresponding axis of
    # rotation. These are typically axes that have rotation limits > 180 and/
    # or < -180. Currently only axes 4 and 6 are supported by attributes on
    # target_CTRL (e.g. invertAxis4)
    axes = [4, 6]
    rotation_axes = ['Z', 'Z']

    for i, axis in enumerate(axes):
        # Get actual initial value based on keyframed value.
        keyed_val = _get_reconciled_rotation_value(robot,
                                                   axis,
                                                   rotation_axes[i],
                                                   start_frame)[0]

        # Replace initial axis values with keyed values.
        commands[0][axis - 1] = keyed_val

        # Traverse through the path table and ensure continuous evaluation on
        # the axes in question.
        for j, val in enumerate(commands):
            if j == 0:
                continue
            commands[j][axis - 1] = _accumulate_rotation(commands[j][axis - 1],
                                                         commands[j - 1][axis - 1])
    return commands, step_sec


def _check_exceeded_velocity_limits(robot, commands, time_interval_val=0.012):
    """
    Check a list of commands for velocity errors.
    :param robot: name string of the selected robot
    :param commands: A list of list of robot axes
    :param time_interval_val: Time between commands
    :return:
    """
    velocity_limits = get_velocity_limits(robot)
    animation_params = _get_animation_parameters()
    framerate = animation_params['Framerate']
    start_frame = animation_params['Start Frame']

    # Speeds becomes an array with num_axes rows and len(commands)-1 columns
    # Each row corresponds to the velocities at each time interval for each
    # robot Axis
    velocities = []

    # Find the speed of each axis at every sampled time interval
    for i in range(len(commands[0])):
        positions = [config[i] for config in commands]
        velocities.append([abs(b - a) / time_interval_val
                           for a, b in zip(positions, positions[1:])])

    # Construct a dictionary of the frames on each axis where velocity
    # limits have been exceeded  
    exceeded_limits = {}
    for i, axis in enumerate(velocities):
        dict_key = 'Axis {}'.format(i + 1)
        # Initialize dictionary of axes
        exceeded_limits[dict_key] = []
        for j, velocity in enumerate(axis):
            if velocity > velocity_limits[i]:
                this_frame = int(math.ceil(framerate * j * time_interval_val))
                frame = start_frame + this_frame
                exceeded_limits[dict_key].append(frame)

    # Remove duplicate frames from exceeded limits
    for each in exceeded_limits:
        exceeded_limits_set = list(set(exceeded_limits[each]))
        exceeded_limits_set.sort()
        exceeded_limits[each] = exceeded_limits_set

    return exceeded_limits


def _format_exceeded_velocity_limits(exceeded_limits):
    """
    Construct string to return printable statement of all exceeded velocities
    for each axis; ex. range [0, 1, 2, 3] will be formatted '0-3'.
    :param exceeded_limits: List of input exceeded limits.
    :return:
    """
    invoke_warning = False
    warning_identifiers = []
    # Get axis keys in order
    axes = exceeded_limits.keys()
    axes.sort()
    for axis in axes:  # Try for all axes
        # Check if the axis key has values
        frames = exceeded_limits[axis]
        if not frames:
            continue  # skip to next
        else:
            invoke_warning = True
            frames = general_utils.list_as_range_strings(frames)
            frames = '\n'.join('\t{}'.format(frame) for frame in frames)
            warning_identifiers.append(axis)
            warning_identifiers.append(frames)
    if invoke_warning:
        warning = 'WARNING!\n' \
                  'Velocity limits exceeded!\n' \
                  'See the following frames:\n'
        warning_identifiers.insert(0, warning)
        return '\n'.join(warning_identifiers)
    else:
        return ''


def _get_program_settings():
    """
    Get program settings from the Mimic UI.
    :return program_settings: dictionary
    """
    program_settings = {}

    # Sample Time
    time_unit_radio_button = pm.radioButtonGrp('time_unit_radio_group',
                                               query=True,
                                               sl=True)
    if time_unit_radio_button == 1:
        time_unit = 'seconds'
    else:
        time_unit = 'frames'

    try:
        time_between_samples = float(pm.textField('t_timeBetweenSamples',
                                                  query=True,
                                                  text=True))
        if time_between_samples <= 0:
            if time_unit == 'seconds':
                pm.warning('Time interval must be greater than zero; ' \
                           'Using default: .012 seconds')
                time_between_samples = 0.012
            else:
                pm.warning('Time interval must be greater than zero; ' \
                           'Using default: 1 frame')
                time_between_samples = 1

    except ValueError:
        if time_unit == 'seconds':
            pm.warning('Time interval must be a float; ' \
                       'using default: .012 seconds')
            time_between_samples = .012
        else:
            pm.warning('Time interval must be a float; ' \
                       'using default: 1 frame')
            time_between_samples = 1

            # Set the UI back to the default unit if necessary
    pm.textField('t_timeBetweenSamples',
                 edit=True,
                 text=str(time_between_samples))

    # Ignore warnings
    ignore_warnings = pm.checkBox('cb_ignoreWarnings',
                                  value=True,
                                  query=True)

    # Get the type of processor from the Mimic UI.
    processor_type = pm.optionMenu('postProcessorList',
                                   query=True,
                                   value=True)

    # Get the user directory from the Mimic UI.
    output_directory = pm.textField('t_programDirectoryText',
                                    text=True,
                                    query=True)

    # Get the file name from the Mimic UI and prepend the name of the
    # current robot.
    output_filename = pm.textField('t_outputFileName',
                                   text=True,
                                   query=True)

    template_filename = pm.textField('t_templateFileName',
                                   text=True,
                                   query=True)

    # Get the sample rate from the Mimic UI
    sample_rate = pm.radioCollection('sample_rate_radio_collection',
                                     q=True,
                                     sl=True)

    # Check if the file should be overwritten if it already exists.
    overwrite_option = pm.checkBox('cb_overwriteFile',
                                   value=True,
                                   query=True)

    # Assign values to output dict
    program_settings['Time Interval'] = {'value': time_between_samples,
                                         'units': time_unit}
    program_settings['Ignore Warnings'] = ignore_warnings
    program_settings['Processor Type'] = processor_type
    program_settings['Output Directory'] = output_directory
    program_settings['Output Filename'] = output_filename
    program_settings['Template Filename'] = template_filename
    program_settings['Overwrite Option'] = overwrite_option

    return program_settings


def check_program(*args):
    """
    Checks robot, command parameters, performs the velocity check on a list of
    commands to be used for use as robot control code.
    :param args:
    :return:
    """
    # TODO: Copied directly from save_program... bad implementation
    # clear output window
    pm.scrollField('programOutputScrollField', clear=True, edit=True)

    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; ' \
                   'Select a valid robot to export; ' \
                   'no program written')
        return

    if len(robots) > 1:
        pm.warning('Too many robots selected; ' \
                   'select a single robot to export')

    robot = robots[0]

    program_settings = _get_program_settings()
    animation_params = _get_animation_parameters()
    # For the selected robot, convert the animation to a robot control
    # program and write it to a file
    if not _check_command_parameters(robot, animation_params):
        pm.scrollField('programOutputScrollField',
                       edit=True,
                       text='No program written \n\n' \
                            'Check script editor for\ndetails \n\n')
        return



    # Get programmed time between samples
    time_interval_value = program_settings['Time Interval']['value']
    time_interval_units = program_settings['Time Interval']['units']

    # Get axis configuration at each time interval (typically every frame)
    raw_commands, step_sec = _get_commands_from_animation(robot, animation_params, time_interval_value, time_interval_units)

    # Check if limits have been exceeded (i.e. velocity, acceleration)
    exceeded_limits = _check_exceeded_velocity_limits(robot, raw_commands, step_sec)
    exceeded_limits_warning = _format_exceeded_velocity_limits(exceeded_limits)
    if exceeded_limits_warning != '':
        pm.scrollField('programOutputScrollField',
                       insertText=exceeded_limits_warning + '\n',
                       edit=True)
        pm.warning('Velocity limits exceeded; expand the Mimic window to see output for details')
    else:
        pm.scrollField('programOutputScrollField',
                       insertText='No limits exceeded!' + '\n',
                       edit=True)

    # _check_selected_vs_supported_options()


def get_keyframed_commands(robot, animation_params):
    """
    Get's robot configuration between the specified program range at each
    keyframe. A "keyframe", in this function, is defined as ONLY an IK or FK
    keyframe that has been set by the user
    :param robot: name string of the selected robot
    :param animation_params: dict of animation parameters
    :return commands: list of list of robot configurations at each step
    """


    # Get relevant animation parameters.
    start_frame = animation_params['Start Frame']
    end_frame = animation_params['End Frame']

    # Get a list of all keyframes on robots IK attribute for the given animation
    # frame range
    ik_keys = pm.keyframe('{}|robot_GRP|target_CTRL'.format(robot),
                          attribute='ik',
                          query=True,
                          time='{}:{}'.format(start_frame, end_frame))

    # Verify that there is also a keyframe set on the FK controls' rotate
    # attributes. If there's not, we remove it from the list
    # Note: we only need to check on controller as they are al keyframed
    # together
    ik_keys_filtered = [key for key in ik_keys if pm.keyframe('{}|robot_GRP|FK_CTRLS|a1FK_CTRL.rotateY'.format(robot),
                                                              query=True,
                                                              time=key)]

    # Initialize output array.
    commands = [[0] * 6 for i in range(len(ik_keys_filtered))]


    # Get the robot's axis configuration at each time step and write it to the
    # output array
    for i, frame in enumerate(ik_keys_filtered):
        for j in range(6):
            commands[i][j] = pm.getAttr('{}|robot_GRP|target_CTRL.axis{}'
                                        .format(robot, j + 1), time=frame)

    # We have to manually inspect axes to ensure proper, continuous
    # evaluation with rotations +/- 180 degrees. 

    # Define which axes to inspect, along with their corresponding axis of
    # rotation. These are typically axes that have rotation
    # limits > 180 and/or < -180. Currently only axes 4 and 6 are 
    # ported by attributes onv target_CTRL (e.g. invertAxis4)

    axes = [4, 6]
    rotation_axes = ['Z', 'Z']
    for i, frame in enumerate(ik_keys_filtered):    
        for j, axis in enumerate(axes):
            # Get actual value based on keyframed value.
            keyed_val = _get_reconciled_rotation_value(robot,
                                                       axis,
                                                       rotation_axes[j],
                                                       frame)[0]

            # Replace initial axis values with keyed values.
            commands[i][axis - 1] = keyed_val

    return commands


def save_program(*args):
    """
    Acquires a list of commands from Mimic and issues it to a post processor;
    saves output as usable robot control code in user-defined directory.
    :param args:
    :return:
    """

    # clear output window
    pm.scrollField('programOutputScrollField', clear=True, edit=True)

    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; ' \
                   'Select a valid robot to export; ' \
                   'no program written')
        return

    if len(robots) > 1:
        pm.warning('Too many robots selected; ' \
                   'select a single robot to export')

    robot = robots[0]
    # For the selected robot, convert the animation to a robot control
    # program and write it to a file

    program_settings = _get_program_settings()
    animation_params = _get_animation_parameters()


    if not _check_command_parameters(robot, animation_params):
        pm.scrollField('programOutputScrollField',
                       edit=True,
                       text='No program written \n\n' \
                            'Check script editor for\ndetails \n\n')
        return


    # If the UI radio button is set to "sample rate"
    if pm.radioCollection('sample_rate_radio_collection', query=True, select=True) == 'rb_timeInterval':
        # Get programmed time between samples
        time_interval_value = program_settings['Time Interval']['value']
        time_interval_units = program_settings['Time Interval']['units']

        # Get axis configuration at each time interval (typically every frame)
        raw_commands, step_sec = _get_commands_from_animation(robot, animation_params, time_interval_value, time_interval_units)

        # Check if limits have been exceeded (i.e. velocity, acceleration)
        exceeded_limits = _check_exceeded_velocity_limits(robot, raw_commands, step_sec)
        exceeded_limits_warning = _format_exceeded_velocity_limits(exceeded_limits)
        if exceeded_limits_warning != '':
            pm.warning('Velocity limits exceeded; expand the Mimic window to see output for details')

    # Otherwise the radio button is set to "Keyframes only"
    else:
        # If we're sampling keyframes only, we assume we're using a post-
        # processor option that's not-time base, and therefor we don't
        # check for velocity limits
        exceeded_limits_warning = ''

        # Get commands at keyframes only
        raw_commands = get_keyframed_commands(robot, animation_params)


    # Check if warnings should be ignored
    ignore_warnings = program_settings['Ignore Warnings']

    if exceeded_limits_warning == '' or ignore_warnings:
        # Get the type of processor from the Mimic UI.
        processor_type = program_settings['Processor Type']

        # Get the user directory from the Mimic UI.
        output_directory = program_settings['Output Directory']

        # Check if the file should be overwritten if it already exists.
        overwrite_option = program_settings['Overwrite Option']

        # Define options that will be passed into the processor.
        user_options = postproc_options.get_user_selected_options()

        # Create processor given above options
        processor = postproc_setup.POST_PROCESSORS[processor_type]()

        # Configure raw_commands (hard coded)
        commands = processor.get_formatted_commands(raw_commands)

        # Make sure we're using the right directory
        processor.set_program_directory(output_directory)

        # Process the raw_commands into relevant robot control code
        template_filename = program_settings['Template Filename']
        filled_template = processor.process(commands, user_options, template_filename)

        # write the processed animation as robot code to a file
        output_filename = program_settings['Output Filename']
        output_path = processor.write(
            filled_template,
            output_filename=output_filename,
            overwrite=overwrite_option)

        # Update the output-text viewer in the Mimic UI
        details = 'Processor name : {}\n' \
                  'Processor type : {}\n' \
                  'Template path  : {}\n' \
                  'Output path    : {}\n' \
                  '\n'
        filled_details = details.format(processor.__class__.__name__,
                                        processor.get_processor_type(),
                                        processor.get_program_template_path(),
                                        processor.get_program_output_path())
        pm.scrollField('programOutputScrollField',
                       insertText=filled_details,
                       edit=True)

        pm.scrollField('programOutputScrollField',
                       insertText=filled_template + '\n',
                       edit=True)

    # Output warnings always
    pm.scrollField('programOutputScrollField',
                   insertText=exceeded_limits_warning + '\n',
                   edit=True)
