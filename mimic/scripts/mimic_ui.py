#!usr/bin/env python

"""
Creates the Mimic UI.
"""

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

from collections import OrderedDict
import general_utils
import mimic_config
import mimic_utils
from postproc import postproc_config
from postproc import postproc_setup

reload(mimic_utils)
reload(mimic_config)
reload(general_utils)
reload(postproc_setup)
reload(postproc_config)

FONT = 'smallObliqueLabelFont'


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
    setup_tab_layout = build_setup_tab(mimic_tab_layout)
    # external_axis_tab_layout = build_external_axes_tab(mimic_tab_layout)
    prefs_tab_layout = build_prefs_tab(mimic_win)

    tabs = [(animate_tab_layout, "Animate"),
            (program_tab_layout, "Program"),
            (setup_tab_layout, "Setup"),
            # (external_axis_tab_layout, "E.Axes"),
            (prefs_tab_layout, "Prefs")]

    assign_tabs(tabs, mimic_tab_layout)

    # Create output column
    outputColumn = pm.columnLayout('outputColumn', width=7, adj=True)
    outputForm = pm.formLayout()
    outputScrollField = pm.scrollField('programOutputScrollField', width=3, height=610)
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
    pm.text(bullets, align='left', annotation='Drag edge to view Output Window!')

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
                          width=245,
                          title='MIMIC {}'.format(mimic_version))
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

    pm.gridLayout(numberOfColumns=2,
                  cellWidth=108,
                  cellHeight=52)

    # Invert Axis 4 button
    pm.symbolButton(image='flipA4Icon.png',
                    command=pm.Callback(mimic_utils.invert_axis, 4))
    # Invert Axis 6 button
    pm.symbolButton(image='flipA6Icon.png',
                    command=pm.Callback(mimic_utils.invert_axis, 6))
    pm.setParent(ik_tab_layout)  # Set parent to IK tab column layout

    pm.separator(height=5, style='none')
    pm.separator(height=11, style='out')

    # Key Animation Tool checkbox
    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_keyToolCtrl',
                label="Key tool controller",
                value=1)

    pm.setParent(ik_tab_layout)  # Set parent to IK tab column layout

    pm.separator(height=5, style='none')

    # Keyframe IK configuration button
    pm.button(label='Set IK Keyframe', command=mimic_utils.key_ik)

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

    # Select axis 1 symbol button
    sel_a1_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(1)'
    pm.symbolButton(image='a1FkIcon.png', command=sel_a1_cmd)

    # Select axis 2 symbol button
    sel_a2_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(2)'
    pm.symbolButton(image='a2FkIcon.png', command=sel_a2_cmd)

    # Select axis 3 symbol button
    sel_a3_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(3)'
    pm.symbolButton(image='a3FkIcon.png', command=sel_a3_cmd)

    # Select axis 4 symbol button
    sel_a4_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(4)'
    pm.symbolButton(image='a4FkIcon.png', command=sel_a4_cmd)

    # Select axis 5 symbol button
    sel_a5_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(5)'
    pm.symbolButton(image='a5FkIcon.png', command=sel_a5_cmd)

    # Select axis 6 symbol button
    sel_a6_cmd = cmd_str + ' mimic_utils.select_fk_axis_handle(6)'
    pm.symbolButton(image='a6FkIcon.png', command=sel_a6_cmd)

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
    pm.button(label="Get Pose", command=mimic_utils.get_fk_pose)
    pm.button(label='Set Pose', command=mimic_utils.set_fk_pose)

    pm.setParent('..')

    # Clear FK pose button
    pm.button(label='Clear', command=mimic_utils.clear_fk_pose_ui)
    pm.separator(height=14, style='out')

    # Keyframe FK button
    pm.button(label="Set FK Keyframe",
              command=mimic_utils.key_fk,
              bgc=[.7, .7, .7])
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
              command=mimic_utils.delete_ik_fk_keys)
    pm.button(label='Select Keyframe Hierarchy',
              command=mimic_utils.select_keyable_robot_objects)

    pm.separator(height=5, style='none')
    pm.setParent(parent_layout)


