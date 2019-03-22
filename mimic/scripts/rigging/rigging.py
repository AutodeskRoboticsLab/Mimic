#!usr/bin/env python
"""
Rigging tool for Mimic.
"""
try:
    import pymel.core as pm
    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False
import os
import rigging_utils

reload(rigging_utils)


FONT = 'smallObliqueLabelFont'


def rigging_ui():
    """
    :param: string:
    :return:
    """
    # If the window already exists, delete the window
    if pm.window("rigging_win", exists=True):
        pm.deleteUI("rigging_win", window=True)

    window_width = 105
    window_height = 450

    # Initialize window and Layout
    rigging_win = pm.window("rigging_win",
                            width=window_width,
                            height=window_height,
                            title='Mimic Rigging')

    pm.formLayout()
    pm.columnLayout(width=105,
                    adj=True)


    pm.separator(height=3, style='none')
    pm.rowLayout(numberOfColumns=1,
                 columnAttach=(1, 'left', 3),
                 height=20,)

    pm.text(l="Robot Model:")
    pm.setParent('..')

    pm.rowLayout(numberOfColumns=1,
                 columnAttach=(1, 'left', 22),
                 height=20,)
    pm.textField('t_robotModel',
                 pht='e.g. KR60-3',
                 width = 77,
                 font=FONT)
    pm.setParent('..')
    pm.separator(height=8, style='none')

    pm.text('Geometry')
    pm.separator(height=5, style='none')

                      
    cell_width = 76

    solver_type = rigging_utils.get_solver_type()

    if solver_type == 1:
        geom_fields = rigging_utils.__HK_GEOM_FIELDS
    else:
        geom_fields = rigging_utils.__SW_GEOM_FIELDS           

    for field in geom_fields:
        pm.rowLayout('row_{}'.format(field),
                     numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width)],
                     height=20,)

        pm.text(l="{}:".format(field))
        pm.textField('t_{}'.format(field),
                     pht='mm',
                     width=cell_width,
                     font=FONT)
        pm.setParent('..')


    pm.separator(height=8, style='none')
    pm.text('Limits')
    pm.separator(height=3, style='none')

    cell_width = 37

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=3,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width), (3, cell_width)],
                     height=20)
        pm.text(label='A{}:'.format(i+1))

        # Axis 1 Min limit
        pm.textField("t_A{}Min".format(i+1),
                     font=FONT,
                     pht='Min',
                     width=cell_width)
        # Axis 1 Max limit
        set_focus_count = ((i+1) % 6) + 1
        pm.textField("t_A{}Max".format(i+1),
                     font=FONT,
                     pht='Max',
                     width=cell_width)
        
        pm.setParent('..')

    pm.separator(height=5, style='none')

    cell_width = 38

    for i in range(6):
        # Axis 1 Limit row
        pm.rowLayout(numberOfColumns=2,
                     columnAttach=(1, 'left', 3),
                     columnWidth=[(2, cell_width)],
                     height=20)
        pm.text(label='A{}:'.format(i+1))

        set_focus_count = ((i+1) % 6) + 1
        # Axis 1 Min limit
        pm.textField("t_A{}vel".format(i+1),
                     font=FONT,
                     pht='deg/sec',
                     width=2*cell_width)
        pm.setParent('..')

    pm.separator(height=5, style='none')

    pm.button('Zero Pivots', c=rigging_utils.zero_axis_pivots)
    pm.button('Print Pivots', c=rigging_utils.print_axis_pivots)
    pm.button('Rig', c=rigging_utils.rig)
    # Launch UI window
    pm.window('rigging_win',
              height=window_height,
              width=window_width,
              edit=True)

    rigging_win.show()


def run():
    """
    Instantiates the Mimic Rigging UI
    :return:
    """

    # Generate UI itself
    rigging_ui()
