#!usr/bin/env python

"""
This module contains basic configuration parameters for Mimic.
"""

# Mimic information!
try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
    # TODO(Harry): Standardize this implementation
    import maya.api.OpenMaya as om

    maya_useNewAPI = True

except ImportError:  # Maya is not running
    pm = None
    om = None
    MAYA_IS_RUNNING = False

import os
import json
import postproc

reload(postproc)

MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 4  # Must coincide with version in mimic.mod
MIMIC_VERSION_PATCH = 1  # Must coincide with version in mimic.mod

USER_PREFS_FILE = 'mimic_user_prefs.json'
BASE_NAMESPACE = 'MIMIC'
DELIM = '::'
PREFIX = BASE_NAMESPACE + DELIM  # 'MIMIC::'
POSTPROC_NAMESPACE = 'POSTPROC' + DELIM
CALLBACK_KEY = '_MIMIC_REGISTERED_CALLBACKS'

# PREFERENCE LEVELS
DEFAULT = 0
USER = 10
FILE = 20


# TODO(Harry): Documentation...
class Prefs(object):
    """
    This class allows for accessing

    Default preferences are stored in this class. These values represent Mimic's initial
    preference values and they should not be changed. These values are applied when creating a
    new file.

    User-level preferences are stored in the USER_PREFS_FILE (defaults to
    /mimic/mimic_user_prefs,json) and can be set through the "Mimic Preferences" window, which is
    accesible through the "Prefs" icon in the Mimic shelf. User-level preferences will override
    default preferences when creating new files.

    File-level preferences are stored in the specific Maya file in which they were set. These
    preferences are persistent, and they are set automatically when a user interacts with the main
    Mimic window. They will override default preferences and user-level preferences. These
    preferences are saved iinn a file's fileInfo object (accessible through pm.fileInfo),
    and the key names are prepended with "MIMIC_" to avoid any name collisions.
    """
    # TODO(Harry): OrderedDict?
    defaults = {
        'DEFAULT_ROBOT': '',  # E.G 'KUKA KR 60-3'

        # Nominal Velocity, Acceleration, and Jerk limits
        # In the where the above limits aren't specified on the robot rig,
        # we can use these nominal values as defaults
        'NOMINAL_VELOCITY_LIMIT': 999.9,
        'NOMINAL_ACCELERATION_LIMIT': 9999.9,
        'NOMINAL_JERK_LIMIT': 99999.9,

        # Postproc_config
        # Default parameters
        'DEFAULT_PROGRAM_DIRECTORY': '',
        'DEFAULT_POST_PROCESSOR': '',  # E.G. 'KUKA EntertainTech'
        'DEFAULT_OUTPUT_NAME': 'output',
        'DEFAULT_TEMPLATE_NAME': 'template',

        # Pre-processor parameters
        'DEFAULT_SAMPLE_RATE_VALUE': 1,
        'DEFAULT_SAMPLE_RATE_UNITS': 'frames',  # 'seconds' or 'frames',
        'SAMPLE_KEYFRAMES_ONLY': False,

        # NOTE: These values aren't settable in the Preferences window because
        # it doesn't make sense to have these as user-level preferences, BUT
        # they will still be tracked as file-level preferences.
        'ANIMATION_RANGE_START': 1,
        'ANIMATION_RANGE_END': 200,

        # Output options
        'OPTS_IGNORE_WARNINGS': False,
        'OPTS_OVERWRITE_EXISTING_FILE': True,

        # User options
        'OPTS_PREVIEW_IN_VIEWPORT': False,
        'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT': False,

        # UI Settings
        # NOTE Shader range is automatically set on robots as they are
        # added to the scene
        'SHADER_RANGE': 20,

        # Postprocessor Options
        'POSTPROC': {
            'DEFAULT': {
                'IGNORE_MOTION': False,
                'USE_MOTION_AS_VARIABLES': False,
                'USE_LINEAR_MOTION': False,
                'USE_NONLINEAR_MOTION': True,
                'USE_CONTINUOUS_MOTION': False,
                'INCLUDE_AXES': True,
                'INCLUDE_POSE': False,
                'INCLUDE_EXTERNAL_AXES': False,
                'INCLUDE_CONFIGURATION': False,
                'IGNORE_IOS': False,
                'PROCESS_IOS_FIRST': False,
                'INCLUDE_DIGITAL_OUTPUTS': False,
                'INCLUDE_DIGITAL_INPUTS': False,
                'INCLUDE_ANALOG_OUTPUTS': False,
                'INCLUDE_ANALOG_INPUTS': False,
                'INCLUDE_CHECKSUM': False,
                'INCLUDE_TIMESTAMP': False,
            }
        }
    }

    @classmethod
    def get(cls, local_key, pref_level=FILE):
        """
        Return the value of the file-level preference with the given name.

        :param local_key: str - name of the preference key
        :return: value cast to the correct type. Type is inferred from the type of
                 the default value.
        """
        print('get()', local_key, pref_level)
        # Make sure the preference should exist.
        assert local_key in cls.defaults, \
            'Error retrieving preference {}. Preference does not exist'.format(local_key)

        prefs = cls.get_prefs_dict(pref_level)

        # Try to get the preference, but if we fail for any reason we should
        # try to get the default preference instead
        try:
            val_str = prefs.get(cls._get_global(local_key))
            # Cast preference to the inferred type
            val = cls._from_value_string(val_str)
        except:
            return cls.get(local_key, DEFAULT)

        # TODO(Harry): figure out what the postprocs need when initializing?
        return val

    @classmethod
    def get_user_pref(cls, local_key):
        return cls.get(local_key, pref_level=USER)

    @classmethod
    def get_default_prefs_dict(cls):
        res = cls._flatten_prefs_dict(cls.defaults)
        return res

    @classmethod
    def get_user_prefs_dict_from_json(cls, mimic_dir):
        """
        Open the user prefs json file and return a stringified (flattened) version for storing in a
        pymel optionVar or fileInfo object.

        :param mimic_dir: path to the Mimic directory
        :return: dictionary of user prefs with strings for keys and values
        """
        user_prefs_path = '{}/{}'.format(mimic_dir, USER_PREFS_FILE)

        if not os.path.exists(user_prefs_path):
            # Create blank user prefs file if one doesn't exist
            cls.reset_user_prefs_file(mimic_dir)
            user_prefs = {}
        else:
            # Read prefs file
            try:
                with open(user_prefs_path, 'r+') as prefs_file:
                    user_prefs = json.load(prefs_file)
            except ValueError as e:
                print('Unable to load user preferences from {}.\nError:{}'
                      .format(user_prefs_path, e))
                user_prefs = {}

        return cls._flatten_prefs_dict(user_prefs)

    @classmethod
    def get_prefs(cls, pref_level=FILE, starts_with=PREFIX):
        """
        Get a dictionary of all Mimic preferences that are set.
        current Maya file
        :return: dict of preferences
        """
        prefs = cls.get_prefs_dict(pref_level)
        file_prefs = {k: v for k, v in prefs.items()
                      if k.startswith(starts_with)}
        return file_prefs

    @classmethod
    def load_into_environment(cls, pref_level, mimic_dir=None):
        """
        Load default Mimic preferences into the Maya environment.
        :return: None
        """
        print('load_into_environment()', (pref_level, mimic_dir))
        if pref_level == DEFAULT:
            pm.optionVar.update(cls.get_default_prefs_dict())
        elif pref_level == USER and mimic_dir is not None:
            pm.optionVar.update(cls.get_user_prefs_dict_from_json(mimic_dir))
        else:
            assert not 'Unable to load preferences into Maya environment'

    @classmethod
    def _to_stringval(cls, value):
        """
        Convert a value to a string representation. The string includes the type of
        the value as well as the value itself. We need to convert to a string
        because Maya's optionVar and fileInfo can only store strings.
            Example: 8.0  will be converted to 'FLOAT::8.0'

        :param value: value to be converted to a stringval
        :return: string: string representation of the value
        """
        print('to_value_string()', value)

        res = None
        if type(value) == str or type(value) == unicode:
            res = 'STR'
        elif type(value) == bool:
            res = 'BOOL'
        elif type(value) == int:
            res = 'INT'
        elif type(value) == float:
            res = 'FLOAT'
        res = res + DELIM + str(value)
        print(res)
        return res

    @classmethod
    def _from_value_string(cls, value_string):
        """
        Convert a string representation of a value to an actual value. The string
        includes the type of the value as well as the value itself.
            Example: 'FLOAT::8.0' will be converted to 8.0

        :param value_string: string representation of a value
        :return: value cast to the embedded correct type
        """
        print('from_value_string()', value_string)
        try:
            val_type, value_string = value_string.split(DELIM)
        except ValueError:
            return value_string
        res = None
        if val_type == 'STR':
            res = str(value_string)
        elif val_type == 'BOOL':
            res = True if value_string == 'True' else False
        elif val_type == 'INT':
            res = int(value_string)
        elif val_type == 'FLOAT':
            res = float(value_string)
        return res

    @classmethod
    def _flatten_prefs_dict(cls, prefs, start_str=PREFIX, delim=DELIM):
        """
        Get a flattened (stringified) version of a prefs dict. This will take dict
        within a dict, and flatten it to a single level with only strings for keys
        and strings for values.

        :param prefs: prefs dict to flatten
        :param start_str: string to prepend on all keys
        :return: flattened dict
        """
        res = {}
        for k, v in prefs.items():
            val_type = type(v)
            if val_type == dict:
                start = start_str + k + delim
                res.update(cls._flatten_prefs_dict(v, start))
            else:
                res.update({start_str + k: cls._to_stringval(v)})
        return res

    @classmethod
    def _nest_pref_dict(cls, prefs, delim=DELIM):
        """
        Return a nested (unflattened) version of a prefs dict.

        :param prefs: flattened prefs dict
        :param delim: dict key delimiter
        :return: nested dict
        """
        res = {}
        for k, v in prefs.items():
            cls._split_keys(k, v, delim, res)
        return res

    @classmethod
    def _split_keys(cls, key, val, delim, res):
        """
        Recursively split the key on the delimiter and update the result dict in
        place with a nested key/value pair. The final key is the last key that is
        split from the key arg.

        :param key: flattened key str. Ex: MIMIC:DEFAULTS:ETC
        :param val: value of the final key value pair
        :param delim: character that splits the key
        :param res: result dict
        :return: None
        """
        keys = key.split(delim, 1)
        start_key = keys.pop(0)
        if keys:
            cls._split_keys(keys[0], val, delim, res.setdefault(start_key, {}))
        else:
            res[start_key] = cls._from_value_string(val)

    @classmethod
    def reset_user_prefs_file(cls, mimic_dir):
        """
        Set a user's prefs json file to an empty json object
        :param mimic_dir: str - Mimic directory
        :return: None
        """
        user_prefs_path = '{}/{}'.format(mimic_dir, USER_PREFS_FILE)
        # Create blank user prefs file
        with open(user_prefs_path, 'w') as prefs_file:
            prefs_file.write('{}')

    @classmethod
    def save_prefs_in_maya_file(cls, mimic_dir):
        """
        Load all (default, user, and file) config settings into the current file.
        Mimic will only access preferences saved in the current file.
        """
        # Get default preferences

        prefs = cls.get_prefs_dict(DEFAULT)
        # print(prefs)

        # Get user preferences and override default preferences
        prefs.update(cls.get_user_prefs_dict_from_json(mimic_dir))
        # print(prefs)

        # Get file preferences and override user preferences
        prefs.update(cls.get_prefs(FILE))
        # print(prefs)
        # Save all preferences in the current maya file (fileInfo)
        pm.fileInfo.update(prefs)

    @classmethod
    def _get_global(cls, local_key):
        return PREFIX + local_key

    @classmethod
    def get_prefs_dict(cls, pref_level):
        if pref_level == FILE:
            return pm.fileInfo
        elif pref_level == USER:
            return pm.optionVar
        elif pref_level == DEFAULT:
            return cls.get_default_prefs_dict()
        assert not 'Invalid pref_level passed'

    @classmethod
    def set(cls, local_key, val, pref_level=FILE, *args):
        """
        Update a preference in the current file
        :param local_key: str - Name of the preference to update
        :param val: str - value of the preference to update
        :param args: Unused. To catch and extra args Maya may optionally pass
        :return: None
        """
        print('set()', (local_key, val, pref_level, args))
        global_key = cls._get_global(local_key)
        prefs = cls.get_prefs_dict(pref_level)
        prefs[global_key] = cls._to_stringval(val)

    @classmethod
    def set_user_pref(cls, local_key, val, *args):
        print('set_user_prefs()', (local_key, val, args))
        cls.set(local_key, val, pref_level=USER)

    @classmethod
    def save_to_json(cls, mimic_dir):
        user_prefs_path = '{}/{}'.format(mimic_dir, USER_PREFS_FILE)

        # Set focus to the Prefs window to force all ui callbacks to complete.
        pm.setFocus('mimic_preferences')

        # Get user preferences saved in the current Maya environment
        user_prefs = {k.split(PREFIX)[1]: v for k, v in pm.optionVar.items()
                      if k.startswith(PREFIX)}

        # Create a nested dictionary so the json output is easier to read
        user_prefs = cls._nest_pref_dict(user_prefs)

        # TODO(Harry): OrderedDict for pretty output?
        with open(user_prefs_path, 'w') as prefs_file:
            json.dump(user_prefs, prefs_file, indent=4)

    @classmethod
    def get_postproc_options(cls, pref_level=FILE):
        """
        Return a UserOptions named-tuple given the desired pref_level

        :param pref_level: str - FILE or USER
        :return:
        """
        print('get_postproc_options()', pref_level)
        base_str = PREFIX + POSTPROC_NAMESPACE + 'DEFAULT' + DELIM
        prefs_dict = cls.get_prefs(pref_level, base_str)

        options = {k.split(base_str)[1].lower(): cls._from_value_string(v)
                   for k, v in prefs_dict.items()}
        print('options:', options)

        # noinspection PyUnresolvedReferences
        return postproc.postproc_options.configure_user_options(**options)

    @classmethod
    def update_postproc_options(cls, pref_level, local_key, value, *args):
        local_key = POSTPROC_NAMESPACE + 'DEFAULT' + DELIM + local_key.upper().replace(' ', '_')
        cls.set(local_key, value, pref_level)

    @classmethod
    def delete_prefs(cls, pref_level):
        if pref_level in (USER, FILE):
            prefs_dict = cls.get_prefs(pref_level)
            to_delete = \
                [pref for pref in prefs_dict if pref.startswith(BASE_NAMESPACE)]
            for pref in to_delete:
                prefs_dict.pop(pref)


