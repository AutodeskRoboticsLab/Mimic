#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates the Mimic UI.
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

FONT = 'smallObliqueLabelFont'
Prefs = mimic_config.Prefs

# MAIN FUNCTION
def build_mimic_ui():
    """
    Builds main mimic UI and defines relationships between UI buttons/features
    and back-end functions
    :return:
    """
    mimic_win = create_mimic_window('mimic_win')

    # Create Main UI column
    pm.columnLayout(width=244, adj=True)

    # Add UI Header Image.
    robotImage = pm.image(image='mimic_logo.png', width=244, height=60)
    mimic_tab_layout = create_mimic_tabs()
    animate_tab_layout = build_animate_tab(mimic_tab_layout)
    program_tab_layout = build_program_tab(mimic_tab_layout)
    setup_tab_layout = build_setup_tab(mimic_win)

    tabs = [(animate_tab_layout, "Animate"),
            (program_tab_layout, "Program"),
            (setup_tab_layout, "Setup")]
    assign_tabs(tabs, mimic_tab_layout)

    # Create output column
    outputColumn = pm.columnLayout('outputColumn', width=7, adj=True)
    outputForm = pm.formLayout()
    outputScrollField = pm.scrollField('programOutputScrollField',
                                       width=3,
                                       height=610)
    pm.formLayout(outputForm,
                  edit=True,
                  attachForm=[(outputScrollField, "top", 3),
                              (outputScrollField, "bottom", 3),
                              (outputScrollField, "left", 3),
                              (outputScrollField, "right", 3)])
    pm.setParent(mimic_win)
    pm.columnLayout('outputBarColumn', width=7)
    pm.separator(height=1, style='none')
    bullets = '\n'.join([unichr(0x2022) for _ in range(3)])
    pm.text(bullets,
            align='left',
            annotation='Drag edge to view Output Window!')

    # Launch UI window
    pm.window('mimic_win', height=560, width=245, edit=True)
    mimic_win.show()

# MIMIC WINDOW
def create_mimic_window(window_name):
    # If the window already exists, delete the window
    if pm.window("mimic_win", exists=True):
        pm.deleteUI("mimic_win", window=True)

    # Initialize window and Layout
    mimic_version = general_utils.get_mimic_version()
    mimic_win = pm.window("mimic_win",
                          closeCommand=on_window_close,
                          width=245,
                          title='MIMIC {}'.format(mimic_version))  # + ' <dev 4.8.19>'))
    pm.rowLayout(numberOfColumns=3, adjustableColumn=2)

    return mimic_win


def create_mimic_tabs():
    # Create Form Layout with embeded Tab Layout
    mimic_form = pm.formLayout()
    mimic_tab_layout = pm.tabLayout()
    pm.formLayout(mimic_form,
                  edit=True,
                  attachForm=[(mimic_tab_layout, "top", 3),
                              (mimic_tab_layout, "bottom", 3),
                              (mimic_tab_layout, "left", 3),
                              (mimic_tab_layout, "right", 3)])

    return mimic_tab_layout


def assign_tabs(tabs, tab_layout, change_command=''):
    for tab in tabs:
        pm.tabLayout(tab_layout,
                     edit=True,
                     tabLabel=[(tab[0], tab[1])])

    if change_command:
        pm.tabLayout(tab_layout,
                     edit=True,
                     changeCommand=change_command)

# ANIMATE TAB
def _build_ik_tab(parent_layout):
    # Create column Layout for IK controls
    ik_tab_layout = pm.columnLayout('ikTab', adj=True, width=100)

    pm.separator(height=3, style='none')

    # IK Configuration Icon
    pm.gridLayout(numberOfColumns=1,
                  cellWidth=216,
                  cellHeight=52)

    # Flip robot base button
    pm.image(image='IK_config_icon.png')
    pm.setParent(ik_tab_layout)  # Set parent to IK tab column layout


    pm.gridLayout(numberOfColumns=3,
                  cellWidth=72,
                  cellHeight=126)

    # Flip robot base button
    pm.symbolButton(image='flipBaseIcon.png',
                    command=mimic_utils.flip_robot_base,
                    annotation='Changes IK solution by flipping robot\'s base')
    # Flip robot elbow button
    pm.symbolButton(image='flipElbowIcon.png',
                    command=mimic_utils.flip_robot_elbow,
                    annotation='Changes IK solution by flipping robot\'s elbow')
    # FLip robot wrist button
    pm.symbolButton(image='flipWristIcon.png',
                    command=mimic_utils.flip_robot_wrist,
                    annotation='Changes IK solution by flipping robot\'s wrist')

    pm.setParent(ik_tab_layout)  # Set parent to IK tab column layout


    pm.separator(height=2, style='none')
    pm.separator(height=11, style='out')

    # Key Animation Tool checkbox
    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_keyToolCtrl',
                label="Key tool controller",
                annotation='If checked, Tool Controller\'s Translate ' \
                           'and Rotate attributes will be keyed',
                value=1)

    pm.setParent(ik_tab_layout)  # Set parent to IK tab column layout

    pm.separator(height=5, style='none')

    # Keyframe IK configuration button
    pm.button(label='Set IK Keyframe',
              command=mimic_utils.key_ik,
              annotation='Keyframes Robot\'s IK-FK hierarchy in IK mode:\n' \
                         'target_CTRL:\n' \
                         '    ik = 1\n' \
                         '    visibility = 1\n' \
                         '    IK Solution 1, 2, and 3\n' \
                         'a*FK_CTRL:\n' \
                         '    rotateX, Y, or Z\n' \
                         'FK_CTRLS\n' \
                         '    visibility = 0')

    pm.setParent(parent_layout)
    return ik_tab_layout


