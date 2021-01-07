#!usr/bin/env python
"""
Configuration parameters/preferences for Mimic.
"""

try:
    import pymel.core as pm
    from maya.api import OpenMaya

    maya_useNewAPI = True

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    OpenMaya = None
    MAYA_IS_RUNNING = False

import os
import json
import logging
import postproc

reload(postproc)

# Mimic Version Info
MIMIC_MODULE_NAME = 'Mimic'
MIMIC_VERSION_MAJOR = 1  # Must coincide with version in mimic.mod
MIMIC_VERSION_MINOR = 4  # Must coincide with version in mimic.mod
MIMIC_VERSION_PATCH = 1  # Must coincide with version in mimic.mod

# Set logging level
logging.getLogger().setLevel(logging.ERROR)

USER_PREFS_FILE = 'mimic_user_prefs.json'
BASE_NAMESPACE = 'MIMIC'
DELIM = '::'
PREFIX = BASE_NAMESPACE + DELIM  # 'MIMIC::'
POSTPROC_NAMESPACE = 'POSTPROC' + DELIM
CALLBACK_KEY = '_MIMIC_REGISTERED_CALLBACKS'

# PREFERENCE LEVELS
DEFAULT = 'DEFAULT'  # Default preferences
USER = 'USER'  # User-level preferences. (Working preferences stored in Maya
# environment in optionVar)
USER_JSON = 'USER_JSON'  # User-level preferences. (Stored on disk in JSON file)
FILE = 'FILE'  # File-level preferences
EXTERNAL = 'EXTERNAL'  # User-level preferences stored in an external json file


