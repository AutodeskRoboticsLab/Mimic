#!usr/bin/env python
# -*- coding: utf-8 -*-

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
from robotmath import inverse_kinematics

reload(mimic_config)
reload(general_utils)
reload(inverse_kinematics)

OUTPUT_WINDOW_NAME = 'programOutputScrollField'

# The following are unformatted strings that represent common transform names
# Used by Mimic. When formatted (e.g. using format_path()) they account for 
# any transform namespaces, allowing referencing of Mimic robot rigs
#
# e.g. '{0}|{1}robot_GRP|{1}target_CTRL' becomes 
# 'namespace:KUKA_KR_60_3_0|namespace:robot_GRP|namespace:targel_CTRL'
#
# If there is no namespace, '{0}|{1}robot_GRP|{1}target_CTRL' becomes 
# 'KUKA_KR_60_3_0|robot_GRP|targel_CTRL'

__TARGET_CTRL_PATH = '{0}|{1}robot_GRP|{1}target_CTRL'
__TOOL_CTRL_PATH = '{0}|{1}robot_GRP|{1}tool_CTRL'
__LOCAL_CTRL_PATH = '{0}|{1}robot_GRP|{1}local_CTRL'
__ROBOT_GRP_PATH = '{0}|{1}robot_GRP'
__WORLD_CTRL_PATH = '{0}|{1}world_CTRL'

__A1_PATH = '{0}|{1}robot_GRP|{1}robot_GEOM|{1}Base|{1}axis1'
__A2_PATH = __A1_PATH + '|{1}axis2'
__A3_PATH = __A2_PATH + '|{1}axis3'
__A4_PATH = __A3_PATH + '|{1}axis4'
__A5_PATH = __A4_PATH + '|{1}axis5'
__A6_PATH = __A5_PATH + '|{1}axis6'

__FK_CTRLS_PATH = '{0}|{1}robot_GRP|{1}FK_CTRLS'
__A1_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a1FK_CTRL'
__A2_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a2FK_CTRL'
__A3_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a3FK_CTRL'
__A4_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a4FK_CTRL'
__A5_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a5FK_CTRL'
__A6_FK_CTRL_PATH = __FK_CTRLS_PATH + '|{1}a6FK_CTRL'


__TCP_HDL_PATH = __A6_PATH + '|{1}tcp_GRP|{1}tcp_HDL'
__TOOL_MDL_PATH = __TCP_HDL_PATH + '|{1}tool_MDL'
__TOOL_CTRL_FK_PATH = __TCP_HDL_PATH + '|{1}tool_CTRL_FK'
__TARGET_HDL_PATH = '{0}|{1}robot_GRP|{1}target_HDL'


def get_robot_roots(all_robots=False, sel=[]):
    """
    Gets the root node name of the robot(s) in the scene (e.g. 'KUKA_KR60_0')
    - If all_robots = True, get_robot_roots returns the robot name(s) for all
      robots in the scene, regardless of selection
    - If all_robots = False, get_robot_roots returns the robot name(s) for
      selected objects, if the object is a child of the robot
      (e.g. 'target_CTRL')
    :param all_robots: boolean; flag to specify which robot names to return:
                       all robots or just the selected ones
    :param sel: list; list of all of the object selected in the Maya viewport
    :return robot_roots: list
    """

    robot_root_names = []

    # If no robots exist, return empty array.
    if not pm.objExists('*|robot_GRP|target_CTRL') and not pm.objExists('*:*|*:robot_GRP|*:target_CTRL'):
        return robot_root_names

    if all_robots:
        # All valid robot rigs will have this hierarchy
        sel = []
        
        # Find robots with and without namespaces
        robots_without_namespace = pm.ls('*|robot_GRP|target_CTRL')
        robots_with_namespace = pm.ls('*:*|*:robot_GRP|*:target_CTRL')
        
        # Add each robot to the selection list
        for robot in robots_without_namespace:
            sel.append(robot)
        for robot in robots_with_namespace:
            sel.append(robot)        

    else:
        # If no selection is passed, manually check for selections in Maya's
        # viewport.
        if not sel:
            sel = pm.ls(selection=True, type='transform')
            # If there is nothing selected in Maya's viewport,
            # return an empty
        if not sel:
            return robot_root_names

    for selection in sel:
        # For current selected object, traverse up its hierarchy to find the
        # root robot transform node, if one exists.
        loop = True
        while loop:
            # Check if the selection has a namespace
            selection_namespace = selection.namespace()
            # Check if the selected object is the root robot transform.
            # e.g. 'KUKA_KR60_0'
            # If so, append it to the list of robots.
            if pm.objExists(format_path(__TARGET_CTRL_PATH, selection)):
                robot_root_names.append(selection)
                loop = False  # Continue to next selected object
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
                    loop = False

    robot_root_names = list(set(robot_root_names))  # Eliminate duplicates
    
    return robot_root_names


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


def get_selected_robot_name():
    """
    Get robot
    :return:
    """
    robots = get_robot_roots(all_robots=False)
    if len(robots) == 0:
        warning = 'No robots selected!'
        raise Exception(warning)
    elif len(robots) > 1:
        warning = 'Too many robots selected!'
        raise Exception(warning)
    robot = robots[0]
    return robot


def format_path(path_string, selection):
    """
    Handles formatting of namespaces that the input selection is associated
    with.

    Takes a raw sting input (e.g. '{0}|{1}robot_GRP') and places the input
    selection string in {0}, and the selections namespace in {1}
    :param path_string: string to be formatted
    :param selection: selected robot transform
    :return:
    """
    return path_string.format(selection, selection.namespace())


def get_robot_configuration(robot_name, frame):
    """
    Get the configuration of this robot.
    :param robot_name: string, name of robot
    :param frame: int, frame parameter
    :return:
    """
    target_ctrl_path = get_target_ctrl_path(robot_name)
    attr = 'ikSolution'
    configurations = []
    for i in range(3):
        index = i + 1
        configuration_path = '{}.{}{}'.format(target_ctrl_path, attr, index)
        configuration = get_attribute_value(configuration_path, frame)
        configurations.append(configuration)
    return configurations


def get_robot_type(robot_name):
    """
    Get Type of robot
    :param robot_name: string, name of robot
    :return:
    """
    attr = 'robotType'
    path = '{}.{}'.format(get_target_ctrl_path(robot_name), attr)
    return get_attribute_value(path)


def get_robot_subtype(robot_name):
    """
    Get subType of robot
    :param robot_name: string, name of robot
    :return:
    """
    attr = 'robotSubtype'
    path = '{}.{}'.format(get_target_ctrl_path(robot_name), attr)
    return get_attribute_value(path)


def get_target_ctrl_path(robot_name):
    """
    Get the long name of input robot's target_CTRL transform.
    :param robot_name: string, name of robot
    :return:
    """
    return format_path(__TARGET_CTRL_PATH, robot_name)


def get_tool_ctrl_path(robot_name):
    """
    Get the long name of input robot's tool_CTRL transform.
    :param robot_name: string, name of robot
    :return:
    """
    return format_path(__TOOL_CTRL_PATH, robot_name)


def get_tool_ctrl_fk_path(robot_name):
    """
    Get the long name of input robot's tool_CTRL_FK transform.
    :param robot_name: string, name of robot
    :return:
    """
    return format_path(__TOOL_CTRL_FK_PATH, robot_name)


def get_tcp_hdl_path(robot_name):
    """
    Get the long name of input robot's tcp_HDL transform.
    :param robot_name: string, name of robot
    :return:
    """
    return format_path(__TCP_HDL_PATH, robot_name)


def get_local_ctrl_path(robot_name):
    """
    Get the long name of input robot's target_CTRL transform.
    :param robot_name: string, name of robot
    :return:
    """
    return format_path(__LOCAL_CTRL_PATH, robot_name)


def get_attribute_value(attribute_path, frame=None):
    """
    Get an attribute's value using its path and, optionally, a frame to sample.
    :param attribute_path: string, attribute path using robot and attribute names
    :param frame: optional frame parameter
    :return:
    """
    if frame is None:
        return pm.getAttr(attribute_path)
    else:
        return pm.getAttr(attribute_path, time=frame)