def _build_fk_tab(parent_layout):
    # Create column Layout with embedded shelf layout in second tab
    fk_tab_layout = pm.columnLayout('fkTab', adjustableColumn=True)

    pm.separator(height=5, style='none')

    pm.gridLayout(numberOfColumns=3,
                  numberOfRows=2,
                  cellWidth=72,
                  cellHeight=44)

    cmd_str = ('import pymel.core as pm; ' \
               'import mimic_utils; ' \
               'pm.setFocus("fkTab");')

    for i in range(6):
        axis = i + 1
        sel_cmd_str = cmd_str + ' mimic_utils.select_fk_axis_handle({})' \
            .format(axis)
        button_img = 'a{}FkIcon.png'.format(axis)
        button_ann = 'Selects Axis {} FK Controller'.format(axis)
        pm.symbolButton(image=button_img,
                        command=sel_cmd_str,
                        annotation=button_ann)
    pm.setParent('..')

    # UI spacing
    pm.separator(height=3, style='none')
    pm.separator(height=11, style='out')

    pm.rowLayout(numberOfColumns=7,
                 adjustableColumn=7,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 20), (2, 45), (3, 22),
                              (4, 45), (5, 22), (6, 45)],
                 height=20)

    pm.text(label='A1:')
    pm.textField("t_a1",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 1),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 1))

    pm.text(label='  A2:')
    pm.textField("t_a2",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 2),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 2))

    pm.text(label='  A3:')
    pm.textField("t_a3",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 3),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 3))

    # UI spacing
    pm.text(label='')
    pm.setParent('..')
    pm.separator(height=2, style='none')

    pm.rowLayout(numberOfColumns=7,
                 adjustableColumn=7,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 20), (2, 45), (3, 22),
                              (4, 45), (5, 22), (6, 45)],
                 height=20)

    pm.text(label='A4:')
    pm.textField("t_a4",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 4),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 4))

    pm.text(label='  A5:')
    pm.textField("t_a5",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 5),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 5))

    pm.text(label='  A6:')
    pm.textField("t_a6",
                 font=FONT,
                 rfc=pm.Callback(mimic_utils.select_fk_axis_handle, 6),
                 changeCommand=pm.Callback(mimic_utils.set_axis, 6))

    # UI Spacing
    pm.text(label='')
    pm.setParent('..')
    pm.separator(height=7, style='none')

    # Get and set FK pose buttons
    pm.gridLayout(nc=2, cw=109, ch=25)
    pm.button(label="Get Pose",
              command=mimic_utils.get_fk_pose,
              annotation='Gets selected robot\'s current axis rotation ' \
                         'values\nand prints them above')
    pm.button(label='Set Pose',
              command=mimic_utils.set_fk_pose,
              annotation='Sets selected robot\'s current axis rotation ' \
                         'values\nto the input values above')

    pm.setParent('..')

    # Clear FK pose button
    pm.button(label='Clear',
              command=mimic_utils.clear_fk_pose_ui,
              annotation='Clears axis rotation input fields above')
    pm.separator(height=14, style='out')

    # Keyframe FK button
    pm.button(label="Set FK Keyframe",
              command=mimic_utils.key_fk,
              backgroundColor=[.7, .7, .7],
              annotation='Keyframes Robot\'s IK-FK hierarchy in FK mode:\n' \
                         'target_CTRL:\n' \
                         '    ik = 0\n' \
                         '    visibility = 0\n' \
                         'a*FK_CTRL:\n' \
                         '    rotateX, Y, or Z\n' \
                         'FK_CTRLS\n' \
                         '    visibility = 1')
    pm.setParent(parent_layout)
    return fk_tab_layout


def _build_switcher_frame(parent_layout):
    # Create a frame for the IK/FK switcher tabs
    switcher_frame = pm.frameLayout(label="IK/FK Switching", collapsable=True)

    # Create Form Layout with embeded Tab Layout
    switcher_form = pm.formLayout()
    switcher_tab_layout = pm.tabLayout('switcher_tab_layout', height=271)
    pm.formLayout(switcher_form,
                  edit=True,
                  attachForm=[(switcher_tab_layout, "top", 3),
                              (switcher_tab_layout, "bottom", 3),
                              (switcher_tab_layout, "left", 3),
                              (switcher_tab_layout, "right", 3)])

    ik_tab_layout = _build_ik_tab(switcher_tab_layout)
    fk_tab_layout = _build_fk_tab(switcher_tab_layout)

    tabs = [[ik_tab_layout, 'IK Controls'],
            [fk_tab_layout, 'FK Controls']]

    change_command = mimic_utils.toggle_ik_fk
    assign_tabs(tabs, switcher_tab_layout, change_command)

    pm.setParent(parent_layout)


