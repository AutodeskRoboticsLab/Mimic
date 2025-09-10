#!usr/bin/env python
"""

"""
try:
    import pymel.core as pm
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False


def get_robot_geometry():
    """
    Gets the robot geometry from rigging UI
    :return robot_geometry: dictionary
    """
    robot_geometry = {}

    try:
        robot_geometry['x1'] = float(pm.textField('t_x1', q=True, text=True))
        robot_geometry['x2'] = float(pm.textField('t_x2', q=True, text=True))
        robot_geometry['x3'] = float(pm.textField('t_x3', q=True, text=True))
        robot_geometry['y1'] = float(pm.textField('t_y1', q=True, text=True))
        robot_geometry['z1'] = float(pm.textField('t_z1', q=True, text=True))
        robot_geometry['z2'] = float(pm.textField('t_z2', q=True, text=True))
        robot_geometry['z3'] = float(pm.textField('t_z3', q=True, text=True))
    except ValueError:
        pm.error('Robot geometry inputs must be floats')

    return robot_geometry


def get_robot_definition(robot_geometry):
    """
    :return robot_definition: dictionary
    """
    robot_definition = {}

    robot_definition['a1'] = robot_geometry['x1']
    robot_definition['a2'] = robot_geometry['z3']
    robot_definition['b'] = robot_geometry['y1']
    robot_definition['c1'] = robot_geometry['z1']
    robot_definition['c2'] = robot_geometry['z2']
    robot_definition['c3'] = robot_geometry['x2']
    robot_definition['c4'] = robot_geometry['x3']

    return robot_definition


def get_position_limits():
    """
    """
    position_limits = {}

    for i in range(6):
        try:
            position_limits['a{}Min'.format(i+1)] = float(pm.textField(
                                                       't_A{}Min'.format(i+1),
                                                        q=True,
                                                        text=True))
            position_limits['a{}Max'.format(i+1)] = float(pm.textField(
                                                       't_A{}Max'.format(i+1),
                                                        q=True,
                                                        text=True))
        except ValueError:
            pm.error('Robot position limits must be floats')        

    return position_limits


def set_position_limits(position_limits):
    """
    """
    for i in range(6):
        pm.setAttr('target_CTRL.axis{}Max'.format(i+1),
                   position_limits['a{}Max'.format(i+1)])

        pm.setAttr('target_CTRL.axis{}Min'.format(i+1),
                   position_limits['a{}Min'.format(i+1)])


def get_velocity_limits():
    """
    """
    velocity_limits = {}

    for i in range(6):
        try:
            velocity_limits['a{}'.format(i+1)] = float(pm.textField(
                                                       't_A{}vel'.format(i+1),
                                                       q=True,
                                                       text=True))
        except ValueError:
            pm.error('Robot velocity limits must be floats')

    return velocity_limits


def set_velocity_limits(velocity_limits):
    """
    """
    for i in range(6):
        pm.setAttr('target_CTRL.axis{}VelocityLimit'.format(i+1),
                   velocity_limits['a{}'.format(i+1)])


def get_axis_pivots(units='cm'):
    """ 
    Converts robot geometry into -x, -y, -z coordinates of axis pivots
    Converts from robot frame to maya frame and converts from mm to cm
    Maya    Robot
      x ----- y
      y ----- z
      z ----- x
    :return axis_pivots: x-y-z loaction of each axis' pivot in Maya space
    """
    # Convery robot geometry from user input to cenitmeters
    # (Maya's default unit)
    robot_geometry = get_robot_geometry()

    a1_x = 0
    a1_y = robot_geometry['z1']/2. # This can be anywhere
    a1_z = 0

    a2_x = 0
    a2_y = robot_geometry['z1']
    a2_z = robot_geometry['x1']

    a3_x = robot_geometry['y1']
    a3_y = robot_geometry['z1'] + robot_geometry['z2']
    a3_z = robot_geometry['x1']

    a4_x = robot_geometry['y1']
    a4_y = robot_geometry['z1'] + robot_geometry['z2'] + robot_geometry['z3']
    a4_z = robot_geometry['x1'] + robot_geometry['x2']/2

    a5_x = robot_geometry['y1']
    a5_y = robot_geometry['z1'] + robot_geometry['z2'] + robot_geometry['z3']
    a5_z = robot_geometry['x1'] + robot_geometry['x2']

    a6_x = robot_geometry['y1']
    a6_y = robot_geometry['z1'] + robot_geometry['z2'] + robot_geometry['z3']
    a6_z = robot_geometry['x1'] + robot_geometry['x2'] + robot_geometry['x3']

    axis_pivots = [[a1_x, a1_y, a1_z],
                   [a2_x, a2_y, a2_z],
                   [a3_x, a3_y, a3_z],
                   [a4_x, a4_y, a4_z],
                   [a5_x, a5_y, a5_z],
                   [a6_x, a6_y, a6_z],
                   ]

    if units == 'cm':
        # Convery to centimeter (Maya's default unit)
        for i, axis in enumerate(axis_pivots):
            axis_pivots[i] = [val/10 for val in axis]

    return axis_pivots


