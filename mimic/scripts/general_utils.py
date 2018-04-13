#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generic utilities for use with Mimic. Utilities contained in this module are
functional and independent of Maya and the Mimic UI. It is expected that these
utilities are reusable throughout this project.
"""

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

import os
import re
import string
import itertools

import mimic_config


def get_mimic_version():
    """
    Returns mimic version as a formatted string.
    :return:
    """
    return '{}.{}'.format(mimic_config.MIMIC_VERSION_MAJOR,
                          mimic_config.MIMIC_VERSION_MINOR)


def get_mimic_dir():
    """
    Find path to mimic directory. Operating system agnostic. If Maya is not
    running, this function will assume that Mimic is installed in the latest
    version of Maya available on this computer.
    :return:
    """
    if MAYA_IS_RUNNING:
        dir_mimic = pm.getModulePath(moduleName='mimic')
        # if RuntimeError raised then mimic is not on Module Path
        # Check version
        installed_version = pm.moduleInfo(version=True, moduleName='mimic')
        if installed_version != get_mimic_version():
            raise Exception('Mimic version conflict')
    else:  # Maya not running
        if os.name == 'posix':  # macOS
            dir_mimic = os.path.expanduser('~/Library/Preferences/Autodesk/maya/modules/mimic')
        elif os.name == 'nt':  # windows
            dir_mimic = os.path.expanduser('~/Documents/maya/modules/mimic')
        else:  # Unsupported operating system
            raise Exception('Unsupported OS')
            # Assume version check passed
    if os.path.isdir(dir_mimic):  # make sure it exists
        return dir_mimic
    else:
        raise Exception('Directory not found: ' + dir_mimic)


def get_rigs_dict():
    """
    Get rigs dict from rigs directory.
    :return:
    """
    rigs = {}
    extension = '.ma'
    # Get rigs directory
    mimic_dir = get_mimic_dir()
    rigs_dir = '{}/rigs'.format(mimic_dir)
    # Get content of the rigs_paths dir
    rigs_dir_contents = os.listdir(rigs_dir)
    # Get rids directories; ignore hidden and user-ignored directories
    # which are prefixed with '.' and '_' respectively
    rigs_sub_dirs = [d for d in rigs_dir_contents
                     if not d.startswith('.') and not d.startswith('_')]
    for sub_dir_name in rigs_sub_dirs:
        sub_dir = '{}/{}'.format(rigs_dir, sub_dir_name)
        # Get content of the subdirectory
        try:
            sub_dir_contents = os.listdir(sub_dir)
            rigs_files = [f for f in sub_dir_contents if f.endswith(extension)]
            for rig_file in rigs_files:
                # Get entry for rigs dictionary
                name = '{} {}'.format(sub_dir_name, rig_file.split('.')[0])
                path = '{}/{}'.format(sub_dir, rig_file)
                rigs[name] = path
        except OSError:  # got a file
            pass  # skip
    return rigs


def get_rigs_names(rigs):
    """
    Get the names of all rigs from rigs dictionary.
    :param rigs: rigs dictionary.
    :return:
    """
    names = rigs.keys()
    names.sort()
    # Get default from config
    default = mimic_config.DEFAULT_ROBOT
    if default in names:
        names.remove(default)
        names.insert(0, default)
    return names


def num_to_str(num, include_sign=False, precision=6, padding=0):
    """
    Converts a number to a string with several.
    :param num: Number to convert to string.
    :param include_sign: If True, include '+' when positive.
    :param precision: Degree of precision for decimal.
    :param padding: Number of characters to use for left-padding.
    :return:
    """
    if num == 'infinity':
        raise ValueError('Invalid number')
    elif isinstance(num, str):
        return num
    elif num == 9E9:
        return '9E9'
    else:
        num = round(num, precision)
        if num == 0:
            num = abs(num)  # remove '-' sign
        num_string = '{:.{precision}f}'.format(num, precision=precision)
        if include_sign:
            if num >= 0:
                num_string = '+' + num_string
        if padding > 0:
            num_string = '{0:>{padding}}'.format(num_string, padding=padding)
        return num_string


def param_is_numeric(p):
    """
    Test whether any parameter is numeric; functionally, determines if any
    parameter is convertible to a float.
    :param p:
    :return:
    """
    try:
        float(p)
        return True
    except ValueError:
        return False


def str_is_numeric(s):
    """
    Tests if a string is numeric; does not respect the expression "infinity" or
    scientific notation such as "1E9"; functionally, determines if a string
    is convertible to a float.
    :param s: String to test
    :return: bool
    """
    l = string.lower(s)
    if l == "infinity" or "e" in l:
        return False
    return param_is_numeric(s)


def str_is_simple(s):
    """
    Tests if a string is valid for filenames. Checks that the string contains
    only lowercase, uppercase, numeric, _, and ' ' characters and that it isn't
    empty or None.
    :param s: String to test
    :return: bool
    """
    if s == '' or s is None:
        return False
    elif not re.match("^[a-zA-Z0-9 _]*$", s):
        return False
    return True


def compare_strings_as_lower(s1, s2):
    """
    Convert two strings to lowercase and check for equivalence.
    :param s1: String 1
    :param s2: String 2
    :return:
    """
    return string.lower(s1) == string.lower(s2)


def matrix_multiply_1xm_nxm(a, b):
    """
    Multiply a 1xM matrix and a NxM matrix.
    :param a: 1xM matrix
    :param b: NxM matrix
    :return:
    """
    result = [[0] * len(b[0]) for _ in range(len(a))]
    for i in range(len(a)):
        # iterate through columns of b
        for j in range(len(b[0])):
            # iterate through rows of b
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    return result


def matrix_multiply_3x3(a, b):
    """
    Multiply a 3x3 matrix by another 3x3 matrix.
    :param a: 3x3 matrix
    :param b: 3x3 matrix
    :return:
    """
    # Initialize output 3x3 matrix
    result = [[0 for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                # Perform matrix computation
                result[i][j] += a[i][k]*b[k][j]
    return result


def matrix_get_3x3_from_4x4(matrix):
    """
    Extract the coordinate vectors from an input matrix [1, 16]
    :param matrix:
    :return:
    """
    output = []
    for i in range(3):
        vector = []
        for j in range(3):
            vector.append(matrix[i][j])
        output.append(vector)
    return output


def transpose_list(l):
    """
    Transpose a list.
    :param l: List to transpose
    :return: Transposed list
    """
    result = [list(x) for x in zip(*l)]
    return result


def list_as_range_strings(values):
    """
    Format a list of single-range strings from a list of values; sorts input.
    :param values:
    :return:
    """
    values.sort()  # make sure numbers are consecutive
    value_groups = itertools.groupby(values, lambda n, c=itertools.count(): n - next(c))
    return [list_as_range_string(group) for i, group in value_groups]


def list_as_range_string(consecutive_values):
    """
    Format a single-range string from a list of consecutive values.
    :param consecutive_values: List of consecutive values
    :return:
    """
    if not isinstance(consecutive_values, list):
        consecutive_values = list(consecutive_values)
    if len(consecutive_values) > 1:
        return '{0}-{1}'.format(consecutive_values[0], consecutive_values[-1])
    else:
        return '{0}'.format(consecutive_values[0])
