#!usr/bin/env python
"""
Rigging tool for Mimic.
"""
try:
    import maya.cmds as cmds
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    cmds = None
    MAYA_IS_RUNNING = False
import os
from rigging import rigging_utils
import importlib

importlib.reload(rigging_utils)


FONT = 'smallObliqueLabelFont'


def rigging_ui():
    """
    :param: string:
    :return:
    """
    # If the window already exists, delete the window
    if cmds.window("rigging_win", exists=True):
        cmds.deleteUI("rigging_win", window=True)

    window_width = 105
    window_height = 450

    # Initialize window and Layout
    rigging_win = cmds.window("rigging_win",
                            width=window_width,
                            height=window_height,
                            title='Mimic Rigging')

    cmds.formLayout()
    cmds.columnLayout(width=105,
                    adj=True)


    cmds.separator(height=3, style='none')
    cmds.rowLayout(numberOfColumns=1,
                 columnAttach=(1, 'left', 3),
                 height=20,)

    cmds.text(l="Robot Model:")
    cmds.setParent('..')

    cmds.rowLayout(numberOfColumns=1,
                 columnAttach=(1, 'left', 22),
                 height=20,)
    cmds.textField('t_robotModel',
                 pht='e.g. KR60-3',
                 width = 77,
                 font=FONT)
    cmds.setParent('..')
    cmds.separator(height=8, style='none')

    cmds.text('Geometry')
    cmds.separator(height=5, style='none')

                      
    cell_width = 76

    solver_type = rigging_utils.get_solver_type()

    if solver_type == 1:
        geom_fields = rigging_utils.__HK_GEOM_FIELDS
    else:
        geom_fields = rigging_utils.__SW_GEOM_FIELDS           

    for field in geom_fields:
        cmds.rowLayout('row_{}'.format(field),
                     numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width)],
                     height=20,)

        cmds.text(l="{}:".format(field))
        cmds.textField('t_{}'.format(field),
                     pht='mm',
                     width=cell_width,
                     font=FONT)
        cmds.setParent('..')


    cmds.separator(height=8, style='none')
    cmds.text('Limits')
    cmds.separator(height=3, style='none')

    cell_width = 37

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        cmds.text(label='A{}:'.format(i+1))

        # Axis 1 Min limit
        cmds.textField("t_A{}Min".format(i+1),
                     font=FONT,
                     pht='Min',
                     width=cell_width)
        # Axis 1 Max limit
        set_focus_count = ((i+1) % 6) + 1
        cmds.textField("t_A{}Max".format(i+1),
                     font=FONT,
                     pht='Max',
                     width=cell_width)
        
        cmds.setParent('..')

    cmds.separator(height=5, style='none')

    cell_width = 38

    for i in range(6):
        # Axis 1 Limit row
        cmds.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width)],
                     height=20)
        cmds.text(label='A{}:'.format(i+1))

        set_focus_count = ((i+1) % 6) + 1
        # Axis 1 Min limit
        cmds.textField("t_A{}vel".format(i+1),
                     font=FONT,
                     pht='deg/sec',
                     width=2*cell_width)
        cmds.setParent('..')

    cmds.separator(height=5, style='none')

    cmds.button('Zero Pivots', c=rigging_utils.zero_axis_pivots)
    cmds.button('Print Pivots', c=rigging_utils.print_axis_pivots)
    cmds.button('Rig', c=rigging_utils.rig)
    # Launch UI window
    cmds.window('rigging_win',
              height=window_height,
              width=window_width,
              edit=True)

    cmds.showWindow(rigging_win)


def run():
    """
    Instantiates the Mimic Rigging UI
    :return:
    """

    # Generate UI itself
    rigging_ui()
