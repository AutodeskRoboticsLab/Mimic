#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions that actually make mFIZ work.
"""

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

# General Imports
from collections import namedtuple

# mFIZ_imports
import mFIZ_config

reload(mFIZ_config)

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
    ctrl = pm.spaceLocator(name=name)
    
    # Lock and hide all default keyable attributes
    keyable_attrs = ctrl.listAttr(keyable=True)
    for attr in keyable_attrs:
        pm.setAttr(attr, k=False, lock=True, channelBox=False)
    
    # Unlock visibility so we can connect to it later
    pm.setAttr(ctrl.visibility, lock=False)
    
    # Add FIZ attrs
    fiz_attrs = FIZ_ATTRS
    fiz_attr_type = 'float'
    fiz_attr_min = 0
    fiz_attr_max = 1
    
    for attr in fiz_attrs:
        ctrl.addAttr(attr, attributeType=fiz_attr_type, minValue=fiz_attr_min, maxValue=fiz_attr_max, keyable=True)
        
    # Add a message(s) attribute to link it to the mFIZ node
    mssg_attr_name = 'mFIZ_node'
    mssg_attr_nice_name = 'mFIZ Node'
    
    ctrl.addAttr(mssg_attr_name, niceName=mssg_attr_nice_name, attributeType='message')
    
    return ctrl
    
    
def _create_mFIZ_node(name):
    """
    """
    name += '_NODE_0'
    node = pm.createNode('mFIZ', name=name)
    
    return node
    

def _connect_controller_to_node(ctrl, node):
    """
    """    
    pm.connectAttr(ctrl.mFIZ_node, node.controller, f=True)

    # Connect FIZ attrs from controller to node
    fiz_attrs = FIZ_ATTRS

    for attr in fiz_attrs:
        ctrl_attr = '{}.{}'.format(ctrl, attr)
        node_attr = '{}.{}'.format(node, attr)
        
        pm.connectAttr(ctrl_attr, node_attr)
        
    # Connect node data sent signal to controller visibility
    # This ensures that the node is computed 
    pm.connectAttr(node.dataSent, ctrl.visibility)
    pm.setAttr(ctrl.visibility, lock=True)
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
    anim_curves = [curve for curve in pm.ls(type="animCurve")]
 
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

    anim_curve.setAttr('useCurveColor', True)
    anim_curve.setAttr('curveColor', mFIZ_config.ANIM_CURVE_COLORS[attr])
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
        if not pm.pluginInfo(plugin, query=True, loaded=True):
            try:
                # Try loading it (and turn on autoload)
                pm.loadPlugin(plugin)
                pm.pluginInfo(plugin, autoload=True)
                print '{} Plug-in loaded'.format(plugin)
            except Exception:  # Unknown error
                pass


def get_mFIZ_version():
    """
    Returns mFIZ version from .mod file as a formatted string.
    :return:
    """
    return pm.moduleInfo(version=True, moduleName='mFIZ')


def get_mFIZ_module_dir():
    """
    Returns mFIZ module directory as a formatted string.
    :return:
    """
    return pm.moduleInfo(path=True, moduleName='mFIZ')  
# --------------------------------------------------------- #


# --------------------------------------------------------- #
def get_all_controllers():
    """
    """
    mFIZ_nodes = pm.ls(type='mFIZ')

    mFIZ_controllers = []

    for node in mFIZ_nodes:
        ctrl = node.controller.get()

        controller = mFIZ_controller(ctrl, node)
        mFIZ_controllers.append(controller)

    return mFIZ_controllers


def is_mFIZ_ctrl(node):
    """
    Checks if input argument is an mFIZ controller
    """
    return pm.attributeQuery('mFIZ_node', node=node, exists=True)


class mFIZError(Exception):
    pass
