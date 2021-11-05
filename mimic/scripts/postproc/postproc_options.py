#!usr/bin/env python
"""
Post-processor User Options. This module contains tools for interfacing both the
postproc package and the Mimic UI and provides the UserOptions tuple, which must
be integrated by all processor subclasses.
"""

import sys
import mimic_config
reload(mimic_config)

sys.dont_write_bytecode = True

try:
    import pymel.core as pm

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

from collections import namedtuple
from collections import OrderedDict
import postproc_setup


# USER OPTIONS
USER_OPTIONS = 'USER_OPTIONS'
_fields = [
    'Ignore_motion',
    'Use_motion_as_variables',
    'Use_linear_motion',
    'Use_nonlinear_motion',
    'Use_continuous_motion',
    'Include_axes',
    'Include_pose',
    'Include_external_axes',
    'Include_configuration',
    'Ignore_IOs',
    'Process_IOs_first',
    'Include_digital_outputs',
    'Include_digital_inputs',
    'Include_analog_outputs',
    'Include_analog_inputs',
    'Include_checksum',
    'Include_timestamp'
]
UserOptions = namedtuple(
    USER_OPTIONS, _fields
)


def configure_user_options(
        ignore_motion=False,
        use_motion_as_variables=False,
        use_linear_motion=False,
        use_nonlinear_motion=False,
        use_continuous_motion=False,
        include_axes=False,
        include_pose=False,
        include_external_axes=False,
        include_configuration=False,
        ignore_ios=False,
        process_ios_first=False,
        include_digital_outputs=False,
        include_digital_inputs=False,
        include_analog_outputs=False,
        include_analog_inputs=False,
        include_checksum=False,
        include_timestamp=False,
        *args,
        **kwargs):
    """
    Configure user options. Defaults every parameter to False unless specified
    by user! Params args and kwargs capture any variables that may be passed
    from old/bad configs.

    :param ignore_motion: Ignore all motion commands.
    :param use_motion_as_variables: Use motion as variables.
    :param use_linear_motion: Move linearly.
    :param use_nonlinear_motion: Move non-linearly.
    :param use_continuous_motion: Move continuously without stopping.
    :param include_axes: Include axes in command.
    :param include_pose: Include pose in command.
    :param include_external_axes: Include external axes in command.
    :param include_configuration: Include configuration in command.
    :param ignore_ios: Ignore all IO commands.
    :param process_ios_first: Process IOs and append to output before motion.
    :param include_digital_outputs: Include digital outputs in command.
    :param include_digital_inputs: Include digital inputs in command.
    :param include_analog_outputs: Include analog outputs in command.
    :param include_analog_inputs: Include analog inputs in command.
    :param include_checksum: Include a CRC32 checksum in output.
    :param include_timestamp: Include a timestamp in output.
    :param args: Unused - capture any invalid params
    :param kwargs: Unused - capture any invalid params.
    :return:
    """
    return UserOptions(
        Ignore_motion=ignore_motion,
        Use_motion_as_variables=use_motion_as_variables,
        Use_linear_motion=use_linear_motion,
        Use_nonlinear_motion=use_nonlinear_motion,
        Use_continuous_motion=use_continuous_motion,
        Include_axes=include_axes,
        Include_pose=include_pose,
        Include_external_axes=include_external_axes,
        Include_configuration=include_configuration,
        Ignore_IOs=ignore_ios,
        Process_IOs_first=process_ios_first,
        Include_digital_outputs=include_digital_outputs,
        Include_digital_inputs=include_digital_inputs,
        Include_analog_outputs=include_analog_outputs,
        Include_analog_inputs=include_analog_inputs,
        Include_checksum=include_checksum,
        Include_timestamp=include_timestamp
    )


# System parameters
__name = 'name'
__value = 'value'
__enable = 'enable'
__visible = 'visible'
_OPTS_COLUMN_NAME = '{}_opts_col_0'


def format_field_name_for_checkbox(field):
    """
    Format the name of an option-checkbox using the field name of the option
    as it exists in the UserOptions tuple for the purpose of having a unique
    codename in the Mimic backend.
    :param field:
    :return:
    """
    return 'cb_{}'.format(field)


def format_field_name_for_pretty_ui(field):
    """
    Format the name of an option-checkbox using the field name of the option
    as it exists in the UserOptions tuple for the purpose of having readable
    text in the Mimic UI.
    :param field:
    :return:
    """
    return field.replace('_', ' ')


def get_user_selected_options(field_namespace=''):
    """
    Get the user-selected options from the Mimic UI and output a complete
    UserOptions tuple. Queries checkboxes only!
    :return:
    """
    values = []
    # Get user-selected options from UI
    for i in range(len(_fields)):
        field = _fields[i]
        checkbox_name = field_namespace + format_field_name_for_checkbox(field)
        checkbox_value = pm.checkBox(checkbox_name,
                                     value=True,
                                     query=True)
        values.append(checkbox_value)
    # Create a new tuple from the above
    return UserOptions(*values)


