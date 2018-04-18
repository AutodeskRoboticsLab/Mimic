#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
External Axis Utily Functions.
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


def get_external_axes(robot, only_active=False):
	"""
	Gets all external axes assigned to the given robot
	:param robot: string, name of selected robot
	:param only_active: bool, if True, removes axes marked as "ignore"
	:return robots_external_axes: list, names of all external axes on robot
	"""
	target_CTRL = robot + '|robot_GRP|target_CTRL' 

	# Find all attributes on the target_CTRL marked as 'externalAxis'
	robots_external_axes = pm.listAttr(target_CTRL, category='externalAxis')

	# Remove parent attribute designation 'externalAxis_' from each axis name
	for i, axis_name in enumerate(robots_external_axes):
		robots_external_axes[i] = axis_name.replace('externalAxis_','')
	
	# If only_active is True, remove axes marked as "Ignore"
	if only_active:
		active_external_axes = [x for x in robots_external_axes if not pm.getAttr(target_CTRL + '.' + x + '_ignore')]

		robots_external_axes = active_external_axes

	return robots_external_axes


def get_external_axis_info(robot, external_axis):
	"""
	Get's all of the external axis settings for the input external_axis
	:param robot: string, name of robot
	:param external_axis: string, name of external axis
	"""

	external_axis_info = {}

	axis_attribute_name = '{}|robot_GRP|target_CTRL.{}'.format(robot,
														external_axis) 

	external_axis_info['Robot Name'] = robot
	external_axis_info['Axis Name'] = external_axis
	external_axis_info['Axis Number'] = pm.getAttr(axis_attribute_name
													+ '_axisNumber')
	
	driving_attr_CTRL, driving_attr_name = _get_axis_connections(axis_attribute_name)

	external_axis_info['Driving Controller'] = driving_attr_CTRL
	external_axis_info['Driving Attribute'] = driving_attr_name
	external_axis_info['Position Limit Min'] = pm.getAttr(
													axis_attribute_name
													+ '_axisMin') 
	external_axis_info['Position Limit Max'] = pm.getAttr(
													axis_attribute_name
													+ '_axisMax')
	external_axis_info['Velocity Limit'] = pm.getAttr(axis_attribute_name
													+ '_maxVelocity')
	external_axis_info['Ignore'] = pm.getAttr(axis_attribute_name
													+ '_ignore')

	return external_axis_info


def _get_axis_connections(axis_attribute_name):

	driving_attribute = pm.listConnections(axis_attribute_name
										   + '_position',
										   plugs=True,
										   s=True)[0]

	driving_attr_CTRL, driving_attr_name = driving_attribute.split('.')

	# If the driving attribute is a 'rotate' attribute, there will be a unit 
	# conversion node between the driving attribute and the external axis
	# position attribute, so we iterate once more to get the actual driving
	# controller and attribute
	if 'unitConversion' in driving_attr_CTRL:
		driving_attribute = pm.listConnections(driving_attr_CTRL
											   + '.input',
											   plugs=True,
											   s=True)[0]
		driving_attr_CTRL, driving_attr_name = driving_attribute.split('.')

	return driving_attr_CTRL, driving_attr_name


def _check_external_axis_name(robot, axis_name):
	"""
	Determines if external axis name is unique
	:param robot: string, name of robot
	:return:
	"""

	# Check that axis name isn't already taken
	robots_external_axes = get_external_axes(robot)
	for axis in robots_external_axes:
		if axis == axis_name:
			pm.error('Mimic: external axis name \'{}\' is taken; '\
					 'axis name must be unique'.format(axis_name))


def _check_external_axis_number(robot, axis_number):
	"""
	Determines if external axis number is unique
	:param robot: string, name of robot
	:return:
	"""

	# Check that axis name isn't already taken
	robots_external_axes = get_external_axes(robot)

	target_CTRL = robot + '|robot_GRP|target_CTRL' 
	for axis_name in robots_external_axes:
		current_axis_number = pm.getAttr('{}.{}_axisNumber'.format(target_CTRL,
														   axis_name))
		if current_axis_number == axis_number:
			pm.error('Mimic: external axis number {} is taken; '\
					 'axis number must be unique'.format(axis_number))


