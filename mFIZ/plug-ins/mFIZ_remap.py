#!usr/bin/env python

"""
Dependency Graph plug-in that handles communication with external motor APIs.
"""

import sys
import maya.api.OpenMaya as OpenMaya


def maya_useNewAPI():
	"""
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
	"""
	pass


# Plug-in information:
kPluginNodeName = 'mFIZ_remap'    # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId(0x87011) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class mFIZ_remap(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    focus_in_attr = OpenMaya.MObject()
    iris_in_attr = OpenMaya.MObject()
    zoom_in_attr = OpenMaya.MObject()

    # resolution_enum_attr = OpenMaya.MObject()

    # Outputs 
    focus_out_attr = OpenMaya.MObject()
    iris_out_attr = OpenMaya.MObject()
    zoom_out_attr = OpenMaya.MObject()

    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
        self.motor = None

    ##################################################
        
    def compute(self, pPlug, pDataBlock):
                   
        ## Obtain the data handles for each attribute
        
        # Input Data Handles 
        focus_in_data_handle = pDataBlock.inputValue(mFIZ_remap.focus_in_attr)
        iris_in_data_handle = pDataBlock.inputValue(mFIZ_remap.iris_in_attr)
        zoom_in_data_handle = pDataBlock.inputValue(mFIZ_remap.zoom_in_attr)

        # resolution_enum_data_handle = pDataBlock.inputValue(mFIZ_remap.resolution_enum_attr)


        # Output Data Handles 
        focus_out_data_handle = pDataBlock.outputValue(mFIZ_remap.focus_out_attr)
        iris_out_data_handle = pDataBlock.outputValue(mFIZ_remap.iris_out_attr)
        zoom_out_data_handle = pDataBlock.outputValue(mFIZ_remap.zoom_out_attr)


        ## Extract the actual value associated to our input attribute
        focus_in_value = focus_in_data_handle.asFloat()
        iris_in_value = iris_in_data_handle.asFloat()
        zoom_in_value = zoom_in_data_handle.asFloat()

        # resolution_enum_value = resolution_enum_data_handle.asInt()


        in_values = [focus_in_value, iris_in_value, zoom_in_value]
        out_values = self._map_values(in_values)

        # Set output data handles
        focus_out_data_handle.setInt(out_values[0])
        iris_out_data_handle.setInt(out_values[1])
        zoom_out_data_handle.setInt(out_values[2])

        # Mark the output data handle as being clean; it need not be computed given its input.
        focus_out_data_handle.setClean()
        iris_out_data_handle.setClean()
        zoom_out_data_handle.setClean()
        
    def _map_values(self, input_values):
        """
        """
        # Define input min/max
        # Our maya controller is set up to send values between 0 and 1
        input_min = 0
        input_max = 1

        # TO-DO: these are hardcoded but should be tied to input attribute
        output_min = 0
        output_max = 65535  # 16-bit unsigned max
        

        ouput_vals = []
        for val in input_values:
            # If the value is outside the input range, clamp it to the input range
            val = self._clamp_value(val, input_min, input_max)

            ouput_val = int(output_min + ((output_max - output_min) / (input_max - input_min)) * (val - input_min))

            ouput_vals.append(ouput_val)

        return ouput_vals

    def _clamp_value(self, value, min_value, max_value):
        """
        """
        return max(min(value, max_value), min_value)        

    def device_disconnected(self, data_sent_data_handle, live_data_handle):
        """
        """
        # If the dataSent attribute is True, make it false
        if data_sent_data_handle.asBool():
            data_sent_data_handle.setBool(False)

        # If the node is Live, turn node off        
        if live_data_handle.asBool():
            live_data_handle.setBool(False)

        # Reset instance attributes
        try:
            self.motor.ser.close()
        except:
            pass

        self.motor = None

        # Mark the output data handle as being clean
        data_sent_data_handle.setClean()

    def device_connected(self, data_sent_data_handle):
        """
        """
        # If the dataSent attribute is False, make it True
        if not data_sent_data_handle.asBool():
                    data_sent_data_handle.setBool(True)

        # Mark the output data handle as being clean
        data_sent_data_handle.setClean()

#========================================================#
#                 Plug-in initialization.                #
#========================================================#

def nodeCreator():
    '''
    Creates an instance of our node class and delivers it to Maya as a pointer.
    '''

    return mFIZ_remap()

def nodeInitializer():
    '''
    Defines the input and output attributes as static variables in our plug-in class.
    '''
    
    # The following function set will allow us to create our attributes.
    numericAttributeFn = OpenMaya.MFnNumericAttribute()
    typedAttributeFn = OpenMaya.MFnTypedAttribute()
    messageAttributeFn = OpenMaya.MFnMessageAttribute()
    compoundAttributeFn = OpenMaya.MFnCompoundAttribute()

    #==================================#
    #      INPUT NODE ATTRIBUTE(S)     #
    #==================================#


    #-----------------------------------------#      
    #            Focus Iris Zoom              #
    #-----------------------------------------# 
    mFIZ_remap.focus_in_attr = numericAttributeFn.create('focus', 'focus', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ_remap.addAttribute(mFIZ_remap.focus_in_attr)

    mFIZ_remap.iris_in_attr = numericAttributeFn.create('iris', 'iris', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ_remap.addAttribute(mFIZ_remap.iris_in_attr)

    mFIZ_remap.zoom_in_attr = numericAttributeFn.create('zoom', 'zoom', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ_remap.addAttribute(mFIZ_remap.zoom_in_attr)
        


    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#
    mFIZ_remap.focus_out_attr = numericAttributeFn.create('focusMapped', 'focusMapped', OpenMaya.MFnNumericData.kInt, 0)                                                           
    numericAttributeFn.writable = False 
    numericAttributeFn.storable = False
    numericAttributeFn.readable = True 
    numericAttributeFn.hidden = False
    mFIZ_remap.addAttribute(mFIZ_remap.focus_out_attr)

    mFIZ_remap.iris_out_attr = numericAttributeFn.create('irisMapped', 'irisMapped', OpenMaya.MFnNumericData.kInt, 0)                                                           
    numericAttributeFn.writable = False 
    numericAttributeFn.storable = False
    numericAttributeFn.readable = True 
    numericAttributeFn.hidden = False
    mFIZ_remap.addAttribute(mFIZ_remap.iris_out_attr)

    mFIZ_remap.zoom_out_attr = numericAttributeFn.create('zoomMapped', 'zoomMapped', OpenMaya.MFnNumericData.kInt, 0)                                                           
    numericAttributeFn.writable = False 
    numericAttributeFn.storable = False
    numericAttributeFn.readable = True 
    numericAttributeFn.hidden = False
    mFIZ_remap.addAttribute(mFIZ_remap.zoom_out_attr)

    
    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    input_attrs = [mFIZ_remap.focus_in_attr,
                   mFIZ_remap.iris_in_attr,
                   mFIZ_remap.zoom_in_attr]

    output_attrs = [mFIZ_remap.focus_out_attr,
                    mFIZ_remap.iris_out_attr,
                    mFIZ_remap.zoom_out_attr]

    for input_attr in input_attrs:
        for output_attr in output_attrs:
            mFIZ_remap.attributeAffects(input_attr, output_attr)
     
           
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