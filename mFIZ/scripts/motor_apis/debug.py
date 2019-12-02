#!usr/bin/env python
# -*- coding: utf-8 -*-

## This prints FIZ values to the output window ##

import serial
from collections import namedtuple

## Motor Specific Parameters
# This is done here for clarity and ease of cusomization
NAME = 'debug'
REQUIRE_HANDSHAKE = False

# Define the motor range of the number representing minimum and maximum values
# for mapping calibrated motors.
__MOTOR_RANGE_MIN = 0
__MOTOR_RANGE_MAX = 65535
__MOTOR_RANGE = namedtuple(
    'motor_range', [
    'min',
    'max'
    ]
)

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

PORT_SETTINGS = __PORT_SETTINGS(__BAUDRATE,
                                __BYTESIZE,
                                __PARITY,
                                __STOPBITS,
                                __TIMEOUT)

class Motor(object):
    """
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
        """
        self.ser = True
        
    def isConnected(self):
        """
        """
        if self.ser:
            return True
        else:
            return False

    def send(self, focus=0, iris=0, zoom=0, calibrate_motors=0):
        """
        """
        # Map input values to range specified by MOTOR_RANGE
        motor_positions = self._map_motor_values([focus, iris, zoom])

        print '# ----------------- #\n' \
              '#  Motor Positions  #\n' \
              '# ----------------- #\n' \
              '# Focus: {}\n' \
              '# Iris: {}\n' \
              '# Zoom: {}'.format(motor_positions.focus, motor_positions.iris, motor_positions.zoom)
        

        return motor_positions

    def make_packet(self, motor_positions, calibrate_motors=0, return_packet=0):
        """
        """
        return None

    # ---------------------------------------------------------------------------- #
    def _map_motor_values(self, raw_values):
        """
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
        """
        return max(min(value, max_value), min_value)