def _build_general_frame(parent_layout):
    general_frame = pm.frameLayout(label="General", collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.button(label='Save Pose', command=mimic_utils.save_pose_to_shelf)
    pm.separator(height=10, style='out')

    pm.gridLayout(numberOfColumns=2,
                  cellWidth=109,
                  cellHeight=25)

    # Zero target button
    pm.button(label='Zero Tool (TCS)', command=mimic_utils.zero_target)
    # Zero robot local controller button
    pm.button(label='Zero Base (LCS)', command=mimic_utils.zero_base_local)
    # Zero robot world controller button
    pm.button(label='Zero Base (WCS)', command=mimic_utils.zero_base_world)
    # Zero all button
    pm.button(label='Zero All', command=mimic_utils.zero_all)
    pm.setParent('..')

    pm.separator(height=10, style='out')

    # Toggle heads up display button
    pm.button(label='Toggle HUD', command=mimic_utils.axis_val_hud)

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
                 text='',
                 ed=False,
                 font=FONT)

    pm.symbolButton('b_directoryImage',
                    image="setDirectory_icon.png",
                    width=32,
                    height=20,
                    command=mimic_utils.set_program_dir)
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 57), (2, 150)],
                 height=20)
    pm.text(label='Filename:')
    pm.textField('t_outputFileName',
                 text=postproc_config.DEFAULT_OUTPUT_NAME,
                 font=FONT)
    pm.setParent('..')

    # pm.rowLayout(numberOfColumns=1,
    #              adjustableColumn=1,
    #              columnAttach=(1, 'left', -1),
    #              height=20)
    # pm.text(label='Sample rate:', align='left')
    # pm.setParent('..')

    # Sample rate radio buttons
    pm.separator(height=3, style='none')
    selected_units = postproc_config.DEFAULT_SAMPLE_RATE_UNITS
    selected_value = postproc_config.DEFAULT_SAMPLE_RATE_VALUE
    radio_indent = 3
    pm.radioCollection('sample_rate_radio_collection')
    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', radio_indent),
                 columnWidth=[(1, 90), (2, 45)],
                 height=20)
    pm.radioButton('rb_timeInterval',
                   label='Sample rate:',
                   select=True)
    pm.textField('t_timeBetweenSamples',
                 text=selected_value,
                 font=FONT)
    pm.radioButtonGrp('time_unit_radio_group',
                      labelArray2=['s', 'f'],
                      annotation='Sample rate units: seconds or frames',
                      numberOfRadioButtons=2,
                      columnWidth2=[32, 30],
                      select=1 if selected_units == 'seconds' else 2)  # 1-based integer
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', radio_indent),
                 height=20)
    pm.radioButton('rb_keyframesOnly',
                   label='Sample keyframes only',
                   enable=False)
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 132), (2, 40), (3, 30)],
                 height=20)
    pm.text(label='Animation frame range:')

    pm.intField("i_programStartFrame",
                value=pm.playbackOptions(animationStartTime=True, query=True),
                minValue=-10,
                maxValue=10000,
                step=1)

    pm.intField("i_programEndFrame",
                value=pm.playbackOptions(animationEndTime=True, query=True),
                minValue=-10,
                maxValue=10000,
                step=1)
    pm.setParent('..')

    pm.separator(height=5, style='none')

    # Post processor option menu list
    pm.optionMenu('postProcessorList',
                  label='Processor:',
                  height=18)

    # Get supported post-processors and fill option menu list
    supported_post_processors = postproc_setup.get_processor_names()
    for post in supported_post_processors:
        pm.menuItem(label=post)
    pm.separator(height=3, style='none')

    pm.setParent(parent_layout)
    return general_settings_tab_layout


def _build_options_columns(name, options, parent_layout):
    pm.rowLayout(name, numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 100), (2, 100)],
                 )

    # Split the options into two
    pm.columnLayout('{}_opts_col_0'.format(name),
                    parent=name,
                    adj=True,
                    width=100)
    pm.columnLayout('{}_opts_col_1'.format(name),
                    parent=name,
                    adj=True,
                    width=100)

    num_opts_in_col = len(options) / 2 + len(options) % 2
    for i, opt in enumerate(options):
        pm.checkBox(options[opt]['name'],
                    label=opt,
                    value=options[opt]['value'],
                    enable=options[opt]['enable'],
                    parent='{}_opts_col_{}'.format(name, i / num_opts_in_col))

    pm.setParent(parent_layout)


