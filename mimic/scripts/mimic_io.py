#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
IO Utility Functions.
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


def get_io_names(robot_name, only_active=False):
    """
    Gets all IOs assigned to the given robot
    :param robot_name: string, name of selected robot
    :param only_active: bool, if True, removes IOs marked as "ignore"
    :return robots_ios: list, names of all IOs on robot
    """

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)

    # Find all attributes on the target_CTRL categorized as 'io'
    robot_io_names = pm.listAttr(target_ctrl_path, category='io')

    # Remove parent attribute designation 'io_' from each IO name
    for i, io_name in enumerate(robot_io_names):
        robot_io_names[i] = io_name.replace('io_', '')

    # If only_active is True, remove IOs marked as "Ignore"
    if only_active:
        active_ios = [x for x in robot_io_names if not pm.getAttr(target_ctrl_path + '.' + x + '_ignore')]

        robot_io_names = active_ios

    return robot_io_names


def get_io_info(robot_name, io_name):
    """
    Get's all of the IO settings for the input IO name
    :param robot_name: string, name of robot
    :param io_name: string, name of IO
    :return info: dict, dictionary of input IO setting
    """

    info = {}

    io_path = _get_io_path(robot_name, io_name)

    info['Robot Name'] = robot_name
    info['IO Name'] = io_name
    info['IO Number'] = _get_io_number(io_path)
    info['Postproc ID'] = _get_postproc_id(io_path)
    info['Type'] = _get_io_type(io_path)
    info['Ignore'] = _get_io_ignore(io_path)

    return info


def get_io_info_simple(robot_name, io_name, frame=None):
    """
    Get a few of the IO settings for the input IO.
    :param robot_name: string, name of robot
    :param io_name: string, name of IO
    :param frame: optional frame parameter
    :return info_simple: dict, dictionary of input IO' setting
    """
    info_simple = {}
    io_path = _get_io_path(robot_name, io_name)
    info_simple['IO Number'] = _get_io_number(io_path)
    info_simple['Postproc ID'] = _get_postproc_id(io_path)
    info_simple['Type'] = _get_io_type(io_path)
    info_simple['Value'] = _get_io_value(io_path, frame)
    info_simple['Ignore'] = _get_io_ignore(io_path)
    return info_simple


def _get_io_path(robot_name, io_name):
    """
    Get the path for an IO.
    :param robot_name: string, name of robot
    :param io_name: string, name of IO
    :return: str, IO attribute path
    """
    return '{}.{}'.format(mimic_utils.get_target_ctrl_path(robot_name), io_name)


def _get_io_type(io_path):
    """
    Get the IO type.
    :param io_path: string, attribute path using robot and IO names
    :return io_type: string, e.g. 'digital' or 'analog'
    """

    attribute_path = io_path + '_value'

    if pm.getAttr(attribute_path, type=True) == 'bool':
        io_type = 'digital'
    else:
        io_type = 'analog'

    return io_type


def _get_io_value(io_path, frame=None):
    """
    Get the value of an IO.
    :param io_path: string, attribute path using robot and IO names
    :param frame: optional frame parameter
    :return io_value: int, 0 or 1 if io type is 'digital'; float otherwise
    """
    attribute_path = io_path + '_value'
    io_value = mimic_utils.get_attribute_value(attribute_path, frame)

    return io_value


def _get_postproc_id(io_path):
    """
    Get the value of an IO.
    :param io_path: string, attribute path using robot and IO names
    :return postproc_id: str
    """
    attribute_path = io_path + '_postprocID'

    return pm.getAttr(attribute_path)


def _get_io_number(io_path):
    """
    Get the number for an IO. 1-indexed!
    :param io_path: string, attribute path using robot and IO names
    :return: int, IO number
    """
    attribute_path = io_path + '_ioNumber'
    return mimic_utils.get_attribute_value(attribute_path)


def _get_io_ignore(io_path):
    """
    Get the ignore (is-ignored) value for an IO
    :param io_path: string, attribute path using robot and IO names
    :return: bool, True if "Ignore IO" is checked, false if not
    """
    attribute_path = io_path + '_ignore'
    return mimic_utils.get_attribute_value(attribute_path)


# ------------------


def _check_io_name(robot_name, io_name):
    """
    Determines if IO name is unique
    Raises an Exception if the input name is already taken by another
    IO on the input robot
    :param robot_name: string, name of robot
    :param io_name: str, filtered user-supplied IO name
    """

    # Check that io name isn't already taken
    robots_ios = get_io_names(robot_name)
    for io in robots_ios:
        if io == io_name:
            raise MimicError('IO name \'{}\' is taken; ' \
                             'io name must be unique'.format(io_name))


