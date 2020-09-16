#!usr/bin/env python

"""
Dependency Graph plug-in that allows the physical rotational limits of the
robot rig to be taken into account when performing an Inverse Kinematic solve.
"""

import sys
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim
import math


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


# Plug-in #
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

    def compute(self, pPlug, pDataBlock):
        # Obtain the data handles for each attribute #
        # Input Data Handles
        live_data_handle = pDataBlock.inputValue(robotAxisDynamics.live_attr)
        # pos_array_data_handle = pDataBlock.inputArrayValue(robotAxisDynamics.pos_attr)  # We get the plug directly

        # Output Data Handles
        vel_array_data_handle = pDataBlock.outputArrayValue(robotAxisDynamics.vel_attr)
        accel_array_data_handle = pDataBlock.outputArrayValue(robotAxisDynamics.accel_attr)
        jerk_array_data_handle = pDataBlock.outputArrayValue(robotAxisDynamics.jerk_attr)

        # Extract the actual value associated to our input attribute
        live = live_data_handle.asBool()

        # If the node is not "live", skip computation
        if not live:
            # Mark the output data handle as being clean;
            vel_array_data_handle.setAllClean()
            accel_array_data_handle.setAllClean()
            jerk_array_data_handle.setAllClean()

            return

        # Solve
        # Get the plug directly. (networkedplug=False)
        # This lets us check connections and get array indices more directly than going through the dataHandle
        obj = self.thisMObject()
        objMfn = OpenMaya.MFnDependencyNode(obj)
        plug = objMfn.findPlug('position', False)

        axis_position_indices = plug.getExistingArrayAttributeIndices()

        if axis_position_indices:
            # Get the current time
            time_0 = OpenMayaAnim.MAnimControl.currentTime()

            # Get the time at the two previous frames, and two next frames for the five-point stencil
            time__2 = time_0 - 2
            time__1 = time_0 - 1
            time_1 = time_0 + 1
            time_2 = time_0 + 2

            # Get the time increment
            delta_t_sec = (time_0 - time__1).asUnits(OpenMaya.MTime.kSeconds)

            # Get the DG context at each time step
            mdg__2 = OpenMaya.MDGContext(OpenMaya.MTime(time__2))
            mdg__1 = OpenMaya.MDGContext(OpenMaya.MTime(time__1))
            mdg_0 = OpenMaya.MDGContext(OpenMaya.MTime(time_0))
            mdg_1 = OpenMaya.MDGContext(OpenMaya.MTime(time_1))
            mdg_2 = OpenMaya.MDGContext(OpenMaya.MTime(time_2))

            # Iterate over connected position inputs. For a robot, this is Theta 1, Theta 2, ... , Theta 6, etc.
            for i in axis_position_indices:
                # Get the i-th axis' plug from the array plug
                axis_i_plug = plug.elementByLogicalIndex(i)

                # Check if the plug still has a connection; if not, continue to the next one
                if not axis_i_plug.isConnected:
                    continue

                # Evaluate the plug value (input position) at each time step (DG Context)
                p__2 = axis_i_plug.asMAngle(mdg__2).asDegrees()
                p__1 = axis_i_plug.asMAngle(mdg__1).asDegrees()
                p_0 = axis_i_plug.asMAngle(mdg_0).asDegrees()
                p_1 = axis_i_plug.asMAngle(mdg_1).asDegrees()
                p_2 = axis_i_plug.asMAngle(mdg_2).asDegrees()

                stencil = [p__2, p__1, p_0, p_1, p_2]

                # Accumulate rotations
                # IK solver solves between +/- 180 even if an axis' limits are beyond that, so this ensures that the
                # positions are continuous within the stencil. This is acceptable because we only care about the
                # magnitude of the derivatives
                for j, point in enumerate(stencil):
                    if j == 0:
                        continue
                    else:
                        p_in = point
                        p_0 = stencil[j - 1]

                        stencil[j] = self.accumulate_rotation(p_in, p_0)

                # Compute derivatives (i.e. velocity, acceleration, jerk) using the five-point stencil technique
                derivatives = self.five_point_stencil(stencil, delta_t_sec)

                vel = abs(round(derivatives[0], 2))
                accel = abs(round(derivatives[1], 2))
                jerk = abs(round(derivatives[2], 2))

                # Get the i-th axis' output handle from the array handle
                # If there is no i-th element (i.e. a connection has not been made on that plug), then
                # jumpToLogicalElement(i) will throw a RuntimeError. If this is the case, we add an element to the
                # output array to store the data
                try:
                    vel_array_data_handle.jumpToLogicalElement(i)
                    vel_data_handle = vel_array_data_handle.outputValue()
                except RuntimeError:
                    vel_data_handle = vel_array_data_handle.builder().addElement(i)

                try:
                    accel_array_data_handle.jumpToLogicalElement(i)
                    accel_data_handle = accel_array_data_handle.outputValue()
                except RuntimeError:
                    accel_data_handle = accel_array_data_handle.builder().addElement(i)

                try:
                    jerk_array_data_handle.jumpToLogicalElement(i)
                    jerk_data_handle = jerk_array_data_handle.outputValue()
                except RuntimeError:
                    jerk_data_handle = jerk_array_data_handle.builder().addElement(i)

                # Set the Output Values
                vel_data_handle.setFloat(vel)
                vel_data_handle.setClean()

                accel_data_handle.setFloat(accel)
                accel_data_handle.setClean()

                jerk_data_handle.setFloat(jerk)
                jerk_data_handle.setClean()

        # Mark the output data handle as being clean;
        vel_array_data_handle.setAllClean()
        accel_array_data_handle.setClean()
        jerk_array_data_handle.setClean()

    def five_point_stencil(self, stencil, delta_t):
        """
        The Five-point stencil is a quick way to approximate the 1st, 2nd, and 3rd-order derivatives of the input
        positions. See: https://en.wikipedia.org/wiki/Five-point_stencil

        :param stencil: list. 5 positions at the 5 corresponding time steps
        :param delta_t: Time step
        :return: list. Computed derivatives representing velocity, acceleration, and jerk at the current time
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


# Plug-in initialization. #
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

    # ================================= #
    #      INPUT NODE ATTRIBUTE(S)      #
    # ================================= #

    # Position #
    robotAxisDynamics.pos_attr = angleAttributeFn.create('position', 'position', OpenMaya.MFnUnitAttribute.kAngle)
    angleAttributeFn.storable = True
    angleAttributeFn.writable = True
    angleAttributeFn.hidden = False
    angleAttributeFn.array = True
    angleAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.pos_attr)

    # Live #
    robotAxisDynamics.live_attr = numericAttributeFn.create('live', 'live', OpenMaya.MFnNumericData.kBoolean, 0)
    numericAttributeFn.writable = True
    numericAttributeFn.storable = True
    numericAttributeFn.hidden = False
    robotAxisDynamics.addAttribute(robotAxisDynamics.live_attr)

    # ================================ #
    #     OUTPUT NODE ATTRIBUTE(S)     #
    # ================================ #

    # Velocity #
    robotAxisDynamics.vel_attr = numericAttributeFn.create('velocity', 'velocity', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.vel_attr)

    # Acceleration #
    robotAxisDynamics.accel_attr = numericAttributeFn.create('acceleration', 'acceleration',  OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.accel_attr)

    # Jerk #
    robotAxisDynamics.jerk_attr = numericAttributeFn.create('jerk', 'jerk', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.storable = False
    numericAttributeFn.writable = False
    numericAttributeFn.readable = True
    numericAttributeFn.hidden = False
    numericAttributeFn.array = True
    numericAttributeFn.usesArrayDataBuilder = True
    robotAxisDynamics.addAttribute(robotAxisDynamics.jerk_attr)

    # ================================= #
    #    NODE ATTRIBUTE DEPENDENCIES    #
    # ================================= #

    input_attrs = [robotAxisDynamics.pos_attr, robotAxisDynamics.live_attr]

    output_attrs = [robotAxisDynamics.vel_attr, robotAxisDynamics.accel_attr, robotAxisDynamics.jerk_attr]

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