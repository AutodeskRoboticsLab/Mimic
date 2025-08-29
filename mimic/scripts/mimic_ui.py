#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates the Mimic UI.
"""
from functools import partial

try:
    import maya.cmds as cmds

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
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
    cmds.columnLayout(width=244, adj=True)

    # Add UI Header Image.
    robotImage = cmds.image(image='mimic_logo.png', width=244, height=60)
    mimic_tab_layout = create_mimic_tabs()
    animate_tab_layout = build_animate_tab(mimic_tab_layout)
    program_tab_layout = build_program_tab(mimic_tab_layout)
    setup_tab_layout = build_setup_tab(mimic_win)

    tabs = [(animate_tab_layout, "Animate"),
            (program_tab_layout, "Program"),
            (setup_tab_layout, "Setup")]
    assign_tabs(tabs, mimic_tab_layout)

    # Create output column
    outputColumn = cmds.columnLayout('outputColumn', width=7, adj=True)
    outputForm = cmds.formLayout()
    outputScrollField = cmds.scrollField('programOutputScrollField',
                                       width=3,
                                       height=610)
    cmds.formLayout(outputForm,
                  edit=True,
                  attachForm=[(outputScrollField, "top", 3),
                              (outputScrollField, "bottom", 3),
                              (outputScrollField, "left", 3),
                              (outputScrollField, "right", 3)])
    cmds.setParent(mimic_win)
    cmds.columnLayout('outputBarColumn', width=7)
    cmds.separator(height=1, style='none')
    bullets = '\n'.join([chr(0x2022) for _ in range(3)])
    cmds.text(bullets,
            align='left',
            annotation='Drag edge to view Output Window!')

    # Launch UI window
    cmds.window('mimic_win', height=560, width=245, edit=True)
    cmds.showWindow(mimic_win)


# MIMIC WINDOW
def create_mimic_window(window_name):
    # If the window already exists, delete the window
    if cmds.window("mimic_win", exists=True):
        cmds.deleteUI("mimic_win", window=True)

    # Initialize window and Layout
    mimic_version = general_utils.get_mimic_version()
    mimic_win = cmds.window("mimic_win",
                          closeCommand=on_window_close,
                          width=245,
                          title='MIMIC {}'.format(mimic_version))  # + ' <dev 4.8.19>'))
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)

    return mimic_win


def create_mimic_tabs():
    # Create Form Layout with embeded Tab Layout
    mimic_form = cmds.formLayout()
    mimic_tab_layout = cmds.tabLayout()
    cmds.formLayout(mimic_form,
                  edit=True,
                  attachForm=[(mimic_tab_layout, "top", 3),
                              (mimic_tab_layout, "bottom", 3),
                              (mimic_tab_layout, "left", 3),
                              (mimic_tab_layout, "right", 3)])

    return mimic_tab_layout


def assign_tabs(tabs, tab_layout, change_command=''):
    for tab in tabs:
        cmds.tabLayout(tab_layout,
                     edit=True,
                     tabLabel=[(tab[0], tab[1])])

    if change_command:
        cmds.tabLayout(tab_layout,
                     edit=True,
                     changeCommand=change_command)

# ANIMATE TAB
def _build_ik_tab(parent_layout):
    # Create column Layout for IK controls
    ik_tab_layout = cmds.columnLayout('ikTab', adj=True, width=100)

    cmds.separator(height=3, style='none')

    # IK Configuration Icon
    cmds.gridLayout(numberOfColumns=1,
                  cellWidth=216,
                  cellHeight=52)

    # Flip robot base button
    cmds.image(image='IK_config_icon.png')
    cmds.setParent(ik_tab_layout)  # Set parent to IK tab column layout


    cmds.gridLayout(numberOfColumns=3,
                  cellWidth=72,
                  cellHeight=126)

    # Flip robot base button
    cmds.symbolButton(image='flipBaseIcon.png',
                    command=mimic_utils.flip_robot_base,
                    annotation='Changes IK solution by flipping robot\'s base')
    # Flip robot elbow button
    cmds.symbolButton(image='flipElbowIcon.png',
                    command=mimic_utils.flip_robot_elbow,
                    annotation='Changes IK solution by flipping robot\'s elbow')
    # FLip robot wrist button
    cmds.symbolButton(image='flipWristIcon.png',
                    command=mimic_utils.flip_robot_wrist,
                    annotation='Changes IK solution by flipping robot\'s wrist')

    cmds.setParent(ik_tab_layout)  # Set parent to IK tab column layout


    cmds.separator(height=2, style='none')
    cmds.separator(height=11, style='out')

    # Key Animation Tool checkbox
    cmds.rowLayout(numberOfColumns=1)
    cmds.checkBox('cb_keyToolCtrl',
                label="Key tool controller",
                annotation='If checked, Tool Controller\'s Translate ' \
                           'and Rotate attributes will be keyed',
                value=1)

    cmds.setParent(ik_tab_layout)  # Set parent to IK tab column layout

    cmds.separator(height=5, style='none')

    # Keyframe IK configuration button
    cmds.button(label='Set IK Keyframe',
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

    cmds.setParent(parent_layout)
    return ik_tab_layout


def _build_fk_tab(parent_layout):
    # Create column Layout with embedded shelf layout in second tab
    fk_tab_layout = cmds.columnLayout('fkTab', adjustableColumn=True)

    cmds.separator(height=5, style='none')

    cmds.gridLayout(numberOfColumns=3,
                  numberOfRows=2,
                  cellWidth=72,
                  cellHeight=44)

    cmd_str = ('import maya.cmds as cmds; ' \
               'import mimic_utils; ' \
               'cmds.setFocus("fkTab");')

    for i in range(6):
        axis = i + 1
        sel_cmd_str = cmd_str + ' mimic_utils.select_fk_axis_handle({})' \
            .format(axis)
        button_img = 'a{}FkIcon.png'.format(axis)
        button_ann = 'Selects Axis {} FK Controller'.format(axis)
        cmds.symbolButton(image=button_img,
                        command=sel_cmd_str,
                        annotation=button_ann)
    cmds.setParent('..')

    # UI spacing
    cmds.separator(height=3, style='none')
    cmds.separator(height=11, style='out')

    cmds.rowLayout(numberOfColumns=7,
                 adjustableColumn=7,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 20), (2, 45), (3, 22),
                              (4, 45), (5, 22), (6, 45)],
                 height=20)

    cmds.text(label='A1:')
    cmds.textField("t_a1",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 1),
                 changeCommand=partial(mimic_utils.set_axis, 1))

    cmds.text(label='  A2:')
    cmds.textField("t_a2",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 2),
                 changeCommand=partial(mimic_utils.set_axis, 2))

    cmds.text(label='  A3:')
    cmds.textField("t_a3",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 3),
                 changeCommand=partial(mimic_utils.set_axis, 3))

    # UI spacing
    cmds.text(label='')
    cmds.setParent('..')
    cmds.separator(height=2, style='none')

    cmds.rowLayout(numberOfColumns=7,
                 adjustableColumn=7,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 20), (2, 45), (3, 22),
                              (4, 45), (5, 22), (6, 45)],
                 height=20)

    cmds.text(label='A4:')
    cmds.textField("t_a4",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 4),
                 changeCommand=partial(mimic_utils.set_axis, 4))

    cmds.text(label='  A5:')
    cmds.textField("t_a5",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 5),
                 changeCommand=partial(mimic_utils.set_axis, 5))

    cmds.text(label='  A6:')
    cmds.textField("t_a6",
                 font=FONT,
                 rfc=partial(mimic_utils.select_fk_axis_handle, 6),
                 changeCommand=partial(mimic_utils.set_axis, 6))

    # UI Spacing
    cmds.text(label='')
    cmds.setParent('..')
    cmds.separator(height=7, style='none')

    # Get and set FK pose buttons
    cmds.gridLayout(nc=2, cw=109, ch=25)
    cmds.button(label="Get Pose",
              command=mimic_utils.get_fk_pose,
              annotation='Gets selected robot\'s current axis rotation ' \
                         'values\nand prints them above')
    cmds.button(label='Set Pose',
              command=mimic_utils.set_fk_pose,
              annotation='Sets selected robot\'s current axis rotation ' \
                         'values\nto the input values above')

    cmds.setParent('..')

    # Clear FK pose button
    cmds.button(label='Clear',
              command=mimic_utils.clear_fk_pose_ui,
              annotation='Clears axis rotation input fields above')
    cmds.separator(height=14, style='out')

    # Keyframe FK button
    cmds.button(label="Set FK Keyframe",
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
    cmds.setParent(parent_layout)
    return fk_tab_layout


def _build_switcher_frame(parent_layout):
    # Create a frame for the IK/FK switcher tabs
    switcher_frame = cmds.frameLayout(label="IK/FK Switching", collapsable=True)

    # Create Form Layout with embeded Tab Layout
    switcher_form = cmds.formLayout()
    switcher_tab_layout = cmds.tabLayout('switcher_tab_layout', height=271)
    cmds.formLayout(switcher_form,
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

    cmds.setParent(parent_layout)


def _build_keyframing_tools_frame(parent_layout):
    keyframing_tools_frame = cmds.frameLayout(label="Keyframing Tools",
                                            collapsable=True)
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.button(label='Delete IK/FK Keyframe',
              command=mimic_utils.delete_ik_fk_keys,
              annotation='Deletes keyframes on all attributes ' \
                         'at current frame created with\n' \
                         '"Set IK-FK Keyframe" buttons')
    cmds.button(label='Select Keyframe Hierarchy',
              command=mimic_utils.select_keyframe_hierarchy,
              annotation='Selects all objects keyframed ' \
                         'with "Set IK-FK Keyframe" buttons:\n' \
                         '    target_CTRL\n' \
                         '    FK_CTRLS\n' \
                         '    a*FK_CTRL\n' \
                         '    tool_CTRL if one exists')

    cmds.separator(height=5, style='none')
    cmds.setParent(parent_layout)


def _build_general_frame(parent_layout):
    general_frame = cmds.frameLayout(label="General", collapsable=True)
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.button(label='Save Pose',
              command=mimic_utils.save_pose_to_shelf,
              annotation='Saves selected robot\'s current configuration\n' \
                         'to a button on the Mimic shelf')
    cmds.separator(height=10, style='out')

    cmds.gridLayout(numberOfColumns=2,
                  cellWidth=109,
                  cellHeight=25)

    # Zero target button
    cmds.button(label='Zero Tool (TCS)',
              command=mimic_utils.zero_target,
              annotation='Sets target_CTRL (or tool_CTRL if it exists)\n'
                         'transform to Zero')
    # Zero robot local controller button
    cmds.button(label='Zero Base (LCS)',
              command=mimic_utils.zero_base_local,
              annotation='Sets local_CTRL transform to Zero')
    # Zero robot world controller button
    cmds.button(label='Zero Base (WCS)',
              command=mimic_utils.zero_base_world,
              annotation='Sets world_CTRL transform to Zero')
    # Zero all button
    cmds.button(label='Zero All',
              command=mimic_utils.zero_all,
              annotation='Sets local_CTRL, world_CTRL, and target_CTRL (or ' \
                         'tool_CTRL if it exists)\ntransforms\' to Zero')
    cmds.setParent('..')

    cmds.separator(height=10, style='out')

    # Toggle heads up display button
    cmds.button(label='Toggle HUD',
              command=mimic_utils.axis_val_hud,
              annotation='Toggles the visibility of Mimic\'s Heads Up Display')

    cmds.separator(height=10, style='none')

    cmds.setParent(parent_layout)


def build_animate_tab(parent_layout):
    # This tab contains tools that aid in the animation process; IK/FK
    # switching, keyframing, and some general tools

    # Create the main column layout for the tab
    animate_tab_layout = cmds.columnLayout(adj=True, width=225, height=525)

    _build_switcher_frame(animate_tab_layout)
    _build_keyframing_tools_frame(animate_tab_layout)
    _build_general_frame(animate_tab_layout)

    cmds.setParent(parent_layout)

    return animate_tab_layout

# PROGRAM TAB
def _build_general_settings_tab(parent_layout):
    # Create column Layout for General settings
    general_settings_tab_layout = cmds.columnLayout('generalSettings',
                                                  adj=True,
                                                  width=100)
    cmds.separator(height=3, style='none')

    cmds.rowLayout(numberOfColumns=3,
                 columnWidth3=(55, 250, 30),
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    cmds.text(label="Directory:")
    cmds.textField('t_programDirectoryText',
                 text=Prefs.get('DEFAULT_PROGRAM_DIRECTORY'),
                 ed=False,
                 font=FONT)

    cmds.symbolButton('b_directoryImage',
                    image="setDirectory_icon.png",
                    width=32,
                    height=20,
                    command=partial(mimic_utils.set_dir,
                                        't_programDirectoryText',
                                        'DEFAULT_PROGRAM_DIRECTORY',
                                        Prefs.get,
                                        Prefs.set))
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 90), (2, 100)],
                 height=20)
    cmds.text(label='Output name:')

    cmds.textField('t_outputFileName',
                 text=Prefs.get('DEFAULT_OUTPUT_NAME'),
                 font=FONT,
                 changeCommand=partial(Prefs.set, 'DEFAULT_OUTPUT_NAME'))
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 90), (2, 100)],
                 height=20)
    cmds.text(label='Template name:')
    cmds.textField('t_templateFileName',
                 text=Prefs.get('DEFAULT_TEMPLATE_NAME'),
                 font=FONT,
                 changeCommand=partial(Prefs.set, 'DEFAULT_TEMPLATE_NAME'))

    cmds.setParent('..')

    # Sample rate radio buttons
    cmds.separator(height=3, style='none')
    selected_units = Prefs.get('DEFAULT_SAMPLE_RATE_UNITS')
    selected_value = Prefs.get('DEFAULT_SAMPLE_RATE_VALUE')
    radio_indent = 3
    cmds.radioCollection('sample_rate_radio_collection')
    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', radio_indent),
                 columnWidth=[(1, 90), (2, 45)],
                 height=20)
    cmds.radioButton('rb_timeInterval',
                   label='Sample rate:',
                   select=not Prefs.get('SAMPLE_KEYFRAMES_ONLY'))
    cmds.floatField('f_timeBetweenSamples',
                 value=selected_value,
                 precision=3,
                 changeCommand=partial(Prefs.set, 'DEFAULT_SAMPLE_RATE_VALUE'))
    cmds.radioButtonGrp('time_unit_radio_group',
                      labelArray2=['s', 'f'],
                      annotation='Sample rate units: seconds or frames',
                      numberOfRadioButtons=2,
                      columnWidth2=[32, 30],
                      select=1 if selected_units == 'seconds' else 2,  # 1-based integer
                      onCommand1 = partial(
                          Prefs.set,
                          'DEFAULT_SAMPLE_RATE_UNITS', 'seconds', mimic_config.FILE),
                      onCommand2 = partial(
                          Prefs.set,
                          'DEFAULT_SAMPLE_RATE_UNITS', 'frames', mimic_config.FILE))
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=1,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', radio_indent),
                 height=20)
    cmds.radioButton('rb_keyframesOnly',
                   label='Sample keyframes only',
                   enable=True,
                   select=Prefs.get('SAMPLE_KEYFRAMES_ONLY'),
                   onCommand=partial(
                       Prefs.set,
                       'SAMPLE_KEYFRAMES_ONLY', True, mimic_config.FILE),
                   offCommand=partial(
                       Prefs.set,
                       'SAMPLE_KEYFRAMES_ONLY', False, mimic_config.FILE))
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 132), (2, 40), (3, 30)],
                 height=20)
    cmds.text(label='Animation frame range:')

    cmds.intField("i_programStartFrame",
                value=cmds.playbackOptions(animationStartTime=True, query=True),
                minValue=-10000,
                maxValue=100000,
                step=1,
                changeCommand=partial(Prefs.set, 'ANIMATION_RANGE_START'))

    cmds.intField("i_programEndFrame",
                value=cmds.playbackOptions(animationEndTime=True, query=True),
                minValue=-10000,
                maxValue=100000,
                step=1,
                changeCommand=partial(Prefs.set, 'ANIMATION_RANGE_END'))

    cmds.setParent('..')

    cmds.separator(height=5, style='none')

    # Post processor option menu list
    cmds.optionMenu('postProcessorList',
                  label='Processor:',
                  height=18,
                  changeCommand=partial(postproc_options.overwrite_options))

    # Get supported post-processors and fill option menu list
    supported_post_processors = postproc_setup.get_processor_names(mimic_config.FILE)
    for post in supported_post_processors:
        cmds.menuItem(label=post)
    cmds.separator(height=3, style='none')

    cmds.setParent(parent_layout)
    return general_settings_tab_layout


def _build_proc_options_tab(parent_layout):
    # Create column Layout for General settings
    proc_options_tab_layout = cmds.columnLayout('procOptions', adj=True, width=100)
    cmds.separator(height=3, style='none')

    # Name this tab? May not be necessary
    cmds.separator(height=3, style='none')
    cmds.text('User options:', align='left')
    cmds.separator(height=3, style='none')

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

    cmds.setParent(parent_layout)
    return proc_options_tab_layout


def _build_program_settings_frame(parent_layout):
    program_settings_frame = cmds.frameLayout(label="Program Settings",
                                            collapsable=True)

    # Create Form Layout with embedded Tab Layout
    program_settings_form = cmds.formLayout()
    program_settings_tab_layout = cmds.tabLayout('program_settings_tab_layout')
    cmds.formLayout(program_settings_form,
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

    program_settings_col = cmds.columnLayout(adj=True, columnAttach=['both', 3])

    # Output options
    cmds.checkBox('cb_overwriteFile',
                label="Overwrite existing file",
                value=Prefs.get('OPTS_OVERWRITE_EXISTING_FILE'),
                annotation='If checked, an existing file with the input ' \
                           'output name will be overwritten',
                changeCommand=partial(Prefs.set, 'OPTS_OVERWRITE_EXISTING_FILE'))
    cmds.checkBox('cb_ignoreWarnings',
                label="Ignore warnings",
                value=Prefs.get('OPTS_IGNORE_WARNINGS'),
                annotation='If checked, all warnings will be ignored and ' \
                           'a program will be written',
                changeCommand=partial(Prefs.set, 'OPTS_IGNORE_WARNINGS'))

    cmds.separator(height=3, style='none')

    # Preview Options
    cmds.separator(height=11, style='out')
    cmds.checkBox('cb_previewInViewport',
                label="Preview in viewport",
                value=Prefs.get('OPTS_PREVIEW_IN_VIEWPORT'),
                annotation='If checked, program will play in viewport during ' \
                           'post-process. Leave unchecked for faster results.',
                changeCommand=partial(Prefs.set, 'OPTS_PREVIEW_IN_VIEWPORT'))
    cmds.checkBox('cb_promptOnRedundantSolutions',
                label="Prompt on redundant solutions",
                value=Prefs.get('OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'),
                annotation='If checked, Maya will as the user to select between ' \
                       'redundant solutions on axes where they occur.',
                changeCommand=partial(Prefs.set,
                                                  'OPTS_REDUNDANT_SOLUTIONS_USER_PROMPT'))

    cmds.separator(height=6, style='none')

    cmds.button('Analyze Program',
              command=mimic_program.analyze_program,
              height=25,
              annotation='Launches graphical analysis tool')
    cmds.button('Save Program',
              command=mimic_program.save_program,
              height=25,
              annotation='Saves robot control program with input parameters')
    cmds.separator(height=3, style='none')

    export_progress_bar = cmds.progressBar('pb_exportProgress',
                                         isInterruptable=True,
                                         maxValue=100,
                                         visible=0)

    cmds.setParent(parent_layout)


def build_program_tab(parent_layout):
    # Create preferences tab Layout
    program_tab_layout = cmds.columnLayout(adj=True, height=525, width=200)

    _build_program_settings_frame(program_tab_layout)
    # _build_output_frame(program_tab_layout)

    cmds.setParent(parent_layout)

    return program_tab_layout

# SETUP TAB
# SETUP - General
def _build_add_robot_frame(parent_layout):
    # Create frame layout with one column
    add_robot_frame = cmds.frameLayout(label="Add Robot", collapsable=True)
    add_robot_col = cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    # Create list of robots
    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 158), (2, 45)],
                 height=20)

    cmds.optionMenu('robotImportList',
                  changeCommand=partial(Prefs.set, 'DEFAULT_ROBOT'))

    rigs = general_utils.get_rigs_dict()
    default_rig = Prefs.get('DEFAULT_ROBOT')
    rig_names = general_utils.get_rigs_names(rigs, default_rig)
    for rig_name in rig_names:
        cmds.menuItem(label=rig_name)

    cmds.button(label=' Add ',
              command=add_robot,
              width=45,
              height=20,
              annotation='Imports selected robot into the scene')

    cmds.setParent(add_robot_frame)

    cmds.separator(style='none')
    cmds.setParent(parent_layout)


def _build_tool_setup_frame(parent_layout):
    controllers_frame = cmds.frameLayout(label="Tool Setup", collapsable=True)
    controllers_column = cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 90), (2, 60), (3, 60)],
                 height=20)
    cmds.text('Tool controller:', align='left')
    cmds.button(label='Attach',
              width=58,
              height=20,
              command=mimic_utils.attach_tool_controller,
              annotation='Attaches selected tool controller to the ' \
                         'selected robot')
    cmds.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_controller,
              annotation='Detaches tool controller from robot')
    cmds.setParent('..')

    cmds.separator(height=3, style='none')

    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 90), (2, 60), (3, 60)],
                 height=20)
    cmds.text('Tool model:', align='left')
    cmds.button(label='Attach',
              width=58,
              height=20,
              command=mimic_utils.attach_tool_model,
              annotation='Attaches selected tool model to the ' \
                         'selected robot')
    cmds.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_model,
              annotation='Detaches selected tool model from its ' \
                         'parent robot')
    cmds.setParent('..')

    cmds.separator(height=8, style='none')
    cmds.setParent(parent_layout)


def _build_position_limits_tab(parent_layout):
    position_limits_tab = cmds.rowColumnLayout('position_limits_tab',
                                             numberOfColumns=2)

    # Input text field width for all axis limits
    cell_width = 80

    # Set up primary axis limits UI
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        cmds.text(label='Axis {}: '.format(i + 1))

        # Axis 1 Min limit
        cmds.textField("t_A{}Min".format(i + 1),
                     font=FONT,
                     pht='Min',
                     width=cell_width,
                     changeCommand='import maya.cmds as cmds; ' \
                                   'cmds.setFocus("t_A{}Max"); ' \
                                   .format(i + 1))
        # Axis 1 Max limit
        set_focus_count = ((i + 1) % 6) + 1
        cmds.textField("t_A{}Max".format(i + 1),
                     font=FONT,
                     pht='Max',
                     width=cell_width,
                     changeCommand='import maya.cmds as cmds; ' \
                                   'cmds.setFocus("t_A{}Min"); ' \
                                   .format(set_focus_count))

        cmds.setParent('..')

    cmds.setParent(parent_layout)

    return position_limits_tab


def _build_velocity_limits_tab(parent_layout):
    velocity_limits_tab = cmds.rowColumnLayout('velocity_limits_tab',
                                             numberOfColumns=2)

    # Set up primary axis velocity limits tab
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        cmds.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        cmds.textField("t_A{}Velocity".format(i + 1),
                     font=FONT,
                     pht='deg/sec',
                     width=cell_width,
                     changeCommand='import maya.cmds as cmds; ' \
                                   'import mimic_utils; ' \
                                   'cmds.setFocus("t_A{}Velocity"); ' \
                     .format(set_focus_count))
        cmds.setParent('..')

    cmds.setParent(parent_layout)

    return velocity_limits_tab


def _build_accel_limits_tab(parent_layout):
    accel_limits_tab = cmds.rowColumnLayout('accel_limits_tab',
                                          numberOfColumns=2)

    # Set up primary axis accel limits tab
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        cmds.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        cmds.textField("t_A{}Accel".format(i + 1),
                     font=FONT,
                     pht='deg/sec' + '\xb2',
                     width=cell_width,
                     changeCommand='import maya.cmds as cmds; ' \
                                   'import mimic_utils; ' \
                                   'cmds.setFocus("t_A{}Accel"); ' \
                     .format(set_focus_count))
        cmds.setParent('..')

    cmds.setParent(parent_layout)

    return accel_limits_tab


def _build_jerk_limits_tab(parent_layout):
    jerk_limits_tab = cmds.rowColumnLayout('jerk_limits_tab', numberOfColumns=2)

    # Set up primary axis accel limits tab
    cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 163

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     adjustableColumn=2,
                     height=20)
        cmds.text(label='Axis {}: '.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        cmds.textField("t_A{}Jerk".format(i + 1),
                     font=FONT,
                     pht='deg/sec' + '\xb3',
                     width=cell_width,
                     changeCommand='import maya.cmds as cmds; ' \
                                   'import mimic_utils; ' \
                                   'cmds.setFocus("t_A{}Jerk"); ' \
                     .format(set_focus_count))
        cmds.setParent('..')

    cmds.setParent(parent_layout)

    return jerk_limits_tab


def _build_axis_limits_frame(parent_layout):
    limits_frame = cmds.frameLayout(label="Axis Limits", collapsable=True)
    limits_tab_layout = cmds.tabLayout('limits_tab_layout', height=155)

    position_limits_tab = _build_position_limits_tab(limits_tab_layout)
    velocity_limits_tab = _build_velocity_limits_tab(limits_tab_layout)
    accel_limits_tab = _build_accel_limits_tab(limits_tab_layout)
    jerk_limits_tab = _build_jerk_limits_tab(limits_frame)

    tabs = [(position_limits_tab, 'Position'),
            (velocity_limits_tab, 'Vel'),
            (accel_limits_tab, 'Accel'),
            (jerk_limits_tab, 'Jerk')]

    assign_tabs(tabs, limits_tab_layout)

    cmds.columnLayout()
    cmds.gridLayout(nc=2, cw=114, ch=25)
    cmds.button(label='Get Axis Limits', command=mimic_utils.write_limits_to_ui)
    cmds.button(label='Set Axis Limits', command=mimic_utils.set_axis_limits)

    cmds.setParent('..')
    cmds.button(label='Clear', width=228, command=mimic_utils.clear_limits_ui)

    cmds.setParent(parent_layout)


def _build_general_setup_tab(parent_layout):
    general_setup_tab_layout = cmds.columnLayout('generalSetupTab',
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

    cmds.setParent(parent_layout)

    return general_setup_tab_layout

# SETUP - External Axes
def _build_add_external_axis_frame(parent_layout):
    cmds.frameLayout('add_external_axis_frame',
                   label="Add External Axis",
                   collapsable=True)
    add_external_axis_col = cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    cmds.text(label='Axis Name: ')
    cmds.textField('t_externalAxisDescriptionText',
                 placeholderText='axisName',
                 font=FONT)
    cmds.setParent('..')
    cmds.separator(height=3, style='none')

    def __set_limit_display_units(*args):
        if 'translate' in args[0]:

            cmds.textField('t_externalAxisLimitMin',
                         edit=True,
                         placeholderText='mm')
            cmds.textField('t_externalAxisLimitMax',
                         edit=True,
                         placeholderText='mm')
            cmds.textField('t_externalAxisVelocityLimit',
                         edit=True,
                         placeholderText='m/s')
        else:
            cmds.textField('t_externalAxisLimitMin',
                         edit=True,
                         placeholderText='deg')
            cmds.textField('t_externalAxisLimitMax',
                         edit=True,
                         placeholderText='deg')
            cmds.textField('t_externalAxisVelocityLimit',
                         edit=True,
                         placeholderText='deg/s')

    cmds.optionMenu('axisNumberMenu',
                  label='Axis Number:',
                  height=18)

    axis_number_list = [i + 1 for i in range(16)]
    for axis_number in axis_number_list:
        cmds.menuItem(label=axis_number)

    cmds.separator(height=3, style='none')

    cmds.optionMenu('drivingAttributeMenu',
                  label='Driving Attribute:',
                  height=18,
                  changeCommand=__set_limit_display_units)

    driving_attributes = ['translateX', 'translateY', 'translateZ',
                          'rotateX', 'rotateY', 'rotateZ']
    for attr in driving_attributes:
        cmds.menuItem(label=attr)

    cmds.separator(height=3, style='none')

    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 80), (2, 65), (3, 65)],
                 height=20)
    cmds.text(label='Position Limits:')

    cmds.textField('t_externalAxisLimitMin',
                 placeholderText='mm')

    cmds.textField('t_externalAxisLimitMax',
                 placeholderText='mm')

    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 80)],
                 height=20)
    cmds.text(label='Velocity Limit:')

    cmds.textField('t_externalAxisVelocityLimit',
                 placeholderText='m/s')
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=1)
    cmds.checkBox('cb_attachRobotToController',
                label="Attach robot to controller", value=0)
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=1)
    cmds.checkBox('cb_ignoreExternalAxis',
                label="Ignore in prostprocessor", value=0)
    cmds.setParent('..')

    cmds.separator(height=4, style='none')

    cmds.setParent(add_external_axis_col)

    cmds.button('b_add_Axis',
              label='Add Axis',
              height=25,
              backgroundColor=[.361, .361, .361],
              command=mimic_external_axes.add_external_axis)
    cmds.separator(height=5, style='none')

    cmds.setParent(parent_layout)


def _build_axis_info_frame(parent_layout):
    # Axis Info
    cmds.frameLayout(label="Axis Info",
                   height=315,
                   collapsable=True)
    cmds.columnLayout(adj=True, columnAttach=('both', 5))

    cmds.textScrollList('tsl_externalAxes',
                      allowMultiSelection=False,
                      height=185,
                      selectCommand=mimic_external_axes.axis_selected)

    cmds.gridLayout(nc=2, cw=109, ch=25)
    cmds.button(label='List Axes',
              annotation='Lists all external axes on selected robot',
              command=mimic_external_axes.list_axes)

    cmds.button(label='Clear List',
              annotation='Clears list above',
              command=mimic_external_axes.clear_external_axis_list)

    cmds.setParent('..')

    cmds.button(label='Deselect',
              annotation='Deselects all axes in list above',
              command=mimic_external_axes.deselect_external_axis)
    cmds.separator(height=10, style='out')

    cmds.button(label='Remove Axis',
              annotation='Removes selected axis from robot',
              command=mimic_external_axes.remove_external_axis)
    cmds.setParent(parent_layout)


def _build_external_axes_tab(parent_layout):
    external_axes_tab_layout = cmds.columnLayout('externalAxesTab',
                                               adj=True,
                                               width=100)
    _build_add_external_axis_frame(external_axes_tab_layout)
    _build_axis_info_frame(external_axes_tab_layout)

    cmds.setParent(parent_layout)
    return external_axes_tab_layout

# SETUP - IOs
def _build_add_io_frame(parent_layout):
    cmds.frameLayout('add_io_frame',
                    label="Add IO",
                    collapsable=True)
    add_io_col = cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])

    cmds.text(label='IO Name: ')
    cmds.textField('t_ioNameText',
                 placeholderText='ioName',
                 font=FONT)
    cmds.setParent('..')

    cmds.separator(height=3, style='none')

    cmds.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAlign=[(1, 'left'),
                              (2, 'left')],
                 columnAttach=[(1, 'both', -1),
                               (2, 'both', 0),
                               (3, 'both', 0)])
    cmds.text(label='Postproc ID: ')
    cmds.textField('t_ioPostprocIDText',
                 placeholderText='postprocID',
                 font=FONT)
    cmds.setParent('..')

    cmds.separator(height=3, style='none')

    cmds.optionMenu('ioNumberMenu',
                  label='IO Number:',
                  height=18)

    io_number_list = [i + 1 for i in range(12)]
    for io_number in io_number_list:
        cmds.menuItem(label=io_number)

    cmds.separator(height=3, style='none')

    cmds.optionMenu('ioTypeMenu',
                  label='IO Type:     ',
                  height=18,
                  changeCommand=__update_enable_resolution)

    io_type = ['digital', 'analog']
    for attr in io_type:
        cmds.menuItem(label=attr)

    cmds.separator(height=3, style='none')

    cmds.optionMenu('ioResolutionMenu',
                  label='IO Resolution:',
                  height=18)

    io_type = ['binary', '16-bit']
    for attr in io_type:
        cmds.menuItem(label=attr)

    cmds.separator(height=3, style='none')

    cmds.rowLayout(numberOfColumns=1)
    cmds.checkBox('cb_ignoreIO',
                label="Ignore in prostprocessor", value=0)
    cmds.setParent('..')

    cmds.separator(height=4, style='none')

    cmds.setParent(add_io_col)

    cmds.button('b_add_io',
              label='Add IO',
              height=25,
              backgroundColor=[.361, .361, .361],
              command=partial(mimic_io.add_io))
    cmds.separator(height=5, style='none')

    cmds.setParent(parent_layout)


def __update_enable_resolution(*args):
    io_type = cmds.optionMenu('ioTypeMenu', query=True, value=True)
    if io_type == 'digital':
        cmds.optionMenu('ioResolutionMenu', edit=True, enable=True)
    else:
        cmds.optionMenu('ioResolutionMenu', edit=True, enable=False)


def _build_io_info_frame(parent_layout):
    # IO Info
    cmds.frameLayout(label="IO Info",
                   height=315,
                   collapsable=True)
    cmds.columnLayout(adj=True, columnAttach=('both', 5))

    cmds.textScrollList('tsl_ios',
                      allowMultiSelection=False,
                      height=198,
                      selectCommand=mimic_io.io_selected)

    cmds.gridLayout(nc=2, cw=109, ch=25)
    cmds.button(label='List IOs',
              annotation='Lists all IOs on selected robot',
              command=mimic_io.list_ios)

    cmds.button(label='Clear List',
              annotation='Clears list above',
              command=mimic_io.clear_io_list)

    cmds.setParent('..')

    cmds.button(label='Deselect',
              annotation='Deselects all axes in list above',
              command=mimic_io.deselect_io)

    cmds.separator(height=10, style='out')

    cmds.button(label='Remove IO',
              annotation='Removes selected axis from robot',
              command=mimic_io.remove_io)

    cmds.setParent(parent_layout)


def _build_io_tab(parent_layout):
    io_tab_layout = cmds.columnLayout('ioTab',
                                    adj=True,
                                    width=100)
    _build_add_io_frame(io_tab_layout)
    _build_io_info_frame(io_tab_layout)
    cmds.setParent(parent_layout)
    return io_tab_layout

# SETUP - mFIZ
def _build_add_mFIZ_node_frame(parent_layout):
    # Create frame layout with one column
    add_mFIZ_node_frame = cmds.frameLayout(label="mFIZ", collapsable=True)
    add_mFIZ_node_col = cmds.columnLayout(adj=True, columnAttach=('both', 5))
    cmds.separator(height=5, style='none')

    cmds.button(label='Attach mFIZ Node to Robot',
              command=mimic_io.add_mFIZ_node,
              height=20,
              annotation='Attaches selected mFIZ node to selected Robot')

    cmds.setParent(add_mFIZ_node_frame)

    cmds.separator(style='none')
    cmds.setParent(parent_layout)


def _build_mFIZ_tab(parent_layout):
    mFIZ_tab_layout = cmds.columnLayout('mFIZTab',
                                       adj=True,
                                       width=100)

    _build_add_mFIZ_node_frame(mFIZ_tab_layout)

    cmds.setParent(parent_layout)
    return mFIZ_tab_layout

# SETUP - Comms
def _build_comms_tab(parent_layout):
    comms_tab_layout = cmds.columnLayout('commsTab',
                                       adj=True,
                                       width=100)
    cmds.setParent(parent_layout)
    return comms_tab_layout


def build_setup_tab(parent_layout):
    # Create setup tab Layout
    setup_tab_layout = cmds.columnLayout(adj=True, height=525, width=200)

    # Create Form Layout with embeded Tab Layout
    setup_tabs_form = cmds.formLayout()
    setup_tabs_layout = cmds.tabLayout('setup_tabs_layout',
                                        height=100,
                                        borderStyle='none')
    cmds.formLayout(setup_tabs_form,
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

    cmds.setParent(parent_layout)

    return setup_tab_layout


def _build_ui_setup_frame(parent_layout):
    cmds.frameLayout(label="UI Setup", collapsable=True)
    ui_setup_column = cmds.columnLayout(adj=True, columnAttach=('both', 5))

    cmds.separator(height=2, style='none')

    # Shader range row layout
    cmds.rowLayout(numberOfColumns=3,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 113), (2, 50), (3, 50)],
                 height=20)

    cmds.text(label='Shader range:')

    # Axis limit shader range float field
    cmds.floatField("f_shaderRange",
                  min=0,
                  pre=0,
                  value=Prefs.get('SHADER_RANGE'),
                  changeCommand=mimic_utils.set_shader_range_ui)

    # Set axis limit shader range button
    cmds.button(label=' Set ',
              width=50,
              height=20,
              command=mimic_utils.set_shader_range_ui)

    cmds.setParent(ui_setup_column)
    cmds.separator(height=8, style='none')
    cmds.setParent(parent_layout)


# UTILS
def add_robot(*args):
    """
    """
    # Get required rigs directories
    dir_mimic = general_utils.get_mimic_dir()
    dir_rigs = dir_mimic + '/rigs'

    new_robot = mimic_utils.import_robot(dir_rigs)
    if new_robot:
        mimic_utils.set_shader_range(Prefs.get('SHADER_RANGE'), robot=new_robot)
        mimic_utils.add_hud_script_node()


def on_window_close(*args):
    """
    Executes when the main Mimic window is closed.
    :return: None
    """
    # De-register callbacks that cause Mimic to restart and load new preferences
    # when a file is opened or created
    mimic_config.de_register_callbacks()

