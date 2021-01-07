#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
The main module.
"""

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False
import os

import general_utils
import mimic_config
import mimic_ui

reload(general_utils)
reload(mimic_config)
reload(mimic_ui)


def load_mimic_plugins():
    """
    Loads required python plugins into Maya from a directory.
    These are Dependency Graph and Command plugins that should be loaded into
    Maya's plugin manager
    :return:
    """
    # Plugin is dependent on the following scripts
    required_plugins = [
        'robotIK',
        'robotLimitBlender',
        'snapTransforms'
    ]
    # Check to see if each plug-in is loaded
    for plugin in required_plugins:
        # If the plug-in is not loaded:
        if not pm.pluginInfo(plugin, query=True, loaded=True):
            try:
                # Try loading it (and turn on autoload)
                pm.loadPlugin(plugin)
                pm.pluginInfo(plugin, autoload=True)
                print '{} Plug-in loaded'.format(plugin)
            except Exception:  # Unknown error
                pass


def confirm_requirements_exist():
    """
    Confirm that the directories required for Mimic to run do, in fact, exist.
    Confirm that the rigs directory contains something. Confirm that files, such
    as LICENSE and mimic.mod, exist.
    :return:
    """
    # Check required directories
    requirements = [
        'rigs',
        'plug-ins',
        'shelves',
        'scripts',
        'docs/LICENSE.md',
        'mimic.mod',
    ]
    dir_mimic = general_utils.get_mimic_dir()
    for requirement in requirements:
        if '.mod' in requirement:  # not a directory (.md, .mod)
            parent = os.path.abspath(os.path.join(dir_mimic, os.pardir))
            path = '{}/{}'.format(parent, requirement)
        else:
            path = '{}/{}'.format(dir_mimic, requirement)
        try:  # Check that directories all exist
            assert os.path.exists(path)
        except AssertionError:
            if 'LICENSE.md' in path:  # Missing license!
                warning = 'Exception: We noticed that you don\'t have a copy of our LICENSE! ' \
                          'It needs to be in your maya/modules directory at all times! ' \
                          'Download the latest release or clone our GitHub repository!'
                raise Exception(warning)
            else:
                warning = 'Exception: We noticed that you\'re missing the requirement: {}! ' \
                          'Download the latest release or clone our GitHub repository! ' \
                    .format(requirement)
                raise Exception(warning)
        except UnicodeError:
            warning = 'Exception: Sorry! You\'ve encountered a known, but unsolved issue! ' \
                      'The path to the Mimic directory contains unicode characters, which ' \
                      'are sometimes found in usernames, and Mimic gets confused. We\'re ' \
                      'working on this and you\'re welcome to help!'
            raise Exception(warning)
        try:  # Check that the rigs directory has robots
            if requirement == 'rigs':
                items = os.listdir(path)
                subdir_paths = [os.path.join(path, item) for item in items]
                assert any(os.path.isdir(subdir_path) for subdir_path in subdir_paths)
                for subdir_path in subdir_paths:
                    try:
                        items = os.listdir(subdir_path)
                        assert any('.ma' in item for item in items)
                        continue
                    except OSError:  # not a directory (.md)
                        pass
        except AssertionError:
            # Don't block Mimic from running
            warning = 'Warning: We noticed that you don\'t have any robot rigs! ' \
                      'Download the latest rigs from out GitHub repository ' \
                      'and add them to mimic/rigs!'
            raise Exception(warning)


def run():
    """
    Check that mimic is all there, loaded, and then create the Mimic UI.
    :return:
    """
    # Perform preliminary checks
    confirm_requirements_exist()
    load_mimic_plugins()
    # Update file preferences with user current preferences
    mimic_config.Prefs.save_prefs_in_maya_file()
    # Build the UI itself
    mimic_ui.build_mimic_ui()
    # Register callbacks that reload mimic when a file is opened/created
    mimic_config.register_config_callbacks()
