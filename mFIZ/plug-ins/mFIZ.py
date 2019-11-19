#!usr/bin/env python

"""
Dependency Graph plug-in that handles communication with external motor APIs.
"""

import sys
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

# General Imports
import importlib


# Import supported motor APIs from mFIZ config dynamically and stor in dict
import mFIZ_config
reload(mFIZ_config)

supported_apis = mFIZ_config.SUPPORTED_MOTOR_APIS
APIS = {}

for api_name in supported_apis:
    APIS[api_name] = importlib.import_module('motor_apis.{}'.format(api_name))
    reload(APIS[api_name])



def maya_useNewAPI():
	"""
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
	"""
	pass


# Plug-in information:
kPluginNodeName = 'mFIZ'    # The name of the node.
kPluginNodeClassify = 'utility/general'     # Where this node will be found in the Maya UI.
kPluginNodeId = OpenMaya.MTypeId( 0x87010 ) # A unique ID associated to this node type.    

#==========================================#
#                Plug-in                   #
#==========================================#
class mFIZ(OpenMaya.MPxNode):    
    # Static variables which will later be replaced by the node's attributes.
    # Inputs
    focus_attr = OpenMaya.MObject()
    iris_attr = OpenMaya.MObject()
    zoom_attr = OpenMaya.MObject()

    live_attr = OpenMaya.MObject()

    api_attr = OpenMaya.MObject()

    port_name_attr = OpenMaya.MObject()

    stop_playback_on_disconnect_attr = OpenMaya.MObject()

    # Outputs
    ''' 
    focus_mapped_attr = OpenMaya.MObject()
    iris_mapped_attr = OpenMaya.MObject()
    zoom_mapped_attr = OpenMaya.MObject()
    '''
    data_sent_attr = OpenMaya.MObject()
    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
    
        self.motor = None

    ##################################################
        
    def compute(self, pPlug, pDataBlock):
                   
        ## Obtain the data handles for each attribute
        
        # Input Data Handles 
        focus_data_handle = pDataBlock.inputValue(mFIZ.focus_attr)
        iris_data_handle = pDataBlock.inputValue(mFIZ.iris_attr)
        zoom_data_handle = pDataBlock.inputValue(mFIZ.zoom_attr)

        live_data_handle = pDataBlock.inputValue(mFIZ.live_attr)
        api_data_handle = pDataBlock.inputValue(mFIZ.api_attr)
        port_name_data_handle = pDataBlock.inputValue(mFIZ.port_name_attr)
        stop_playback_on_disconnect_data_handle = pDataBlock.inputValue(mFIZ.stop_playback_on_disconnect_attr)

        # Output Data Handles 
        data_sent_data_handle = pDataBlock.outputValue(mFIZ.data_sent_attr)


        ## Extract the actual value associated to our input attribute
        focus_value = focus_data_handle.asFloat()
        iris_value = iris_data_handle.asFloat()
        zoom_value = zoom_data_handle.asFloat()

        live = live_data_handle.asBool()
        api = api_data_handle.asString()
        port_name = port_name_data_handle.asString()
        stop_on_disconnect = stop_playback_on_disconnect_data_handle.asBool()

        '''
        print '# ------------------------- #'
        print '#         NODE DATA         #'
        print '# ------------------------- #'
        print '#'
        print '# Node is Live: ', live
        print '# Port Name: ', port_name        
        print '# API Enum: ', api
        print '# Stop on Disconnect: ', stop_on_disconnect
        print '#'
        print '# ------------------------- #'
        '''

        if live and api and port_name:

            # If the node has no motor assigned, assign one
            if not self.motor:
                self.motor = APIS[api].Motor()

            # If the assigned motor is not connected, try connecting
            if not self.motor.isConnected():
                self.motor.connect(port_name)


            # If there is now a connection, try sending data
            if self.motor.isConnected():
                # All checks have passed, try sending packets

                try:
                    self.motor.send(focus_value, iris_value, zoom_value)
                    self.device_connected(data_sent_data_handle)
                except:
                    # If playback in on, and stop on disconnect is on stop playback
                    if stop_on_disconnect:
                        anim = OpenMayaAnim.MAnimControl
                        if anim.isPlaying():
                            anim.stop()

                            current_time = anim.currentTime()
                            # Set time to current_time + 1 to trigger a scriptJob
                            anim.setCurrentTime(current_time + 1)

                    self.device_disconnected(data_sent_data_handle, live_data_handle)
                    # throw exception?

            # If there is still no connection, turn the node off
            else:
                self.device_disconnected(data_sent_data_handle, live_data_handle)
                # raise exception??
        else:
            # Turn the node off
            self.device_disconnected(data_sent_data_handle, live_data_handle)
        

        

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

    return mFIZ()

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
    mFIZ.focus_attr = numericAttributeFn.create('focus', 'focus', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ.addAttribute(mFIZ.focus_attr)

    mFIZ.iris_attr = numericAttributeFn.create('iris', 'iris', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ.addAttribute(mFIZ.iris_attr)

    mFIZ.zoom_attr = numericAttributeFn.create('zoom', 'zoom', OpenMaya.MFnNumericData.kFloat)
    numericAttributeFn.writable = True 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    numericAttributeFn.setMin(0)
    numericAttributeFn.setMax(1)
    mFIZ.addAttribute(mFIZ.zoom_attr)
        
    #-----------------------------------------#      
    #                Connection               #
    #-----------------------------------------# 
    mFIZ.live_attr = numericAttributeFn.create('live', 'live', OpenMaya.MFnNumericData.kBoolean, 0)                                                           
    numericAttributeFn.writable = True 
    numericAttributeFn.connectable = False 
    numericAttributeFn.storable = False 
    numericAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.live_attr)

    #-----------------------------------------#      
    #                 Port Name               #
    #-----------------------------------------# 
    mFIZ.port_name_attr = typedAttributeFn.create('portName', 'portName', OpenMaya.MFnData.kString)                                                           
    typedAttributeFn.writable = True 
    typedAttributeFn.connectable = False 
    typedAttributeFn.storable = False 
    typedAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.port_name_attr)

    #-----------------------------------------#      
    #                 API Type                #
    #-----------------------------------------#
    mFIZ.api_attr= typedAttributeFn.create('api', 'api', OpenMaya.MFnData.kString)
    typedAttributeFn.writable = True
    typedAttributeFn.storable = False
    typedAttributeFn.connectable = False
    typedAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.api_attr)
    ''' 
    mFIZ.api_attr= numericAttributeFn.create('api', 'api', OpenMaya.MFnNumericData.kInt, 0)
    numericAttributeFn.writable = True
    numericAttributeFn.storable = False
    numericAttributeFn.connectable = False
    numericAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.api_attr)     
    '''

    #-----------------------------------------#      
    #       Stop Playback on Disconnect       #
    #-----------------------------------------# 
    mFIZ.stop_playback_on_disconnect_attr = numericAttributeFn.create('stopPlaybackOnDisconnect', 'stopPlaybackOnDisconnect', OpenMaya.MFnNumericData.kBoolean, 0)                                                           
    numericAttributeFn.writable = True 
    numericAttributeFn.connectable = False 
    numericAttributeFn.storable = True 
    numericAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.stop_playback_on_disconnect_attr)


    #==================================#
    #     OUTPUT NODE ATTRIBUTE(S)     #
    #==================================#
    mFIZ.data_sent_attr = numericAttributeFn.create('dataSent', 'dataSent', OpenMaya.MFnNumericData.kBoolean, 0)                                                           
    numericAttributeFn.writable = False 
    numericAttributeFn.storable = False
    numericAttributeFn.readable = True 
    numericAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.data_sent_attr)


    mFIZ.controller_attr = messageAttributeFn.create('controller', 'controller')                                                           
    messageAttributeFn.writable = True 
    messageAttributeFn.storable = True
    messageAttributeFn.hidden = False
    mFIZ.addAttribute(mFIZ.controller_attr)

    
    #===================================#
    #    NODE ATTRIBUTE DEPENDENCIES    #
    #===================================#

    input_attrs = [mFIZ.focus_attr,
                   mFIZ.iris_attr,
                   mFIZ.zoom_attr,
                   mFIZ.live_attr,
                   mFIZ.api_attr,
                   mFIZ.stop_playback_on_disconnect_attr]

    output_attrs = [mFIZ.data_sent_attr]

    for input_attr in input_attrs:
        for output_attr in output_attrs:
            mFIZ.attributeAffects(input_attr, output_attr)
     
           
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