def _build_keyframing_tools_frame(parent_layout):
    keyframing_tools_frame = pm.frameLayout(label="Keyframing Tools",
                                            collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.button(label='Delete IK/FK Keyframe',
              command=mimic_utils.delete_ik_fk_keys,
              annotation='Deletes keyframes on all attributes ' \
                         'at current frame created with\n' \
                         '"Set IK-FK Keyframe" buttons')
    pm.button(label='Select Keyframe Hierarchy',
              command=mimic_utils.select_keyframe_hierarchy,
              annotation='Selects all objects keyframed ' \
                         'with "Set IK-FK Keyframe" buttons:\n' \
                         '    target_CTRL\n' \
                         '    FK_CTRLS\n' \
                         '    a*FK_CTRL\n' \
                         '    tool_CTRL if one exists')

    pm.separator(height=5, style='none')
    pm.setParent(parent_layout)


def _build_general_frame(parent_layout):
    general_frame = pm.frameLayout(label="General", collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.button(label='Save Pose',
              command=mimic_utils.save_pose_to_shelf,
              annotation='Saves selected robot\'s current configuration\n' \
                         'to a button on the Mimic shelf')
    pm.separator(height=10, style='out')

    pm.gridLayout(numberOfColumns=2,
                  cellWidth=109,
                  cellHeight=25)

    # Zero target button
    pm.button(label='Zero Tool (TCS)',
              command=mimic_utils.zero_target,
              annotation='Sets target_CTRL (or tool_CTRL if it exists)\n'
                         'transform to Zero')
    # Zero robot local controller button
    pm.button(label='Zero Base (LCS)',
              command=mimic_utils.zero_base_local,
              annotation='Sets local_CTRL transform to Zero')
    # Zero robot world controller button
    pm.button(label='Zero Base (WCS)',
              command=mimic_utils.zero_base_world,
              annotation='Sets world_CTRL transform to Zero')
    # Zero all button
    pm.button(label='Zero All',
              command=mimic_utils.zero_all,
              annotation='Sets local_CTRL, world_CTRL, and target_CTRL (or ' \
                         'tool_CTRL if it exists)\ntransforms\' to Zero')
    pm.setParent('..')

    pm.separator(height=10, style='out')

    # Toggle heads up display button
    pm.button(label='Toggle HUD',
              command=mimic_utils.axis_val_hud,
              annotation='Toggles the visibility of Mimic\'s Heads Up Display')

    pm.separator(height=5, style='none')

    pm.setParent(parent_layout)


def build_animate_tab(parent_layout):
    # This tab contains tools that aid in the animation process; IK/FK
    # switching, keyframing, and some general tools

    # Create the main column layout for the tab
    animate_tab_layout = pm.columnLayout(adj=True, width=225, height=525)

    _build_switcher_frame(animate_tab_layout)
    _build_keyframing_tools_frame(animate_tab_layout)
    _build_general_frame(animate_tab_layout)

    pm.setParent(parent_layout)

    return animate_tab_layout

# PROGRAM TAB
def _build_general_settings_tab(parent_layout):
    # Create column Layout for General settings
    general_settings_tab_layout = pm.columnLayout('generalSettings',
                                                  adj=True,
                                                  width=100)
    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=3,
                 columnWidth3=(55, 250, 30),
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    pm.text(label="Directory:")
    pm.textField('t_programDirectoryText',
                 text=Prefs.get('DEFAULT_PROGRAM_DIRECTORY'),
                 ed=False,
                 font=FONT)

    pm.symbolButton('b_directoryImage',
                    image="setDirectory_icon.png",
                    width=32,
                    height=20,
                    command=pm.Callback(mimic_utils.set_dir,
                                        't_programDirectoryText',
                                        'DEFAULT_PROGRAM_DIRECTORY',
                                        Prefs.get,
                                        Prefs.set))
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 90), (2, 100)],
                 height=20)
    pm.text(label='Output name:')

    pm.textField('t_outputFileName',
                 text=Prefs.get('DEFAULT_OUTPUT_NAME'),
                 font=FONT,
                 changeCommand=pm.CallbackWithArgs(Prefs.set, 'DEFAULT_OUTPUT_NAME'))
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 90), (2, 100)],
                 height=20)
    pm.text(label='Template name:')
    pm.textField('t_templateFileName',
                 text=Prefs.get('DEFAULT_TEMPLATE_NAME'),
                 font=FONT,
                 changeCommand=pm.CallbackWithArgs(Prefs.set, 'DEFAULT_TEMPLATE_NAME'))

    pm.setParent('..')

    # Sample rate radio buttons
    pm.separator(height=3, style='none')
    selected_units = Prefs.get('DEFAULT_SAMPLE_RATE_UNITS')
    selected_value = Prefs.get('DEFAULT_SAMPLE_RATE_VALUE')
    radio_indent = 3
    pm.radioCollection('sample_rate_radio_collection')
    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', radio_indent),
                 columnWidth=[(1, 90), (2, 45)],
                 height=20)
    pm.radioButton('rb_timeInterval',
                   label='Sample rate:',
                   select=not Prefs.get('SAMPLE_KEYFRAMES_ONLY'))
    pm.floatField('f_timeBetweenSamples',
                 value=selected_value,
                 precision=3,
                 changeCommand=pm.CallbackWithArgs(Prefs.set, 'DEFAULT_SAMPLE_RATE_VALUE'))
    pm.radioButtonGrp('time_unit_radio_group',
                      labelArray2=['s', 'f'],
                      annotation='Sample rate units: seconds or frames',
                      numberOfRadioButtons=2,
                      columnWidth2=[32, 30],
                      select=1 if selected_units == 'seconds' else 2,  # 1-based integer
                      onCommand1 = pm.CallbackWithArgs(
                          Prefs.set,
                          'DEFAULT_SAMPLE_RATE_UNITS', 'seconds', mimic_config.FILE),
                      onCommand2 = pm.CallbackWithArgs(
                          Prefs.set,
                          'DEFAULT_SAMPLE_RATE_UNITS', 'frames', mimic_config.FILE))
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', radio_indent),
                 height=20)
    pm.radioButton('rb_keyframesOnly',
                   label='Sample keyframes only',
                   enable=True,
                   select=Prefs.get('SAMPLE_KEYFRAMES_ONLY'),
                   onCommand=pm.CallbackWithArgs(
                       Prefs.set,
                       'SAMPLE_KEYFRAMES_ONLY', True, mimic_config.FILE),
                   offCommand=pm.CallbackWithArgs(
                       Prefs.set,
                       'SAMPLE_KEYFRAMES_ONLY', False, mimic_config.FILE))
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 132), (2, 40), (3, 30)],
                 height=20)
    pm.text(label='Animation frame range:')

    pm.intField("i_programStartFrame",
                value=pm.playbackOptions(animationStartTime=True, query=True),
                minValue=-10000,
                maxValue=100000,
                step=1,
                changeCommand=pm.CallbackWithArgs(Prefs.set, 'ANIMATION_RANGE_START'))

    pm.intField("i_programEndFrame",
                value=pm.playbackOptions(animationEndTime=True, query=True),
                minValue=-10000,
                maxValue=100000,
                step=1,
                changeCommand=pm.CallbackWithArgs(Prefs.set, 'ANIMATION_RANGE_END'))

    pm.setParent('..')

    pm.separator(height=5, style='none')

    # Post processor option menu list
    pm.optionMenu('postProcessorList',
                  label='Processor:',
                  height=18,
                  changeCommand=pm.CallbackWithArgs(postproc_options.overwrite_options))

    # Get supported post-processors and fill option menu list
    supported_post_processors = postproc_setup.get_processor_names(mimic_config.FILE)
    for post in supported_post_processors:
        pm.menuItem(label=post)
    pm.separator(height=3, style='none')

    pm.setParent(parent_layout)
    return general_settings_tab_layout


