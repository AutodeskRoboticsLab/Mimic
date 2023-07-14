#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create the Mimic Preferences UI
"""

try:
    import pymel.core as pm
    import maya.cmds as cmds

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

import general_utils
import mimic_config
import mimic_program
import mimic_utils
import mimic_external_axes
import mimic_io
import mimic_ui
from postproc import postproc_setup
from postproc import postproc_options
from analysis import analysis
import importlib

importlib.reload(general_utils)
importlib.reload(mimic_config)
importlib.reload(mimic_program)
importlib.reload(mimic_utils)
importlib.reload(mimic_external_axes)
importlib.reload(mimic_io)
importlib.reload(postproc_setup)
importlib.reload(postproc_options)
importlib.reload(analysis)

Prefs = mimic_config.Prefs


class Window(object):
    """
    Main Window class that other UI windows should inherit from. Right now only
    the Preferences window inherits from this class. It should probably get
    moved out to mimic_ui if we want other windows to inherit from it.
    """

    def __init__(self, title, name, width):
        """
        :param title: str - window title displayed at the tope of the window
        :param name:  str - unique identifier for the window
        :param width:  int - desired window width. This can be overridden by
            chilren UI elements that require additional width
        """
        self.window_title = title
        self.window_name = name
        self.window_width = width  # Overall window width
        # Maximum width of a nested/inner frame (assumes a 5px pad on left/right of window)
        self.frame_width = self.window_width - 10

    def _create_window(self):
        # Create window
        window = cmds.window(self.window_name,
                             sizeable=False,
                             resizeToFitChildren=True,
                             title=self.window_title)

        # Set window size. This needs to be set separately from window creation,
        # because Maya overrides settings passed during window creation.
        # Setting height/width equal to one forces the window to resize to the
        # smallest possible size to contain any children UI elements
        cmds.window(window, edit=True, width=1, height=1)
        return window

    def reload_window(self):
        """
        Relaunches the window.
        :return: None
        """
        command = "import sys\n" \
                  "sys.dont_write_bytecode = True  # don't write PYCs\n" \
                  "import importlib\n" \
                  "import {}\n" \
                  "importlib.reload({})\n" \
                  "{}.{}()".format(__name__,
                                   __name__,
                                   __name__,
                                   self.__class__.__name__)
        cmds.evalDeferred(command)

    def delete_window(self):
        """
        Delete the window.
        :return: None
        """
        # If the window already exists, delete the window
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name, window=True)

    def _push_ui_template(self):
        """
        Create a UI template that holds default parameters for commonly used UI
        elements. Push the template onto the UI stack so that all following UI
        elements will automatically inherit these default parameters. This must
        be called after the UI window is created.
        """
        if cmds.uiTemplate(self.window_name, exists=True):
            cmds.deleteUI(self.window_name, uiTemplate=True)

        cmds.uiTemplate(self.window_name)
        cmds.setUITemplate(self.window_name, pushTemplate=True)

    def _pop_ui_template(self):
        """
        Pop the UI template from the UI stack. All elements after this call will
        not inherit from the window's UI template.
        """
        cmds.setUITemplate(self.window_name, popTemplate=True)

    @staticmethod
    def warning_window(title, message):
        """
        Display simple Yes/No confirmation window with a warning icon.

        :param title: str - Title of the confirmation window
        :param message: str - Message that the window should display

        :return: bool: True is user clicks "Yes", otherwise False
        """
        res = cmds.confirmDialog(title=title,
                                 messageAlign='right',
                                 message=message,
                                 button=['Yes', 'No'],
                                 defaultButton='Yes',
                                 cancelButton='No',
                                 dismissString='No',
                                 icon='warning')
        return True if res == 'Yes' else False


class MimicPreferencesWindow(Window):
    def __init__(self):
        super(MimicPreferencesWindow, self).__init__(title='Mimic Preferences',
                                                     name='mimic_preferences',
                                                     width=325)
        # TODO(evanatherton): Replace this header
        self.header_file = 'prefs_header.png'
        self.header_width = 244
        self.header_height = 60

        self.delete_window()

        # Load Default Mimic prefs into Maya environment
        Prefs.copy_prefs(mimic_config.DEFAULT, mimic_config.USER)
        Prefs.copy_prefs(mimic_config.USER_JSON, mimic_config.USER)

        self._push_ui_template()
        self.__build_ui()

    def _push_ui_template(self):
        """
        Set UI style.
        :return: None
        """
        # Call super class to set up the UI template for us
        super(MimicPreferencesWindow, self)._push_ui_template()

        # Set UI template
        cmds.rowLayout(defineTemplate=self.window_name, numberOfColumns=2, adjustableColumn=2,
                       columnWidth2=(90, 1), height=20)
        cmds.separator(defineTemplate=self.window_name, height=5, style='none')
        cmds.columnLayout(defineTemplate=self.window_name, adj=True, columnAttach=('both', 5))
        cmds.textField(defineTemplate=self.window_name, font=mimic_ui.FONT)
        cmds.frameLayout(defineTemplate=self.window_name, collapsable=False)
        cmds.button(defineTemplate=self.window_name, height=25)

    def __build_ui(self):
        # Create window
        mimic_prefs_window = self._create_window()
        self._push_ui_template()

        # Draw header/logo
        cmds.columnLayout()
        self.__add_header_image(self.header_file)
        cmds.setParent('..')

        # Set up Tab Layout
        tabs = cmds.tabLayout()

        # Build "General" Tab
        general_tab = cmds.columnLayout(width=self.frame_width, columnAttach=('both', 0))
        self.__build_general_settings_frame()
        self.__build_motion_limits_frame()
        self.__build_ui_settings_frame()
        self.__build_program_settings_frame()
        self.__build_save_prefs_button()
        cmds.setParent('..')

        # Build "Post Processor" Tab
        postproc_tab = cmds.columnLayout(width=self.frame_width, columnAttach=('both', 0))
        self.__build_postproc_settings_frame()
        cmds.setParent('..')

        # Build "Hotkeys" Tab
        hotkeys_tab = cmds.columnLayout(width=self.frame_width, columnAttach=('both', 0))
        self.__build_hotkeys_frame()
        cmds.setParent('..')

        # Build "Advanced" Tab
        advanced_tab = cmds.columnLayout(width=self.frame_width, columnAttach=('both', 0))
        self.__build_advanced_frame()
        cmds.setParent('..')

        # Register tabs
        cmds.tabLayout(tabs, edit=True, tabLabel=((general_tab, 'General'),
                                                  (postproc_tab, 'Post Processor'),
                                                  (hotkeys_tab, 'Hotkeys'),
                                                  (advanced_tab, 'Advanced')))

        # Draw window
        cmds.showWindow(mimic_prefs_window)
        # Reset UI template
        self._pop_ui_template()

        return mimic_prefs_window

    @staticmethod
    def __add_header_image(image_path):
        """
        """
        # Create rowLayout to hold out header image. This is done to get the proper
        # logo alignment and response to window size adjustments
        cmds.separator(height=8, style='none')
        cmds.rowLayout(height=50,
                       backgroundColor=[0.2, 0.2, 0.2],
                       numberOfColumns=3,
                       adjustableColumn=1,
                       columnAttach=[(3, 'right', -3)],
                       rowAttach=[(2, 'top', 15)])
        cmds.text(label='')
        cmds.image(image=image_path)
        cmds.text(label='')
        cmds.setParent('..')

    @staticmethod
    def __build_general_settings_frame():
        # General Settings Frame
        cmds.frameLayout(label="General Settings")
        cmds.columnLayout()
        cmds.separator()
        # Create list of robots
        cmds.rowLayout()
        cmds.text('Robot:')
        cmds.optionMenu(changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref, 'DEFAULT_ROBOT'))
        rigs = general_utils.get_rigs_dict()
        default_rig = Prefs.get_user_pref('DEFAULT_ROBOT')
        rig_names = general_utils.get_rigs_names(rigs, default_rig)
        for rig_name in rig_names:
            cmds.menuItem(label=rig_name)

        cmds.setParent('..')
        cmds.separator()
        cmds.setParent('..')
        cmds.setParent('..')

    @staticmethod
    def __build_motion_limits_frame():
        # Motion Limits Frame
        cmds.frameLayout(label="Motion Limits")
        cmds.columnLayout()
        cmds.rowLayout()
        cmds.text(label='Velocity:')
        cmds.floatField(min=0, pre=1, value=Prefs.get_user_pref('NOMINAL_VELOCITY_LIMIT'),
                        changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref, 'NOMINAL_VELOCITY_LIMIT'))
        cmds.setParent('..')
        cmds.rowLayout()
        cmds.text(label='Acceleration:')
        cmds.floatField(min=0, pre=1, value=Prefs.get_user_pref('NOMINAL_ACCELERATION_LIMIT'),
                        changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref, 'NOMINAL_ACCELERATION_LIMIT'))
        cmds.setParent('..')
        cmds.rowLayout()
        cmds.text(label='Jerk:')
        cmds.floatField(min=0, pre=1, value=Prefs.get_user_pref('NOMINAL_JERK_LIMIT'),
                        changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref, 'NOMINAL_JERK_LIMIT'))

        cmds.setParent('..')

        cmds.separator()
        cmds.setParent('..')
        cmds.setParent('..')

    @staticmethod
    def __build_ui_settings_frame():
        # UI Settings Frame
        cmds.frameLayout(label="UI Settings")
        cmds.columnLayout()
        cmds.separator()
        # Shader range row layout
        cmds.rowLayout()
        cmds.text(label='Shader range:')
        # Axis limit shader range float field
        cmds.floatField(min=0,
                        pre=0,
                        value=Prefs.get_user_pref('SHADER_RANGE'),
                        changeCommand=pm.CallbackWithArgs(
                            Prefs.set_user_pref,
                            'SHADER_RANGE'))

        cmds.setParent('..')
        cmds.separator()
        cmds.setParent('..')
        cmds.setParent('..')

    @staticmethod
    def __build_program_settings_frame():
        # Program Settings Frame
        cmds.frameLayout(label="Program Settings")
        cmds.columnLayout()

        cmds.rowLayout(numberOfColumns=3, columnWidth3=(90, 250, 30))
        cmds.text(label="Output directory:")
        cmds.textField('pref_programDirectoryText',
                       text=Prefs.get_user_pref('DEFAULT_PROGRAM_DIRECTORY'),
                       editable=False)
        cmds.symbolButton(image="setDirectory_icon.png",
                          width=32,
                          height=20,
                          command=pm.Callback(mimic_utils.set_dir,
                                              'pref_programDirectoryText',
                                              'DEFAULT_PROGRAM_DIRECTORY',
                                              Prefs.get_user_pref,
                                              Prefs.set_user_pref))
        cmds.setParent('..')  # End of rowLayout

        cmds.rowLayout()
        cmds.text(label='Output name:')
        cmds.textField(text=Prefs.get_user_pref('DEFAULT_OUTPUT_NAME'),
                       changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                         'DEFAULT_OUTPUT_NAME'))
        cmds.setParent('..')  # End of rowLayout

        cmds.rowLayout()
        cmds.text(label='Template name:')
        cmds.textField(text=Prefs.get_user_pref('DEFAULT_TEMPLATE_NAME'),
                       changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                         'DEFAULT_TEMPLATE_NAME'))
        cmds.setParent('..')  # End of rowLayout

        # Sample rate radio buttons
        cmds.separator(height=3)
        selected_units = Prefs.get_user_pref('DEFAULT_SAMPLE_RATE_UNITS')
        selected_value = Prefs.get_user_pref('DEFAULT_SAMPLE_RATE_VALUE')
        cmds.radioCollection('sample_rate_radio_collection_prefs')

        cmds.rowLayout(numberOfColumns=3,
                       adjustableColumn=3,
                       columnAttach=(1, 'left', 3),
                       columnWidth=[(1, 90), (2, 45)])

        cmds.radioButton('rb_timeInterval',
                         label='Sample rate:',
                         select=not Prefs.get_user_pref('SAMPLE_KEYFRAMES_ONLY'))
        cmds.floatField(minValue=0,
                        value=selected_value,
                        changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                          'DEFAULT_SAMPLE_RATE_VALUE'))
        cmds.radioButtonGrp('time_unit_radio_group',
                            labelArray2=['s', 'f'],
                            annotation='Sample rate units: seconds or frames',
                            numberOfRadioButtons=2,
                            columnWidth2=[32, 30],
                            select=1 if selected_units == 'seconds' else 2,
                            # 1-based int
                            onCommand1=pm.CallbackWithArgs(
                                Prefs.set_user_pref,
                                'DEFAULT_SAMPLE_RATE_UNITS', 'seconds'),
                            onCommand2=pm.CallbackWithArgs(
                                Prefs.set_user_pref,
                                'DEFAULT_SAMPLE_RATE_UNITS', 'frames'))

        cmds.setParent('..')  # End of rowLayout

        cmds.rowLayout(numberOfColumns=1,
                       adjustableColumn=1,
                       columnAttach=(1, 'left', 3))
        cmds.radioButton('rb_keyframesOnly',
                         label='Sample keyframes only',
                         enable=True,
                         select=Prefs.get_user_pref('SAMPLE_KEYFRAMES_ONLY'),
                         onCommand=pm.CallbackWithArgs(
                             Prefs.set_user_pref,
                             'SAMPLE_KEYFRAMES_ONLY', True),
                         offCommand=pm.CallbackWithArgs(
                             Prefs.set_user_pref,
                             'SAMPLE_KEYFRAMES_ONLY', False)
                         )

        cmds.setParent('..')  # End of rowLayout

        # Output options
        cmds.separator(height=11, style='out')
        cmds.checkBox(label="Overwrite existing file",
                      value=Prefs.get_user_pref('OPTS_OVERWRITE_EXISTING_FILE'),
                      annotation='If checked, an existing file with the input '
                                 'output name will be overwritten',
                      changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                        'OPTS_OVERWRITE_EXISTING_FILE'))
        cmds.checkBox(label="Ignore warnings",
                      value=Prefs.get_user_pref('OPTS_IGNORE_WARNINGS'),
                      annotation='If checked, all warnings will be ignored and '
                                 'a program will be written',
                      changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                        'OPTS_IGNORE_WARNINGS'))

        # Preview Options
        cmds.checkBox(label="Preview in viewport",
                      value=Prefs.get_user_pref('OPTS_PREVIEW_IN_VIEWPORT'),
                      annotation='If checked, program will play in viewport during '
                                 'post-process. Leave unchecked for faster results.',
                      changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                        'OPTS_PREVIEW_IN_VIEWPORT'))
        cmds.checkBox(label="Prompt on redundant solutions",
                      value=Prefs.get_user_pref(
                          'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'),
                      annotation='If checked, Maya will as the user to select between '
                                 'redundant solutions on axes where they occur.',
                      changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                        'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'))

        cmds.setParent('..')  # End of columnLayout
        cmds.setParent('..')  # End of frameLayout

    @staticmethod
    def __build_postproc_settings_frame():
        # Post Processor Settings Frame
        cmds.frameLayout(label="Post Processor Settings")
        cmds.columnLayout()

        cmds.separator()
        cmds.rowLayout(columnWidth2=(60, 1))
        # Post processor option menu list
        cmds.text(label='Processor:')
        cmds.optionMenu('prefs_postProcessorList',
                        height=20,
                        changeCommand=pm.CallbackWithArgs(
                            postproc_options.update_prefs_ui_postroc_options))
        cmds.setParent('..')  # End of rowLayout

        # Get supported post-processors and fill option menu list
        post_processors = postproc_setup.get_processor_names(mimic_config.USER)
        for post in post_processors:
            cmds.menuItem(label=post)

        cmds.rowLayout()
        cmds.text(label='User Options:')
        cmds.separator()
        cmds.setParent('..')  # End of rowLayout

        cmds.columnLayout(columnAttach=('left', 65))
        # Get the options
        selected_options = Prefs.get_postproc_options(mimic_config.USER)
        supported_options = postproc_options.get_processor_supported_options(
            'prefs_postProcessorList')

        # Create the options dictionary and build the output
        options_dict = postproc_options.create_options_dict(
            selected_options, supported_options)

        # Construct the output columns
        for option_name, option_val in list(options_dict.items()):
            cmds.checkBox('prefs_' + option_val['name'],  # cb_...
                          label=option_name,  # _checkbox_name_pretty
                          value=option_val['value'],
                          enable=option_val['enable'],
                          visible=True,
                          changeCommand=pm.CallbackWithArgs(
                              Prefs.update_postproc_options,
                              mimic_config.USER,
                              option_name))
        cmds.setParent('..')  # End of columnLayout
        cmds.setParent('..')  # End of columnLayout
        cmds.setParent('..')  # End of frameLayout

    @staticmethod
    def __build_save_prefs_button():
        # "Save Preferences" Button
        cmds.columnLayout()
        cmds.separator()
        cmds.button('Save Preferences',
                    command=pm.Callback(Prefs.save_user_prefs_to_json),
                    annotation='Save Preferences')
        cmds.separator()
        cmds.setParent('..')  # End of columnLayout

    @staticmethod
    def __build_hotkeys_frame():
        # Hotkeys Frame
        cmds.frameLayout(label="Hotkeys")
        cmds.columnLayout()
        cmds.separator()
        # Toggle IK/FK mode Hotkey
        toggle_mode_cmd_name = 'mimic_toggleIkFkMode'
        toggle_mode_annotation_str = 'Toggles Mimic Robot plugin IK/FK mode'
        toggle_mode_command_str = 'import mimic_utils; mimic_utils.toggle_ik_fk_ui()'

        cmds.rowLayout(numberOfColumns=4,
                       columnAttach=(1, 'left', 0),
                       columnWidth=[(1, 72), (3, 45), (4, 50)])

        # Find hotkey assignment, if one exists, to populate the ui
        toggle_mode_hotkey_name = toggle_mode_cmd_name + 'Hotkey'
        toggle_mode_key = mimic_utils.find_hotkey(toggle_mode_hotkey_name)
        if not toggle_mode_key:
            toggle_mode_key = ' key'

        cmds.text(label='Toggle IK/FK:')
        cmds.textField("t_toggleIkFk", placeholderText=toggle_mode_key)

        cmds.button(label='Create',
                    width=45,
                    height=20,
                    command=pm.Callback(mimic_utils.assign_hotkey,
                                        toggle_mode_cmd_name,
                                        toggle_mode_annotation_str,
                                        toggle_mode_command_str))

        cmds.button(label='Remove',
                    width=50,
                    height=20,
                    command=pm.Callback(mimic_utils.remove_hotkey,
                                        toggle_mode_cmd_name))

        cmds.setParent('..')  # End of rowLayout

        cmds.separator(height=3)

        # Keyframe IK/FK Hotkey
        key_ik_fk_cmd_name = 'mimic_keyIkFk'
        key_ik_fk_annotation_str = 'Keys Mimic robot IK/FK attributes'
        key_ik_fk_command_str = 'import mimic_utils; mimic_utils.key_ik_fk()'

        cmds.rowLayout(numberOfColumns=4,
                       columnAttach=(1, 'left', 0),
                       columnWidth=[(1, 72), (3, 45), (4, 50)])

        # Find hotkey assignment, if one exists, to populate the ui
        key_ik_fk_hotkey_name = key_ik_fk_cmd_name + 'Hotkey'
        key_ik_fk_key = mimic_utils.find_hotkey(key_ik_fk_hotkey_name)
        if not key_ik_fk_key:
            key_ik_fk_key = ' key'

        cmds.text(label='Key IK/FK:')
        cmds.textField("t_keyIkFk", placeholderText=key_ik_fk_key)

        cmds.button(label='Create',
                    width=45,
                    height=20,
                    command=pm.Callback(mimic_utils.assign_hotkey,
                                        key_ik_fk_cmd_name,
                                        key_ik_fk_annotation_str,
                                        key_ik_fk_command_str))

        cmds.button(label='Remove',
                    width=50,
                    height=20,
                    command=pm.Callback(mimic_utils.remove_hotkey,
                                        key_ik_fk_cmd_name))

        cmds.setParent('..')  # End of rowLayout
        cmds.setParent('..')  # End of columnLayout
        cmds.setParent('..')  # End of frameLayout

    def __build_advanced_frame(self):
        # Advanced Frame
        frame_advanced = cmds.frameLayout(label='Advanced')
        column_layout_1 = cmds.columnLayout(p=frame_advanced)
        cmds.separator(p=column_layout_1)
        cmds.text('User Preference Management:', align='left', p=column_layout_1)
        column_layout_2 = cmds.columnLayout(columnAttach=('both', 20), p=column_layout_1)
        cmds.separator(height=10, p=column_layout_2)
        cmds.button('Reset to Mimic defaults',
                    command=self.__reset_user_prefs_to_mimic_defaults,
                    p=column_layout_2)
        cmds.separator(p=column_layout_2)
        cmds.button('Load from JSON file',
                    command=self.__load_user_prefs_from_json_file,
                    p=column_layout_2)
        cmds.separator(p=column_layout_2)
        cmds.button('Load from current Maya file',
                    command=self.__load_user_prefs_from_current_maya_file,
                    p=column_layout_2)
        cmds.separator(height=20, p=column_layout_2)
        cmds.setParent('..')
        cmds.text('File Preference Management:', align='left', p=column_layout_1)
        column_layout_3 = cmds.columnLayout(columnAttach=('both', 20), p=column_layout_1)
        cmds.separator(height=10, p=column_layout_3)
        cmds.button('Reset to Mimic defaults',
                    command=self.__reset_file_prefs_to_mimic_defaults,
                    p=column_layout_3)
        cmds.separator(p=column_layout_3)
        cmds.button('Load from User Preferences',
                    command=self.__load_file_prefs_from_user_prefs,
                    p=column_layout_3)
        cmds.separator(p=column_layout_3)
        cmds.button('Delete File Preferences',
                    command=self.__delete_file_prefs_in_current_file,
                    p=column_layout_3)
        cmds.separator(p=column_layout_3)
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

    def __reset_user_prefs_to_mimic_defaults(self, *_args):
        confirmed = self.warning_window(
            'Reset User Preferences to Mimic defaults',
            'Are you sure you want to reset your user preferences to Mimic\'s default '
            'preferences?  This will delete previously saved user preferences.')

        if confirmed:
            Prefs.reset_user_prefs_file()
            Prefs.copy_prefs(mimic_config.DEFAULT, mimic_config.USER)
            self.reload_window()

    def __load_user_prefs_from_current_maya_file(self, *_args):
        confirmed = self.warning_window(
            'Load User Preferences from current Maya file',
            'Are you sure you want to load user preferences from the opened Maya '
            'file?  This will delete all previously saved user preferences.')

        if confirmed:
            Prefs.copy_prefs(mimic_config.FILE, mimic_config.USER)
            Prefs.save_user_prefs_to_json()
            self.reload_window()

    def __load_user_prefs_from_json_file(self, *_args):
        confirmed = self.warning_window(
            'Load User Preferences from JSON file',
            'Are you sure you want to load user preferences from a JSON file?  '
            'This will delete all previously saved user preferences.')

        if confirmed:
            json_file = cmds.fileDialog2(fileFilter='*.json', fileMode=1, dialogStyle=2)

            if json_file:
                Prefs.copy_prefs(mimic_config.EXTERNAL, mimic_config.USER,
                                 source_file_path=json_file[0])
                Prefs.save_user_prefs_to_json()
                self.reload_window()

    def __reset_file_prefs_to_mimic_defaults(self, *_args):
        confirmed = self.warning_window(
            'Reset File Preferences to Mimic defaults',
            'Are you sure you want to reset preferences saved in the currently '
            'open Maya file to Mimic default values?  '
            'This will delete all previously saved file preferences.')

        if confirmed:
            Prefs.copy_prefs(mimic_config.DEFAULT, mimic_config.FILE)
            cmds.saveFile(force=True)
            if cmds.window("mimic_win", exists=True):
                mimic_config.reload_mimic()

    def __load_file_prefs_from_user_prefs(self, *_args):
        confirmed = self.warning_window(
            'Load File Preferences to User preferences',
            'Are you sure you want to overwrite preferences saved in the '
            'currently open Maya file with your user preferences?  '
            'This will delete all previously saved file preferences.')

        if confirmed:
            Prefs.copy_prefs(mimic_config.USER_JSON, mimic_config.FILE)
            cmds.saveFile(force=True)
            if cmds.window("mimic_win", exists=True):
                mimic_config.reload_mimic()

    def __delete_file_prefs_in_current_file(self, *_args):
        confirmed = self.warning_window(
            'Delete File Preferences in current file',
            'Are you sure you want to delete preferences saved in the currently '
            'open Maya file?  '
            'This will delete all previously saved file preferences.')

        if confirmed:
            Prefs.delete_prefs(mimic_config.FILE)
            cmds.saveFile(force=True)