def print_axis_pivots(*args):
    axis_pivots = get_axis_pivots()

    for i, axis in enumerate(axis_pivots):
        print('Axis {}:'.format(i+1), axis)


def zero_axis_pivots(*args):
    for i in range(6):
        pm.xform('axis{}'.format(i+1), pivots=[0,0,0], ws=True)


def set_axis_pivots(axis_pivots):
    """
    """
    for i in range(6):
        axis_pivot = axis_pivots[i]
        a_x = axis_pivot[0]
        a_y = axis_pivot[1]
        a_z = axis_pivot[2]
        pm.xform('axis{}'.format(i+1), pivots=[a_x, a_y, a_z], ws=True)


def set_robot_definition(robot_definition, units='cm'):
    """
    """
    if units == 'cm':
        unit = 10
    else:
        unit = 1

    pm.setAttr('target_CTRL.a1', robot_definition['a1']/unit, lock=True)
    pm.setAttr('target_CTRL.a2', robot_definition['a2']/unit, lock=True)
    pm.setAttr('target_CTRL.b', robot_definition['b']/unit, lock=True)
    pm.setAttr('target_CTRL.c1', robot_definition['c1']/unit, lock=True)
    pm.setAttr('target_CTRL.c2', robot_definition['c2']/unit, lock=True)
    pm.setAttr('target_CTRL.c3', robot_definition['c3']/unit, lock=True)
    pm.setAttr('target_CTRL.c4', robot_definition['c4']/unit, lock=True)


def get_robot_model():
    robot_model = pm.textField('t_robotModel', q=True, text=True)

    return robot_model


def set_robot_model(robot_model):
    pm.setAttr('target_CTRL.robotSubtype', robot_model, type='string')
    pm.setAttr('target_CTRL.robotSubtype', lock=True)


def set_tcp_grp(flange_loc):
    """
    """
    pm.xform('tcp_GRP', t=flange_loc, os=True)

    # Freeze translate attribute
    pm.makeIdentity('tcp_GRP', apply=True, translate=True)

    # Lock tX, tY, tZ attributes
    pm.setAttr('tcp_GRP.translate', lock=True)


def set_target_ctrl(flange_loc):
    """
    """
    pm.xform('target_CTRL', t=flange_loc, ws=True)

    # Freeze translate attribute
    pm.makeIdentity('target_CTRL', apply=True, translate=True)


def rig(*args):
    """
    :return:
    """    
    robot_geometry = get_robot_geometry()
    axis_pivots = get_axis_pivots()
    robot_definition = get_robot_definition(robot_geometry)
    velocity_limits = get_velocity_limits()
    robot_model = get_robot_model()
    position_limits = get_position_limits()
    
    set_axis_pivots(axis_pivots)
    set_position_limits(position_limits)
    set_robot_model(robot_model)
    set_robot_definition(robot_definition)
    set_velocity_limits(velocity_limits)
    

    flange_loc = axis_pivots[5]
    set_tcp_grp(flange_loc)
    set_target_ctrl(flange_loc)

    pm.setAttr('target_CTRL.ik', 1)