def _build_proc_options_tab(parent_layout):
    # Create column Layout for General settings
    proc_options_tab_layout = pm.columnLayout('procOptions', adj=True, width=100)
    pm.separator(height=3, style='none')

    # Name this tab? May not be necessary
    pm.separator(height=3, style='none')
    pm.text('User options:', align='left')
    pm.separator(height=3, style='none')

    # Get the options
    selected_options = Prefs.get_postproc_options()
    supported_options = postproc_options.get_processor_supported_options()

    # Create the options dictionary and build the output
    options_dict = postproc_options.create_options_dict(
        selected_options, supported_options)

    # Construct the output columns
    postproc_options.build_options_columns(
        'procOptions',
        options_dict,
        proc_options_tab_layout)

    pm.setParent(parent_layout)
    return proc_options_tab_layout


def _build_program_settings_frame(parent_layout):
    program_settings_frame = pm.frameLayout(label="Program Settings",
                                            collapsable=True)

    # Create Form Layout with embedded Tab Layout
    program_settings_form = pm.formLayout()
    program_settings_tab_layout = pm.tabLayout('program_settings_tab_layout')
    pm.formLayout(program_settings_form,
                  edit=True,
                  attachForm=[(program_settings_tab_layout, "top", 3),
                              (program_settings_tab_layout, "bottom", 3),
                              (program_settings_tab_layout, "left", 3),
                              (program_settings_tab_layout, "right", 3)])

    general_settings_tab_layout = _build_general_settings_tab(program_settings_tab_layout)
    proc_options_tab_layout = _build_proc_options_tab(program_settings_frame)

    tabs = [[general_settings_tab_layout, 'General'],
            [proc_options_tab_layout, 'Advanced']]

    assign_tabs(tabs, program_settings_tab_layout)

    program_settings_col = pm.columnLayout(adj=True, columnAttach=['both', 3])

    # Output options
    pm.checkBox('cb_overwriteFile',
                label="Overwrite existing file",
                value=Prefs.get('OPTS_OVERWRITE_EXISTING_FILE'),
                annotation='If checked, an existing file with the input ' \
                           'output name will be overwritten',
                changeCommand=pm.CallbackWithArgs(Prefs.set, 'OPTS_OVERWRITE_EXISTING_FILE'))
    pm.checkBox('cb_ignoreWarnings',
                label="Ignore warnings",
                value=Prefs.get('OPTS_IGNORE_WARNINGS'),
                annotation='If checked, all warnings will be ignored and ' \
                           'a program will be written',
                changeCommand=pm.CallbackWithArgs(Prefs.set, 'OPTS_IGNORE_WARNINGS'))

    pm.separator(height=3, style='none')

    # Preview Options
    pm.separator(height=11, style='out')
    pm.checkBox('cb_previewInViewport',
                label="Preview in viewport",
                value=Prefs.get('OPTS_PREVIEW_IN_VIEWPORT'),
                annotation='If checked, program will play in viewport during ' \
                           'post-process. Leave unchecked for faster results.',
                changeCommand=pm.CallbackWithArgs(Prefs.set, 'OPTS_PREVIEW_IN_VIEWPORT'))
    pm.checkBox('cb_promptOnRedundantSolutions',
                label="Prompt on redundant solutions",
                value=Prefs.get('OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'),
                annotation='If checked, Maya will as the user to select between ' \
                       'redundant solutions on axes where they occur.',
                changeCommand=pm.CallbackWithArgs(Prefs.set,
                                                  'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'))

    pm.separator(height=6, style='none')

    pm.button('Analyze Program',
              command=mimic_program.analyze_program,
              height=25,
              annotation='Launches graphical analysis tool')
    pm.button('Save Program',
              command=mimic_program.save_program,
              height=25,
              annotation='Saves robot control program with input parameters')
    pm.separator(height=3, style='none')

    export_progress_bar = pm.progressBar('pb_exportProgress',
                                         isInterruptable=True,
                                         maxValue=100,
                                         visible=0)

    pm.setParent(parent_layout)