def _check_external_axis_params(external_axis_params):
	"""
	Check to ensure that user inputs proper value types for external axis
	parametars
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
		pm.error('{} must have a user input'.format(empty_params))

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
		pm.error('{} must be float(s)'.format(non_float_params))


def _filter_external_axis_name(axis_name):
	"""
	Axis name must be formatted to match Maya's attribute name requirements
	This is typically cameCase. More specifially, the name can't contain spaces
	or special characters
	"""

	# Replace spaces with underscores
	axis_name = axis_name.replace(' ', '_')
	# Remove special characters
	axis_name = ''.join(re.findall(r"[_a-zA-Z0-9]+", axis_name))
	
	return axis_name


def _get_external_axis_params():
	"""
	Finds the user-defined external axis parameters from the Mimic UI
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

    sel = pm.ls(selection=True, type='transform')
    robots = mimic_utils.get_robot_roots()

    # Exception handling
    if not sel:
        pm.error('Nothing selected; ' \
                   'select a valid robot control and external axis controller')
    if not robots:
        pm.error('No robot selected; ' \
                 'select a valid robot')
    if len(robots) > 1:
        pm.error('Too many robots selected; ' \
                 'select a single robot')
    if len(sel) > 2:
        pm.error('Too many selections; ' \
                 'select a single robot control, ' \
                 'and single external axis controller')
    if len(sel) == 1:
        pm.error('Not enough selections; ' \
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
	:return:
	"""

	# Create parent constraint between robot base's local control and
	# external axis control
	local_CTRL = robot + '|robot_GRP|local_CTRL'
	pm.parentConstraint(external_axis_CTRL,
						local_CTRL,
						maintainOffset=True,
						name='localCTRL_externalAxisCTRL_parentConstraint')

	# Hide robot's local_CTRL
	pm.setAttr(local_CTRL + '.v', 0)


def add_external_axis(*args):

	# Get the External Axis' parameters from the Mimic UI
	external_axis_params = _get_external_axis_params()

	axis_name = external_axis_params['Axis Name']
	axis_number = external_axis_params['Axis Number']
	driving_attribute = external_axis_params['Driving Attribute']
	position_limit_min = external_axis_params['Position Limit Min']
	position_limit_max = external_axis_params['Position Limit Max']
	velocity_limit = external_axis_params['Velocity Limit']
	attach_robot_to_external = external_axis_params['Attach']
	ingnore_in_postproc = external_axis_params['Ignore']


	# Get and check the proper controllers from viewport selection
	robot, external_axis_CTRL = _get_selection_input()

	target_CTRL = '{}|robot_GRP|target_CTRL'.format(robot)

	# Ensure axis name is unique
	_check_external_axis_name(robot, axis_name)

	# Check that the external axis number is unique
	_check_external_axis_number(robot, axis_number)

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

	# Set all External Axis attributes accordingly
	axis_parent_attribute = target_CTRL + '.' + axis_name
	pm.setAttr(axis_parent_attribute + '_axisNumber', axis_number, lock=True)
	pm.setAttr(axis_parent_attribute + '_axisMin', position_limit_min)
	pm.setAttr(axis_parent_attribute + '_axisMax', position_limit_max)
	pm.setAttr(axis_parent_attribute + '_maxVelocity', velocity_limit)
	pm.setAttr(axis_parent_attribute + '_ignore', ingnore_in_postproc)


	# Connect position attribute to driving attribute
	driving_attribute_name = external_axis_CTRL + '.' + driving_attribute
	destination_attribute_name = axis_parent_attribute + '_position'
	pm.connectAttr(driving_attribute_name,
				   destination_attribute_name)
	
	# If attach to robot is true, parent the robot's local control to the 
	# external axis controller
	if attach_robot_to_external:
		_attach_robot_to_external_axis(robot, external_axis_CTRL)

	# Select the robot's target/tool controller
	tool_CTRL = robot + '|robot_GRP|tool_CTRL'
	if pm.objExists(tool_CTRL):
		pm.select(tool_CTRL)
	else:
		pm.select(target_CTRL)


	pm.headsUpMessage('Mimic: external axis {} added successfully'
					  .format(axis_name))


def clear_external_axis_list(*args):
	# Clear previus UI list
	pm.textScrollList('tsl_externalAxes', edit=True, removeAll=True)
	reset_external_axis_UI()


def deselect_external_axis(*args):
	# Clear UI list selection
	pm.textScrollList('tsl_externalAxes', edit=True, deselectAll=True)
	reset_external_axis_UI()


def list_axes(*args):
	# Clear previus UI list
	clear_external_axis_list()

	# Check viewport selection for a single robot
	robots = mimic_utils.get_robot_roots()
	if not mimic_utils.check_robot_selection(number_of_robots=1):
		pm.error('Mimic: must select exactly one robot')

	robot = robots[0]

	# Get list of all external axes on robot
	robots_external_axes = get_external_axes(robot)
	
	# Update Mimic UI with list of external axes
	for axis in robots_external_axes:
		append_string = robot + ': ' + axis
		pm.textScrollList('tsl_externalAxes', edit=True, append=append_string)



def update_external_axis_UI(axis_info):

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

	pm.textField('t_externalAxisLimitMin',
				 edit=True,
				 text=str(axis_info['Position Limit Min']))
	pm.textField('t_externalAxisLimitMax',
				 edit=True,
				 text=str(axis_info['Position Limit Max']))
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
			  #command=mimic_external_axes.update_external_axis
			  )


def reset_external_axis_UI():
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

	# Get the selected item from the Mimic UI
	selection = pm.textScrollList('tsl_externalAxes',
								  selectItem=True,
								  query=True)[0]

	# Split the selection into the robot's name and the external axis name
	robot, axis_name = selection.split(': ')

	# Get selected axis' settings
	axis_info = get_external_axis_info(robot, axis_name)

	# Switch Mimic UI to Update External Axis Mode and populate it with the
	# selected axis' info
	update_external_axis_UI(axis_info)

	# Select the external axis controller in the viewport
	axis_CTRL = axis_info['Driving Controller']
	pm.select(axis_CTRL)