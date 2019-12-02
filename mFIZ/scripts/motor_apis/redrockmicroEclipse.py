#!usr/bin/env python
# -*- coding: utf-8 -*-

import serial
from collections import namedtuple

## Motor Specific Parameters
# This is done here for clarity and ease of cusomization
NAME = 'redrockmicroEclipse'
REQUIRE_HANDSHAKE = True

"""
Define the motor range of the number representing minimum and maximum values
for mapping calibrated motors.

Maya will always pass a value between 0 and 1. The API will clamp a passed value 
between 0 and 1, then map it to the range set below before sending the value to the motor
"""

# rerdrockmicroEclipse API uses 16-bit integer mapping
__MOTOR_RANGE_MIN = 0
__MOTOR_RANGE_MAX = 65535
__MOTOR_RANGE = namedtuple(
    'motor_range', [
    'min',
    'max'
    ]
)

# Store the motor range in a namedtuple
MOTOR_RANGE = __MOTOR_RANGE(__MOTOR_RANGE_MIN,
                            __MOTOR_RANGE_MAX)

# Create a namedtuple specifying the serial port settings for this API
__BAUDRATE = 115200
__BYTESIZE = serial.EIGHTBITS
__PARITY = serial.PARITY_NONE
__STOPBITS = serial.STOPBITS_ONE
__TIMEOUT = None

__PORT_SETTINGS = namedtuple(
    'serial_settings', [
        'baudrate',
        'bytesize',
        'parity',
        'stopbits',
        'timeout'
    ]
)

# Store the port settings in a namedtuple
PORT_SETTINGS = __PORT_SETTINGS(__BAUDRATE,
                                __BYTESIZE,
                                __PARITY,
                                __STOPBITS,
                                __TIMEOUT)

class Motor(object):
    """
    Redrockmicro Eclipse system API
    """

    def __init__(self):

        # Assign instance attributes
        self.name = NAME
        self.require_handshake = REQUIRE_HANDSHAKE
        self.motor_range = MOTOR_RANGE

        self.port_settings = PORT_SETTINGS
        self.ser = None

    def connect(self, port_name):
        """
        Establishes a serial connect to the input port, using the settings specified
        If a connection is established, assigns the resultant serial.Serial object
        to the instance attribute `self.ser`

        :param port_name: str, name of the serial port representing the device
                          Ex. PC: 'COM8'
                          Ex. Mac: '/dev/tty.USB-DEVICE'
        """
        try:
            self.ser = serial.Serial(port=port_name,
                                     baudrate=self.port_settings.baudrate,
                                     bytesize=self.port_settings.bytesize,
                                     parity=self.port_settings.parity,
                                     stopbits=self.port_settings.stopbits,
                                     timeout=self.port_settings.timeout)

            self.ser.close()
            self.ser.open()

        except:
            # Return exception?
            self.ser = None
        
    def isConnected(self):
        """
        Checks if there is a serial connection
        Returns True if so, False if not        
        """
        if self.ser:
            return True
        else:
            return False

    def send(self, focus=0, iris=0, zoom=0, calibrate_motors=0):
        """
        Maps input values to motor range, formats the serial packet, then sends
        the formatted packed to the motor

        Note: "calibrate_motors" is not yet implemented

        :param focus: float between 0 and 1 representing the focus value to be set
        :param iris: float between 0 and 1 representing the iris value to be set
        :param zoom: float between 0 and 1 representing the zoom value to be set
        """
        # Map input values to range specified by MOTOR_RANGE
        motor_positions = self._map_motor_values([focus, iris, zoom])

        # Assemble send pack
        packet = self.make_packet(motor_positions, calibrate_motors)

        self.ser.write(packet)

    def make_packet(self, motor_positions, calibrate_motors=0, return_packet=0):
        """
        Build the Redrockmicro Eclipse serial API packet. See docs for details

        :param motor_positions: namedtuple with mapped focus, iris, zoom values
        :param calibrate_motors: bool; If True, sends a calibration command
                                       to initiate motor calibration routine if your
                                       API supports it
        :param return_packet: bool; If True, requests a formatted return packet from
                                    the device if your device supports it
        :return packet: str; formatted packet to send the device
        """

        #Focus
        focus_out_value = motor_positions.focus  #Focus Value to send to motor
        focus_out = bytearray()
        focus_out.append(focus_out_value & 0xFF)
        focus_out.append(focus_out_value >> 8)
        
        #Iris
        iris_out_value = motor_positions.iris      #Iris Value to send to motor
        iris_out = bytearray()
        iris_out.append(iris_out_value & 0xFF)
        iris_out.append(iris_out_value >> 8)

        #Zoom
        zoom_out_value = motor_positions.zoom       #Zoom Value to send to motor
        zoom_out = bytearray()
        zoom_out.append(zoom_out_value & 0xFF)
        zoom_out.append(zoom_out_value >> 8)

        packet = bytearray()
        packet.append("R")          #Header 1
        packet.append("R")          #Header 2
        packet.append("M")          #Header 3
        packet.append("G")          #Packet Type
        packet.append(0x0D)         #Packet Length
        packet.append(focus_out[0]) #Focus Byte 1
        packet.append(focus_out[1]) #Focus Byte 2
        packet.append(iris_out[0])  #Iris Byte 1
        packet.append(iris_out[1])  #Iris Byte 2
        packet.append(zoom_out[0])  #Zoom Byte 1
        packet.append(zoom_out[1])  #Zoom Byte 2
        
        if calibrate_motors:
            packet.append(0x01)     #Auto Calibration       0x00 = None, 0x01 = Start Calibration
            print "Calibrating Motors..."
        else:
            packet.append(0x00)     #Auto Calibration       0x00 = None, 0x01 = Start Calibration
        
        if return_packet:
            packet.append(0x01)         #Return Motor Packet    0x00 = None, 0x01 = Return the motor packet
        else:
            packet.append(0x00)

        return packet

    # -- Utility Functions ------------------------------------------------------- #
    def _map_motor_values(self, raw_values):
        """
        Takes raw input value and maps them to the specified range of the calibrated
        motor.

        :param raw_values: list of floats, motor values between 0 and 1 to be mapped
        :return motor_positions: namedtuple containing mapped focus, iris, zoom int values
        """
        # Define input min/max
        # Our maya controller is set up to send values between 0 and 1
        input_min = 0
        input_max = 1

        output_min = self.motor_range.min
        output_max = self.motor_range.max

        mapped_vals = []
        for val in raw_values:
            # If the value is outside the input range, clamp it to the input range
            val = self._clamp_value(val, input_min, input_max)

            mapped_val = int(output_min + ((output_max - output_min) / (input_max - input_min)) * (val - input_min))

            mapped_vals.append(mapped_val)

        focus = mapped_vals[0]
        iris = mapped_vals[1]
        zoom = mapped_vals[2]

        # Return the result as a namedtuple
        motor_positions = namedtuple('motor_positions', [
                                'focus',
                                'iris',
                                'zoom']
                                )


        return motor_positions(focus, iris, zoom)

    def _clamp_value(self, value, min_value, max_value):
        """
        Clamps the input value between the min/max range
        """
        return max(min(value, max_value), min_value)