def build_program_tab(parent_layout):
    # Create preferences tab Layout
    program_tab_layout = pm.columnLayout(adj=True, height=525, width=200)

    _build_program_settings_frame(program_tab_layout)
    # _build_output_frame(program_tab_layout)

    pm.setParent(parent_layout)

    return program_tab_layout

# SETUP TAB
# SETUP - General
def _build_add_robot_frame(parent_layout):
    # Create frame layout with one column
    add_robot_frame = pm.frameLayout(label="Add Robot", collapsable=True)
    add_robot_col = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Create list of robots
    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 158), (2, 45)],
                 height=20)

    pm.optionMenu('robotImportList',
                  changeCommand=pm.CallbackWithArgs(Prefs.set, 'DEFAULT_ROBOT'))

    rigs = general_utils.get_rigs_dict()
    default_rig = Prefs.get('DEFAULT_ROBOT')
    rig_names = general_utils.get_rigs_names(rigs, default_rig)
    for rig_name in rig_names:
        pm.menuItem(label=rig_name)

    pm.button(label=' Add ',
              command=add_robot,
              width=45,
              height=20,
              annotation='Imports selected robot into the scene')

    pm.setParent(add_robot_frame)

    pm.separator(style='none')
    pm.setParent(parent_layout)


def _build_tool_setup_frame(parent_layout):
    controllers_frame = pm.frameLayout(label="Tool Setup", collapsable=True)
    controllers_column = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 90), (2, 60), (3, 60)],
                 height=20)
    pm.text('Tool controller:', align='left')
    pm.button(label='Attach',
              width=58,
              height=20,
              command=mimic_utils.attach_tool_controller,
              annotation='Attaches selected tool controller to the ' \
                         'selected robot')
    pm.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_controller,
              annotation='Detaches tool controller from robot')
    pm.setParent('..')

    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 90), (2, 60), (3, 60)],
                 height=20)
    pm.text('Tool model:', align='left')
    pm.button(label='Attach',
              width=58,
              height=20,
              command=mimic_utils.attach_tool_model,
              annotation='Attaches selected tool model to the ' \
                         'selected robot')
    pm.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_model,
              annotation='Detaches selected tool model from its ' \
                         'parent robot')
    pm.setParent('..')

    pm.separator(height=8, style='none')
    pm.setParent(parent_layout)


def _build_position_limits_tab(parent_layout):
    position_limits_tab = pm.rowColumnLayout('position_limits_tab',
                                             numberOfColumns=2)

    # Input text field width for all axis limits
    cell_width = 80

    # Set up primary axis limits UI
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        pm.text(label='Axis {}: '.format(i + 1))

        # Axis 1 Min limit
        pm.textField("t_A{}Min".format(i + 1),
                     font=FONT,
                     pht='Min',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'pm.setFocus("t_A{}Max"); ' \
                                   .format(i + 1))
        # Axis 1 Max limit
        set_focus_count = ((i + 1) % 6) + 1
        pm.textField("t_A{}Max".format(i + 1),
                     font=FONT,
                     pht='Max',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'pm.setFocus("t_A{}Min"); ' \
                                   .format(set_focus_count))

        pm.setParent('..')

    pm.setParent(parent_layout)

    return position_limits_tab