def _check_io_number(robot_name, io_number):
    """
    Determines if IO number is unique
    Raises an Exception if the input io number is already taken by another
    IO on the input robot
    :param robot_name: string, name of robot
    :param io_number: int, user-supplied IO number
    """

    # Check that io name isn't already taken
    robots_ios = get_io_names(robot_name)

    target_ctrl_path = mimic_utils.get_target_ctrl_path(robot_name)
    for io_name in robots_ios:
        current_io_number = pm.getAttr('{}.{}_ioNumber'.format(target_ctrl_path, io_name))
        if current_io_number == io_number:
            raise MimicError('IO number {} is taken; ' \
                             'io number must be unique'.format(io_number))


def _check_io_params(io_params):
    """
    Check to ensure that user inputs proper value types for IO parameters.
    Raises exceptions if criteria are not met
    """

    # Make sure the following parameters have user inputs
    must_have_input = ['IO Name', 'Postproc ID']

    empty_params = []
    for param in must_have_input:
        if not io_params[param]:
            empty_params.append(param)

    if empty_params:
        raise MimicError('{} must have a user input'.format(empty_params))


def _filter_io_name(io_name):
    """
    IO name must be formatted to match Maya's attribute name requirements
    This is typically came'Case. More specifically, the name can't contain spaces
    or special characters
    :param io_name: str, raw user input for IO name
    :return io_name: str, filtered string for user-supplied io name
    """

    # Replace spaces with underscores
    io_name = io_name.replace(' ', '_')
    # Remove special characters
    io_name = ''.join(re.findall(r"[_a-zA-Z0-9]+", io_name))

    return io_name


def _get_io_params():
    """
    Finds the user-defined IO parameters from the Mimic UI
    Checks that user inputs meet parameter riteria 
    :return io_param_dict: dict containing IO params
        "IO Name" (str)
        "Postproc ID" (str)
        "IO Number" (int)
        "Type" (str)
        "Ignore" (bool)
    """

    io_param_dict = {}

    io_param_dict['IO Name'] = pm.textField(
        't_ioNameText',
        query=True,
        text=True)
    io_param_dict['Postproc ID'] = pm.textField(
        't_ioPostprocIDText',
        query=True,
        text=True)
    io_param_dict['IO Number'] = int(pm.optionMenu(
        'ioNumberMenu',
        query=True,
        value=True))
    io_param_dict['Type'] = pm.optionMenu(
        'ioTypeMenu',
        query=True,
        value=True)
    io_param_dict['Ignore'] = pm.checkBox(
        'cb_ignoreIO',
        query=True,
        value=True)

    _check_io_params(io_param_dict)

    # Ensure IO name input complies with Maya's attribute name requirements
    io_name = io_param_dict['IO Name']
    io_param_dict['IO Name'] = _filter_io_name(io_name)

    return io_param_dict


def _get_selection_input():
    """
    Takes Maya's viewport selection and filters it to a robot.
    Raises exception of selection criteria is not met
    :return robot: str, root node of robot in Maya viewport selection
    """
    sel = pm.ls(selection=True, type='transform')
    robots = mimic_utils.get_robot_roots()

    # Exception handling
    if not robots:
        raise MimicError('No robot selected; ' \
                         'select a valid robot')
    if len(robots) > 1:
        raise MimicError('Too many robots selected; ' \
                         'select a single robot')

    robot = robots[0]

    return robot