# -------------------------------------------------------------------------------
#   Callback related functions
# -------------------------------------------------------------------------------
#
# Callbacks and related functions to handle reloading Mimic when a file is
# opened or created. This ensures that we load the correct preferences for the
# file instead of relying on stale data.

def reload_pref_callback(*args):
    """
    :param args: Unused. Handles args that Maya passes when calling this function
    :return: None
    """
    # TODO(Harry): Track down bug where mimic window is re-launched multiple
    #  times when this callback fires
    import mimic
    reload(mimic)
    mimic.run()


def de_register_callbacks():
    callbacks = pm.optionVar.get(CALLBACK_KEY)
    pm.optionVar[CALLBACK_KEY] = ' '

    if callbacks:
        callback_ids = [int(callback_id) for callback_id in callbacks.split()]
        for callback_id in callback_ids:
            try:
                om.MMessage.removeCallback(callback_id)
            except RuntimeError:
                # Most likely Maya crashed and the callback was automatically
                # removed.
                pass


def register_config_callbacks():
    # Make sure there are no callbacks that we've registered and never
    # de-registered... this could happen if Mimic crashed.
    de_register_callbacks()

    callbacks = [str(om.MSceneMessage.addCallback(
        om.MSceneMessage.kAfterNew, reload_pref_callback)),
        str(om.MSceneMessage.addCallback(
            om.MSceneMessage.kAfterOpen, reload_pref_callback))]

    pm.optionVar[CALLBACK_KEY] = ' '.join(callbacks)