def _build_velocity_limits_tab(parent_layout):
    velocity_limits_tab = pm.rowColumnLayout('velocity_limits_tab',
                                             numberOfColumns=2)

    # Set up primary axis velocity limits tab
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        pm.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}Velocity".format(i + 1),
                     font=FONT,
                     pht='deg/sec',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}Velocity"); ' \
                     .format(set_focus_count))
        pm.setParent('..')

    pm.setParent(parent_layout)

    return velocity_limits_tab


def _build_accel_limits_tab(parent_layout):
    accel_limits_tab = pm.rowColumnLayout('accel_limits_tab',
                                          numberOfColumns=2)

    # Set up primary axis accel limits tab
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        pm.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}Accel".format(i + 1),
                     font=FONT,
                     pht='deg/sec' + u'\xb2',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}Accel"); ' \
                     .format(set_focus_count))
        pm.setParent('..')

    pm.setParent(parent_layout)

    return accel_limits_tab


def _build_jerk_limits_tab(parent_layout):
    jerk_limits_tab = pm.rowColumnLayout('jerk_limits_tab', numberOfColumns=2)

    # Set up primary axis accel limits tab
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        pm.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}Jerk".format(i + 1),
                     font=FONT,
                     pht='deg/sec' + u'\xb3',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}Jerk"); ' \
                     .format(set_focus_count))
        pm.setParent('..')

    pm.setParent(parent_layout)

    return jerk_limits_tab


def _build_axis_limits_frame(parent_layout):
    limits_frame = pm.frameLayout(label="Axis Limits", collapsable=True)
    limits_tab_layout = pm.tabLayout('limits_tab_layout')

    position_limits_tab = _build_position_limits_tab(limits_tab_layout)
    velocity_limits_tab = _build_velocity_limits_tab(limits_tab_layout)
    accel_limits_tab = _build_accel_limits_tab(limits_tab_layout)
    jerk_limits_tab = _build_jerk_limits_tab(limits_frame)

    tabs = [(position_limits_tab, 'Position'),
            (velocity_limits_tab, 'Vel'),
            (accel_limits_tab, 'Accel'),
            (jerk_limits_tab, 'Jerk')]

    assign_tabs(tabs, limits_tab_layout)

    pm.columnLayout()
    pm.gridLayout(nc=2, cw=114, ch=25)
    pm.button(label='Get Axis Limits', command=mimic_utils.write_limits_to_ui)
    pm.button(label='Set Axis Limits', command=mimic_utils.set_axis_limits)

    pm.setParent('..')
    pm.button(label='Clear', width=228, command=mimic_utils.clear_limits_ui)

    pm.setParent(parent_layout)


def _build_general_setup_tab(parent_layout):
    general_setup_tab_layout = pm.columnLayout('generalSetupTab',
                                               adj=True,
                                               width=100)
    # Add robot frame
    _build_add_robot_frame(general_setup_tab_layout)

    # Add tool setup frame
    _build_tool_setup_frame(general_setup_tab_layout)

    # UI frame
    _build_ui_setup_frame(general_setup_tab_layout)

    # Axis Limits frame
    _build_axis_limits_frame(general_setup_tab_layout)

    pm.setParent(parent_layout)

    return general_setup_tab_layout

# SETUP - External Axes
def _build_add_external_axis_frame(parent_layout):
    pm.frameLayout('add_external_axis_frame',
                   label="Add External Axis",
                   collapsable=True)
    add_external_axis_col = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    pm.text(label='Axis Name: ')
    pm.textField('t_externalAxisDescriptionText',
                 placeholderText='axisName',
                 font=FONT)
    pm.setParent('..')
    pm.separator(height=3, style='none')

    def __set_limit_display_units(*args):
        if 'translate' in args[0]:

            pm.textField('t_externalAxisLimitMin',
                         edit=True,
                         placeholderText='mm')
            pm.textField('t_externalAxisLimitMax',
                         edit=True,
                         placeholderText='mm')
            pm.textField('t_externalAxisVelocityLimit',
                         edit=True,
                         placeholderText='m/s')
        else:
            pm.textField('t_externalAxisLimitMin',
                         edit=True,
                         placeholderText='deg')
            pm.textField('t_externalAxisLimitMax',
                         edit=True,
                         placeholderText='deg')
            pm.textField('t_externalAxisVelocityLimit',
                         edit=True,
                         placeholderText='deg/s')

    pm.optionMenu('axisNumberMenu',
                  label='Axis Number:',
                  height=18)

    axis_number_list = [i + 1 for i in range(6)]
    for axis_number in axis_number_list:
        pm.menuItem(label=axis_number)

    pm.separator(height=3, style='none')

    pm.optionMenu('drivingAttributeMenu',
                  label='Driving Attribute:',
                  height=18,
                  changeCommand=__set_limit_display_units)

    driving_attributes = ['translateX', 'translateY', 'translateZ',
                          'rotateX', 'rotateY', 'rotateZ']
    for attr in driving_attributes:
        pm.menuItem(label=attr)

    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 80), (2, 65), (3, 65)],
                 height=20)
    pm.text(label='Position Limits:')

    pm.textField('t_externalAxisLimitMin',
                 placeholderText='mm')

    pm.textField('t_externalAxisLimitMax',
                 placeholderText='mm')

    pm.setParent('..')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 80)],
                 height=20)
    pm.text(label='Velocity Limit:')

    pm.textField('t_externalAxisVelocityLimit',
                 placeholderText='m/s')
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_attachRobotToController',
                label="Attach robot to controller", value=0)
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_ignoreExternalAxis',
                label="Ignore in prostprocessor", value=0)
    pm.setParent('..')

    pm.separator(height=4, style='none')

    pm.setParent(add_external_axis_col)

    pm.button('b_add_Axis',
              label='Add Axis',
              height=25,
              backgroundColor=[.361, .361, .361],
              command=mimic_external_axes.add_external_axis)
    pm.separator(height=5, style='none')

    pm.setParent(parent_layout)