def add_io(*args):
    """
    Adds an IO to a robot based on user inputs in Mimic UI.
    :param args: required by Maya to call a function from UI button
    """
    # Get the IO's parameters from the Mimic UI
    io_params = _get_io_params()

    io_name = io_params['IO Name']
    io_number = io_params['IO Number']
    postproc_id = io_params['Postproc ID']
    io_type = io_params['Type']
    ignore_in_postproc = io_params['Ignore']

    # Get and check the proper controllers from viewport selection
    robot = _get_selection_input()

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    # Ensure IO name is unique
    _check_io_name(robot, io_name)

    # Check that the IO number is unique
    _check_io_number(robot, io_number)

    # Establish attribute type from input Type
    if io_type == 'digital':
        attr_type = 'bool'
    else:
        attr_type = 'float'

    # Add attributes to robots
    # Parent Attrubute
    parent_attribute = 'io_{}'.format(io_name)
    pm.addAttr(target_CTRL,
               longName=parent_attribute,
               niceName='IO: {}'.format(io_name),
               numberOfChildren=4,
               category='io',
               attributeType='compound')
    # Define 4 children of the IO parent attribute
    pm.addAttr(target_CTRL,
               longName=io_name + '_value',
               niceName=io_name,
               keyable=True,
               attributeType=attr_type,
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=io_name + '_postprocID',
               niceName='Postproc ID',
               keyable=False,
               dataType='string',
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=io_name + '_ioNumber',
               niceName='IO Number',
               keyable=False,
               attributeType='long',
               minValue=1,
               maxValue=12,
               defaultValue=1,
               parent=parent_attribute)
    pm.addAttr(target_CTRL,
               longName=io_name + '_ignore',
               niceName='Ignore',
               keyable=False,
               attributeType='bool',
               parent=parent_attribute)

    # Set all IO attributes accordingly
    io_parent_attribute = target_CTRL + '.' + io_name
    
    pm.setAttr(io_parent_attribute + '_ioNumber', io_number)
    
    # Try locking the io_number attribute
    try:
        # If the robot is referenced, Maya will throw an exception when it
        # tries to lock an attribute
        pm.setAttr(io_parent_attribute + '_ioNumber', lock=True)
    except:
        pass

    pm.setAttr(io_parent_attribute + '_postprocID', postproc_id)
    pm.setAttr(io_parent_attribute + '_ignore', ignore_in_postproc)

    # Select the robot's target/tool controller
    tool_CTRL = mimic_utils.get_tool_ctrl_path(robot)
    if pm.objExists(tool_CTRL):
        pm.select(tool_CTRL)
    else:
        pm.select(target_CTRL)

    list_ios()
    pm.headsUpMessage('IO \'{}\' added successfully to {}'
                      .format(io_name, robot))


def update_io(*args):
    """
    Updates an IO based on user inputs in Mimic UI.
    :param args: required by Maya to call a function from UI button
    """
    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_ios',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the IO name
    robot_str, io_name = selection.split(': ')
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]

    io_params = _get_io_params()

    io_number = io_params['IO Number']
    postproc_id = io_params['Postproc ID']
    io_type = io_params['Type']
    ignore_in_postproc = io_params['Ignore']

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    # Set all IO attributes accordingly
    io_parent_attribute = target_CTRL + '.' + io_name

    # Check that the IO number is unique
    if io_number == pm.getAttr(io_parent_attribute + '_ioNumber'):
        pass
    else:
        _check_io_number(robot, io_number)

    # Set all appropriate attributes on the robot
    # If the robot is referenced, Maya will throw an exceptrion when it
    # tries to lock an attribute
    try:
        pm.setAttr(io_parent_attribute + '_ioNumber', lock=False)
    except:
        pass

    pm.setAttr(io_parent_attribute + '_ioNumber', io_number)
    
    try:
        pm.setAttr(io_parent_attribute + '_ioNumber', lock=True)
    except:
        pass

    pm.setAttr(io_parent_attribute + '_postprocID', postproc_id)
    pm.setAttr(io_parent_attribute + '_ignore', ignore_in_postproc)

    pm.headsUpMessage('{}: IO \'{}\' successfully updated'
                      .format(robot, io_name))

    pm.select(target_CTRL)


def clear_io_list(*args):
    """
    Clears IO list in Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    pm.textScrollList('tsl_ios', edit=True, removeAll=True)
    reset_io_UI()


def deselect_io(*args):
    """
    Deselects item from IO list in Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    pm.textScrollList('tsl_ios', edit=True, deselectAll=True)
    reset_io_UI()


def remove_io(*args):
    """
    Removes IO from the robot it's attached to by deleting all of
    its attributes. The io controller and models are preserved.
    This function just breaks the connection between the robot and the io
    controller
    :param args: required by Maya to call a function from UI button required by Maya UI
    :return:
    """

    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_ios',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the IO name
    robot_str, io_name = selection.split(': ')
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]

    target_CTRL = mimic_utils.get_target_ctrl_path(robot)

    parent_attribute = '{}.io_{}'.format(target_CTRL, io_name)

    # Delete IO attribute on the robot controller
    pm.deleteAttr(parent_attribute)

    # Clear the io from the Mimic UI selection and reset the UI
    pm.textScrollList('tsl_ios',
                      edit=True,
                      removeItem=selection)
    if not pm.textScrollList('tsl_ios',
                             query=True,
                             numberOfItems=True):
        reset_io_UI()

    pm.select(target_CTRL)
    pm.headsUpMessage('IO \'{}\' removed successfully from {}'
                      .format(io_name, robot))


