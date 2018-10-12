#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
External Axis Utility Functions.
"""

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False
import re

import general_utils
import mimic_config
import mimic_program
import mimic_utils

reload(mimic_utils)
reload(mimic_config)
reload(mimic_program)
reload(general_utils)


def get_external_axis_names(robot_name, only_active=False):
    """
    Gets all external axes assigned to the given robot
    :param robot_name: string, name of selected robot
    :param only_active: bool, if True, removes axes marked as "ignore"
    :return robots_external_axes: list, names of all external axes on robot
    """

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)

    # Find all attributes on the target_CTRL categorized as 'externalAxis'
    robot_external_axis_names = pm.listAttr(target_ctrl_path,
                                            category='externalAxis')

    # Remove parent attribute designation 'externalAxis_' from each axis name
    for i, axis_name in enumerate(robot_external_axis_names):
        robot_external_axis_names[i] = axis_name.replace('externalAxis_', '')

    # If only_active is True, remove axes marked as "Ignore"
    if only_active:
        active_external_axes = [x for x in robot_external_axis_names if
                                not pm.getAttr(target_ctrl_path + '.' + x + '_ignore')]

        robot_external_axis_names = active_external_axes

    return robot_external_axis_names


def get_external_axis_info(robot_name, external_axis_name):
    """
    Get's all of the external axis settings for the input external axis name
    :param robot_name: string, name of robot
    :param external_axis_name: string, name of external axis
    :return info: dict, dictionary of input external axis setting
    """

    info = {}

    info['Robot Name'] = robot_name
    info['Axis Name'] = external_axis_name

    external_axis_path = _get_external_axis_path(robot_name, external_axis_name)
    info['Axis Number'] = _get_external_axis_number(external_axis_path)

    driving_attr_ctrl, driving_attr_name = _get_external_axis_connections(external_axis_path)
    info['Driving Controller'] = driving_attr_ctrl

    info['Driving Attribute'] = driving_attr_name

    info['Position Limit Min'] = _get_external_axis_limits_min(external_axis_path)

    info['Position Limit Max'] = _get_external_axis_limits_max(external_axis_path)

    info['Velocity Limit'] = _get_external_axis_velocity_limit(external_axis_path)

    info['Ignore'] = _get_external_axis_ignore(external_axis_path)

    return info


def get_external_axis_info_simple(robot_name, external_axis_name, frame=None):
    """
    Get a few of the external axis settings for the input external axis.
    :param robot_name: string, name of robot
    :param external_axis_name: string, name of external axis
    :param frame: optional frame parameter
    :return info_simple: dict, dictionary of input external axis' setting
    """
    info_simple = {}
    external_axis_path = _get_external_axis_path(robot_name, external_axis_name)
    info_simple['Axis Number'] = _get_external_axis_number(external_axis_path)
    info_simple['Position'] = _get_external_axis_position(external_axis_path, frame)
    info_simple['Ignore'] = _get_external_axis_ignore(external_axis_path)
    return info_simple


def _get_external_axis_path(robot_name, external_axis_name):
    """
    Get the path for an external axis.
    :param robot_name: string, name of robot
    :param external_axis_name: string, name of external axis
    :return: str, external axis attribute path
    """
    return '{}.{}'.format(mimic_utils.get_target_ctrl_path(robot_name), external_axis_name)


def _get_external_axis_position(external_axis_path, frame=None):
    """
    Get the position of an external axis.
    :param external_axis_path: string, attribute path using robot and external axis names
    :param frame: optional frame parameter
    :return external_axis_position: float, external axis position at current
                                    frame or input frame
    """
    attribute_path = external_axis_path + '_position'
    external_axis_position = mimic_utils.get_attribute_value(attribute_path, frame)

    # If the axis' driving attribute is a translation, we need to convert from
    # Maya's units (cm) to millimeters
    driving_attribute = pm.listConnections(attribute_path,
                                           plugs=True,
                                           s=True)[0]
    driving_attr_ctrl, driving_attr_name = driving_attribute.split('.')

    if 'translate' in driving_attr_name:
        external_axis_position = external_axis_position * 10

    return external_axis_position


def _get_external_axis_number(external_axis_path):
    """
    Get the number for an external axis. 1-indexed!
    :param external_axis_path: string, attribute path using robot and
    external axis names
    :return: int, external axis number
    """
    attribute_path = external_axis_path + '_axisNumber'
    return mimic_utils.get_attribute_value(attribute_path)


def _get_external_axis_connections(axis_attribute_name):
    """
    Gets the input external axis' driving controller and driving attribute
    by checking the connections on the axis' position attribute
    :param axis_attribute_name: string, name of external axis
    :return driving_atr_ctrl: string, name of external axis' assigned
                              controller
    :return driving_attr_name: string, name of the attribute that's driving
                               the external axis' position value
                               (e.g. 'translateX')
    """

    # Check the incomming connections on the external axis' position attribute
    driving_attribute = pm.listConnections(axis_attribute_name
                                           + '_position',
                                           plugs=True,
                                           s=True)[0]

    # Split the driving attribute into its controller name and driving
    # attribute name
    # (e.g. 'axis_CTRL.translateX' becomes 'axis_CTRL' and 'translateX')
    driving_attr_ctrl, driving_attr_name = driving_attribute.split('.')

    # If the driving attribute is a 'rotate' attribute, there will be a unit
    # conversion node between the driving attribute and the external axis
    # position attribute, so we iterate once more to get the actual driving
    # controller and attribute
    if 'unitConversion' in driving_attr_ctrl:
        driving_attribute = pm.listConnections(driving_attr_ctrl
                                               + '.input',
                                               plugs=True,
                                               s=True)[0]
        driving_attr_ctrl, driving_attr_name = driving_attribute.split('.')

    return driving_attr_ctrl, driving_attr_name


def _get_external_axis_ignore(external_axis_path):
    """
    Get the ignore (is-ignored) value for an external axis
    :param external_axis_path: string, attribute path using robot and
                               external axis names
    :return: bool, True if "Ignore axis" is checked, false if not
    """
    attribute_path = external_axis_path + '_ignore'
    return mimic_utils.get_attribute_value(attribute_path)


def _get_external_axis_limits_min(external_axis_path):
    """
    Get the minimum position limit for an external axis.
    :param external_axis_path: string, attribute path using robot and
                               external axis names
    :return: float, axis minimum limit
    """
    attribute_path = external_axis_path + '_axisMin'
    return mimic_utils.get_attribute_value(attribute_path)


def _get_external_axis_limits_max(external_axis_path):
    """
    Get the maximum position limit for an external axis.
    :param external_axis_path: string, attribute path using robot and
                               external axis names
    :return: float, axis maximum limit
    """
    attribute_path = external_axis_path + '_axisMax'
    return mimic_utils.get_attribute_value(attribute_path)


def _get_external_axis_velocity_limit(external_axis_path):
    """
    Get the velocity limit for an external axis.
    :param external_axis_path: string, attribute path using robot and
                               external axis names
    :return: float, axis velocity limit
    """
    attribute_path = external_axis_path + '_maxVelocity'
    return mimic_utils.get_attribute_value(attribute_path)


# ------------------


def _check_external_axis_name(robot_name, axis_name):
    """
    Determines if external axis name is unique
    Raises an Exception if the input name is already taken by another
    external axis on the input robot
    :param robot_name: string, name of robot
    :param axis_name: str, filtered user-supplied external axis name
    """

    # Check that axis name isn't already taken
    robots_external_axes = get_external_axis_names(robot_name)
    for axis in robots_external_axes:
        if axis == axis_name:
            raise MimicError('External axis name \'{}\' is taken; ' \
                             'axis name must be unique'.format(axis_name))


def _check_external_axis_number(robot_name, axis_number):
    """
    Determines if external axis number is unique
    Raises an Exception if the input axis number is already taken by another
    external axis on the input robot
    :param robot_name: string, name of robot
    :param axis_number: int, user-supplied external axis number
    """

    # Check that axis name isn't already taken
    robots_external_axes = get_external_axis_names(robot_name)

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)
    for axis_name in robots_external_axes:
        current_axis_number = pm.getAttr('{}.{}_axisNumber'.format(target_ctrl_path, axis_name))
        if current_axis_number == axis_number:
            raise MimicError('External axis number {} is taken; ' \
                             'axis number must be unique'.format(axis_number))


def _check_external_axis_params(external_axis_params):
    """
    Check to ensure that user inputs proper value types for external axis
    parameters.
    Raises exceptions if criteria are not met
    """

    # Make sure the following parameters have user inputs
    must_have_input = ['Axis Name',
                       'Position Limit Min',
                       'Position Limit Max',
                       'Velocity Limit']

    empty_params = []
    for param in must_have_input:
        if not external_axis_params[param]:
            empty_params.append(param)

    if empty_params:
        raise MimicError('{} must have a user input'.format(empty_params))

    # Make sure axis limits are all floats
    must_be_floats = ['Position Limit Min',
                      'Position Limit Max',
                      'Velocity Limit']
    non_float_params = []
    for param in must_be_floats:
        try:
            external_axis_params[param] = float(external_axis_params[param])
        except:
            non_float_params.append(param)
    if non_float_params:
        raise MimicError('{} must be float(s)'.format(non_float_params))


def _check_if_robot_is_attached_to_external_axis(robot_name):
    """
    Checks if the robot is attached to an external axis controller
    :param robot_name: name of the robot being checked
    :return: bool, True if robot is attached
    to an external axis, False if otherwise
    """
    if pm.objExists(mimic_utils.get_local_ctrl_path(robot_name) +
                    '|localCTRL_externalAxisCTRL_parentConstraint'):
        return True
    else:
        return False


def _filter_external_axis_name(axis_name):
    """
    Axis name must be formatted to match Maya's attribute name requirements
    This is typically cameCase. More specifially, the name can't contain spaces
    or special characters
    :param axis_name: str, raw user input for external axis name
    :return axis_name: str, filtered string for user-supplied axis name
    """

    # Replace spaces with underscores
    axis_name = axis_name.replace(' ', '_')
    # Remove special characters
    axis_name = ''.join(re.findall(r"[_a-zA-Z0-9]+", axis_name))

    return axis_name


def _get_external_axis_params():
    """
    Finds the user-defined external axis parameters from the Mimic UI
    Checks that user inputs meet parameter riteria 
    :return external_axis_param_dict: dict containing external axis params
        "Axis Name" (str)
        "Axis Number" (int)
        "Driving Attribute" (str)
        "Position Limti Min" (float)
        "Position Limti Max" (float)
        "Velocity Limit" (float)
        "Attach" (bool)
        "Ignore" (bool)
    """

    external_axis_param_dict = {}

    external_axis_param_dict['Axis Name'] = pm.textField(
        't_externalAxisDescriptionText',
        query=True,
        text=True)
    external_axis_param_dict['Axis Number'] = int(pm.optionMenu(
        'axisNumberMenu',
        query=True,
        value=True))
    external_axis_param_dict['Driving Attribute'] = pm.optionMenu(
        'drivingAttributeMenu',
        query=True,
        value=True)
    external_axis_param_dict['Position Limit Min'] = pm.textField(
        't_externalAxisLimitMin',
        query=True,
        text=True)
    external_axis_param_dict['Position Limit Max'] = pm.textField(
        't_externalAxisLimitMax',
        query=True,
        text=True)
    external_axis_param_dict['Velocity Limit'] = pm.textField(
        't_externalAxisVelocityLimit',
        query=True,
        text=True)
    external_axis_param_dict['Attach'] = pm.checkBox(
        'cb_attachRobotToController',
        query=True,
        value=True)
    external_axis_param_dict['Ignore'] = pm.checkBox(
        'cb_ignoreExternalAxis',
        query=True,
        value=True)

    _check_external_axis_params(external_axis_param_dict)

    # Ensure axis name input complies with Maya's attribute name requirements
    axis_name = external_axis_param_dict['Axis Name']
    external_axis_param_dict['Axis Name'] = _filter_external_axis_name(axis_name)

    return external_axis_param_dict


def _get_selection_input():
    """
    Takes Maya's viewport selection and filters it to a robot and external
    axis controller. Raises exception of selection criteria is not met
    :return robot: str, root node of robot in Maya viewport selection
    :return external_axis_CTRL: str, name of external axis controller
        selected in Maya's viewport
    """
    sel = pm.ls(selection=True, type='transform')
    robots = mimic_utils.get_robot_roots()

    # Exception handling
    if not sel:
        raise MimicError('Nothing selected; ' \
                         'select a valid robot control and external axis controller')
    if not robots:
        raise MimicError('No robot selected; ' \
                         'select a valid robot')
    if len(robots) > 1:
        raise MimicError('Too many robots selected; ' \
                         'select a single robot')
    if len(sel) > 2:
        raise MimicError('Too many selections; ' \
                         'select a single robot control, ' \
                         'and single external axis controller')
    if len(sel) == 1:
        raise MimicError('Not enough selections; ' \
                         'select a single robot control, ' \
                         'and single tool control')

    # find which selected object is the external axis controller
    if not mimic_utils.get_robot_roots(0, [sel[0]]):
        external_axis_CTRL = sel[0]
    else:
        external_axis_CTRL = sel[1]

    robot = robots[0]
    return robot, external_axis_CTRL


def _attach_robot_to_external_axis(robot, external_axis_CTRL):
    """
    Parent Constrains the input robot's local_CTRL to the input external
    axis controller. This is primarily used for attaching robots to linear
    sliders
    :param robot: string, name pointing to selected robot
    :param external_axis_CTRL: string, name pointing to selected external
    axis ctrl
    """

    # Create parent constraint between robot base's local control and
    # external axis control
    local_ctrl_path = mimic_utils.get_local_ctrl_path(robot)
    pm.parentConstraint(external_axis_CTRL,
                        local_ctrl_path,
                        maintainOffset=True,
                        name='localCTRL_externalAxisCTRL_parentConstraint')

    # Hide robot's local_CTRL
    pm.setAttr(local_ctrl_path + '.v', 0)


def _enable_external_axis_limits(external_axis_CTRL, driving_attribute_trunc, driving_axis, enable=True):
    """
    Enables/Disables external axis' limit attributes
    :param external_axis_CTRL: str, name of external axis control
    :param driving_attribute_trunc: str, truncated name of driving attribute
        (e.g. Trans, Rot)
    :param driving_axis: str, 'X', 'Y', or 'Z'
    :param enable: bool, default True
    """

    pm.setAttr('{}.min{}{}LimitEnable'.format(external_axis_CTRL,
                                              driving_attribute_trunc,
                                              driving_axis),
               enable)

    pm.setAttr('{}.max{}{}LimitEnable'.format(external_axis_CTRL,
                                              driving_attribute_trunc,
                                              driving_axis),
               enable)


def _set_external_axis_CTRL_limits(robot_name, external_axis_CTRL, external_axis_params):
    """
    Sets the selected external axis controller translation or rotation limits
    :param robot_name: string, name of selected robot
    :param external_axis_CTRL: string, name of external axis controller
    :param external_axis_params: dict, axis parameters set by the user in the 
        Mimic UI
    """

    axis_name = external_axis_params['Axis Name']
    driving_attribute = external_axis_params['Driving Attribute']
    position_limit_min = external_axis_params['Position Limit Min']
    position_limit_max = external_axis_params['Position Limit Max']
    velocity_limit = external_axis_params['Velocity Limit']

    # Break down driving attribute into transform and axis companents
    # 'translateX' becomes 'translate', 'X'
    driving_axis = driving_attribute[-1]

    # Prep transformation string for Maya's limit attributes
    if 'translate' in driving_attribute:
        driving_attribute_trunc = 'Trans'
    else:
        driving_attribute_trunc = 'Rot'

    # Define external axis' attribute path on robot
    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)
    external_axis_min_limit_path = target_ctrl_path + '.{}_axisMin'.format(axis_name)

    external_axis_max_limit_path = target_ctrl_path + '.{}_axisMax'.format(axis_name)

    # Enable the external axis controllers' limits and connect them to the 
    # position attribute on the target controller
    _enable_external_axis_limits(external_axis_CTRL,
                                 driving_attribute_trunc,
                                 driving_axis,
                                 enable=True)

    pm.connectAttr(external_axis_min_limit_path,
                   '{}.min{}{}Limit'.format(external_axis_CTRL,
                                            driving_attribute_trunc,
                                            driving_axis))

    pm.connectAttr(external_axis_max_limit_path,
                   '{}.max{}{}Limit'.format(external_axis_CTRL,
                                            driving_attribute_trunc,
                                            driving_axis))


def _clear_external_axis_CTRL_limits(robot_name, external_axis_CTRL, driving_attribute, axis_name):
    """
    Disables the axis limit attributes for the input controller.
    :param robot_name: string, name of selected robot
    :param external_axis_CTRL: string, name of external axis controller
    :param driving_attribute: string, driving attribute e.g. 'rotateX'
    """

    # Break down driving attribute into transform and axis companents
    # 'translateX' becomes 'translate', 'X'
    driving_axis = driving_attribute[-1]

    # Prep transformation string for Maya's limit attributes
    if 'translate' in driving_attribute:
        driving_attribute_trunc = 'Trans'
    else:
        driving_attribute_trunc = 'Rot'

    # Define external axis' attribute path on robot
    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)
    external_axis_min_limit_path = target_ctrl_path + '.{}_axisMin'.format(axis_name)

    external_axis_max_limit_path = target_ctrl_path + '.{}_axisMax'.format(axis_name)

    _enable_external_axis_limits(external_axis_CTRL,
                                 driving_attribute_trunc,
                                 driving_axis,
                                 enable=False)

    pm.disconnectAttr(external_axis_min_limit_path,
                      '{}.min{}{}Limit'.format(external_axis_CTRL,
                                               driving_attribute_trunc,
                                               driving_axis))

    pm.disconnectAttr(external_axis_max_limit_path,
                      '{}.max{}{}Limit'.format(external_axis_CTRL,
                                               driving_attribute_trunc,
                                               driving_axis))


def add_external_axis(*args):
    """
    Adds an external axis to a robot based on user inputs in Mimic UI.
    :param args: required by Maya to call a function from UI button
    """
    # Get the External Axis' parameters from the Mimic UI
    external_axis_params = _get_external_axis_params()

    axis_name = external_axis_params['Axis Name']
    axis_number = external_axis_params['Axis Number']
    driving_attribute = external_axis_params['Driving Attribute']
    position_limit_min = external_axis_params['Position Limit Min']
    position_limit_max = external_axis_params['Position Limit Max']
    velocity_limit = external_axis_params['Velocity Limit']
    attach_robot_to_external = external_axis_params['Attach']
    ignore_in_postproc = external_axis_params['Ignore']

    # Get and check the proper controllers from viewport selection
    robot, external_axis_CTRL = _get_selection_input()

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    # Ensure axis name is unique
    _check_external_axis_name(robot, axis_name)

    # Check that the external axis number is unique
    _check_external_axis_number(robot, axis_number)

    # If attach to robot is true, parent the robot's local control to the
    # external axis controller
    if attach_robot_to_external:
        if _check_if_robot_is_attached_to_external_axis(robot):
            raise MimicError('{} is already attached to an external ' \
                             'axis controller'.format(robot))
        _attach_robot_to_external_axis(robot, external_axis_CTRL)

    # Add attributes to robots
    # Parent Attrubute
    parent_attribute = 'externalAxis_{}'.format(axis_name)
    pm.addAttr(target_CTRL,
               longName=parent_attribute,
               niceName='External Axis: {}'.format(axis_name),
               numberOfChildren=6,
               category='externalAxis',
               attributeType='compound')
    # Define 6 children of the External Axis parent attribute
    pm.addAttr(target_CTRL,
               longName=axis_name + '_position',
               niceName='Position',
               keyable=False, attributeType='float',
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=axis_name + '_axisNumber',
               niceName='Axis Number',
               keyable=False,
               attributeType='long',
               minValue=1,
               maxValue=6,
               defaultValue=1,
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=axis_name + '_axisMin',
               niceName='Min',
               keyable=False,
               attributeType='float',
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=axis_name + '_axisMax',
               niceName='Max',
               keyable=False,
               attributeType='float',
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=axis_name + '_maxVelocity',
               niceName='Max Velocity',
               keyable=False,
               attributeType='float',
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=axis_name + '_ignore',
               niceName='Ignore',
               keyable=False,
               attributeType='bool',
               parent=parent_attribute)

    # If the driving attribute is a translate attribute, we convert the user
    # input from millimeters to Maya's default unit of centimeters
    if 'translate' in driving_attribute:
        position_limit_min = position_limit_min / 10
        position_limit_max = position_limit_max / 10

    # Set all External Axis attributes accordingly
    axis_parent_attribute = target_CTRL + '.' + axis_name
    
    pm.setAttr(axis_parent_attribute + '_axisNumber', axis_number)
    
    # Try locking the axis_number attribute
    try:
        # If the robot is referenced, Maya will throw an exceptrion when it
        # tries to lock an attribute
        pm.setAttr(axis_parent_attribute + '_axisNumber', lock=True)
    except:
        pass

    pm.setAttr(axis_parent_attribute + '_axisMin', position_limit_min)
    pm.setAttr(axis_parent_attribute + '_axisMax', position_limit_max)
    pm.setAttr(axis_parent_attribute + '_maxVelocity', velocity_limit)
    pm.setAttr(axis_parent_attribute + '_ignore', ignore_in_postproc)

    # Connect position attribute to driving attribute
    driving_attribute_name = external_axis_CTRL + '.' + driving_attribute
    destination_attribute_name = axis_parent_attribute + '_position'
    pm.connectAttr(driving_attribute_name,
                   destination_attribute_name)

    # Set the External Axis control limits
    _set_external_axis_CTRL_limits(robot,
                                   external_axis_CTRL,
                                   external_axis_params)

    # Select the robot's target/tool controller
    tool_CTRL = mimic_utils.get_tool_ctrl_path(robot)
    if pm.objExists(tool_CTRL):
        pm.select(tool_CTRL)
    else:
        pm.select(target_CTRL)

    list_axes()
    pm.headsUpMessage('External axis \'{}\' added successfully to {}'
                      .format(axis_name, robot))


def update_external_axis(*args):
    """
    Updates an external based on user inputs in Mimic UI.
    :param args: required by Maya to call a function from UI button
    """
    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_externalAxes',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the external axis name
    robot_str, axis_name = selection.split(': ')
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]

    external_axis_params = _get_external_axis_params()

    axis_number = external_axis_params['Axis Number']
    driving_attribute = external_axis_params['Driving Attribute']
    position_limit_min = external_axis_params['Position Limit Min']
    position_limit_max = external_axis_params['Position Limit Max']
    velocity_limit = external_axis_params['Velocity Limit']
    attach_robot_to_external = external_axis_params['Attach']
    ignore_in_postproc = external_axis_params['Ignore']

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    # Set all External Axis attributes accordingly
    axis_parent_attribute = target_CTRL + '.' + axis_name

    # Check that the external axis number is unique
    if axis_number == pm.getAttr(axis_parent_attribute + '_axisNumber'):
        pass
    else:
        _check_external_axis_number(robot, axis_number)

    # If attach to robot is true, parent the robot's local control to the
    # external axis controller
    if attach_robot_to_external:
        # Check if the robot is already attached to an external axis controller
        if _check_if_robot_is_attached_to_external_axis(robot):
            raise MimicError('{} is already attached to an external ' \
                             'axis controller'.format(robot))
        # Get and check the proper controllers from viewport selection
        _, external_axis_CTRL = _get_selection_input()
        _attach_robot_to_external_axis(robot, external_axis_CTRL)

    # Check if our driving attribute needs to be updated. If not, do nothing
    # If so, update the connection
    axis_attribute_name = target_CTRL + '.{}'.format(axis_name)
    external_axis_CTRL, old_driving_attribute = _get_external_axis_connections(axis_attribute_name)
    if old_driving_attribute == driving_attribute:
        pass
    else:
        # Connect position attribute to driving attribute
        old_driving_attribute_path = external_axis_CTRL + '.' + old_driving_attribute
        new_driving_attribute_path = external_axis_CTRL + '.' + driving_attribute
        destination_attribute_name = axis_parent_attribute + '_position'
        pm.disconnectAttr(old_driving_attribute_path, destination_attribute_name)
        pm.connectAttr(new_driving_attribute_path, destination_attribute_name)

        # Update the external axis' position/rotation limits
        # Find the original driving attribute and disable it's axis limits
        _clear_external_axis_CTRL_limits(robot,
                                         external_axis_CTRL,
                                         old_driving_attribute,
                                         axis_name)

        _set_external_axis_CTRL_limits(robot,
                                       external_axis_CTRL,
                                       external_axis_params)

    # If the driving attribute is a translate attribute, we convert the user
    # input from millimeters to Maya's default unit of centimeters
    if 'translate' in driving_attribute:
        position_limit_min = position_limit_min / 10
        position_limit_max = position_limit_max / 10

    # Set all appropriate attributes on the robot
    # If the robot is referenced, Maya will throw an exceptrion when it
    # tries to lock an attribute
    try:

        pm.setAttr(axis_parent_attribute + '_axisNumber', lock=False)
    except:
        pass

    pm.setAttr(axis_parent_attribute + '_axisNumber', axis_number)
    
    try:
        pm.setAttr(axis_parent_attribute + '_axisNumber', lock=True)
    except:
        pass

    pm.setAttr(axis_parent_attribute + '_axisMin', position_limit_min)
    pm.setAttr(axis_parent_attribute + '_axisMax', position_limit_max)
    pm.setAttr(axis_parent_attribute + '_maxVelocity', velocity_limit)
    pm.setAttr(axis_parent_attribute + '_ignore', ignore_in_postproc)

    # Select the external axis
    pm.select(external_axis_CTRL)

    pm.headsUpMessage('{}: Axis \'{}\' successfully updated'
                      .format(robot, axis_name))


def clear_external_axis_list(*args):
    """
    Clears external axis list in Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    pm.textScrollList('tsl_externalAxes', edit=True, removeAll=True)
    reset_external_axis_UI()