def get_processor_supported_options(postproc_list='postProcessorList'):
    """
    Get the user-selected options from the user-selected processor and output
    a complete UserOptions tuple.
    :return:
    """
    processor_type = pm.optionMenu(postproc_list,
                                   query=True,
                                   value=True)
    processor = postproc_setup.POST_PROCESSORS[processor_type]()
    return processor.supported_options


def assert_selected_vs_supported_options(selected_options, supported_options):
    """
    Assert that user-selected options match processor-supported options; raises
    an exception if a user-selected option is found to be unsupported.
    :param selected_options: User-selected options
    :param supported_options: Processor-supported options
    :return:
    """
    count = len(selected_options)
    i = 0
    try:
        for i in range(count):
            assert selected_options[i] == supported_options[i]
    except AssertionError:
        error_option = selected_options._fields[i]
        raise Exception('User-selected option not supported by processor: '
                        + error_option)


def create_options_dict(selected_options, supported_options):
    """
    Create an options Ordered Dictionary using user-selected options and
    processor-supported options. If the processor does not support an option
    that has been selected by the user, the user selection is overridden.
    :param selected_options: User-selected options
    :param supported_options: Processor-supported options
    :return:    """
    # Begin creating the dictionary
    options_dict = OrderedDict()
    for i in range(len(selected_options)):
        field = _fields[i]  # name of the option
        # Set the checkbox parameters for the Mimic UI
        _checkbox_name_pretty = format_field_name_for_pretty_ui(field)
        _checkbox_name = format_field_name_for_checkbox(field)
        _checkbox_value = selected_options[i]
        _checkbox_enable = supported_options[i]
        options_dict[_checkbox_name_pretty] = {
            __name: _checkbox_name,
            __value: _checkbox_value,
            __enable: _checkbox_enable,
            __visible: _checkbox_enable
        }
    return options_dict


def build_options_columns(name, options_dict, parent_tab_layout):
    """
    Build a pair of columns to present UserOptions in the Mimic UI.
    :param name: Name of this column.
    :param options_dict: UserOptions as OrderedDict where the key is a string
    and where the value is a dictionary of checkbox parameters for the UI.
    :param parent_tab_layout: Parent tab layout in which columns will live.
    :return: 
    """
    # Create two options columns
    pm.rowLayout(name,
                 numberOfColumns=1,
                 adjustableColumn=1,
                 columnAttach=(1, 'left', 3),
                 columnWidth=[(1, 200)])
    # Rename the columns
    global _OPTS_COLUMN_NAME
    _OPTS_COLUMN_NAME = _OPTS_COLUMN_NAME.format(name)
    pm.columnLayout(_OPTS_COLUMN_NAME,
                    parent=name,
                    adj=True,
                    width=200)
    for i, option in enumerate(options_dict):
        pm.checkBox(options_dict[option][__name],  # cb_...
                    label=option,  # _checkbox_name_pretty
                    value=options_dict[option][__value],
                    enable=options_dict[option][__enable],
                    visible=options_dict[option][__visible],
                    parent=_OPTS_COLUMN_NAME,
                    changeCommand=pm.CallbackWithArgs(mimic_config.Prefs.update_postproc_options,
                                                      mimic_config.FILE,
                                                      option))
    # Return to parent
    pm.setParent(parent_tab_layout)


def _overwrite_options(post_proc, postproc_list, field_namespace, pref_level, all_visible):
    """
    Update the Postrocessor options UI in the Mimic ui and the Preferences ui windows.

    Get the available Postprocessor options. Display all options as checkboxes,
    and automatically check the user-selected boxes. Save updates as options are
    selected/deselected.

    :param post_proc: bool: value of the option that was selected
    :param postproc_list: str: id of the postproc option list to update
    :param field_namespace: str: namespace of the checkbox fields
    :param pref_level: mimic_config preference level
    :param all_visible: bool: Will update UI to display un-selectable options

    :return:
    """
    mimic_config.Prefs.set('DEFAULT_POST_PROCESSOR', post_proc, pref_level)

    # Get the new parameters from the Mimic UI
    try:
        selected_options = get_user_selected_options(field_namespace)
    except Exception:  # none configured
        selected_options = configure_user_options(
                                mimic_config.Prefs.get_postproc_options(pref_level))
    supported_options = get_processor_supported_options(postproc_list)
    options_dict = create_options_dict(selected_options, supported_options)

    # Fill both columns with User-Options
    for i, option in enumerate(options_dict):

        pm.checkBox(field_namespace + options_dict[option][__name],  # cb_...
                    edit=True,
                    value=options_dict[option][__value],
                    enable=options_dict[option][__enable],
                    visible=True if all_visible else options_dict[option][__visible])


def overwrite_options(post_proc, *args):
    _overwrite_options(post_proc=post_proc,
                       postproc_list='postProcessorList',
                       field_namespace='',
                       pref_level=mimic_config.FILE,
                       all_visible=False)


def update_prefs_ui_postroc_options(post_proc, *args):
    _overwrite_options(post_proc=post_proc,
                       postproc_list='prefs_postProcessorList',
                       field_namespace='prefs_',
                       pref_level=mimic_config.USER,
                       all_visible=True)
