#!usr/bin/env python

"""
Dependency Graph plug-in that allows the physical rotational limits of the
robot rig to be taken into account when performing an Inverse Kinematic solve.
"""

import sys
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim
import math


##### Change name to something with "Dynamics"

def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# Plug-in information:
kPluginNodeName = 'robotAxisDynamics'  # The name of the node.
kPluginNodeClassify = 'utility/general'  # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId(0x87002)  # A unique ID associated to this node type.


# ==========================================#
#                Plug-in                   #
# ==========================================#
class robotAxisDynamics(OpenMaya.MPxNode):
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    pos_attr = OpenMaya.MAngle()

    live_attr = OpenMaya.MObject()

    # Outputs
    vel_attr = OpenMaya.MObject()
    accel_attr = OpenMaya.MObject()
    jerk_attr = OpenMaya.MObject()

    def __init__(self):
        OpenMaya.MPxNode.__init__(self)

    ##################################################

    def compute(self, pPlug, pDataBlock):

        ## Obtain the data handles for each attribute
        # Input Data Handles
        # pos_data_handle = pDataBlock.inputValue(robotAxisDynamics.pos_attr)
        live_data_handle = pDataBlock.inputValue(robotAxisDynamics.live_attr)

        pos_array_data_handle = pDataBlock.inputArrayValue(robotAxisDynamics.pos_attr)
        num_elements = len(pos_array_data_handle)

        # Output Data Handles
        # vel_data_handle = pDataBlock.outputValue(robotAxisDynamics.vel_attr)
        accel_data_handle = pDataBlock.outputValue(robotAxisDynamics.accel_attr)
        jerk_data_handle = pDataBlock.outputValue(robotAxisDynamics.jerk_attr)

        vel_array_data_handle = pDataBlock.outputArrayValue(robotAxisDynamics.vel_attr)

        ## Extract the actual value associated to our input attribute
        # pos = pos_data_handle.asAngle().asDegrees()
        live = live_data_handle.asBool()

        # ==================================#
        #     Limit Blender Solve Code     #
        # ==================================#
        if live:

            for i in range(num_elements):
                pos_array_data_handle.jumpToLogicalElement(i)
                pos_data_handle = pos_array_data_handle.inputValue()

                axis_i_pos = pos_data_handle.asAngle().asDegrees()

                try:
                    vel_array_data_handle.jumpToLogicalElement(i)
                    vel_data_handle = vel_array_data_handle.outputValue()
                except:
                    vel_data_handle = vel_array_data_handle.builder().addElement(i)

                # Convert to MAngle data type for output
                # (the "2" is for data type degrees. 1 = radians)
                # axis_i_vel = OpenMaya.MAngle(axis_i_pos - 10, 2)

                # Set the Output Values
                # vel_data_handle.setMAngle(axis_i_vel)
                print "Pos: {} | Vel: {}".format(axis_i_pos, axis_i_pos - 10)
                vel_data_handle.setFloat(axis_i_pos - 10)

                # if not vel_array_data_handle.next():
                #     vel_array_data_handle.builder().growArray(1)

            # TODO Go back to original way of accessing input plug elements, but use output array builder to add
            # Corresponding output elements

            # obj = self.thisMObject()
            # objMfn = OpenMaya.MFnDependencyNode(obj)
            #
            # ## Get the plug of the node. (networkedplug = False, as it no longer profides a speed improvement)
            # plug = objMfn.findPlug('position', False)
            #
            # axis_position_indices = plug.getExistingArrayAttributeIndices()
            #
            # if axis_position_indices:
            #     axis_position_connections = []
            #
            #     # Get the current time
            #     time_0 = OpenMayaAnim.MAnimControl.currentTime()
            #
            #     time__2 = time_0 - 2
            #     time__1 = time_0 - 1
            #     time_1 = time_0 + 1
            #     time_2 = time_0 + 2
            #
            #     delta_t_sec = (time_0 - time__1).asUnits(OpenMaya.MTime.kSeconds)
            #
            #     mdg__2 = OpenMaya.MDGContext(OpenMaya.MTime(time__2))
            #     mdg__1 = OpenMaya.MDGContext(OpenMaya.MTime(time__1))
            #     mdg_0 = OpenMaya.MDGContext(OpenMaya.MTime(time_0))
            #     mdg_1 = OpenMaya.MDGContext(OpenMaya.MTime(time_1))
            #     mdg_2 = OpenMaya.MDGContext(OpenMaya.MTime(time_2))
            #
            #     for i in axis_position_indices:
            #         axis_i_plug = plug.elementByLogicalIndex(i)
            #
            #         # Check if the plug still has a connection; if not, continue to the next one
            #         if not axis_i_plug.isConnected:
            #             continue
            #
            #         # If the plug has a connection, add its index to the list of axes
            #         axis_position_connections.append(i)
            #
            #         p__2 = axis_i_plug.asMAngle(mdg__2).asDegrees()
            #         p__1 = axis_i_plug.asMAngle(mdg__1).asDegrees()
            #         p_0 = axis_i_plug.asMAngle(mdg_0).asDegrees()
            #         p_1 = axis_i_plug.asMAngle(mdg_1).asDegrees()
            #         p_2 = axis_i_plug.asMAngle(mdg_2).asDegrees()
            #
            #         stencil = [p__2, p__1, p_0, p_1, p_2]
            #
            #         ####ACCUMULATE ROTATIONS#####
            #         for i, point in enumerate(stencil):
            #             if i == 0:
            #                 continue
            #             else:
            #                 p_in = point
            #                 p_0 = stencil[i - 1]
            #
            #                 stencil[i] = self.accumulate_rotation(p_in, p_0)
            #
            #         derivatives = self.five_point_stencil(stencil, delta_t_sec)
            #
            #         vel = abs(round(derivatives[0], 2))
            #         accel = abs(round(derivatives[1], 2))
            #         jerk = abs(round(derivatives[2], 2))
            #
            # # Set the Output Values
            # # vel_data_handle.setFloat(vel)
            # # accel_data_handle.setFloat(accel)
            # # jerk_data_handle.setFloat(jerk)

        # Mark the output data handle as being clean;
        vel_data_handle.setClean()
        accel_data_handle.setClean()
        jerk_data_handle.setClean()

    def five_point_stencil(self, stencil, delta_t):
        """
        """
        p__2 = stencil[0]
        p__1 = stencil[1]
        p_0 = stencil[2]
        p_1 = stencil[3]
        p_2 = stencil[4]

        d1 = (-p_2 + 8.0 * p_1 - 8.0 * p__1 + p__2) / (12.0 * delta_t)
        d2 = (-p_2 + 16.0 * p_1 - 30.0 * p_0 + 16.0 * p__1 - p__2) / (12.0 * math.pow(delta_t, 2))
        d3 = (p_2 - 2.0 * p_1 + 2.0 * p__1 - p__2) / (2.0 * math.pow(delta_t, 3))

        return [d1, d2, d3]

    def accumulate_rotation(self, a_in, a_0):
        """
        Compares current Axis value with its previous value to determine if there
        has been a 360 degree flip in the Axis' evaluation.
        e.g.:If a_0 = 94 and a_in = -265; instead of -266, this function would
        output a_out = 95
        :param a_in: float; current evaluation of axis rotation
        :param a_0: float; previous evaluation of axis rotation
        :return a_out: float
        """
        # If the input value and previous value differ by a large amount, we assume
        # the evaluation has been flipped, so we manually flip it back. Otherwise,
        # we output the input value unchanged

        try:
            sign = int(a_0 / abs(a_0))
        except ZeroDivisionError:
            sign = 1

        if abs(a_in - a_0) > 300:

            # Find how many multiples of 360 we're off by
            a = int(round(abs(a_in - a_0) / 360.0))

            a_out = a_in + sign * a * 360.0
        else:
            a_out = a_in

        return a_out