def deselect_external_axis(*args):
    """
    Deselects item from external axis list in Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    pm.textScrollList('tsl_externalAxes', edit=True, deselectAll=True)
    reset_external_axis_UI()


def remove_external_axis(*args):
    """
    Removes external axis from the robot it's attached to by deleting all of
    its attributes. The axis controller and models are preserved.
    This function just breaks the connection between the robot and the axis
    controller
    :param args: required by Maya to call a function from UI button required by Maya UI
    :return:
    """

    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_externalAxes',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the external axis name
    robot_str, axis_name = selection.split(': ')
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    parent_attribute = '{}.externalAxis_{}'.format(target_CTRL, axis_name)

    # Remove connections between the axis controller and the robot
    external_axis_attribute_path = target_CTRL + '.' + axis_name
    external_axis_CTRL, driving_attribute = _get_external_axis_connections(
        external_axis_attribute_path)
    driving_axis = driving_attribute[-1]
    # Prep transformation string for Maya's limit attributes
    if 'translate' in driving_attribute:
        driving_attribute_trunc = 'Trans'
    else:
        driving_attribute_trunc = 'Rot'
    _enable_external_axis_limits(external_axis_CTRL,
                                 driving_attribute_trunc,
                                 driving_axis,
                                 enable=False)

    # Delete External Axis attribute on the robot controller
    pm.deleteAttr(parent_attribute)

    # Clear the axis from the Mimic UI selection and reset the UI
    pm.textScrollList('tsl_externalAxes',
                      edit=True,
                      removeItem=selection)
    if not pm.textScrollList('tsl_externalAxes',
                             query=True,
                             numberOfItems=True):
        reset_external_axis_UI()

    '''
    # NEEDS Attention. This deletes parent constraint even if the axis
    # being removed isn't the one the robot is attached to
    if _check_if_robot_is_attached_to_external_axis(robot):
        pm.delete('{}|robot_GRP|local_CTRL|' \
                  'localCTRL_externalAxisCTRL_parentConstraint'
                  .format(robot))
        pm.setAttr('{}|robot_GRP|local_CTRL.visibility'.format(robot), 1)
    '''

    pm.select(target_CTRL)
    pm.headsUpMessage('External Axis \'{}\' removed successfully from {}'
                      .format(axis_name, robot))


def list_axes(*args):
    """
    If no robot is selected, prints list of all external axis in scene to Mimci UI
    If robot is selected, prints external axes assigned to that robot to Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    # Clear previus UI list
    clear_external_axis_list()

    # Check viewport robot selection
    # If robots are selected, list all external axes on selected robots
    selected_robots = mimic_utils.get_robot_roots()
    if selected_robots:
        robots = selected_robots
    # If no robots are selected, list all axes in the scene
    else:
        robots_in_scene = mimic_utils.get_robot_roots(all_robots=True)
        # If there are no robots in the scene, raise an exception
        if not robots_in_scene:
            raise MimicError('No robots in scene')
        else:
            robots = robots_in_scene

    # Keep track of selected robots without axes for a heads-up message
    selected_robots_without_axes = []

    # For each robots, get a list of all its external axes
    for robot in robots:
        robots_external_axes = get_external_axis_names(robot)

        # If we're only looking at selected robots, check if each selected
        # robot has external axes. If not, add it to a list to display in
        # a heads up message
        if selected_robots:
            if not robots_external_axes:
                selected_robots_without_axes.append(robot)

        # Update Mimic UI with list of external axes
        for axis in robots_external_axes:
            append_string = robot + ': ' + axis
            pm.textScrollList('tsl_externalAxes',
                              edit=True,
                              append=append_string)

    if selected_robots_without_axes:
        robot_list_str = ''
        for each in selected_robots_without_axes:
            robot_list_str += each + ', '

        pm.headsUpMessage('{} has no External Axes'
                          .format(robot_list_str))