def _build_axis_info_frame(parent_layout):
    # Axis Info
    pm.frameLayout(label="Axis Info",
                   # height=215,
                   collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))

    pm.textScrollList('tsl_externalAxes',
                      allowMultiSelection=False,
                      height=185,
                      selectCommand=mimic_external_axes.axis_selected)

    pm.gridLayout(nc=2, cw=109, ch=25)
    pm.button(label='List Axes',
              annotation='Lists all external axes on selected robot',
              command=mimic_external_axes.list_axes)

    pm.button(label='Clear List',
              annotation='Clears list above',
              command=mimic_external_axes.clear_external_axis_list)

    pm.setParent('..')

    pm.button(label='Deselect',
              annotation='Deselects all axes in list above',
              command=mimic_external_axes.deselect_external_axis)
    pm.separator(height=10, style='out')

    pm.button(label='Remove Axis',
              annotation='Removes selected axis from robot',
              command=mimic_external_axes.remove_external_axis)
    pm.setParent(parent_layout)


def _build_external_axes_tab(parent_layout):
    external_axes_tab_layout = pm.columnLayout('externalAxesTab',
                                               adj=True,
                                               width=100)
    _build_add_external_axis_frame(external_axes_tab_layout)
    _build_axis_info_frame(external_axes_tab_layout)

    pm.setParent(parent_layout)
    return external_axes_tab_layout

# SETUP - IOs
def _build_add_io_frame(parent_layout):
    pm.frameLayout('add_io_frame',
                    label="Add IO",
                    collapsable=True)
    add_io_col = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])

    pm.text(label='IO Name: ')
    pm.textField('t_ioNameText',
                 placeholderText='ioName',
                 font=FONT)
    pm.setParent('..')

    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    pm.text(label='Postproc ID: ')
    pm.textField('t_ioPostprocIDText',
                 placeholderText='postprocID',
                 font=FONT)
    pm.setParent('..')

    pm.separator(height=3, style='none')

    pm.optionMenu('ioNumberMenu',
                  label='IO Number:',
                  height=18)

    io_number_list = [i + 1 for i in range(12)]
    for io_number in io_number_list:
        pm.menuItem(label=io_number)

    pm.separator(height=3, style='none')

    pm.optionMenu('ioTypeMenu',
                  label='IO Type:     ',
                  height=18,
                  changeCommand=__update_enable_resolution)

    io_type = ['digital', 'analog']
    for attr in io_type:
        pm.menuItem(label=attr)

    pm.separator(height=3, style='none')

    pm.optionMenu('ioResolutionMenu',
                  label='IO Resolution:',
                  height=18)

    io_type = ['binary', '16-bit']
    for attr in io_type:
        pm.menuItem(label=attr)

    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_ignoreIO',
                label="Ignore in prostprocessor", value=0)
    pm.setParent('..')

    pm.separator(height=4, style='none')

    pm.setParent(add_io_col)

    pm.button('b_add_io',
              label='Add IO',
              height=25,
              backgroundColor=[.361, .361, .361],
              command=pm.Callback(mimic_io.add_io))
    pm.separator(height=5, style='none')

    pm.setParent(parent_layout)


def __update_enable_resolution(*args):
    io_type = pm.optionMenu('ioTypeMenu', query=True, value=True)
    if io_type == 'digital':
        pm.optionMenu('ioResolutionMenu', edit=True, enable=True)
    else:
        pm.optionMenu('ioResolutionMenu', edit=True, enable=False)