def _build_proc_options_tab(parent_layout):
    # Create column Layout for General settings
    proc_options_tab_layout = pm.columnLayout('procOptions',
                                              adj=True,
                                              width=100)

    pm.separator(height=3, style='none')

    # Postproc options
    _name = 'name'
    _value = 'value'
    _enable = 'enable'

    # Motion options
    pm.separator(height=3, style='none')
    pm.text('Motion options:', align='left')
    pm.separator(height=3, style='none')
    pm.radioCollection('motion_type_radio_collection')
    pm.rowLayout(numberOfColumns=1,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 3),
                 height=20)
    pm.radioButtonGrp('motion_type_radio_group',
                      labelArray2=['Linear', 'Nonlinear'],
                      annotation='Motion type for robot commands',
                      numberOfRadioButtons=2,
                      columnWidth2=[100, 100],
                      select=1 if postproc_config.OPTS_USE_LINEAR_MOTION else 2,
                      enable1=False,
                      enable2=True)  # 1-based integer
    pm.setParent('..')
    proc_motion_options = OrderedDict([
        ('Ignore motion', {_name: 'cb_ignoreMotion',
                           _value: postproc_config.OPTS_IGNORE_MOTION_COMMANDS,
                           _enable: False}),
        ('Use as variables', {_name: 'cb_useMotionAsVariables',
                              _value: postproc_config.OPTS_USE_MOTION_AS_VARIABLES,
                              _enable: False}),
    ])
    _build_options_columns('motion_opts',
                           proc_motion_options,
                           proc_options_tab_layout)

    # IO Options
    pm.separator(height=3, style='none')
    pm.text('IO options:', align='left')
    pm.separator(height=3, style='none')
    proc_io_options = OrderedDict([
        ('Ignore IOs', {_name: 'cb_ignoreIOs',
                        _value: postproc_config.OPTS_IGNORE_IO_COMMANDS,
                        _enable: False}),
        ('Set IOs first', {_name: 'cb_processIOCommandsFirst',
                           _value: postproc_config.OPTS_PROCESS_IOS_FIRST,
                           _enable: False}),
    ])
    _build_options_columns('io_opts',
                           proc_io_options,
                           proc_options_tab_layout)

    # Include options
    proc_include_options = OrderedDict([
        ('Axes', {_name: 'cb_includeAxes',
                  _value: postproc_config.OPTS_INCLUDE_AXES,
                  _enable: False}),
        ('Pose', {_name: 'cb_includePose',
                  _value: postproc_config.OPTS_INCLUDE_POSE,
                  _enable: False}),
        ('External axes', {_name: 'cb_includeExternalAxes',
                           _value: postproc_config.OPTS_INCLUDE_EXTERNAL_AXES,
                           _enable: False}),
        ('Configuration', {_name: 'cb_includeConfiguration',
                           _value: postproc_config.OPTS_INCLUDE_CONFIGURATION,
                           _enable: False}),
        ('Digital output', {_name: 'cb_includeDigitalOutput',
                            _value: postproc_config.OPTS_INCLUDE_DIGITAL_OUTPUT,
                            _enable: False}),
        ('Checksum', {_name: 'cb_includeChecksum',
                      _value: postproc_config.OPTS_INCLUDE_CHECKSUM,
                      _enable: True}),
    ])

    pm.separator(height=3, style='none')
    pm.text('Include in output:', align='left')
    pm.separator(height=3, style='none')
    _build_options_columns('include_opts',
                           proc_include_options,
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
    pm.checkBox('cb_overwriteFile', label="Overwrite existing file", value=postproc_config.OPTS_OVERWRITE_EXISTING_FILE)
    pm.checkBox('cb_ignoreWarnings', label="Ignore warnings", value=postproc_config.OPTS_IGNORE_WARNINGS)
    pm.separator(height=3, style='none')

    pm.separator(height=3, style='none')
    pm.button('Check Program', command=mimic_utils.check_program, height=25)
    pm.button('Save Program', command=mimic_utils.save_program, height=25)
    pm.separator(height=3, style='none')

    pm.setParent(parent_layout)


# def _build_output_frame(parent_layout):
#
#     program_output_frame = pm.frameLayout(label="Output",
#                                           height=195,
#                                           collapsable=True)
#     program_output_scroll_field = pm.scrollField('programOutputScrollField')
#
#
#     pm.setParent(parent_layout)


def build_program_tab(parent_layout):
    # Create preferences tab Layout
    program_tab_layout = pm.columnLayout(adj=True, height=525, width=200)

    _build_program_settings_frame(program_tab_layout)
    # _build_output_frame(program_tab_layout)

    pm.setParent(parent_layout)

    return program_tab_layout


# SETUP TAB 
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

    pm.optionMenu('robotImportList')

    rigs = general_utils.get_rigs_dict()
    rig_names = general_utils.get_rigs_names(rigs)
    for rig_name in rig_names:
        pm.menuItem(label=rig_name)

    # Get required rigs directories
    dir_mimic = general_utils.get_mimic_dir()
    dir_rigs = dir_mimic + '/rigs'
    add_robot_command_string = \
        'import mimic_utils; reload(mimic_utils); ' \
        'mimic_utils.import_robot("{}"); ' \
        'mimic_utils.add_mimic_script_node(); ' \
        'mimic_utils.add_hud_script_node()' \
            .format(dir_rigs)

    pm.button(label=' Add ',
              command=add_robot_command_string,
              width=45,
              height=20)

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
              command=mimic_utils.attach_tool_controller)
    pm.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_controller)
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
              command=mimic_utils.attach_tool_model)
    pm.button(label='Detach',
              width=58,
              height=20,
              command=mimic_utils.detach_tool_model)
    pm.setParent('..')

    pm.separator(height=8, style='none')
    pm.setParent(parent_layout)