def list_ios(*args):
    """
    If no robot is selected, prints list of all IO in scene to Mimic UI
    If robot is selected, prints IOs assigned to that robot to Mimic UI
    :param args: required by Maya to call a function from UI button
    :return:
    """
    # Clear previous UI list
    clear_io_list()

    # Check viewport robot selection
    # If robots are selected, list all IOs on selected robots
    selected_robots = mimic_utils.get_robot_roots()
    if selected_robots:
        robots = selected_robots
    # If no robots are selected, list all IOs in the scene
    else:
        robots_in_scene = mimic_utils.get_robot_roots(all_robots=True)
        # If there are no robots in the scene, raise an exception
        if not robots_in_scene:
            raise MimicError('No robots in scene')
        else:
            robots = robots_in_scene

    # Keep track of selected robots without IOs for a heads-up message
    selected_robots_without_ios = []

    # For each robots, get a list of all its IOs
    for robot in robots:
        robots_ios = get_io_names(robot)

        # If we're only looking at selected robots, check if each selected
        # robot has IOs. If not, add it to a list to display in
        # a heads up message
        if selected_robots:
            if not robots_ios:
                selected_robots_without_ios.append(robot)

        # Update Mimic UI with list of IOs
        for io in robots_ios:
            append_string = robot + ': ' + io
            pm.textScrollList('tsl_ios',
                              edit=True,
                              append=append_string)

    if selected_robots_without_ios:
        robot_list_str = ''
        for each in selected_robots_without_ios:
            robot_list_str += each + ', '

        pm.headsUpMessage('{} has no IOs'
                          .format(robot_list_str))


def update_io_UI(io_info):
    """
    Updates IO inputs of Mimic UI based on IO selection
    in io list
    :param io_info: dict containing info about selected io
    :return:
    """
    # Change frame name from "Add" to "Update"
    pm.frameLayout('add_io_frame',
                   edit=True,
                   label="Update IO")

    # Update io parameters
    pm.textField('t_ioNameText',
                 edit=True,
                 text=io_info['IO Name'],
                 editable=False)
    pm.textField('t_ioPostprocIDText',
                 edit=True,
                 text=io_info['Postproc ID'])
    pm.optionMenu('ioNumberMenu',
                  edit=True,
                  value=str(io_info['IO Number']))
    pm.optionMenu('ioTypeMenu',
                  edit=True,
                  value=io_info['Type'],
                  enable=False)
    pm.checkBox('cb_ignoreIO',
                edit=True,
                value=io_info['Ignore'])

    # Change "Add IO" button to "Update IO"
    # Change background color of button
    pm.button('b_add_io',
              edit=True,
              label='Update IO',
              backgroundColor=[.7, .7, .7],
              command=update_io)


def reset_io_UI():
    """
    Restores IO UI inputs in Mimic UI to defaults
    :return:
    """
    pm.frameLayout('add_io_frame',
                   edit=True,
                   label="Add IO")

    # Update io parameters
    pm.textField('t_ioNameText',
                 edit=True,
                 text='',
                 editable=True)
    pm.textField('t_ioPostprocIDText',
                 edit=True,
                 text='',
                 editable=True)
    pm.optionMenu('ioNumberMenu',
                  edit=True,
                  value='1')
    pm.optionMenu('ioTypeMenu',
                  edit=True,
                  value='digital',
                  enable=True)
    pm.checkBox('cb_ignoreIO',
                edit=True,
                value=0)

    # Change "Add IO" button to "Update IO"
    # Change background color of button
    pm.button('b_add_io',
              edit=True,
              label='Add IO',
              backgroundColor=[.361, .361, .361],
              command=add_io)


def io_selected(*args):
    """
    Command that is called when an io is selected in IO list
    in Mimic UI, which gets the IO name and info, and updates
    the IO Mimic UI accordingly
    Selects the io controller in Maya's viewport
    :param args: required by Maya to call a function from UI button
    :return:
    """
    # Get the selected item from the Mimic UI
    selection = pm.textScrollList('tsl_ios',
                                  selectItem=True,
                                  query=True)[0]

    # Split the selection into the robot's name and the IO name
    robot_str, io_name = selection.split(': ')

    # Get selected io' settings
    pm.select(robot_str)
    robot = mimic_utils.get_robot_roots()[0]
    io_info = get_io_info(robot, io_name)

    # Switch Mimic UI to Update IO Mode and populate it with the
    # selected io' info
    update_io_UI(io_info)

    # Select the robot that the IO is assigned to
    target_CTRL = mimic_utils.get_target_ctrl_path(robot)
    pm.select(target_CTRL)


class MimicError(Exception):
    pass
