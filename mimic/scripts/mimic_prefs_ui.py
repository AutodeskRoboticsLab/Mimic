#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create the Mimic Preferences UI
"""

try:
    import pymel.core as pm

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

reload(general_utils)
reload(mimic_config)
reload(mimic_program)
reload(mimic_utils)
reload(mimic_external_axes)
reload(mimic_io)
reload(postproc_setup)
reload(postproc_options)
reload(analysis)

Prefs = mimic_config.Prefs


class MimicPreferencesWindow(object):
    def __init__(self):
        self.ui_template = 'PrefsTemplate'
        self.window_name = 'mimic_preferences'
        self.window_title = 'Mimic Preferences'
        self._delete_window()
        self._build_ui_template()
        self._load_prefs()
        window = self._build_ui()
        window.show()

    def _confirm_reset_default_prefs(self, *args):
        delete_prefs = pm.confirmDialog \
            (title='Reset Mimic Preferences',
             messageAlign='right',
             message='Are you sure you want to reset to default preferences?\n'
                     'This will delete all user preferences.',
             button=['Yes', 'No'], defaultButton='Yes',
             cancelButton='No',
             dismissString='No', icon='warning')

        if delete_prefs == 'Yes':
            Prefs.reset_user_prefs_file(general_utils.get_mimic_dir())
            Prefs.load_into_environment(mimic_config.DEFAULT)
            pm.deleteUI(self.window_name)

            command = "import sys\n" \
                      "sys.dont_write_bytecode = True  # don't write PYCs\n" \
                      "import mimic_prefs_ui\n" \
                      "reload(mimic_prefs_ui)\n" \
                      "mimic_prefs_ui.MimicPreferencesWindow()"
            pm.evalDeferred(command)

    def _build_ui_template(self):
        if pm.uiTemplate(self.ui_template, exists=True):
            pm.deleteUI(self.ui_template, uiTemplate=True)

        pm.uiTemplate(self.ui_template)
        pm.rowLayout(defineTemplate=self.ui_template, numberOfColumns=2, adjustableColumn=2,
                     columnWidth2=(90, 1), height=20)
        pm.separator(defineTemplate=self.ui_template, height=5, style='none')
        pm.columnLayout(defineTemplate=self.ui_template, adj=True, columnAttach=('both', 5))
        pm.textField(defineTemplate=self.ui_template, font=mimic_ui.FONT)
        # pm.frameLayout(defineTemplate=self.ui_template, collapsable=True)

    def _delete_window(self):
        # If the window already exists, delete the window
        if pm.window(self.window_name, exists=True):
            pm.deleteUI(self.window_name, window=True)

    def _load_prefs(self):
        print('_load_prefs()')
        Prefs.load_into_environment(mimic_config.DEFAULT)
        Prefs.load_into_environment(mimic_config.USER, general_utils.get_mimic_dir())

    def _build_ui(self):
        """
        Builds main Preferences UI and defines relationships between UI buttons/features
        and back-end functions
        :return:
        """
        # Create window
        mimic_prefs_window = pm.window(self.window_name,
                                       sizeable=False,
                                       resizeToFitChildren=True,
                                       title=self.window_title)

        # Set window size. This needs to be set separately from window creation,
        # because Maya overrides settings passsed during window creation.
        # Setting height/width equal to one forces the window to resize to the
        # smallest possible size to contain any children UI elements
        pm.window(mimic_prefs_window, edit=True, width=1, height=1)

        # Set UI template
        pm.setUITemplate(self.ui_template, pushTemplate=True)

        # TODO(Harry): Align Mimic Logo
        with pm.columnLayout(width=300, columnAttach=('left', 0)):
            padding = (300 - 244) / 2
            with pm.rowLayout(numberOfColumns=1, height=60,
                              columnAttach=(1, 'both', padding)):
                pm.image(image='mimic_logo.png', width=244, height=60)

        # Set up Tabs
        form = pm.formLayout()
        tabs = pm.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
        pm.formLayout(form, edit=True, attachForm=(
            (tabs, 'top', 0), (tabs, 'left', 0), (tabs, 'bottom', 0), (tabs, 'right', 0)))

        # Build "General" Tab
        with pm.columnLayout(width=250, columnAttach=('both', 0)) as general_tab:
            self._build_general_settings_frame()
            self._build_motion_limits_frame()
            self._build_ui_settings_frame()
            self._build_program_settings_frame()
            self._build_buttons()

        # Build "PostProcessor" Tab
        with pm.columnLayout(width=270, columnAttach=('both', 0)) as postproc_tab:
            self._build_postproc_settings_frame()

        # Build "Hotkeys" Tab
        with pm.columnLayout(width=270, columnAttach=('both', 0)) as hotkeys_tab:
            self._build_hotkeys_frame()

        pm.tabLayout(tabs, edit=True, tabLabel=((general_tab, 'General'),
                                                (postproc_tab, 'PostProcessor'),
                                                (hotkeys_tab, 'Hotkeys')))

        # Reset UI template
        pm.setUITemplate(self.ui_template, popTemplate=True)
        return mimic_prefs_window

    def _build_general_settings_frame(self):
        # General Settings Frame
        with pm.frameLayout(label="General Settings"):
            with pm.columnLayout():
                pm.separator()
                # Create list of robots
                with pm.rowLayout():
                    pm.text('Robot:')
                    pm.optionMenu(changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                                    'DEFAULT_ROBOT'))
                    # TODO(Harry): get function to access file and user level list of robots
                    rigs = general_utils.get_rigs_dict()
                    default_rig = Prefs.get_user_pref('DEFAULT_ROBOT')
                    rig_names = general_utils.get_rigs_names(rigs, default_rig)
                    for rig_name in rig_names:
                        pm.menuItem(label=rig_name)
                pm.separator()

    def _build_motion_limits_frame(self):
        # Motion Limits Frame
        with pm.frameLayout(label="Motion Limits"):
            with pm.columnLayout():
                with pm.rowLayout():
                    pm.text(label='Velocity:')
                    pm.floatField(min=0,
                                  pre=1,
                                  value=Prefs.get_user_pref('NOMINAL_VELOCITY_LIMIT'),
                                  changeCommand=pm.CallbackWithArgs(
                                      Prefs.set_user_pref,
                                      'NOMINAL_VELOCITY_LIMIT'))
                with pm.rowLayout():
                    pm.text(label='Acceleration:')
                    pm.floatField(min=0,
                                  pre=1,
                                  value=Prefs.get_user_pref('NOMINAL_ACCELERATION_LIMIT'),
                                  changeCommand=pm.CallbackWithArgs(
                                      Prefs.set_user_pref,
                                      'NOMINAL_ACCELERATION_LIMIT'))
                with pm.rowLayout():
                    pm.text(label='Jerk:')
                    pm.floatField(min=0,
                                  pre=1,
                                  value=Prefs.get_user_pref('NOMINAL_JERK_LIMIT'),
                                  changeCommand=pm.CallbackWithArgs(
                                      Prefs.set_user_pref,
                                      'NOMINAL_JERK_LIMIT'))
                pm.separator()

    def _build_ui_settings_frame(self):
        # UI Settings Frame
        with pm.frameLayout(label="UI Settings"):
            with pm.columnLayout():
                pm.separator()
                # Shader range row layout
                with pm.rowLayout():
                    pm.text(label='Shader range:')
                    # Axis limit shader range float field
                    pm.floatField(min=0,
                                  pre=0,
                                  value=Prefs.get_user_pref('SHADER_RANGE'),
                                  changeCommand=pm.CallbackWithArgs(
                                      Prefs.set_user_pref,
                                      'SHADER_RANGE'))
                pm.separator()

    def _build_program_settings_frame(self):
        # Program Settings Frame
        with pm.frameLayout(label="Program Settings"):
            with pm.columnLayout():
                with pm.rowLayout(numberOfColumns=3,
                                  columnWidth3=(90, 250, 30)):
                    pm.text(label="Output directory:")
                    pm.textField('pref_programDirectoryText',
                                 text=Prefs.get_user_pref('DEFAULT_PROGRAM_DIRECTORY'),
                                 editable=False)

                    pm.symbolButton(image="setDirectory_icon.png",
                                    width=32,
                                    height=20,
                                    command=pm.Callback(mimic_utils.set_dir,
                                                        'pref_programDirectoryText',
                                                        'DEFAULT_PROGRAM_DIRECTORY',
                                                        Prefs.get_user_pref,
                                                        Prefs.set_user_pref))
                with pm.rowLayout():
                    pm.text(label='Output name:')
                    pm.textField(text=Prefs.get_user_pref('DEFAULT_OUTPUT_NAME'),
                                 changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                                   'DEFAULT_OUTPUT_NAME'))
                with pm.rowLayout():
                    pm.text(label='Template name:')
                    pm.textField(text=Prefs.get_user_pref('DEFAULT_TEMPLATE_NAME'),
                                 changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                                   'DEFAULT_TEMPLATE_NAME'))
                # Sample rate radio buttons
                pm.separator(height=3)
                selected_units = Prefs.get_user_pref('DEFAULT_SAMPLE_RATE_UNITS')
                selected_value = Prefs.get_user_pref('DEFAULT_SAMPLE_RATE_VALUE')
                pm.radioCollection('sample_rate_radio_collection_prefs')
                with pm.rowLayout(numberOfColumns=3,
                                  adjustableColumn=3,
                                  columnAttach=(1, 'left', 3),
                                  columnWidth=[(1, 90), (2, 45)]):
                    pm.radioButton('rb_timeInterval',
                                   label='Sample rate:',
                                   select=not Prefs.get_user_pref('SAMPLE_KEYFRAMES_ONLY'))
                    pm.intField(minValue=0,
                                value=selected_value,
                                changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                                  'DEFAULT_SAMPLE_RATE_VALUE'))
                    pm.radioButtonGrp('time_unit_radio_group',
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
                with pm.rowLayout(numberOfColumns=1,
                                  adjustableColumn=1,
                                  columnAttach=(1, 'left', 3)):
                    pm.radioButton('rb_keyframesOnly',
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

                # Output options
                pm.separator(height=11, style='out')
                pm.checkBox(label="Overwrite existing file",
                            value=Prefs.get_user_pref('OPTS_OVERWRITE_EXISTING_FILE'),
                            annotation='If checked, an existing file with the input '
                                       'output name will be overwritten',
                            changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                              'OPTS_OVERWRITE_EXISTING_FILE'))
                pm.checkBox(label="Ignore warnings",
                            value=Prefs.get_user_pref('OPTS_IGNORE_WARNINGS'),
                            annotation='If checked, all warnings will be ignored and '
                                       'a program will be written',
                            changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                              'OPTS_IGNORE_WARNINGS'))

                # Preview Options
                pm.checkBox(label="Preview in viewport",
                            value=Prefs.get_user_pref('OPTS_PREVIEW_IN_VIEWPORT'),
                            annotation='If checked, program will play in viewport during '
                                       'post-process. Leave unchecked for faster results.',
                            changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                              'OPTS_PREVIEW_IN_VIEWPORT'))
                pm.checkBox(label="Prompt on redundant solutions",
                            value=Prefs.get_user_pref(
                                'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'),
                            annotation='If checked, Maya will as the user to select between '
                                       'redundant solutions on axes where they occur.',
                            changeCommand=pm.CallbackWithArgs(Prefs.set_user_pref,
                                                              'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'))

    def _build_postproc_settings_frame(self):
        # Postprocessor Settings Frame
        with pm.frameLayout(label="Postprocessor Settings"):
            with pm.columnLayout():
                pm.separator()
                with pm.rowLayout(columnWidth2=(60, 1)):
                    # Post processor option menu list
                    pm.text(label='Processor:')
                    pm.optionMenu('prefs_postProcessorList',
                                  height=20,
                                  changeCommand=pm.CallbackWithArgs(
                                      postproc_options.update_prefs_ui_postroc_options))

                    # Get supported post-processors and fill option menu list
                    post_processors = postproc_setup.get_processor_names(mimic_config.USER)
                    for post in post_processors:
                        pm.menuItem(label=post)
                with pm.rowLayout():
                    pm.text(label='User Options:')
                    pm.separator()
                with pm.columnLayout(columnAttach=('left', 65)):
                    # Get the options
                    selected_options = Prefs.get_postproc_options(mimic_config.USER)
                    supported_options = postproc_options.get_processor_supported_options(
                        'prefs_postProcessorList')

                    # Create the options dictionary and build the output
                    options_dict = postproc_options.create_options_dict(
                        selected_options, supported_options)

                    # Construct the output columns
                    for option_name, option_val in options_dict.items():
                        pm.checkBox('prefs_' + option_val['name'],  # cb_...
                                    label=option_name,  # _checkbox_name_pretty
                                    value=option_val['value'],
                                    enable=option_val['enable'],
                                    visible=True,
                                    changeCommand=pm.CallbackWithArgs(
                                        Prefs.update_postproc_options,
                                        mimic_config.USER,
                                        option_name))

    def _build_buttons(self):
        # Buttons
        with pm.columnLayout():
            pm.separator()
            # TODO(Harry): Confirmation window. Does user REALLY want to reset??
            pm.button('Reset to Defaults',
                      command=self._confirm_reset_default_prefs,
                      height=25,
                      annotation='Reset Preferences to default values.')
            pm.separator()
            # TODO(Harry): Add pm.setFocus('something') to release focus
            pm.button('Save Preferences',
                      command=pm.Callback(Prefs.save_to_json,
                                          general_utils.get_mimic_dir()),
                      height=25,
                      annotation='Save Preferences')
            pm.separator()

    def _build_hotkeys_frame(self):
        with pm.frameLayout(label="Hotkeys"):
            with pm.columnLayout():
                pm.separator()
                # Toggle IK/FK mode Hotkey
                toggle_mode_cmd_name = 'mimic_toggleIkFkMode'
                toggle_mode_annotation_str = 'Toggles Mimic Robot plugin IK/FK mode'
                toggle_mode_command_str = 'import mimic_utils; ' \
                                          'mimic_utils.toggle_ik_fk_ui()'

                with pm.rowLayout(numberOfColumns=4,
                                  columnAttach=(1, 'left', 0),
                                  columnWidth=[(1, 72), (3, 45), (4, 50)]):

                    # Find hotkey assignment, if one exists, to populate the ui
                    toggle_mode_hotkey_name = toggle_mode_cmd_name + 'Hotkey'
                    toggle_mode_key = mimic_utils.find_hotkey(toggle_mode_hotkey_name)
                    if not toggle_mode_key:
                        toggle_mode_key = ' key'

                    pm.text(label='Toggle IK/FK:')
                    pm.textField("t_toggleIkFk",
                                 placeholderText=toggle_mode_key)

                    pm.button(label='Create',
                              width=45,
                              height=20,
                              command=pm.Callback(mimic_utils.assign_hotkey,
                                                  toggle_mode_cmd_name,
                                                  toggle_mode_annotation_str,
                                                  toggle_mode_command_str))

                    pm.button(label='Remove',
                              width=50,
                              height=20,
                              command=pm.Callback(mimic_utils.remove_hotkey,
                                                  toggle_mode_cmd_name))

                pm.separator(height=3)

                # Keyframe IK/FK Hotkey
                key_ik_fk_cmd_name = 'mimic_keyIkFk'
                key_ik_fk_annotation_str = 'Keys Mimic robot IK/FK attributes'
                key_ik_fk_command_str = 'import mimic_utils; ' \
                                        'mimic_utils.key_ik_fk()'

                with pm.rowLayout(numberOfColumns=4,
                                  columnAttach=(1, 'left', 0),
                                  columnWidth=[(1, 72), (3, 45), (4, 50)]):

                    # Find hotkey assignment, if one exists, to populate the ui
                    key_IkFk_hotkey_name = key_ik_fk_cmd_name + 'Hotkey'
                    key_IkFk_key = mimic_utils.find_hotkey(key_IkFk_hotkey_name)
                    if not key_IkFk_key:
                        key_IkFk_key = ' key'

                    pm.text(label='Key IK/FK:')
                    pm.textField("t_keyIkFk", placeholderText=key_IkFk_key)

                    pm.button(label='Create',
                              width=45,
                              height=20,
                              command=pm.Callback(mimic_utils.assign_hotkey,
                                                  key_ik_fk_cmd_name,
                                                  key_ik_fk_annotation_str,
                                                  key_ik_fk_command_str))
                    pm.button(label='Remove',
                              width=50,
                              height=20,
                              command=pm.Callback(mimic_utils.remove_hotkey,
                                                  key_ik_fk_cmd_name))