def _build_position_limits_tab(parent_layout):
    position_limits_tab = pm.rowColumnLayout(numberOfColumns=2)

    # Input text field width for all axis limits
    cell_width = 37

    # Set up primary axis limits UI
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        pm.text(label='A{}:'.format(i + 1))

        # Axis 1 Min limit
        pm.textField("t_A{}Min".format(i + 1),
                     font=FONT,
                     pht='Min',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}Max"); ' \
                                   'mimic_utils.set_axis_limit({},"Min")' \
                     .format(i + 1, i + 1))
        # Axis 1 Max limit
        set_focus_count = ((i + 1) % 6) + 1
        pm.textField("t_A{}Max".format(i + 1),
                     font=FONT,
                     pht='Max',
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}Min"); ' \
                                   'mimic_utils.set_axis_limit({},"Max")' \
                     .format(set_focus_count, i + 1))

        pm.setParent('..')

    pm.setParent(position_limits_tab)

    # Set up external axis limits UI
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    for i in range(6):
        # External Axis 1 Limit row
        pm.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        pm.text(label='E{}:'.format(i + 1),
                enable=False)

        # External Axis 1 Min limit
        pm.textField("t_E{}Min".format(i + 1),
                     font=FONT,
                     pht='Min',
                     enable=False,
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'pm.setFocus("t_E{}Max"); ' \
                     .format(i + 1, i + 1))
        # Extarnal Axis 1 Max limit
        set_focus_count = ((i + 1) % 6) + 1
        pm.textField("t_E{}Max".format(i + 1),
                     font=FONT,
                     pht='Max',
                     enable=False,
                     width=cell_width,
                     changeCommand='import pymel.core as pm; ' \
                                   'pm.setFocus("t_E{}Min"); ' \
                     .format(set_focus_count, i + 1))

        pm.setParent('..')

    pm.setParent(parent_layout)

    return position_limits_tab