# ========================================================#
#                 Plug-in initialization.                #
# ========================================================#

def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a pointer.
    '''

    return robotAxisDynamics()


def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our plug-in class.
    '''

    # The following function set will allow us to create our attributes.
    angleAttributeFn = OpenMaya.MFnUnitAttribute()
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    # ==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    # ==================================#

    ## Position ##
    robotAxisDynamics.pos_attr = angleAttributeFn.create('position', 'position', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    angleAttributeFn.array = True
    angleAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.pos_attr)

    ## Live ##
    robotAxisDynamics.live_attr = numericAttributeFn.create('live', 'live', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True
    numericAttributeFn.storable = True
    numericAttributeFn.hidden = False
    robotAxisDynamics.addAttribute(robotAxisDynamics.live_attr)

    # ==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    # ==================================#

    ## Velocity ##
    robotAxisDynamics.vel_attr = numericAttributeFn.create('velocity', 'velocity', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.vel_attr)

    ## Acceleration ##
    robotAxisDynamics.accel_attr = numericAttributeFn.create('acceleration', 'acceleration',
                                                             OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.accel_attr)

    ## Jerk ##
    robotAxisDynamics.jerk_attr = numericAttributeFn.create('jerk', 'jerk', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.jerk_attr)

    # ===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    # ===================================#

    input_attrs = [robotAxisDynamics.pos_attr,
                   robotAxisDynamics.live_attr
                   ]

    output_attrs = [robotAxisDynamics.vel_attr,
                    robotAxisDynamics.accel_attr,
                    robotAxisDynamics.jerk_attr,
                    ]

    for input_attr in input_attrs:
        for output_attr in output_attrs:
            robotAxisDynamics.attributeAffects(input_attr, output_attr)


def initializePlugin(mobject):
    '''
    Initialize the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kPluginNodeName, kPluginNodeId, nodeCreator,
                             nodeInitializer, OpenMaya.MPxNode.kDependNode, kPluginNodeClassify)
    except:
        sys.stderr.write('Failed to register node: ' + kPluginNodeName)
        raise


def uninitializePlugin(mobject):
    '''
    Uninitializes the plug-in
    '''

    mplugin = OpenMaya.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write('Failed to deregister node: ' + kPluginNodeName)
        raise