def _build_io_info_frame(parent_layout):
    # IO Info
    pm.frameLayout(label="IO Info",
                   # height=215,
                   collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))

    pm.textScrollList('tsl_ios',
                      allowMultiSelection=False,
                      height=198,
                      selectCommand=mimic_io.io_selected)

    pm.gridLayout(nc=2, cw=109, ch=25)
    pm.button(label='List IOs',
              annotation='Lists all IOs on selected robot',
              command=mimic_io.list_ios)

    pm.button(label='Clear List',
              annotation='Clears list above',
              command=mimic_io.clear_io_list)

    pm.setParent('..')

    pm.button(label='Deselect',
              annotation='Deselects all axes in list above',
              command=mimic_io.deselect_io)

    pm.separator(height=10, style='out')

    pm.button(label='Remove IO',
              annotation='Removes selected axis from robot',
              command=mimic_io.remove_io)

    pm.setParent(parent_layout)


def _build_io_tab(parent_layout):
    io_tab_layout = pm.columnLayout('ioTab',
                                    adj=True,
                                    width=100)
    _build_add_io_frame(io_tab_layout)
    _build_io_info_frame(io_tab_layout)
    pm.setParent(parent_layout)
    return io_tab_layout

# SETUP - mFIZ
def _build_add_mFIZ_node_frame(parent_layout):
    # Create frame layout with one column
    add_mFIZ_node_frame = pm.frameLayout(label="Add Robot", collapsable=True)
    add_mFIZ_node_col = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.button(label='Add mFIZ Node',
              command=mimic_io.add_mFIZ_node,
              height=20,
              annotation='Attaches selected mFIZ node to selected Robot')

    pm.setParent(add_mFIZ_node_frame)

    pm.separator(style='none')
    pm.setParent(parent_layout)


def _build_mFIZ_tab(parent_layout):
    mFIZ_tab_layout = pm.columnLayout('mFIZTab',
                                       adj=True,
                                       width=100)

    _build_add_mFIZ_node_frame(mFIZ_tab_layout)

    pm.setParent(parent_layout)
    return mFIZ_tab_layout

# SETUP - Comms
def _build_comms_tab(parent_layout):
    comms_tab_layout = pm.columnLayout('commsTab',
                                       adj=True,
                                       width=100)
    pm.setParent(parent_layout)
    return comms_tab_layout


def build_setup_tab(parent_layout):
    # Create setup tab Layout
    setup_tab_layout = pm.columnLayout(adj=True, height=525, width=200)

    # Create Form Layout with embeded Tab Layout
    setup_tabs_form = pm.formLayout()
    setup_tabs_layout = pm.tabLayout('setup_tabs_layout',
                                        height=100,
                                        borderStyle='none')
    pm.formLayout(setup_tabs_form,
                  edit=True,
                  attachForm=[(setup_tabs_layout, "top", 0),
                              (setup_tabs_layout, "bottom", 0),
                              (setup_tabs_layout, "left", 0),
                              (setup_tabs_layout, "right", 0)])

    general_setup_tab_layout = _build_general_setup_tab(setup_tabs_layout)
    external_axes_tab_layout = _build_external_axes_tab(setup_tabs_layout)
    io_tab_layout = _build_io_tab(setup_tabs_layout)
    mFIZ_tab_layout = _build_mFIZ_tab(setup_tabs_layout)
    # comms_tab_layout = _build_comms_tab(setup_tabs_layout)

    tabs = [[general_setup_tab_layout, 'General'],
            [external_axes_tab_layout, 'E. Axes'],
            [io_tab_layout, 'IOs'],
            [mFIZ_tab_layout, 'mFIZ'],
            # [comms_tab_layout, 'Comms']
            ]

    assign_tabs(tabs, setup_tabs_layout)

    pm.setParent(parent_layout)

    return setup_tab_layout


def _build_ui_setup_frame(parent_layout):
    pm.frameLayout(label="UI Setup", collapsable=True)
    ui_setup_column = pm.columnLayout(adj=True, columnAttach=('both', 5))

    pm.separator(height=2, style='none')

    # Shader range row layout
    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 113), (2, 50), (3, 50)],
                 height=20)

    pm.text(label='Shader range:')

    # Axis limit shader range float field
    pm.floatField("f_shaderRange",
                  min=0,
                  pre=0,
                  value=Prefs.get('SHADER_RANGE'),
                  changeCommand=mimic_utils.set_shader_range_ui)

    # Set axis limit shader range button
    pm.button(label=' Set ',
              width=50,
              height=20,
              command=mimic_utils.set_shader_range_ui)

    pm.setParent(ui_setup_column)
    pm.separator(height=8, style='none')
    pm.setParent(parent_layout)


# UTILS
def add_robot(*args):
    """
    """
    # Get required rigs directories
    dir_mimic = general_utils.get_mimic_dir()
    dir_rigs = dir_mimic + '/rigs'

    mimic_utils.import_robot(dir_rigs)
    mimic_utils.set_shader_range(Prefs.get('SHADER_RANGE'), True)
    mimic_utils.add_hud_script_node()
    mimic_utils.add_mimic_script_node()


def on_window_close(*args):
    """
    Executes when the main Mimic window is closed.
    :return: None
    """
    # De-register callbacks that cause Mimic to restart and load new preferences
    # when a file is opened or created
    mimic_config.de_register_callbacks()

