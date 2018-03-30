#!usr/bin/env python

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


def load_mimic_plugins(plugin_file_names):
    """
    Loads required python plugins into Maya from a directory.
    These are Dependency Graph and Command plugins that should be loaded into
    Maya's plugin manager
    :param plugin_file_names: List of required plug-ins 
    :return:
    """
    # Check to see if each plug-in is loaded
    for script in plugin_file_names:
        # If the plug-in is not loaded:
        if not pm.pluginInfo(script, query=True, loaded=True):
            try:
                # Try loading it (and turn on autoload)
                pm.loadPlugin(script)
                pm.pluginInfo(script, autoload=True)
                print '{} Plug-in loaded'.format(script)
                continue
            except Exception as e:
                pm.warning('Could not load plugin {}: {}'.format(script, e))
        # If it's already loaded:
        print '{} Plug-in already loaded'.format(script)


def check_required_directories():
    """
    Confirm that the directories required for Mimic to run do, in fact, exist.
    Confirm that the rigs directory contains something.
    :return:
    """
    # Check required directories
    required_directories = [
        'rigs',
        'plug-ins',
        'shelves',
        'scripts/postproc'
    ]
    dir_mimic = general_utils.get_mimic_dir()
    for d in required_directories:
        path = '{}/{}'.format(dir_mimic, d)
        try:
            assert os.path.isdir(path)
            if d == 'rigs':  # Check for rigs
                items = os.listdir(path)
                assert any(os.path.isdir(os.path.join(path, item)) for item in items)
        except AssertionError:
            raise Exception("You don't have all of the necessary directories "
                            "for Mimic to run. Download the latest release from "
                            "our GitHub repository!")


def run():
    """
    Creates the Mimic UI.
    :return:
    """
    # Confirm that Mimic is all there
    check_required_directories()

    # Load dependencies
    load_mimic_plugins(mimic_config.REQUIRED_PLUGINS)

    # Generate UI itself
    mimic_ui.build_mimic_ui()