def get_tool_path(robot_name):
    """
    Get path to robot tool
    :param robot_name: string, name of robot
    :return:
    """
    tool_name = get_tool_ctrl_path(robot_name)
    try:  # Try to grab the named tool
        tool_object = pm.ls(tool_name)[0]  # Try to get tool, may raise an exception
    except IndexError:  # No tool attached, use flange
        tool_name = format_path(__TCP_HDL_PATH, robot_name)
    return tool_name


def clear_limits_ui(*args):
    """
    Clears the axis limit fields in the Mimic UI.
    :param args: Required for Maya to pass command from the UI
    :return:
    """
    current_tab = pm.tabLayout('limits_tab_layout',
                               query=True,
                               selectTab=True)

    for i in range(6):
        if current_tab == 'position_limits_tab':
            pm.textField('t_A{}Min'.format(i + 1), edit=True, text='')
            pm.textField('t_A{}Max'.format(i + 1), edit=True, text='')
        elif current_tab == 'velocity_limits_tab':
            pm.textField('t_A{}Velocity'.format(i + 1), edit=True, text='')
        elif current_tab == 'accel_limits_tab':
            pm.textField('t_A{}Accel'.format(i + 1), edit=True, text='')
        elif current_tab == 'jerk_limits_tab':
            pm.textField('t_A{}Jerk'.format(i + 1), edit=True, text='')


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


def get_closest_ik_keyframe(robot, current_frame):
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
    ik_keys = pm.keyframe(get_target_ctrl_path(robot),
                          attribute='ik',
                          query=True,
                          time='-10:')

    # Verify that there is also a keyframe set on the FK controls' rotate
    # attributes. If there's not, we remove it from the list
    # Note: we only need to check one controller as they are all keyframed
    # together
    ik_keys_filtered = [key for key in ik_keys if pm.keyframe(format_path(__A1_FK_CTRL_PATH, robot) + '.rotateY', query=True, time=key)]

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


def accumulate_rotation(a_in, a_0):
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


def get_reconciled_rotation_value(robot, axis, rotation_axis, current_frame):
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
    target_ctrl_path = get_target_ctrl_path(robot)
    # Find the closest keyframe on the robot's IK attribute
    closest_ik_key, count_direction = get_closest_ik_keyframe(robot,
                                                              current_frame)

    attr_path = '{0}|{1}robot_GRP|{1}FK_CTRLS|{1}a{2}FK_CTRL.rotate{3}' \
                .format(robot, robot.namespace(), axis, rotation_axis)

    # If there are no IK attribute keyframes on the current robot,
    # return the DG produced value and exit the function.
    if not type(closest_ik_key) == float:
        keyed_val = pm.getAttr(target_ctrl_path + '.axis{}'.format(axis),
                               time=current_frame)
        return keyed_val, flip

    # If the current frame has an ik attribute keyframe,
    # assign that value as the keyed value.
    if closest_ik_key == current_frame:
        # Axis rotation value as given by the Dependency Graph
        dg_val = pm.getAttr(target_ctrl_path + '.axis{}'.format(axis))

        # Axis rotation as approximated by an IK keyframe
        keyed_val = pm.getAttr(attr_path, time=current_frame)
        keyed_val = accumulate_rotation(dg_val, keyed_val)

        if abs(dg_val - keyed_val) > 300:
            flip = True

    # If the current frame doesn't have an IK attribute keyframe,
    # find the closest one and traverse the timeline to determine the correct
    # evaluation.
    else:
        # Initialize axis value as keyframed value.
        keyed_val = pm.getAttr(attr_path, time=closest_ik_key)

        # Traverse the timeline from the closest IK attribute keyframe to the
        # current frame. Determine desired rotation angle at each frame
        for frame in range(int(closest_ik_key),
                           int(current_frame + count_direction),
                           count_direction):
            #pm.refresh()
            # Find the axis value at the current frame as given by the
            # Dependency Graph.
            dg_val = pm.getAttr(target_ctrl_path + '.axis{}'.format(axis),
                                time=frame)

            # Compare Dependency Graph evaluation with keyframed value
            keyed_val = accumulate_rotation(dg_val, keyed_val)

        if abs(dg_val - keyed_val) > 300:
            flip = True

    return keyed_val, flip


