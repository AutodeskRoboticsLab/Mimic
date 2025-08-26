#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions that actually make mFIZ work.
"""

try:
    import maya.cmds as cmds

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    cmds = None
    MAYA_IS_RUNNING = False

# General Imports
from collections import namedtuple

# mFIZ_imports
import mFIZ_config
import importlib

importlib.reload(mFIZ_config)

FIZ_ATTRS = mFIZ_config.FIZ_ATTRS


mFIZ_controller = namedtuple('mFIZ_controller', ['ctrl', 'node'])


# --------------------------------------------------------- #
def add_mFIZ_controller_to_scene(name):
    """
    """
    ctrl = _create_mFIZ_controller(name)
    node = _create_mFIZ_node(name)

    _connect_controller_to_node(ctrl, node)

    return mFIZ_controller(ctrl, node)


def _create_mFIZ_controller(name):
    """
    """
    name += '_CTRL_0'
    ctrl = cmds.spaceLocator(name=name)[0]
    
    # Lock and hide all default keyable attributes
    keyable_attrs = cmds.listAttr(ctrl, keyable=True)
    if keyable_attrs:
        for attr in keyable_attrs:
            cmds.setAttr('{}.{}'.format(ctrl, attr), keyable=False, lock=True, channelBox=False)
    
    # Unlock visibility so we can connect to it later
    cmds.setAttr('{}.visibility'.format(ctrl), lock=False)
    
    # Add FIZ attrs
    fiz_attrs = FIZ_ATTRS
    fiz_attr_type = 'float'
    fiz_attr_min = 0
    fiz_attr_max = 1
    
    for attr in fiz_attrs:
        cmds.addAttr(ctrl, longName=attr, attributeType=fiz_attr_type, minValue=fiz_attr_min, maxValue=fiz_attr_max, keyable=True)
        
    # Add a message(s) attribute to link it to the mFIZ node
    mssg_attr_name = 'mFIZ_node'
    mssg_attr_nice_name = 'mFIZ Node'
    
    cmds.addAttr(ctrl, longName=mssg_attr_name, niceName=mssg_attr_nice_name, attributeType='message')
    
    return ctrl
    
    
def _create_mFIZ_node(name):
    """
    """
    name += '_NODE_0'
    node = cmds.createNode('mFIZ', name=name)
    
    return node
    

def _connect_controller_to_node(ctrl, node):
    """
    """    
    cmds.connectAttr('{}.mFIZ_node'.format(ctrl), '{}.controller'.format(node), f=True)

    # Connect FIZ attrs from controller to node
    fiz_attrs = FIZ_ATTRS

    for attr in fiz_attrs:
        ctrl_attr = '{}.{}'.format(ctrl, attr)
        node_attr = '{}.{}'.format(node, attr)
        
        cmds.connectAttr(ctrl_attr, node_attr)
        
    # Connect node data sent signal to controller visibility
    # This ensures that the node is computed 
    cmds.connectAttr('{}.dataSent'.format(node), '{}.visibility'.format(ctrl))
    cmds.setAttr('{}.visibility'.format(ctrl), lock=True)
# --------------------------------------------------------- #


# --------------------------------------------------------- #
def anim_curve_exists(attr_curve_name):
    """
    """
    anim_curve = get_anim_curve(attr_curve_name)

    if not anim_curve:
        return True
    else:
        return False


def get_anim_curve(attr_curve_name):
    """
    """
    anim_curve = None

    # Get a list of all animCurves
    anim_curves = cmds.ls(type="animCurve") or []
 
    # Check if the attr curve name exists in any of the anim curves
    # We do this as a list comprehension to make sure it retruns true if the
    # attr_curve_name exists in any part of the anim_curve_name
    try:
        anim_curve = [curve for curve in anim_curves if attr_curve_name in str(curve)][0]
    except IndexError:
        pass

    return anim_curve


def set_curve_color(attr_curve_name, attr):
    """
    """
    anim_curve = get_anim_curve(attr_curve_name)

    # Make sure the curve exists, just in case
    if not anim_curve:
        return

    cmds.setAttr('{}.useCurveColor'.format(anim_curve), True)
    color = mFIZ_config.ANIM_CURVE_COLORS[attr]
    cmds.setAttr('{}.curveColor'.format(anim_curve), color[0], color[1], color[2], type='double3')
# --------------------------------------------------------- #


# --------------------------------------------------------- #
def load_mFIZ_plugins():
    """
    Loads required python plugins into Maya from a directory.
    These are Dependency Graph and Command plugins that should be loaded into
    Maya's plugin manager
    :return:
    """
    # Plugin is dependent on the following scripts
    required_plugins = mFIZ_config.REQUIRED_PLUGINS

    # Check to see if each plug-in is loaded
    for plugin in required_plugins:
        # If the plug-in is not loaded:
        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            try:
                # Try loading it (and turn on autoload)
                cmds.loadPlugin(plugin)
                cmds.pluginInfo(plugin, autoload=True)
                print('{} Plug-in loaded'.format(plugin))
            except Exception:  # Unknown error
                pass


def get_mFIZ_version():
    """
    Returns mFIZ version from .mod file as a formatted string.
    :return:
    """
    return cmds.moduleInfo(version=True, moduleName='mFIZ')


def get_mFIZ_module_dir():
    """
    Returns mFIZ module directory as a formatted string.
    :return:
    """
    return cmds.moduleInfo(path=True, moduleName='mFIZ')  
# --------------------------------------------------------- #


# --------------------------------------------------------- #
def get_all_controllers():
    """
    """
    mFIZ_nodes = cmds.ls(type='mFIZ') or []

    mFIZ_controllers = []

    for node in mFIZ_nodes:
        ctrl_connections = cmds.listConnections('{}.controller'.format(node))
        if not ctrl_connections:
            continue
        ctrl = ctrl_connections[0]

        controller = mFIZ_controller(ctrl, node)
        mFIZ_controllers.append(controller)

    return mFIZ_controllers


def is_mFIZ_ctrl(node):
    """
    Checks if input argument is an mFIZ controller
    """
    return cmds.attributeQuery('mFIZ_node', node=node, exists=True)


class mFIZError(Exception):
    pass