def _build_velocity_limits_tab(parent_layout):
    velocity_limits_tab = pm.rowColumnLayout(numberOfColumns=2)

    # Set up primary axis velocity limts tab
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Input text field width for all axis limits
    cell_width = 37

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, 2 * cell_width)],
                     height=20)
        pm.text(label='A{}:'.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}vel".format(i + 1),
                     font=FONT,
                     pht='deg/sec',
                     width=2 * cell_width,
                     enable=False,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_A{}vel"); ' \
                     .format(set_focus_count))
        pm.setParent('..')

    pm.setParent(velocity_limits_tab)

    # Set up external axis velocity limits tab
    pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    for i in range(6):
        # External Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, 2 * cell_width)],
                     height=20)
        pm.text(label='E{}:'.format(i + 1), enable=False)

        set_focus_count = ((i + 1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}vel".format(i + 1),
                     font=FONT,
                     pht='',
                     width=2 * cell_width,
                     enable=False,
                     changeCommand='import pymel.core as pm; ' \
                                   'import mimic_utils; ' \
                                   'pm.setFocus("t_E{}vel"); ' \
                     .format(set_focus_count))
        pm.setParent('..')

    pm.setParent(parent_layout)

    return velocity_limits_tab


def _build_axis_limits_frame(parent_layout):
    limits_frame = pm.frameLayout(label="Axis Limits", collapsable=True)
    limits_tab_layout = pm.tabLayout()

    position_limits_tab = _build_position_limits_tab(limits_tab_layout)
    velocity_limits_tab = _build_velocity_limits_tab(limits_frame)

    tabs = [(position_limits_tab, 'Postition'),
            (velocity_limits_tab, 'Velocity')]

    assign_tabs(tabs, limits_tab_layout)

    pm.columnLayout()
    pm.gridLayout(nc=2, cw=114, ch=25)
    pm.button(label='Get Axis Limits', command=mimic_utils.get_axis_limits)
    pm.button(label='Set Axis Limits', command=mimic_utils.set_axis_limits)

    pm.setParent('..')
    pm.button(label='Clear', width=228, command=mimic_utils.clear_limits_ui)

    pm.setParent(parent_layout)


def build_setup_tab(parent_layout):
    # Create setup tab Layout
    setup_tab_layout = pm.columnLayout(adj=True, height=525, width=200)

    # Add robot frame
    _build_add_robot_frame(setup_tab_layout)

    # Add tool setup frame
    _build_tool_setup_frame(setup_tab_layout)

    # Axis Limits frame
    _build_axis_limits_frame(parent_layout)

    pm.setParent(parent_layout)

    return setup_tab_layout


# EXTERNAL AXES TAB
def _build_add_external_axis_frame(parent_layout):
    add_external_axis_frame = pm.frameLayout(label="Add External Axis",
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
    pm.text(label='Description: ')
    pm.textField('t_externalAxisDescriptionText',
                 text='',
                 font=FONT)

    pm.setParent('..')
    pm.separator(height=3, style='none')

    driving_attributes = ['translateX', 'translateY', 'translateZ',
                          'rotateX', 'rotateY', 'rotateZ']

    pm.optionMenu('drivingAttributeMenu', label='Driving Attribute:', height=18)

    for attr in driving_attributes:
        pm.menuItem(label=attr)

    pm.separator(height=3, style='none')

    pm.rowLayout(numberOfColumns=3,
                 adjustableColumn=3,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 110), (2, 50), (3, 50)],
                 height=20)
    pm.text(label='Axis Position Limits:')

    pm.textField('t_externalAxisLimitMin',
                 pht='Min')

    pm.textField('t_externalAxisLimitMax',
                 pht='Max')

    pm.setParent('..')

    pm.rowLayout(numberOfColumns=2,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', -1),
                 columnWidth=[(1, 110)],
                 height=20)
    pm.text(label='Axis Velocity Limit:')

    pm.textField('t_externalAxisVelocityLimit',
                 pht='Max Velocity')

    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1)
    pm.checkBox('cb_lockOtherAttrs', label="Lock Other Axis Attributes", value=1)
    pm.setParent('..')
    pm.separator(height=4, style='none')

    pm.setParent(add_external_axis_col)

    pm.button('Add Axis', height=25)
    pm.separator(height=5, style='none')

    pm.setParent(parent_layout)