class Prefs(object):
    """
    This class allows for accessing Mimic Preferences. Preferences are divided
    into three disctinct types: default, user-level, and file-level.

    Default preferences represent Mimic's initial settings, are hard-coded into
    these source files, and should not be changed. These values are used when
    user-level and file-level preferences are unavailable.

    User-level preferences are stored in the USER_PREFS_FILE (defaults to
    /mimic/mimic_user_prefs.json) and can be set through the "Mimic Preferences"
    window, which is accesible through the "Prefs" icon in the Mimic shelf.
    User-level preferences (if available) will override default preferences.

    File-level preferences are stored in the specific Maya file in which they
    are set. These preferences are persistent, and they are set automatically
    when a user interacts with the main Mimic window. They will override default
    preferences and user-level preferences. These preferences are saved in a
    file's fileInfo object (accessible through pm.fileInfo), and the key names
    are prepended with "MIMIC_" to avoid any namespace collisions.

    This class is designed as a static class to encapsulate the related methods.
    You should import this class to access it's methods, but you should  not
    instantiate it.
    """
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

        :param local_key: str - name of the preference in the preference dict
        :param pref_level: str - PREFERENCE LEVEL defined above
        :return: value cast to the correct type. Type is inferred from the type
                 of the default value (stored in self.defaults).
        """
        logging.debug('Prefs.get(), local_key={}, pref_level={}'.format(local_key, pref_level))
        # Make sure the preference should exist.
        assert local_key in cls.defaults, \
            'Error retrieving preference {}. Preference does not exist'.format(local_key)

        prefs = cls._get_prefs_dict(pref_level)

        # Try to get the preference, but if we fail for any reason we should
        # try to get the default preference instead
        # noinspection PyBroadException
        try:
            val_str = prefs.get(cls._get_global(local_key))
            # Cast preference to the inferred type
            val = cls._from_value_string(val_str)
        except:
            logging.warning('Unable to return preference {} in {} preferences.'
                            'Returning default value instead.'
                            .format(local_key, pref_level))
            return cls.get(local_key, DEFAULT)

        logging.debug('value={}'.format(val))
        return val

    @classmethod
    def get_user_pref(cls, local_key):
        """
        Convenience wrapper around get().
        """
        return cls.get(local_key, pref_level=USER)

    @classmethod
    def get_prefs_from_json_file(cls, file_path):
        """
        Open a json file and return a stringified (flattened) version for
        storing in a pymel optionVar or fileInfo object.

        :param file_path: str - path to the json file
        :return: dictionary of user prefs with keys and values as type str
        """
        assert os.path.exists(file_path), 'File path does not exist!'
        # Read prefs file
        try:
            with open(file_path, 'r+') as prefs_file:
                user_prefs = json.load(prefs_file)
        except ValueError as e:
            logging.error('Unable to load user preferences from {}.\nError:{}'
                          .format(file_path, e))
            user_prefs = {}
        return cls._flatten_prefs_dict(user_prefs)

    @classmethod
    def _get_user_prefs_from_json_file(cls):
        """
        Wrapper around get_prefs_from_json_file() for accessing the default user
        prefs json file. Additional logic added to create a blank user prefs
        file if one doesn't exist.

        :return: dictionary of user prefs with keys and values as type str
        """
        logging.debug('Prefs.get_user_prefs()')
        user_prefs_path = '{}/{}'.format(cls._get_mimic_dir(), USER_PREFS_FILE)

        if not os.path.exists(user_prefs_path):
            logging.warning('User prefs json file not found.'
                            'Creating blank file.')
            # Create blank user prefs file if one doesn't exist
            cls.reset_user_prefs_file()
            user_prefs = {}
        else:
            user_prefs = cls.get_prefs_from_json_file(user_prefs_path)
        return user_prefs

    @classmethod
    def get_prefs(cls, pref_level=FILE, starts_with=PREFIX):
        """
        Get a dictionary of all Mimic preferences at the give preference level.

        :param pref_level: str - PREFERENCE LEVEL defined above
        :param starts_with: str - used to filter the larger dictionaries
            (fileInfo, optionVar) so that we only get a subset of all their values.
        :return: dict of preferences
        """
        prefs = cls._get_prefs_dict(pref_level)
        prefs = {k: v for k, v in prefs.items()
                 if k.startswith(starts_with)}
        return prefs

    @classmethod
    def copy_prefs(cls, source_prefs, dest_prefs, source_file_path=None):
        """
        Copy a preference dictionary the source location to the destination
        location. For example, this can be used to override a file's saved
        preferences with Mimic's default preferences.

        :param source_prefs: int - PREFERENCE LEVEL defined above
        :param dest_prefs: int - PREFERENCE LEVEL defined above
        :param source_file_path: str - Required when attempting to load
            preferences from an external json file
        :return: None
        """
        logging.debug('Prefs.copy_prefs(), source_prefs={}, dest_prefs={}'
                      .format(source_prefs, dest_prefs,))
        if source_prefs in (DEFAULT, USER, USER_JSON, FILE):
            src = cls.get_prefs(source_prefs)
        elif source_prefs == EXTERNAL:
            src = Prefs.get_prefs_from_json_file(source_file_path)
        else:
            logging.error('Error obtaining source prefs')
            return

        if dest_prefs in (USER, FILE):  # Can't override the other preferences
            dest = cls._get_prefs_dict(dest_prefs)
        else:
            logging.error('Error obtaining dest prefs dict')
            return

        # Update preferences dict
        dest.update(src)

    @classmethod
    def _to_stringval(cls, value):
        """
        Convert a value to a string representation. The string includes the type of
        the value as well as the value itself. We need to convert to a string
        because Maya's optionVar and fileInfo can only store strings.
            Example: 8.0  will be converted to 'FLOAT::8.0'

        :param value: any - value to be converted to a stringval
        :return: str - string representation of the value
        """
        # logging.debug('Prefs._to_stringval(), value={}'.format(value))

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
        return res

    @classmethod
    def _from_value_string(cls, value_string):
        """
        Convert a string representation of a value to an actual value. The
        string includes the type of the value as well as the value itself.
            Example: 'FLOAT::8.0' will be converted to 8.0

        :param value_string: str - string representation of a value
        :return: any - value cast to the correct type as defined by the value's type
            in the default preference dict
        """
        # logging.debug('Prefs._from_value_string(), value_string={}'.format(value_string))
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

        :param prefs: dict - prefs dict to flatten
        :param start_str: str - string to prepend on all keys
        :param delim: str - delimiter to use when concatenating strings
        :return: dict - flattened dict
        """
        logging.debug('Prefs._flatten_prefs_dict(), prefs={}, start_str={}, '
                      'delim={}'.format(prefs, start_str, delim))
        res = {}
        for k, v in prefs.items():
            logging.debug('Flattening k={}, v={}'.format(k, v))
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

        :param prefs: dict - flattened prefs dict
        :param delim: str - delimiter used when dict was flattened
        :return: dict - nested dict
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

        :param key: str - flattened key str. Ex: MIMIC:DEFAULTS:ETC
        :param val: any - value of the last key-value pair
        :param delim: str - delimiter to use when concatenating strings
        :param res: dict - result dict that holds the intermediate k/v pairs.
        Updated in place.
        :return: None
        """
        keys = key.split(delim, 1)
        start_key = keys.pop(0)
        if keys:
            cls._split_keys(keys[0], val, delim, res.setdefault(start_key, {}))
        else:
            res[start_key] = cls._from_value_string(val)

    @classmethod
    def reset_user_prefs_file(cls):
        """
        Set a user's prefs json file to an empty json object

        :return: None
        """
        user_prefs_path = '{}/{}'.format(cls._get_mimic_dir(), USER_PREFS_FILE)
        # Create blank user prefs file
        with open(user_prefs_path, 'w') as prefs_file:
            prefs_file.write('{}')

    @classmethod
    def save_prefs_in_maya_file(cls,):
        """
        Load all (default, user, and file) config settings into the current file.
        Mimic will only access preferences saved in the current file.
        """
        # Get default preferences
        prefs = cls.get_prefs(DEFAULT)
        # Get user preferences and override default preferences
        prefs.update(cls.get_prefs(USER_JSON))
        # Get file preferences and override user preferences
        prefs.update(cls.get_prefs(FILE))

        # Save all preferences in the current maya file
        file_prefs = cls._get_prefs_dict(FILE)
        file_prefs.update(prefs)

    @staticmethod
    def _get_mimic_dir():
        """
        Wrapper around get_mimic_dir() to eliminate circular import issues.
        :return: str - mimic directory
        """
        from general_utils import get_mimic_dir
        return get_mimic_dir()

    @classmethod
    def _get_global(cls, local_key):
        """
        Prepend a prefix to the local key so there will be no namespace
        collisions when it is inserted into one of the dictionaries holding
        preferences.

        :param local_key: str - preference key in the preference dict
        :return: str - global key to be inserted/updated in the preference dict
        """
        return PREFIX + local_key

    @classmethod
    def _get_prefs_dict(cls, pref_level):
        """
        Return a flattened preference dictionary. This dictionary may contain
        keys that are not preferences. It is up to the user to filter and update
        these dictanaries.

        :param pref_level: str - PREFERENCE LEVEL defined above
        :return: dict - flat preference dict
        """
        assert pref_level in (DEFAULT, USER, USER_JSON, FILE),\
            'Invalid pref_level passed'
        if pref_level == FILE:
            return pm.fileInfo
        elif pref_level == USER:
            return pm.optionVar
        elif pref_level == USER_JSON:
            return cls._get_user_prefs_from_json_file()
        elif pref_level == DEFAULT:
            return cls._flatten_prefs_dict(cls.defaults)

    @classmethod
    def set(cls, local_key, val, pref_level=FILE, *_args):
        """
        Update a preference value.

        :param pref_level: str - PREFERENCE LEVEL defined above
        :param local_key: str - Name of the preference to update
        :param val: any - value of the preference to update. Must match the type
            of the default preference value
        :param _args: required by Maya to call a function from UI button
        :return: None
        """
        logging.debug('Prefs.set(), local_key={}, val={}, pref_level={}'
                      .format(local_key, val, pref_level))
        global_key = cls._get_global(local_key)
        prefs = cls._get_prefs_dict(pref_level)
        prefs[global_key] = cls._to_stringval(val)

    @classmethod
    def set_user_pref(cls, local_key, val, *_args):
        """
        Convenience wrapper around set()
        """
        cls.set(local_key, val, pref_level=USER)

    @classmethod
    def save_user_prefs_to_json(cls):
        """
        Save user preferences to the default json file.

        :return: None
        """
        logging.debug('Prefs.save_to_json()')
        user_prefs_path = '{}/{}'.format(cls._get_mimic_dir(), USER_PREFS_FILE)

        # Set focus to the Prefs window to force all ui callbacks to complete.
        pm.setFocus('mimic_preferences')

        # Get user preferences saved in the current Maya environment
        user_prefs = {k.split(PREFIX)[1]: v for k, v in pm.optionVar.items()
                      if k.startswith(PREFIX)}

        # Create a nested dictionary so the json output is easier to read
        user_prefs = cls._nest_pref_dict(user_prefs)

        with open(user_prefs_path, 'w') as prefs_file:
            json.dump(user_prefs, prefs_file, indent=4)

    @classmethod
    def get_postproc_options(cls, pref_level=FILE):
        """
        Return a UserOptions named-tuple given the desired pref_level

        :param pref_level: str - Prefence Level defined in this file
        :return: UserOptions named-tuple
        """
        logging.debug('Prefs.get_postproc_options(), pref_level={}'
                      .format(pref_level))
        base_str = PREFIX + POSTPROC_NAMESPACE + 'DEFAULT' + DELIM
        prefs_dict = cls.get_prefs(pref_level, base_str)

        # Fall back on default prefs if we can't access file prefs
        if not prefs_dict and pref_level == FILE:
            prefs_dict = cls.get_prefs(DEFAULT, base_str)

        options = {k.split(base_str)[1].lower(): cls._from_value_string(v)
                   for k, v in prefs_dict.items()}
        logging.debug('options={}'.format(options))

        # noinspection PyUnresolvedReferences
        return postproc.postproc_options.configure_user_options(**options)

    @classmethod
    def update_postproc_options(cls, pref_level, local_key, value, *_args):
        """
        Wrapper around set(). Builds a modified local key (needed if we want to
        implement custom post-proc settings for each post-proc) later.

        :param pref_level: str - PREFERENCE LEVEL defined above
        :param local_key: str - Name of the preference to update
        :param value: any - value of the preference to set
        :param _args: required by Maya to call a function from UI button
        :return: None
        """
        local_key = POSTPROC_NAMESPACE + 'DEFAULT' + DELIM + \
                    local_key.upper().replace(' ', '_')
        cls.set(local_key, value, pref_level)

    @classmethod
    def delete_prefs(cls, pref_level):
        """
        Delete preferences associated with a given preference level.

        :param pref_level: str - PREFERENCE LEVEL defined above. USER or FILE
        :return: None
        """
        assert pref_level in (USER, FILE), \
            'Unable to delete preferences. Incorrect preference level specfied.'

        prefs_dict = cls._get_prefs_dict(pref_level)
        to_delete = \
            [pref for pref in prefs_dict if pref.startswith(BASE_NAMESPACE)]
        for pref in to_delete:
            prefs_dict.pop(pref)

# -----------------------------------------------------------------------------
#   Callback related functions
# -----------------------------------------------------------------------------
#
# Callbacks and related functions to handle reloading Mimic when a file is
# opened or created. This ensures that we load the correct preferences for the
# file and we don't use stale data.


def reload_mimic(*_args):
    """
    Callback function to re-launch Mimic.
    :param _args: required by Maya to call a function from UI button
    :return: None
    """
    command = "import sys\n" \
              "sys.dont_write_bytecode = True  # don't write PYCs\n" \
              "import mimic\n" \
              "reload(mimic)\n" \
              "mimic.run()"
    pm.evalDeferred(command)


# noinspection PyUnresolvedReferences
def register_config_callbacks():
    """
    Registers callback function to fire whenever a Maya file is opened or
    created.

    :return: None
    """

    # Make sure there are no callbacks that we've registered and never
    # de-registered... this could happen if Mimic crashed.
    de_register_callbacks()

    callbacks = [str(OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kAfterNew, reload_mimic)),
        str(OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kAfterOpen, reload_mimic))]

    pm.optionVar[CALLBACK_KEY] = ' '.join(callbacks)


# noinspection PyUnresolvedReferences
def de_register_callbacks():
    """
    De-registers callback function.

    :return: None
    """
    callbacks = pm.optionVar.get(CALLBACK_KEY)
    pm.optionVar[CALLBACK_KEY] = ' '

    if callbacks:
        callback_ids = [int(callback_id) for callback_id in callbacks.split()]
        for callback_id in callback_ids:
            try:
                OpenMaya.MMessage.removeCallback(callback_id)
            except RuntimeError:
                # Most likely Maya crashed and the callback was automatically
                # removed.
                pass
