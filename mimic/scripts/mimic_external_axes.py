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
    robot = mimic_utils.get_robot_roots()

    # Exception handling
    if not sel:
        pm.error('Nothing selected; ' \
                   'select a valid robot control and external axis controller')
    if not robot:
        pm.error('No robot selected; ' \
                 'select a valid robot')
    if len(robot) > 1:
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

    robot_CTRL = '{}|robot_GRP|target_CTRL'.format(robot[0])

    # find which selected object is the external axis controller
    if not mimic_utils.get_robot_roots(0, [sel[0]]):
        external_axis_CTRL = sel[0]
    else:
        external_axis_CTRL = sel[1]

    return robot_CTRL, external_axis_CTRL


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
	robot_CTRL, external_axis_CTRL = _get_selection_input()

	# Add attributes to robots
	# Parent Attrubute
	parent_attribute = 'externalAxis_{}'.format(axis_name)
	pm.addAttr(robot_CTRL,
			   longName=parent_attribute,
			   niceName='External Axis: {}'.format(axis_name),
			   numberOfChildren=6,
			   category='externalAxis',
			   attributeType='compound')
	# Define 6 children of the External Axis parent attribute
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_position',
			   niceName='Position',
			   keyable=False, attributeType='float',
			   parent=parent_attribute)
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_axisNumber',
			   niceName='Axis Number',
			   keyable=False,
			   attributeType='long',
			   minValue=1,
			   maxValue=6,
			   defaultValue=1,
			   parent=parent_attribute)
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_axisMin',
		       niceName='Min',
		       keyable=False,
		       attributeType='float',
		       parent=parent_attribute)
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_axisMax',
			   niceName='Max',
			   keyable=False,
			   attributeType='float',
			   parent=parent_attribute)
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_maxVelocity',
			   niceName='Max Velocity',
			   keyable=False,
			   attributeType='float',
			   parent=parent_attribute)
	pm.addAttr(robot_CTRL,
			   longName=axis_name + '_ignore',
			   niceName='Ignore',
			   keyable=False,
			   attributeType='bool',
			   parent=parent_attribute)

	# Set all External Axis attributes accordingly
	axis_parent_attribute = robot_CTRL + '.' + axis_name
	pm.setAttr(axis_parent_attribute + '_axisNumber', axis_number, lock=True)
	pm.setAttr(axis_parent_attribute + '_axisMin', position_limit_min)
	pm.setAttr(axis_parent_attribute + '_axisMax', position_limit_max)
	pm.setAttr(axis_parent_attribute + '_maxVelocity', velocity_limit)
	pm.setAttr(axis_parent_attribute + '_ignore', ingnore_in_postproc)

	print 'Mimic: external axis {} added successfully'.format(axis_name)

	# Connect position attribute to driving attribute
	driving_attribute_name = external_axis_CTRL + '.' + driving_attribute
	destination_attribute_name = axis_parent_attribute + '_position'
	pm.connectAttr(driving_attribute_name,
				   destination_attribute_name)
	
	# If attach to robot is true, parent the robot's local control to the 
	# external axis controller