def _build_external_axis_tools_frame(parent_layout):
    external_axis_tools_frame = pm.frameLayout(label="External Axis Tools",
                                               collapsable=True)
    external_axis_tools_column = pm.columnLayout(adj=True,
                                                 columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    pm.button('Parent Robot to Axis Controller')
    pm.separator(height=3, style='none')

    pm.button('Remove External Axis from Robot')
    pm.separator(height=3, style='none')

    pm.button('Active | Inactive')

    pm.separator(height=5, style='none')
    pm.setParent(parent_layout)


def _build_axis_info_frame(parent_layout):
    # Axis Info
    program_output_frame = pm.frameLayout(label="Axis Info",
                                          height=195,
                                          collapsable=True)
    output_scroll_field = pm.scrollField('externalAxisInfotScrollField')

    pm.button(label='List Robot\'s External Axes', height=25)
    pm.setParent(parent_layout)


def build_external_axes_tab(parent_layout):
    # Create preferences tab Layout
    external_axis_tab_layout = pm.columnLayout(adj=True, height=525, width=200)

    # Add External Axis Frame
    _build_add_external_axis_frame(external_axis_tab_layout)

    # External axis tools frame
    _build_external_axis_tools_frame(external_axis_tab_layout)

    # Axis info frame
    _build_axis_info_frame(external_axis_tab_layout)

    pm.setParent(parent_layout)
    return external_axis_tab_layout


# PREFS TAB
def _build_hotkeys_frame(parent_layout):
    hotkeys_frame = pm.frameLayout(label="Hotkeys", collapsable=True)
    hotkeys_column = pm.columnLayout(adj=True, columnAttach=('both', 5))
    pm.separator(height=5, style='none')

    # Toggle IK/FK mode Hotkey
    toggle_mode_cmd_name = 'mimic_toggleIkFkMode'
    toggle_mode_annotation_str = 'Toggles Mimic Robot plugin IK/FK mode'
    toggle_mode_command_str = 'import mimic_utils; ' \
                              'mimic_utils.toggle_ik_fk_ui()'

    pm.rowLayout(numberOfColumns=4,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 72), (3, 45), (4, 50)],
                 height=20)

    # Find hotkey assignment, if one exists, to populate the ui
    toggle_mode_hotkey_name = toggle_mode_cmd_name + 'Hotkey'
    toggle_mode_key = mimic_utils.find_hotkey(toggle_mode_hotkey_name)
    if not toggle_mode_key:
        toggle_mode_key = ' key'

    pm.text(label='Toggle IK/FK:')
    pm.textField("t_toggleIkFk", font=FONT, pht=toggle_mode_key)

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

    pm.setParent('..')
    pm.separator(height=3, style='none')

    # Keyframe IK/FK Hotkey
    key_ik_fk_cmd_name = 'mimic_keyIkFk'
    key_ik_fk_annotation_str = 'Keys Mimic robot IK/FK attributes'
    key_ik_fk_command_str = 'import mimic_utils; ' \
                            'mimic_utils.key_ik_fk()'

    pm.rowLayout(numberOfColumns=4,
                 adjustableColumn=2,
                 columnAttach=(1, 'left', 0),
                 columnWidth=[(1, 72), (3, 45), (4, 50)],
                 height=20)

    # Find hotkey assignment, if one exists, to populate the ui
    key_IkFk_hotkey_name = key_ik_fk_cmd_name + 'Hotkey'
    key_IkFk_key = mimic_utils.find_hotkey(key_IkFk_hotkey_name)
    if not key_IkFk_key:
        key_IkFk_key = ' key'

    pm.text(label='Key IK/FK:')
    pm.textField("t_keyIkFk", font=FONT, pht=key_IkFk_key)

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

    pm.setParent(hotkeys_column)
    pm.separator(height=8, style='none')
    pm.setParent(parent_layout)


def _build_ui_prefs_frame(parent_layout):
    pm.frameLayout(label="UI", collapsable=True)
    pm.columnLayout(adj=True, columnAttach=('both', 5))

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
                  value=20,
                  changeCommand=mimic_utils.set_shader_range)

    # Set axis limit shader range button
    pm.button(label=' Set ',
              width=50,
              height=20,
              command=mimic_utils.set_shader_range)
    pm.setParent(parent_layout)


def build_prefs_tab(parent_layout):
    # Create preferences tab Layout
    prefs_tab_layout = pm.columnLayout('prefs_tab_layout', height=525, adj=True, width=200)

    # Hotkeys frame
    _build_hotkeys_frame(prefs_tab_layout)

    # UI frame
    _build_ui_prefs_frame(prefs_tab_layout)

    pm.setParent(parent_layout)

    return prefs_tab_layout