def update_external_axis_UI(axis_info):
    """
    Updates external axis inputs of Mimic UI based on external axis selection
    in axis list
    :param axis_info: dict containing info about selected axis
    :return:
    """
    # Change frame name from "Add" to "Update"
    pm.frameLayout('add_external_axis_frame',
                   edit=True,
                   label="Update External Axis")

    # Update axis parameters
    pm.textField('t_externalAxisDescriptionText',
                 edit=True,
                 text=axis_info['Axis Name'],
                 editable=False)
    pm.optionMenu('axisNumberMenu',
                  edit=True,
                  value=str(axis_info['Axis Number']))
    pm.optionMenu('drivingAttributeMenu',
                  edit=True,
                  value=axis_info['Driving Attribute'])

    # If the driving attribute is a translate attribute, we convert the user
    # input from millimeters to Maya's default unit of centimeters
    position_limit_min = axis_info['Position Limit Min']
    position_limit_max = axis_info['Position Limit Max']
    if 'translate' in axis_info['Driving Attribute']:
        position_limit_min = position_limit_min * 10
        position_limit_max = position_limit_max * 10

    pm.textField('t_externalAxisLimitMin',
                 edit=True,
                 text=str(position_limit_min))
    pm.textField('t_externalAxisLimitMax',
                 edit=True,
                 text=str(position_limit_max))
    pm.textField('t_externalAxisVelocityLimit',
                 edit=True,
                 text=str(axis_info['Velocity Limit']))
    pm.checkBox('cb_ignoreExternalAxis',
                edit=True,
                value=axis_info['Ignore'])

    # Change "Add Axis" button to "Update Axis"
    # Change background color of button
    pm.button('b_add_Axis',
              edit=True,
              label='Update Axis',
              backgroundColor=[.7, .7, .7],
              command=update_external_axis)


