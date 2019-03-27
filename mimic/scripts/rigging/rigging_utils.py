#!usr/bin/env python
"""

"""
try:
    import pymel.core as pm
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

__TARGET_CTRL_NAME = 'target_CTRL'

# Geometry fields required for Spherical Wrist solver
__SW_GEOM_FIELDS =  ['x1', 'x2', 'x3', 'y1', 'z1', 'z2', 'z3']
# Geometry fields required for Hawkins-Keating solver
__HK_GEOM_FIELDS =  ['d1', 'd4', 'd5', 'd6', 'a2', 'a3']


def get_robot_geometry(solver_type):
    """
    Gets the robot geometry from rigging UI
    :return robot_geometry: dictionary
    """

    robot_geometry = {}


    if solver_type == 1:
        geom_fields = __HK_GEOM_FIELDS
    else:
        geom_fields = __SW_GEOM_FIELDS  

    for each in geom_fields:
        try:
            robot_geometry[each] = float(pm.textField('t_{}'.format(each), q=True, text=True))
        except ValueError:
            pm.error('Field {} input must be a float value'.format(each))

    return robot_geometry


def get_robot_definition(robot_geometry, solver_type):
    """
    :return robot_definition: dictionary
    """
    robot_definition = {}

    if solver_type == 1:
        robot_definition['a1'] = robot_geometry['d1']
        robot_definition['a2'] = robot_geometry['d4']
        robot_definition['b'] = robot_geometry['d5']
        robot_definition['c1'] = robot_geometry['d6']
        robot_definition['c2'] = robot_geometry['a2']
        robot_definition['c3'] = robot_geometry['a3']
        robot_definition['c4'] = 0  # Unused param
    else:
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


def get_axis_pivots(robot_geometry, solver_type):
    """ 
    Converts robot geometry into -x, -y, -z coordinates of axis pivots
    Converts from robot frame to maya frame and converts from mm to cm
    Maya    Robot
      x ----- y
      y ----- z
      z ----- x
    :return axis_pivots: x-y-z loaction of each axis' pivot in Maya space
    """

    if solver_type == 1:
        axis_pivots = _get_axis_pivots_HK(robot_geometry)
    else:
        axis_pivots = _get_axis_pivots_SW(robot_geometry)

    return axis_pivots


def _get_axis_pivots_SW(robot_geometry, units='cm'):
    """
    Converts robot geometry into -x, -y, -z coordinates of axis pivots
    Converts from robot frame to maya frame and converts from mm to cm
    Maya    Robot
      x ----- y
      y ----- z
      z ----- x
    :return axis_pivots: x-y-z loaction of each axis' pivot in Maya space
    """

    a1_x = 0
    a1_y = robot_geometry['z1']/2. # This can be anywhere
    a1_z = 0

    a2_x = 0
    a2_y = robot_geometry['z1']
    a2_z = robot_geometry['x1']

    a3_x = robot_geometry['y1']
    a3_y = a2_y + robot_geometry['z2']
    a3_z = a2_z

    a4_x = a3_x
    a4_y = a3_y + robot_geometry['z3']
    a4_z = a3_z + robot_geometry['x2']/2

    a5_x = a4_x
    a5_y = a4_y
    a5_z = a3_z + robot_geometry['x2']

    a6_x = a5_x
    a6_y = a5_y
    a6_z = a5_z + robot_geometry['x3']

    axis_pivots = [[a1_x, a1_y, a1_z],
                   [a2_x, a2_y, a2_z],
                   [a3_x, a3_y, a3_z],
                   [a4_x, a4_y, a4_z],
                   [a5_x, a5_y, a5_z],
                   [a6_x, a6_y, a6_z]]

    if units == 'cm':
        # Convert to centimeter (Maya's default unit)
        for i, axis in enumerate(axis_pivots):
            axis_pivots[i] = [val/10 for val in axis]

    return axis_pivots


def _get_axis_pivots_HK(robot_geometry, units='cm'):
    """
    """    
    a1_x = 0
    a1_y = robot_geometry['d1']/2.0 # This can be anywhere
    a1_z = 0

    a2_x = robot_geometry['d4']/2.0
    a2_y = robot_geometry['d1']
    a2_z = 0

    a3_x = a2_x
    a3_y = a2_y + robot_geometry['a2']
    a3_z = 0

    a4_x = a3_x
    a4_y = a3_y
    a4_z = robot_geometry['a3']

    a5_x = robot_geometry['d4'] 
    a5_y = a4_y + robot_geometry['d5']/2.0 
    a5_z = a4_z

    a6_x = a5_x
    a6_y = a4_y + robot_geometry['d5']
    a6_z = a5_z + robot_geometry['d6']

    axis_pivots = [[a1_x, a1_y, a1_z],
                   [a2_x, a2_y, a2_z],
                   [a3_x, a3_y, a3_z],
                   [a4_x, a4_y, a4_z],
                   [a5_x, a5_y, a5_z],
                   [a6_x, a6_y, a6_z]]

    if units == 'cm':
        # Convert to centimeter (Maya's default unit)
        for i, axis in enumerate(axis_pivots):
            axis_pivots[i] = [val/10 for val in axis]

    return axis_pivots


def get_robot_model():
    robot_model = pm.textField('t_robotModel', q=True, text=True)

    return robot_model


def get_solver_type():
    """
    """

    # We use try-except here because most robot rigs don't have the
    # 'solverType' attribute, as it was added for UR dev
    # Defaults to 0 if attr doesn't exist, representing the standard
    # spherical wrist solver
    try:
        target_ctrl = pm.ls(__TARGET_CTRL_NAME, type='transform')[0]
        solver_type = target_ctrl.getAttr('solverType')
    except:
        solver_type = 0
    
    return solver_type


def set_position_limits(position_limits):
    """
    """
    for i in range(6):
        pm.setAttr('target_CTRL.axis{}Max'.format(i+1),
                   position_limits['a{}Max'.format(i+1)])

        pm.setAttr('target_CTRL.axis{}Min'.format(i+1),
                   position_limits['a{}Min'.format(i+1)])


def set_velocity_limits(velocity_limits):
    """
    """
    for i in range(6):
        pm.setAttr('target_CTRL.axis{}VelocityLimit'.format(i+1),
                   velocity_limits['a{}'.format(i+1)])


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


def print_axis_pivots(*args):
    """
    """
    solver_type = get_solver_type()
    robot_geometry = get_robot_geometry(solver_type)
    axis_pivots = get_axis_pivots(robot_geometry, solver_type)

    for i, axis in enumerate(axis_pivots):
        print 'Axis {}:'.format(i+1), axis


def zero_axis_pivots(*args):
    for i in range(6):
        pm.xform('axis{}'.format(i+1), pivots=[0,0,0], ws=True)


def rig(*args):
    """
    :return:
    """

    solver_type = get_solver_type()
    robot_geometry = get_robot_geometry(solver_type)
    axis_pivots = get_axis_pivots(robot_geometry, solver_type)
    robot_definition = get_robot_definition(robot_geometry, solver_type)
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


