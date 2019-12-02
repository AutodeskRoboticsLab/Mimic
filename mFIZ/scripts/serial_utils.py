#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions that aid in serial port setup and functions.
"""
import os
import serial
import serial.tools.list_ports as list_ports

# mFIZ imports
import serial_config

reload(serial_config)


PORT_PREFIXES = {'posix': '/dev/tty.', 'nt': ''}

def get_device_names():
    """
    """

    devices = [comport.device for comport in serial.tools.list_ports.comports()]
    
    devices = [comport.device for comport in serial.tools.list_ports.comports()]
    device_names = []
    if os.name == 'posix':  # macOS
        # Strip the device prefix
        device_names = [device.split('.')[-1] for device in devices]
    
    elif os.name == 'nt':  # windows
        device_names = devices

    else:  # Unsupported operating system
        raise Exception('Unsupported OS')

    ## Default device and ignored devices can be set in mFIZ/scripts/serial_config.py
    # Place the default device at the top of the list
    device_names = _set_default_device(device_names)

    # Remove ignored devices from the list
    device_names = _remove_ignored_devices(device_names)

    return device_names

def format_port_name(device_name):
    """
    """
    try:
        port_name = PORT_PREFIXES[os.name] + device_name
    except KeyError:
        raise Exception('Unsupported OS')

    return port_name

def _set_default_device(device_names):
    """
    """
    # Get default from config and put it at the front of the list
    default = serial_config.DEFAULT_DEVICE
    if default in device_names:
        device_names.remove(default)
        device_names.insert(0, default)

    return device_names


def _remove_ignored_devices(device_names):
    """
    """
    # Get list of devices to ignore from confog
    ignored = serial_config.IGNORE_DEVICES

    for ignore in ignored:
        if ignore in device_names:
            device_names.remove(ignore)

    return device_names
# --------------------------------------------------------- #
# --------------------------------------------------------- #