def reconcile_rotation(force_eval=False):
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

    # If the Mimic UI is not open, use the default setting
    if not pm.window("mimic_win", exists=True):
        execute_reconcile_rotation = mimic_config.EXECUTE_RECONCILE_ROTATION_DEFAULT
    else:
        execute_reconcile_rotation = pm.checkBox('cb_executeReconcileRotation',
                                                 query=True,
                                                 value=True)

    # If execute Reconcile Rotation is set to False, end the function
    if not execute_reconcile_rotation:
        if force_eval:
            pass
        else:
            return

    # Define which axes this function will operate on, along with their
    # corresponding axis of rotation. These are typically axes that have
    # rotation limits > 180 and/or < -180. Currently only axes 4 and 6 are
    # supported by attributes on target_CTRL (e.g. invertAxis4).
    axes = [4, 6]
    rotation_axes = ['Z', 'Z']

    current_frame = pm.currentTime()

    for robot in robots:
        in_ik_mode = pm.getAttr(get_target_ctrl_path(robot) + '.ik')

        # If the scene is in FK mode, do nothing.
        if not in_ik_mode:
            continue

        # For each axis, determine if the value needs to be manually flipped
        # +/- 360 degrees. If so, flip the axis value
        for i, axis in enumerate(axes):
            keyed_val, flip = get_reconciled_rotation_value(robot,
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
    runs close_hud(). This ensures that the HUD closes when the scene is
    closed.
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
    current position of the tool center point, local base frame, and
    target frame.

    This function is used to determine which IK configuration is necessary to
    match a given FK pose. To do this, we only need to inspect and compare
    axes 1, 2, and 5.
    :param robot: name string of the selected robot
    :return ik_sols: list of possible axis configurations
    """
    target_ctrl_path = get_target_ctrl_path(robot)

    # Get the robot geometry from robot definition attributes on the rig.
    a1 = pm.getAttr(target_ctrl_path + '.a1')
    a2 = pm.getAttr(target_ctrl_path + '.a2')
    b = pm.getAttr(target_ctrl_path + '.b')
    c1 = pm.getAttr(target_ctrl_path + '.c1')
    c2 = pm.getAttr(target_ctrl_path + '.c2')
    c3 = pm.getAttr(target_ctrl_path + '.c3')
    c4 = pm.getAttr(target_ctrl_path + '.c4')

    robot_definition = [a1, a2, b, c1, c2, c3, c4]

    # Each robot manufacturer has a pose in which all axis values are zero.
    # Determine the offset of Axis 2 between the zero pose of the
    # manufacturer and the zero pose of the IK solver (see documentation).
    a2_offset = pm.getAttr(target_ctrl_path + '.axis2Offset')

    # Most rigs don't have an A5 offset attribute. Had to add for Yaskawas
    if pm.objExists(target_ctrl_path + '.axis5Offset'):
        a5_offset = pm.getAttr(target_ctrl_path + '.axis5Offset')
    else:
        a5_offset = 0

    # Each robot manufacturer defines positive and negative axis rotation
    # differently in relation our IK solver implementation.
    # This is defined on each robot rig by the axis* attribute
    flip_a1 = pm.getAttr(target_ctrl_path + '.flipAxis1direction')
    flip_a2 = pm.getAttr(target_ctrl_path + '.flipAxis2direction')
    flip_a5 = pm.getAttr(target_ctrl_path + '.flipAxis5direction')

    # Initialized lists
    tcp_rot = [[0] * 3 for _ in range(3)]
    target_rot = [[0] * 3 for _ in range(3)]
    lcs_trans = [[0] * 1 for _ in range(3)]
    tcp_trans = [[0] * 1 for _ in range(3)]
    target_point = [[0] * 1 for _ in range(3)]
    flange_point = [[0] * 3 for _ in range(1)]
    pivot_point = [[0] * 3 for _ in range(1)]

    # Define translation vector from wrist pivot point to tool flange.
    _t = [[0], [0], [c4]]

    # =====================#
    #  Frame Definitions  #
    # =====================#

    # Tool Center Point (TCP) locater
    tcp_path = format_path(__TCP_HDL_PATH, robot)
    tcp = pm.ls(tcp_path)[0]
    # Local Base Frame controller (circle control at base of the robot).
    lcs = pm.ls(format_path(__LOCAL_CTRL_PATH, robot))[0]
    # Target Frame controller (square control at the robot's tool flange).
    target_path = format_path(__TARGET_HDL_PATH, robot)
    target = pm.ls(target_path)[0]

    # Maya uses a different coordinate system than our IK solver, so we have
    # to convert from Maya's frame to the solver's frame.

    # Solver's tool frame (X,Y,Z) = Maya's tool frame (Z, X, Y)
    # Rotation matrix from Maya tool frame to solver's tool frame.
    r_tool_frame = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    # Solver world frame (X,Y,Z) = Maya world frame (-Y, X, Z)
    # Rotation matrix from Maya's world frame to solver world frame.
    r_world_frame = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]

    # Get local translation of the TCP w.r.t. tool flange.
    tcp_trans[0][0] = tcp.getTranslation()[0]
    tcp_trans[1][0] = tcp.getTranslation()[1]
    tcp_trans[2][0] = tcp.getTranslation()[2]
    # Convert TCP translation from Maya's tool frame to solver tool frame.
    tcp_trans = general_utils.matrix_multiply_1xm_nxm(r_tool_frame, tcp_trans)

    # Get translation of local base frame (Circle controller) w.r.t robot's
    # world frame (Square controller).
    lcs_trans[0][0] = lcs.getTranslation()[0]
    lcs_trans[1][0] = lcs.getTranslation()[1]
    lcs_trans[2][0] = lcs.getTranslation()[2]
    # Convert lcs translation from Maya's world frame to solver world frame.
    lcs_trans = general_utils.matrix_multiply_1xm_nxm(r_world_frame, lcs_trans)

    # Get translation of target in Maya's world frame w.r.t robot world frame
    # (Square controller).
    target_point[0][0] = target.getTranslation()[0]
    target_point[1][0] = target.getTranslation()[1]
    target_point[2][0] = target.getTranslation()[2]
    # Convert target translation from Maya's world frame to solver world frame.
    target_point = general_utils.matrix_multiply_1xm_nxm(r_world_frame, target_point)

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
        general_utils.matrix_multiply_1xm_nxm(r_tool_frame, tcp_matrix_truncated))

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
        general_utils.matrix_multiply_1xm_nxm(r_world_frame,
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
        general_utils.matrix_multiply_1xm_nxm(r_world_frame,
                                              target_matrix_truncated))

    # Find Flange and Pivot locations in local solver world frame
    # Rotation of the tcp w.r.t to the target in solver world frame
    _re = general_utils.matrix_multiply_1xm_nxm(
        general_utils.transpose_list(target_rot), tcp_rot)

    # Rotation of the robot's local coordinate system (circle
    # controller) w.r.t the solver world frame
    _rlm = general_utils.matrix_multiply_1xm_nxm(r_world_frame, lcs_rot)

    # Find distance from the robot's local coordinate system (circle
    # controller) to target point in solver world frame
    target_point = [i - j for i, j in zip(
        general_utils.transpose_list(target_point)[0],
        general_utils.transpose_list(lcs_trans)[0])]

    # Find the flange point in the solver's world frame
    flange_point = [i - j for i, j in zip(target_point,
                                          general_utils.transpose_list(
                                              general_utils.matrix_multiply_1xm_nxm(_re, tcp_trans))[0])]

    # Find the pivot point in the solver's world frame
    pivot_point = [i - j for i, j in zip(flange_point,
                                         general_utils.transpose_list(
                                             general_utils.matrix_multiply_1xm_nxm(_re, _t))[0])]

    # Find the flange point w.r.t the robot's local frame (circle controller)
    # in solver's world frame
    flange_point = general_utils.transpose_list(
        general_utils.matrix_multiply_1xm_nxm(_rlm,
                                              [[flange_point[0]],
                                               [flange_point[1]],
                                               [flange_point[2]]]))[0]

    # Find the pivot point w.r.t the robot's local frame (circle controller)
    # in solver's world frame
    pivot_point = general_utils.transpose_list(
        general_utils.matrix_multiply_1xm_nxm(_rlm,
                                              [[pivot_point[0]],
                                               [pivot_point[1]],
                                               [pivot_point[2]]]))[0]

    # Define the Rotation of the tcp w.r.t the target in robot's local frame
    # (cirlce controller)
    _re = general_utils.matrix_multiply_1xm_nxm(_rlm, _re)

    # Find all IK solutions for the given configuration
    all_ik_sols = inverse_kinematics.solver(robot_definition, pivot_point, _re)

    # We only need to compare axes 1, 2, and 5 when switching between
    # IK and FK
    theta1_sol = all_ik_sols[0]
    theta2_sol = all_ik_sols[1]
    theta5_sol = all_ik_sols[4]

    # Account for robot manufacturer's Axis 2 offset from solver
    theta2_sol[:] = [x - a2_offset for x in theta2_sol]
    theta5_sol[:] = [x - a5_offset for x in theta5_sol]

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
    a1_path = format_path(__A1_PATH, robot)
    a2_path = format_path(__A2_PATH, robot)
    a3_path = format_path(__A3_PATH, robot)
    a4_path = format_path(__A4_PATH, robot)
    a5_path = format_path(__A5_PATH, robot)
    a6_path = format_path(__A6_PATH, robot)

    a1 = pm.getAttr(a1_path + '.rotateY')
    a2 = pm.getAttr(a2_path + '.rotateX')
    a3 = pm.getAttr(a3_path + '.rotateX')
    a4 = pm.getAttr(a4_path + '.rotateZ')
    a5 = pm.getAttr(a5_path + '.rotateX')
    a6 = pm.getAttr(a6_path + '.rotateZ')

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
    c = [zip(fk_configuration, row) for row in ik_solutions]
    d = [[] for i in range(len(ik_solutions))]
    # Find the difference between the initial configuration and each possible
    # configuration. The row with the smallest difference represents the
    # closest solution to to the initial configuration
    for i, row in enumerate(c):
        d[i] = [abs(a - b) for a, b in row]
        d[i] = sum(d[i])

    solution_index = d.index(min(d))
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
        target_ctrl_attr = get_target_ctrl_path(robot) + '.ikSolution1'
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
        target_ctrl_attr = get_target_ctrl_path(robot) + '.ikSolution2'
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
        target_ctrl_attr = get_target_ctrl_path(robot) + '.ikSolution3'
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

    try:
        for robot in robots:
            target_ctrl_attr = get_target_ctrl_path(robot) \
                             + '.invertAxis{}'.format(axis_number)
            pm.setAttr(target_ctrl_attr, 1)
            pm.refresh()
            pm.setAttr(target_ctrl_attr, 0)
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
            target_ctrl_path = get_target_ctrl_path(robot)
            tool_ctrl_path = get_tool_ctrl_path(robot)

            ik_mode = pm.getAttr(target_ctrl_path + '.ik')

            if ik_mode:
                if pm.objExists(tool_ctrl_path):
                    pm.setAttr(tool_ctrl_path + '.translate', 0, 0, 0)
                    pm.setAttr(tool_ctrl_path + '.rotate', 0, 0, 0)
                else:
                    pm.setAttr(target_ctrl_path + '.translate', 0, 0, 0)
                    pm.setAttr(target_ctrl_path + '.rotate', 0, 0, 0)
            else:
                a1_fk_ctrl_path = format_path(__A1_FK_CTRL_PATH, robot)
                a2_fk_ctrl_path = format_path(__A2_FK_CTRL_PATH, robot)
                a3_fk_ctrl_path = format_path(__A3_FK_CTRL_PATH, robot)
                a4_fk_ctrl_path = format_path(__A4_FK_CTRL_PATH, robot)
                a5_fk_ctrl_path = format_path(__A5_FK_CTRL_PATH, robot)
                a6_fk_ctrl_path = format_path(__A6_FK_CTRL_PATH, robot)

                pm.setAttr(a1_fk_ctrl_path + '.rotateY', 0)
                pm.setAttr(a2_fk_ctrl_path + '.rotateX', 0)
                pm.setAttr(a3_fk_ctrl_path + '.rotateX', 0)
                pm.setAttr(a4_fk_ctrl_path + '.rotateZ', 0)
                pm.setAttr(a5_fk_ctrl_path + '.rotateX', 0)
                pm.setAttr(a6_fk_ctrl_path + '.rotateZ', 0)
    except:
        pm.warning('Cannot zero target')


def zero_base_world(*args):
    """
    Set translation and rotation of robot base in world space
    (square controller) in channel box to zero, 0.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        for robot in robots:
            world_ctrl_path = format_path(__WORLD_CTRL_PATH, robot)
            pm.setAttr(world_ctrl_path + '.translate', 0, 0, 0)
            pm.setAttr(world_ctrl_path + '.rotate', 0, 0, 0)
    except:
        pm.warning('Cannot zero base (world)')


def zero_base_local(*args):
    """
    Set translation and rotation of robot base in local space
    (circular controller) in channel box to zero, 0.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    try:
        for robot in robots:
            local_ctrl_path = get_local_ctrl_path(robot)
            pm.setAttr(local_ctrl_path + '.translate', 0, 0, 0)
            pm.setAttr(local_ctrl_path + '.rotate', 0, 0, 0)
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
        target_ctrl_path = get_target_ctrl_path(robot)

        if round_val:
            axis_val.append(round(pm.getAttr(target_ctrl_path
                                + '.axis{}'.format(axis_number))))
        else:
            axis_val.append(pm.getAttr(target_ctrl_path
                                     + '.axis{}'.format(axis_number)))
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
            limit_meter_ctrl_path = format_path('{0}|{1}robot_GRP|{1}limitMeter_CTRL', robot)
            limit_meter_grp_path = format_path('{0}|{1}robot_GRP|{1}limitMeter_GRP', robot)
            pm.setAttr(limit_meter_ctrl_path + '.v', 0)
            pm.setAttr(limit_meter_grp_path + '.v', 0)
        return
    else:  # If not, create it
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
            limit_meter_ctrl_path = format_path('{0}|{1}robot_GRP|{1}limitMeter_CTRL', robot)
            limit_meter_grp_path = format_path('{0}|{1}robot_GRP|{1}limitMeter_GRP', robot)
            pm.setAttr(limit_meter_ctrl_path + '.v', 1)
            pm.setAttr(limit_meter_grp_path + '.v', 1)


def close_hud():
    """
    Close the heads-up-display (HUD) in Maya; runs in a script node
    that executes when the Maya scene is closed.
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
        return
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
    if pm.objExists(get_tool_ctrl_path(robot[0])):
        pm.warning('Robot already has an assigned tool controller')
        return

    robot = robot[0] 

    ns = robot.namespace()
    robot_grp_path = format_path(__ROBOT_GRP_PATH, robot)

    # find which selected object is the tool controller
    if not get_robot_roots(0, [sel[0]]):
        tool_ctrl = sel[0]
    else:
        tool_ctrl = sel[1]
        
    target_ctrl_path = get_target_ctrl_path(robot)
    tool_ctrl_path = get_tool_ctrl_path(robot)
    tool_ctrl_fk_path = get_tool_ctrl_fk_path(robot)

    try:
        pm.parent(tool_ctrl, robot_grp_path, absolute=True)
        pm.rename(robot_grp_path + '|' + tool_ctrl, '{}tool_CTRL'.format(ns))
      
        pm.parentConstraint(tool_ctrl_path,
                            target_ctrl_path,
                            name='targetToToolCtrl_pCnst',
                            maintainOffset=True)

        # Duplicate and add to FK parent chain
        tool_ctrl_dup = pm.duplicate(tool_ctrl_path)
        pm.rename(tool_ctrl_dup, '{}tool_CTRL_FK'.format(ns))
        pm.parent('{0}|{1}robot_GRP|{1}tool_CTRL_FK'.format(robot, ns),
                  format_path(__TCP_HDL_PATH, robot),
                  absolute=True)
        pm.setAttr(tool_ctrl_fk_path + '.v', 0)

        # Lock rotation/translation of IK/FK CTRL (only works if prefs | file
        # references | edits on references is checked)

        try:
            
            pm.setAttr(target_ctrl_path + '.translate', lock=True)
            pm.setAttr(target_ctrl_path + '.rotate', lock=True)

            pm.setAttr(tool_ctrl_fk_path + '.translate', lock=True)
            pm.setAttr(tool_ctrl_fk_path + '.rotate', lock=True)

        except:
            pass

        pm.select(tool_ctrl_path)
        pm.headsUpMessage('Tool Controller attatched successfuly!')
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

    robot = robot[0]

    # find which selected object is the tool model
    tools = []
    for each in sel:
        if not get_robot_roots(0, [each]):
            tools.append(each)
        else:
            pass

    ns = robot.namespace()
    tcp_hdl_path = format_path(__TCP_HDL_PATH, robot)
    tool_mdl_path = format_path(__TOOL_MDL_PATH, robot)
    tool_ctrl_path = get_tool_ctrl_path(robot)

    for tool_model in tools:
        try:
            pm.parent(tool_model, tcp_hdl_path, absolute=True)

            try:
                pm.rename(tcp_hdl_path + '|{}'.format(tool_model),
                          '{}tool_MDL'.format(ns))
            except:
                pass

            # Lock rotation/translation of Tool Model
            pm.setAttr(tool_mdl_path + '*.translate', lock=True)
            pm.setAttr(tool_mdl_path + '*.rotate', lock=True)

            if pm.objExists(tool_ctrl_path):
                pm.select(tool_ctrl_path)
            else:
                pm.select(get_target_ctrl_path(robot))
            pm.headsUpMessage('Tool Model attached successfuly!')

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
                target_ctrl_path = get_target_ctrl_path(robot)
                tool_ctrl_fk_path = get_tool_ctrl_fk_path(robot)

                pm.delete(target_ctrl_path + '|targetToToolCtrl_pCnst')
                pm.delete(tool_ctrl_fk_path)

                try: 
                    pm.setAttr(target_ctrl_path + '.translate', lock=False)
                    pm.setAttr(target_ctrl_path + '.rotate', lock=False)
                except:
                    pm.warning('Mimic: target_CTRL.translate is from a referenced file, and cannot be unlocked.')

                pm.parent(sel, world=True, absolute=True)
                tools = 1  # Our selection is a tool controller
                pm.headsUpMessage('Tool Controller detached successfuly!')

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
                pm.headsUpMessage('Tool Model detached successfuly!')

    # If there were no tools in our selection, alert the user
    if not tools:
        pm.warning('No tool models selected')
        return


def write_limits_to_ui(*args):
    """
    """
    current_tab = pm.tabLayout('limits_tab_layout',
                               query=True,
                               selectTab=True)

    if current_tab == 'position_limits_tab':
        write_position_limits_to_ui()
    elif current_tab == 'velocity_limits_tab':
        write_deriv_limits_to_ui('Velocity')
    elif current_tab == 'accel_limits_tab':
        write_deriv_limits_to_ui('Accel')
    elif current_tab == 'jerk_limits_tab':
        write_deriv_limits_to_ui('Jerk')
    else:
        raise MimicError('Derivative type limits not supported')


def write_position_limits_to_ui():
    """
    """
    axis_position_limits = get_axis_limits()

    # TODO: HARD CODED - Number of robot axes; should include external axes
    num_axes = 6
    for i in range(num_axes):
        axis_number = i + 1 
        axis_name = 'Axis {}'.format(axis_number)

        val_min = axis_position_limits[axis_name]['Min Limit']
        val_max = axis_position_limits[axis_name]['Max Limit']

        pm.textField('t_A{}Min'.format(axis_number), edit=True, text=val_min)
        pm.textField('t_A{}Max'.format(axis_number), edit=True, text=val_max)


def write_deriv_limits_to_ui(limit_type):
    """
    """
    robots = get_robot_roots()
    if not robots:
        raise MimicError('Nothing Selected; Select a valid robot')
        return

    if len(robots) > 1:
        MimicError('Too many selections: Select a single robot')
        return

    robot = robots[0]

    axis_deriv_limits = _get_limits(robot, limit_type)

   # TODO: HARD CODED - Number of robot axes; should include external axes
    num_axes = 6
    for i in range(num_axes):
        axis_number = i + 1 
        axis_name = 'Axis {}'.format(axis_number)

        val = axis_deriv_limits[axis_name]['Max Limit']

        pm.textField('t_A{}{}'.format(axis_number, limit_type),
                     edit=True,
                     text=round(val,3))


def get_axis_limits():
    """
    Gets the current axis position limits and updates UI with those values.
    :param args:
    :return axis_position_limits: dict containing axis position limits
    """
    robots = get_robot_roots()
    if not robots:
        raise MimicError('Nothing Selected; Select a valid robot')
        return

    if len(robots) > 1:
        MimicError('Too many selections: Select a single robot')
        return

    robot = robots[0]
    target_ctrl_path = get_target_ctrl_path(robot)

    axis_position_limits = {}

    # TODO: HARD CODED - Number of robot axes; should include external axes
    num_axes = 6

    for i in range(num_axes):
        axis_number = i + 1  # Axis numbers are 1-indexed
        axis_name = 'Axis {}'.format(axis_number)
        val_min = int(pm.getAttr(target_ctrl_path + '.axis{}Min'.format(axis_number)))
        val_max = int(pm.getAttr(target_ctrl_path + '.axis{}Max'.format(axis_number)))

        # Save value to dictionary
        axis_position_limits[axis_name] = {'Min Limit': val_min,
                                           'Max Limit': val_max}
    
    # TO-DO: Add external axes
    return axis_position_limits


def set_axis_limits(*args):
    """
    Gets user-input value from UI and sets all axis limits at once
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        raise MimicError('Nothing Selected; Select a valid robot')
        return

    current_tab = pm.tabLayout('limits_tab_layout',
                               query=True,
                               selectTab=True)

    if current_tab == 'position_limits_tab':
        set_position_limits()
    elif current_tab == 'velocity_limits_tab':
        set_deriv_limits('Velocity')
    elif current_tab == 'accel_limits_tab':
        set_deriv_limits('Accel')
    elif current_tab == 'jerk_limits_tab':
        set_deriv_limits('Jerk')


def set_position_limits():
    """
    """        
    # number of robot axes; could include external axes potentially
    num_axes = 6
    try:
        for i in range(num_axes):
            axis_number = i + 1  # Axis numbers are 1-indexed
            set_axis_limit(axis_number, 'Min')
            set_axis_limit(axis_number, 'Max')
    except:
        pass
    

def set_axis_limit(axis_number, min_max):
    """
    Gets user-input value from UI and sets corresponding axis limits
    on the robot
    :param axis_number: Index of axis to effect (1 indexed)
    :param min_max: string, either 'Min' or 'Max'
    :return:
    """
    robots = get_robot_roots()

    if not robots:
        raise MimicError('Nothing Selected; Select a valid robot')
        return

    try:
        val = float(pm.textField('t_A{}{}'.format(axis_number, min_max),
                                 query=True,
                                 text=True))
        robot_list_str = ''
        for robot in robots:
            pm.setAttr(get_target_ctrl_path(robot)
                     + '.axis{}{}'.format(axis_number, min_max),
                       val)
            robot_list_str += robot + ' '
    except:
        pass

    pm.headsUpMessage('Axis Position Limits for {} set successfuly!'.format(robot_list_str))


def set_deriv_limits(limit_type):
    # number of robot axes; could include external axes potentially
    num_axes = 6
    try:
        for i in range(num_axes):
            axis_number = i + 1  # Axis numbers are 1-indexed
            set_deriv_limit(axis_number, limit_type)
    except:
        pass

    pm.headsUpMessage('Axis {} Limits set successfuly!'.format(limit_type))


def set_deriv_limit(axis_number, limit_type):
    """
    Gets user-input value from UI and sets corresponding axis limits
    on the robot
    :param axis_number: Index of axis to effect (1 indexed)
    :param min_max: string, limit type; ex. 'Velocity'
    :return:
    """
    robots = get_robot_roots()

    if not robots:
        raise MimicError('Nothing Selected; Select a valid robot')
        return

    try:  # If there is not a float input in the UI box, do nothing
        val = float(pm.textField('t_A{}{}'.format(axis_number, limit_type),
                                 query=True,
                                 text=True))
        robot_list_str = ''
        for robot in robots:
            target_ctrl_path = get_target_ctrl_path(robot)

            # Check if the rig has attributes for the input limit type
            # If not, add the corresponding limit attributes
            # This is mostly used for backwards-compatibility
            if not pm.attributeQuery('axis{}Limits'.format(limit_type),
                                     n=target_ctrl_path, ex=True):
                add_limits_to_robot(robot, limit_type)

            # Set the axis' limit to the user-input value
            pm.setAttr(target_ctrl_path + '.axis{}{}Limit'.format(axis_number, limit_type), val)

            robot_list_str += robot + ' '
    except:
        pass


def get_velocity_limits(robot):
    """
    Gets the current velocity limits and updates UI with those values.
    :param robot: name string of the selected robot
    :return:
    """
    return _get_limits(robot, "Velocity")


def get_acceleration_limits(robot):
    """
    Gets the current acceleration limits and updates UI with those values.
    :param robot: name string of the selected robot
    :return:
    """
    return _get_limits(robot, "Accel")


def get_jerk_limits(robot):
    """
    Gets the current jerk limits and updates UI with those values.
    :param robot: name string of the selected robot
    :return:
    """
    return _get_limits(robot, "Jerk")


def _get_limits(robot, limit_type):
    """
    Gets the current velocity limits and updates UI with those values.
    :param robot: name string of the selected robot
    :param limit_type: name string of the limit type
                       'Velocity', 'Accel', or 'Jerk'
    :return:
    """
    target_ctrl_path = get_target_ctrl_path(robot)

    limits = {}

    # Check if the rig has attributes for the input limit type
    # If not, add the corresponding limit attributes
    # This is mostly used for backwards-compatibility

    if not pm.attributeQuery('axis{}Limits'.format(limit_type),
                             n=target_ctrl_path, ex=True):
        add_limits_to_robot(robot, limit_type)

    # HARD CODED - Number of robot axes; should include external axes
    num_axes = 6

    # Create a list of robot's limits
    for i in range(num_axes):
        axis_number = i + 1  # Axis numbers are 1-indexed
        axis_name = 'Axis {}'.format(axis_number)
        limits[axis_name] = {'Min Limit': None, 'Max Limit': None}

        try:
            limit = pm.getAttr(target_ctrl_path + '.axis{}' \
                               '{}Limit'.format(axis_number, limit_type))
        except AttributeError:
            limit = None

        if limit:
            limits[axis_name] = {'Min Limit': -limit,
                                 'Max Limit': limit}
    
    # TO-DO: Add external axes
    return limits


def get_all_limits(robot):
    """
    Gets all axis limits for the selected robot and places them in a dictionary
    limits_data = {
        "Position": {
                   "Axis 1":{"Min Limit": limit, "Max Limit": limit},
                   "Axis 2":{"Min Limit": limit, "Max Limit": limit},
                ...
                   "Axis n":{"Min Limit": limit, "Max Limit": limit}
                   },
            
        "Velocity": {
                   "Axis 1":{"Min Limit": limit, "Max Limit": limit},
                   "Axis 2":{"Min Limit": limit, "Max Limit": limit},
                ...
                   "Axis n":{"Min Limit": limit, "Max Limit": limit}
                   },

        "Accel": {
                   "Axis 1":{"Min Limit": limit, "Max Limit": limit},
                   "Axis 2":{"Min Limit": limit, "Max Limit": limit},
                ...
                   "Axis n":{"Min Limit": limit, "Max Limit": limit}
                   },

        "Jerk": {
                   "Axis 1":{"Min Limit": limit, "Max Limit": limit},
                   "Axis 2":{"Min Limit": limit, "Max Limit": limit},
                ...
                   "Axis n":{"Min Limit": limit, "Max Limit": limit}
                   }
        }
    :param robot: name string of the selected robot
    :return limits_data: dict containing all limit data
    """
    limits_data = {}

    limits_data['Position'] = get_axis_limits()
    limits_data['Velocity'] = get_velocity_limits(robot)
    limits_data['Accel'] = get_acceleration_limits(robot)
    limits_data['Jerk'] = get_jerk_limits(robot)

    return limits_data


def get_fk_pose(*args):
    """
    Get the Forward Kinematic pose for a selected robot in the Maya scene.
    :param args:
    :return:
    """
    robots = get_robot_roots()
    if not robots:
        pm.warning('Nothing Selected; Select a valid robot')
        return

    if len(robots) > 1:
        pm.warning('Too many selections; Select a single robot')
        return

    robot = robots[0]
    axes = find_fk_config(robot)

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
        ns = robot.namespace()
        fk_ctrl_path = '{0}|{1}robot_GRP|{1}FK_CTRLS|{1}a{2}FK_CTRL'.format(robot, ns, axis_number)
        selection.append(fk_ctrl_path)

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
            ns = robot.namespace()
            pm.setAttr('{0}|{1}robot_GRP|{1}FK_CTRLS|{1}a{2}FK_CTRL.rotate{3}'.format(robot, ns, axis_number, rotation_axis), val)
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


def _snap_ik_target_to_fk(robot):
    """
    Snaps the IK control handle to the end of the FK heirarchy
    Used for IK/FK switching and keyframing.
    :param robot: name string of the selected robot
    :return:
    """

    # Snap IK Ctrl to FK location
    # If robot has tool controller, use that
    target_ctrl_path = get_target_ctrl_path(robot)
    tool_ctrl_path = get_tool_ctrl_path(robot)
    tool_ctrl_fk_path = get_tool_ctrl_fk_path(robot)
    tcp_hdl_path = format_path(__TCP_HDL_PATH, robot)

    if pm.objExists(tool_ctrl_path):
        ctrl_ik = tool_ctrl_path
        ctrl_fk = tool_ctrl_fk_path

    # If robot doesn't have a tool controller, use target_CTRL.
    else:
        ctrl_ik = target_ctrl_path
        ctrl_fk = tcp_hdl_path

    # Snap tool_CTRL to tool_CTRL_FK.
    try:
        pm.snapTransforms(s=ctrl_fk, d=ctrl_ik)
    except:
        pm.warning('Coundn\'t snap {} tool_CTRL handle to FK' \
                   .format(robot))


def _ik_and_fk_aligned(ik_ctrl, tcp_handle):
    """
    Checks if the IK controller is already aligned to the FK hierarchy
    :param ik_ctrl: string, object representing the ik controller
    :param tcp_handle: string, object representing the tcp location on the fk
    hierarchy
    :return ik_fk_are_aligned: bool, True if the ik_ctrl and tcp_handle are
    aligned, False if they are not
    """

    # Define some small number to threshold our output
    delta = .0001

    # Initialize variables
    # translation_is_aligned = False
    # rotation_is_aligned = False
    ik_fk_are_aligned = False

    # Find the translation of each object and compare them
    ik_trans = pm.xform(ik_ctrl, q=True, rp=True, ws=True)
    tcp_trans = pm.xform(tcp_handle, q=True, rp=True, ws=True)

    # Find the distance between the ik controller and the tcp handle
    trans_diff = math.sqrt((ik_trans[0] - tcp_trans[0]) ** 2
                           + (ik_trans[1] - tcp_trans[1]) ** 2
                           + (ik_trans[2] - tcp_trans[2]) ** 2)

    if round(trans_diff, 6) < delta:
        ik_fk_are_aligned = True

    return ik_fk_are_aligned


def switch_to_ik(robot):
    """
    Switches all robots in scene to IK mode
    :param robot: name string of the selected robot
    :return:
    """

    target_ctrl_path = get_target_ctrl_path(robot)
    tool_ctrl_path = get_tool_ctrl_path(robot)
    fk_ctrls_path = format_path(__FK_CTRLS_PATH, robot)

    try:
        # Turn FK control visibility off
        pm.setAttr(fk_ctrls_path + '.v', 0)

        # Turn IK control visibility on
        pm.setAttr(target_ctrl_path + '.v', 1)
        pm.setAttr(format_path(__TARGET_CTRL_PATH + '|{1}target_CTRLShape',
                               robot) + '.visibility', 1)

        if pm.objExists(tool_ctrl_path):
            pm.setAttr(tool_ctrl_path + '.v'.format(robot), 1)

        # Snap IK Ctrl to FK location
        _snap_ik_target_to_fk(robot)

        # Find closest IK configuration to current FK pose
        ik_sols = find_ik_solutions(robot)
        fk_config = find_fk_config(robot)

        # Only use a1, a2, and a5 to determing closest config.
        fk_config_trunc = [fk_config[i] for i in [0, 1, 4]]
        ik_config = find_closest_config(fk_config_trunc, ik_sols)

        # Match IK config to FK pose
        pm.setAttr(target_ctrl_path + '.ikSolution1', ik_config[0])
        pm.setAttr(target_ctrl_path + '.ikSolution2', ik_config[1])
        pm.setAttr(target_ctrl_path + '.ikSolution3', ik_config[2])

        # turn ik solve back on
        pm.setAttr(target_ctrl_path + '.ik', 1)

    except:
        pm.warning('Error swithching to IK')


def switch_to_fk(robot):
    """
    Switches all robots in the scene to IK mode.
    :param robot: name string of the selected robot
    :return:
    """
    target_ctrl_path = get_target_ctrl_path(robot)
    tool_ctrl_path = get_tool_ctrl_path(robot)
    fk_ctrls_path = format_path(__FK_CTRLS_PATH, robot)

    try:
        # Turn IK control visibility off
        pm.setAttr(get_target_ctrl_path(robot) + '.v', 0)

        if pm.objExists(tool_ctrl_path):
            pm.setAttr(tool_ctrl_path + '.v'.format(robot), 0)

            # Turn FK control visibility on
        pm.setAttr(fk_ctrls_path + '.v'.format(robot), 1)

        # Find axis angles from IK pose, and match FK control handles
        fk_config = find_fk_config(robot)

        pm.setAttr(format_path(__A1_FK_CTRL_PATH, robot) + '.rotateY',
                   fk_config[0])
        pm.setAttr(format_path(__A2_FK_CTRL_PATH, robot) + '.rotateX',
                   fk_config[1])
        pm.setAttr(format_path(__A3_FK_CTRL_PATH, robot) + '.rotateX',
                   fk_config[2])
        pm.setAttr(format_path(__A4_FK_CTRL_PATH, robot) + '.rotateZ',
                   fk_config[3])
        pm.setAttr(format_path(__A5_FK_CTRL_PATH, robot) + '.rotateX',
                   fk_config[4])
        pm.setAttr(format_path(__A6_FK_CTRL_PATH, robot) + '.rotateZ',
                   fk_config[5])

        pm.setAttr(target_ctrl_path + '.ik', 0)

    except:
        pm.warning('Error switching to FK')


def toggle_ik_fk(*args):
    """
    Toggles all robots in scene between IK and FK modes
    :param args:
    :return:
    """

    current_tab = pm.tabLayout('switcher_tab_layout',
                               query=True,
                               selectTab=True)

    if current_tab == 'ikTab':
        ik_tab = 1
    else:
        ik_tab = 0

    robots = get_robot_roots(1)
    if not robots:
        return

    for robot in robots:
        target_ctrl_path = get_target_ctrl_path(robot)
        try:
            if ik_tab:
                if pm.getAttr(target_ctrl_path + '.ik'):
                    continue

                switch_to_ik(robot)

            else:
                if not pm.getAttr(target_ctrl_path  + '.ik'):
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
                    target_ctrl_path = get_target_ctrl_path(robot)
                    tool_ctrl_path = get_tool_ctrl_path(robot)

                    if pm.objExists(tool_ctrl_path):
                        selection.append(tool_ctrl_path)
                    else:
                        selection.append(target_ctrl_path)
            else:
                for robot in active_robots:
                    selection.append(format_path(__A6_FK_CTRL_PATH, robot))
                    
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
        target_ctrl_path = get_target_ctrl_path(robot)
        tool_ctrl_path = get_tool_ctrl_path(robot)
        fk_ctrls_path = format_path(__FK_CTRLS_PATH, robot)

        if not pm.getAttr(target_ctrl_path + '.ik'):
            switch_to_ik(robot)

        ik_attributes = ['ik',
                         'v',
                         'ikSolution1',
                         'ikSolution2',
                         'ikSolution3']

        # Key all IK elements
        for attr in ik_attributes:
            pm.setKeyframe(target_ctrl_path, attribute=attr)

        if pm.objExists(tool_ctrl_path):
            pm.setKeyframe(tool_ctrl_path, attribute='v')

        fk_pose = find_fk_config(robot)

        # Key all FK elements
        pm.setKeyframe(format_path(__A1_FK_CTRL_PATH, robot),
                       attribute='rotateY',
                       value=fk_pose[0])
        pm.setKeyframe(format_path(__A2_FK_CTRL_PATH, robot),
                       attribute='rotateX',
                       value=fk_pose[1])
        pm.setKeyframe(format_path(__A3_FK_CTRL_PATH, robot),
                       attribute='rotateX',
                       value=fk_pose[2])
        pm.setKeyframe(format_path(__A4_FK_CTRL_PATH, robot),
                       attribute='rotateZ',
                       value=fk_pose[3])
        pm.setKeyframe(format_path(__A5_FK_CTRL_PATH, robot),
                       attribute='rotateX',
                       value=fk_pose[4])
        pm.setKeyframe(format_path(__A6_FK_CTRL_PATH, robot),
                       attribute='rotateZ',
                       value=fk_pose[5])

        # Key visibility of FK controllers
        pm.setKeyframe(fk_ctrls_path, attribute='visibility')

        # Key tool controllers
        if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
            if pm.objExists(tool_ctrl_path):
                pm.setKeyframe(tool_ctrl_path, attribute='translate')
                pm.setKeyframe(tool_ctrl_path, attribute='rotate')
            else:
                pm.setKeyframe(target_ctrl_path, attribute='translate')
                pm.setKeyframe(target_ctrl_path, attribute='rotate')


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
        target_ctrl_path = get_target_ctrl_path(robot)
        tool_ctrl_path = get_tool_ctrl_path(robot)

        if pm.getAttr(target_ctrl_path + '.ik'):
            switch_to_fk(robot)

        # We first check if the target/tool controller transformation and
        # orientation is already aligned with the FK chain. If so, it
        # indicates that we're performing an IK to FK switch, and we
        # keyframe its position and orientation directly, without
        # snapping the IK control to the FK hierarchy. This is to avoid
        # unneccessarily changing the controllers Euler Angle rotation
        # representation that can cause unpredictable behavior between frames

        if pm.objExists(tool_ctrl_path):
            ctrl_ik = tool_ctrl_path
            ctrl_fk = format_path(__TOOL_CTRL_FK_PATH, robot)

        # If robot doesn't have a tool controller, use target_CTRL.
        else:
            ctrl_ik = target_ctrl_path
            ctrl_fk = format_path(__TCP_HDL_PATH, robot)

        if not _ik_and_fk_aligned(ctrl_ik, ctrl_fk):
            _snap_ik_target_to_fk(robot)

        # Key all FK elements
        try:
            pm.setKeyframe(format_path(__A1_FK_CTRL_PATH, robot),
                           attribute='rotateY')
            pm.setKeyframe(format_path(__A2_FK_CTRL_PATH, robot),
                           attribute='rotateX')
            pm.setKeyframe(format_path(__A3_FK_CTRL_PATH, robot),
                           attribute='rotateX')
            pm.setKeyframe(format_path(__A4_FK_CTRL_PATH, robot),
                           attribute='rotateZ')
            pm.setKeyframe(format_path(__A5_FK_CTRL_PATH, robot),
                           attribute='rotateX')
            pm.setKeyframe(format_path(__A6_FK_CTRL_PATH, robot),
                           attribute='rotateZ')

            # Key visibility of FK controllers
            for i in range(6):
                pm.setKeyframe(format_path(__FK_CTRLS_PATH, robot),
                               attribute='visibility')
        except:
            pm.warning('Error setting FK keys in FK mode')

        # Key all IK elements
        try:
            pm.setKeyframe(target_ctrl_path, attribute='ik')
            pm.setKeyframe(target_ctrl_path, attribute='v', value=0)

            if pm.objExists(tool_ctrl_path):
                pm.setKeyframe(tool_ctrl_path, attribute='v')

            # Key tool controllers
            if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
                if pm.objExists(tool_ctrl_path):
                    pm.setKeyframe(tool_ctrl_path, attribute='translate')
                    pm.setKeyframe(tool_ctrl_path, attribute='rotate')
                else:
                    pm.setKeyframe(target_ctrl_path, attribute='translate')
                    pm.setKeyframe(target_ctrl_path, attribute='rotate')

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

    object_list = [__TARGET_CTRL_PATH,
                   __FK_CTRLS_PATH,
                   __A1_FK_CTRL_PATH,
                   __A2_FK_CTRL_PATH,
                   __A3_FK_CTRL_PATH,
                   __A4_FK_CTRL_PATH,
                   __A5_FK_CTRL_PATH,
                   __A6_FK_CTRL_PATH]

    keyable_robot_objects = []
    robots = get_robot_roots()

    for robot in robots:
        for obj in object_list:
            obj_path = format_path(obj, robot)
            keyable_robot_objects.append(obj_path)

        tool_ctrl_path = get_tool_ctrl_path(robot)
        if pm.objExists(tool_ctrl_path):
            keyable_robot_objects.append(tool_ctrl_path)

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

    keyed_attrs = {__TARGET_CTRL_PATH: ['ik',
                                        'visibility',
                                        'ikSolution1',
                                        'ikSolution2',
                                        'ikSolution3'],
                   __FK_CTRLS_PATH: ['visibility'],
                   __A1_FK_CTRL_PATH: ['rotateY'],
                   __A2_FK_CTRL_PATH: ['rotateX'],
                   __A3_FK_CTRL_PATH: ['rotateX'],
                   __A4_FK_CTRL_PATH: ['rotateZ'],
                   __A5_FK_CTRL_PATH: ['rotateX'],
                   __A6_FK_CTRL_PATH: ['rotateZ']}

    robots = get_robot_roots()

    current_frame = pm.currentTime()
    for robot in robots:
        target_ctrl_path = get_target_ctrl_path(robot)
        tool_ctrl_path = get_tool_ctrl_path(robot)
        # Check if there's a keyframe set on the target_CTRL.ik attribute
        key = pm.keyframe(target_ctrl_path,
                          attribute='ik',
                          query=True,
                          time=current_frame)

        # If there is no keyframe set on the IK attribute, continue to the
        # next robot
        if not key:
            pm.warning('{} has no IK|FK keyframe at frame {}' \
                       .format(robot, current_frame))
            continue

        # If there is a keyframe on the IK attribute, we also check if there's
        # a keyframe on an FK controller as well, as we only consider there to
        # be a proper IK or FK keyframe if both are true
        # Note, we only need to check a single FK controller as they should all
        # be keyframed (or not) together
        fk_test_handle_path = format_path(__A1_FK_CTRL_PATH + '.rotateY', robot)
        fk_key = pm.keyframe(fk_test_handle_path,
                             query=True,
                             time=current_frame)
        # If there is no keyframe set on the FK controller attribute,
        # continue to the next robot
        if not fk_key:
            pm.warning('{} has no IK|FK keyframe at frame {}' \
                       .format(robot, current_frame))
            continue        

        for obj in keyed_attrs:
            for attr in keyed_attrs[obj]:
                pm.cutKey(format_path(obj, robot),
                          time=current_frame,
                          attribute=attr,
                          option="keys")

        if pm.objExists(tool_ctrl_path):
            pm.cutKey(tool_ctrl_path,
                      time=current_frame,
                      attribute='visibility',
                      option="keys")

        if pm.checkBox('cb_keyToolCtrl', query=True, value=True):
            if pm.objExists(tool_ctrl_path):
                pm.cutKey(tool_ctrl_path,
                          time=current_frame,
                          attribute='translate',
                          option="keys")
                pm.cutKey(tool_ctrl_path,
                          time=current_frame,
                          attribute='rotate',
                          option="keys")
            else:
                pm.cutKey(target_ctrl_path,
                          time=current_frame,
                          attribute='translate',
                          option="keys")
                pm.cutKey(target_ctrl_path,
                          time=current_frame,
                          attribute='rotate',
                          option="keys")


def toggle_ik_fk_ui(*args):
    """
    Toggle control mode of Inverse Kinematics or Forward Kinematics
    in the Mimic UI.
    :param args:
    :return:
    """
    if not pm.window("mimic_win", exists=True):
        return

    current_tab = pm.tabLayout('switcher_tab_layout',
                               query=True,
                               selectTabIndex=True)

    if current_tab == 1:
        pm.tabLayout('switcher_tab_layout', edit=True, selectTabIndex=2)
    elif current_tab == 2:
        pm.tabLayout('switcher_tab_layout', edit=True, selectTabIndex=1)
    else:
        pm.warning('Error toggling IK/FK tabs')


def get_ui_ik_fk_state(*args):
    """
    Get the control mode of Inverse Kinematics or Forward Kinematics
    in the Mimic UI.
    :param args:
    :return: either None, 'ik' or 'fk'
    """
    if not pm.window("mimic_win", exists=True):
        return None

    current_tab = pm.tabLayout('switcher_tab_layout',
                               query=True,
                               selectTabIndex=True)

    if current_tab == 1:
        return 'ik'
    elif current_tab == 2:
        return 'fk'
    else:
        pm.warning('Error getting IK/FK tabs status')
        return None


def key_ik_fk(*args):
    """
    Key the Inverse Kinematic or Forward Kinematic pose of a robot in the Maya
    scene, depending on control mode selected in the Mimic UI.
    :param args:
    :return:
    """
    if not pm.window("mimic_win", exists=True):
        return

    current_tab = pm.tabLayout('switcher_tab_layout',
                               query=True,
                               selectTabIndex=True)

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
    :param command_name: Name of the Mimic command for hotkey
                        (acquired from Mimic)
    :param annotation_str: Comment or description of hotkey
    :param command_string: String-form of the actual command to execute
    :return:
    """
    key_str = None
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
        pm.setAttr(get_target_ctrl_path(robot) + '.shaderRange', shader_range)


def import_robot(rigs_dir):
    """
    Imports selected robot from Mimic UI dropdown menu into the scene
    :return:
    """

    # If the scene is in IK mode, switch to FK before importing the robot
    current_tab = pm.tabLayout('switcher_tab_layout',
                               query=True,
                               selectTabIndex=True)
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

    start_line_code = "["
    end_line_code = "],\n"

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

        target_ctrl_path = get_target_ctrl_path(robot)
        tool_ctrl_path = get_tool_ctrl_path(robot)
        target_ctrl_str = __TARGET_CTRL_PATH

        config_attrs = ['ik', 'v', 'ikSolution1', 'ikSolution2', 'ikSolution3']
        for each in config_attrs:
            find_val = pm.getAttr(target_ctrl_path + "." + each)
            save_to_shelf = (start_line_code
                             + "'"
                             + (target_ctrl_str + "." + each)
                             + "', " + " %f" + end_line_code) % find_val

            store_cmds += save_to_shelf

        # If a tool controller exists, use that to keyframe transformation
        # attributes
        if pm.objExists(tool_ctrl_path):
            target_ctrl = tool_ctrl_path
            target_ctrl_str = __TOOL_CTRL_PATH
        else:
            target_ctrl = target_ctrl_path
            target_ctrl_str = __TARGET_CTRL_PATH

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

        for each in keyable:
            find_val = pm.getAttr(target_ctrl + "." + each)
            save_to_shelf = (start_line_code + "'" + (
                target_ctrl_str + "." + each) + "', " + " {}".format(find_val) + end_line_code)
            store_cmds += save_to_shelf

    # FK MODE
    else:

        store_cmds += 'tab = 2 \n'
        store_cmds += 'attrs = ['

        target_ctrl_path = get_target_ctrl_path(robot)
        target_ctrl_str = __TARGET_CTRL_PATH

        config_attrs = ['ik', 'v']
        for each in config_attrs:
            find_val = pm.getAttr(target_ctrl_path + "." + each)
            save_to_shelf = (start_line_code + "'" + (
                target_ctrl_str + "." + each) + "', " + " %f" + end_line_code) % find_val
            store_cmds += save_to_shelf

        joint_vals = [__A1_FK_CTRL_PATH,
                      __A2_FK_CTRL_PATH,
                      __A3_FK_CTRL_PATH,
                      __A4_FK_CTRL_PATH,
                      __A5_FK_CTRL_PATH,
                      __A6_FK_CTRL_PATH]
        joint_val_attr = ['rotateY', 'rotateX', 'rotateX', 'rotateZ', 'rotateX', 'rotateZ']

        for i, each in enumerate(joint_vals):
            attrs = format_path(each + "." + joint_val_attr[i], robot)
            attr_str = each + "." + joint_val_attr[i]
            find_val = pm.getAttr(attrs)
            save_to_shelf = (start_line_code + "'" + attr_str + "', " + " %f" + end_line_code) % find_val
            store_cmds += save_to_shelf

    store_cmds += '] \n\n' \
                  'mimic_utils.assign_saved_pose(attrs, tab) \n'

    prompt_dialog = pm.promptDialog(t="Robot Pose", m="Pose Name:", b="Save")

    # Condition statement that checks if our button gets clicked.
    # If this condition is met, then run the following commands
    if prompt_dialog == "Save":
        # This variable stores the Name we add to our Prompt Dialog
        prompt_dialog_name = pm.promptDialog(query=True, text=True)
        # This line creates our Shelf Button that uses MEL as the source type
        # for the commands stored in "store_cmds", and adds the Shelf Button
        # under our custom tab named "Body Poses"
        pm.shelfButton(l=prompt_dialog_name,
                       annotation=prompt_dialog_name,
                       imageOverlayLabel=prompt_dialog_name,
                       i='commandButton.png',
                       command=store_cmds,
                       p=target_shelf,
                       sourceType="python")


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
        pm.setAttr(format_path(attr[0], robot), attr[1])
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


def add_limits_to_robot(robot, limit_type):
    """
    Adds attributes for input limit_type to robot
    """
    target_ctrl_path = get_target_ctrl_path(robot)

    print limit_type
    # Get nominal limits from mimic config file
    nominal_limit = mimic_config.NOMINAL_LIMIT[limit_type]

    # Define Parent Attribute
    parent_attr_path = 'axis{}Limits'.format(limit_type)
    pm.addAttr(target_ctrl_path,
               longName=parent_attr_path,
               nc=6,
               at='compound')

    # Add an attribute for each axis
    num_axes = 6
    for i in range(num_axes):
        axis_number = i + 1
        pm.addAttr(target_ctrl_path,
                   longName='axis{}{}Limit'.format(axis_number, limit_type),
                   at='float',
                   nn='Axis {}'.format(axis_number),
                   defaultValue=nominal_limit,
                   parent=parent_attr_path)


class MimicError(Exception):
    pass