def reset_external_axis_UI():
    """
    Restores externa axis UI inputs in Mimic UI to defaults
    :return:
    """
    pm.frameLayout('add_external_axis_frame',
                   edit=True,
                   label="Add External Axis")

    # Update axis parameters
    pm.textField('t_externalAxisDescriptionText',
                 edit=True,
                 text='',
                 editable=True)
    pm.optionMenu('axisNumberMenu',
                  edit=True,
                  value='1')
    pm.optionMenu('drivingAttributeMenu',
                  edit=True,
                  value='translateX')

    pm.textField('t_externalAxisLimitMin',
                 edit=True,
                 text='')
    pm.textField('t_externalAxisLimitMax',
                 edit=True,
                 text='')
    pm.textField('t_externalAxisVelocityLimit',
                 edit=True,
                 text='')
    pm.checkBox('cb_ignoreExternalAxis',
                edit=True,
                value=0)

    # Change "Add Axis" button to "Update Axis"
    # Change background color of button
    pm.button('b_add_Axis',
              edit=True,
              label='Add Axis',
              backgroundColor=[.361, .361, .361],
              command=add_external_axis)


def axis_selected(*args):
    """
    Command that is called when an axis is selected in external axis list
    in Mimic UI, which gets the external axis name and info, and updates
    the external axis Mimic UI accordingly
    Selets the axis controller in Maya's viewport
    :param args: required by Maya to call a function from UI button
    :return:
    """
    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_externalAxes',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the external axis name
    robot_str, axis_name = selection.split(': ')

    # Get selected axis' settings
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]
    axis_info = get_external_axis_info(robot, axis_name)

    # Switch Mimic UI to Update External Axis Mode and populate it with the
    # selected axis' info
    update_external_axis_UI(axis_info)

    # Select the external axis controller in the viewport
    axis_CTRL = axis_info['Driving Controller']
    pm.select(axis_CTRL)


class MimicError(Exception):
    pass
