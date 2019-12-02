#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates the mFIZ UI.
"""

try:
    import pymel.core as pm
    from maya.api import OpenMaya

    MAYA_IS_RUNNING = True
except ImportError:  # Maya is not running
    pm = None
    MAYA_IS_RUNNING = False

# General imports 
import re
from collections import namedtuple

# mFIZ Imports
import mFIZ_utils
import mFIZ_config
import serial_utils

reload(mFIZ_utils)
reload(mFIZ_config)
reload(serial_utils)


ADD_CONTROLLER_TEXTFIELD_NAME = 'add_controller_textField'
MOTOR_API_OPTIONMENU_EXT = '_motor_api_optionMenu'
DEVICE_NAME_OPTION_MENU_EXT = '_device_name_optionMenu'
KEYABLE_ATTR_FILTER_NAME = 'keyable_attr_filter'

FIZ_ATTRS = mFIZ_config.FIZ_ATTRS
CONNECTION_INDICATOR_COLORS = mFIZ_config.CONNECTION_INDICATOR_COLORS
CONNECTION_ICON_NAMES = ['connect_icon.png',
                         'disconnect_icon.png']

CONTROLS_TAB_DATA = namedtuple('tab_data', ['controller', \
                                            'connection_indicator_field',
                                            'connection_icon',
                                            'motor_api_optionMenu',
                                            'device_name_optionMenu'])

def run():
    """
    Check that mFIZ is all there, loaded, and then create the mFIZ UI.
    :return:
    """
    # Perform preliminary checks
    mFIZ_utils.load_mFIZ_plugins()

    # Get any controllers that're already in the scene
    mFIZ_controllers = mFIZ_utils.get_all_controllers()
    
    # Build the UI itself
    mFIZ_win = mFIZWin(mFIZ_controllers)

    return mFIZ_win


class mFIZWin(object):
    """
    """
    def __init__(self, controllers):
        """
        """  
        __WINDOW_NAME = 'mFIZ_win'
        __WINDOW_TITLE = 'mFIZ'  # Replace this with .mod version number
        
        __SCRIPTED_PANEL_NAME = 'mFIZ_graphEditor'
        
        # Set default window parameters
        __WINDOW_HEIGHT = 335
        __WINDOW_WIDTH = 1000
        __CONTROL_PANE_WIDTH = 25  # Percent of total window width
        __SHOW_OUTLINER = False  # Not yet implemented

        # __DOCKABLE_AREAS = ['bottom', 'top']
        # __FLOATING = True

        self.__LOGO_NAME = 'mFIZ_logo.png'
                
        self.name = __WINDOW_NAME
        self.version = mFIZ_utils.get_mFIZ_version()
        self.title = '{} {}'.format(__WINDOW_TITLE, self.version)

        self.graph_editor = __SCRIPTED_PANEL_NAME

        # Initialize instance attributes for clarity

        ## UI Controls
        # These are assigned as the UI is built
        self.win = None  # pymel.core.uitypes.Window
        self.main_layout = None  # pymel.core.uitypes.PaneLayout
        self.controls_tab_layout = None  # pymel.core.uitypes.TabLayout
        self.connection_button_icon = None  # pymel.core.uitypes.SymbolButton
        self.outliner_selection_connection = None  # selectionConnection that controls the mFIZ Graph Editor panel Outliner
        self.stop_playback_checkBox = None  # pymel.core.uitypes.CheckBox

        ## Callback ID's
        # These are used to control the connection state of the mFIZ UI tabs
        # and the tab selections
        self.selection_changed_callback_id = None  # Callback ID for active_selection_changed Callback
        self.time_change_scriptJob_id = None  # scriptJob ID for timeChanged scriptJob
        self.attribute_changed_callback_ids = []  # Callback ID for attributeChanged Callback

        ## mFIZ controller data
        self.controllers = controllers  # List of tuples: [(ctrl, node)] == [(Locator Transform), (mFIZ Plugin Node)]
        self.controls_tab_data = {}  # Nested Dict:
                                     # {tabName: {tab_data: namedtuple(),
                                     #            connected: bool}}

        ## Build UI 
        # Delete existing UI elements
        self._delete_existing_uis()

        # Create the main window, with the main paneLayout
        # assigns self.win and self.main_layout
        self._create_mFIZ_window(__CONTROL_PANE_WIDTH)
                
        # Build the control pane (leftmost pane of the UI)
        self._build_control_pane(parent_layout=self.main_layout)

        # Build the graphEditor pane (rightmost pane of the UI)
        self._build_graph_editor_pane(parent_layout=self.main_layout)

        # Add a callback to check when the active selection changes and
        # set the ui control tab accordingly
        self._add_selection_changed_callback()
        
        # Add scriptJob to check connection state and update UI if neceesary
        self._add_time_changed_script_job()

        # Initialize each controller's tab connection state
        self.set_ui_connection_state()

        '''
        # Show the UI Window
        pm.dockControl(__WINDOW_TITLE,
                       area=__DOCKABLE_AREAS[0],
                       floating=__FLOATING,
                       width=__WINDOW_WIDTH,
                       height=__WINDOW_HEIGHT,
                       content=self.win,
                       allowedArea=__DOCKABLE_AREAS)
        '''
        pm.window(self.win, edit=True, width=__WINDOW_WIDTH, height=__WINDOW_HEIGHT)
        pm.showWindow(self.win)

        # Initialize the selectionConnection by calling the _tab_changed function
        self._tab_changed()

    def _delete_existing_uis(self):
        """
        """
        # Delete main window, if it exists
        if pm.window(self.name, exists=True):
            pm.deleteUI(self.name, window=True)

        '''
        # Delete Dock Control, if it exists
        # Remove special characters from title
        dock_name = self.title
        special_chars = [' ', '.']
        for char in special_chars:
            dock_name = dock_name.replace(char, '_')

        if pm.dockControl(dock_name, exists=True):
            pm.deleteUI(dock_name, control=True)    
        '''

        # Delete Scripted Panel (graphEditor), if it exists
        if pm.scriptedPanel(self.graph_editor, exists=True):
            pm.deleteUI(self.graph_editor, panel=True)

        # Delete keyable attribute filter from the outlinerEditor
        if pm.objExists(KEYABLE_ATTR_FILTER_NAME):
            pm.delete(KEYABLE_ATTR_FILTER_NAME)

    def _create_mFIZ_window(self, controls_width):
        """
        """
        self.win = pm.window(self.name, title=self.title)
        

        self.main_layout = pm.paneLayout('mFIZ_paneLayout',
                                configuration="vertical2",
                                staticWidthPane=1,
                                paneSize=[1, controls_width, 100])
    
    # ---------------- #
    #   Control Pane   #
    # ---------------- #
    def _build_control_pane(self, parent_layout):
        """
        """
        # Create a frameLayout with a nested columnLayout to hold all of our 
        # control pane elements
        control_pane_frameLayout = pm.frameLayout('control_pane_frameLayout', labelVisible=False)
        control_pane_columnLayout = pm.columnLayout('control_pane_columnLayout', adj=True)

        # Add the header image
        self._add_header_image(parent_layout=control_pane_columnLayout)
        
        # Add the control tabs
        self._add_control_tabs(parent_layout=control_pane_frameLayout)

        # Add text output field
        self._add_output_field(parent_layout=control_pane_frameLayout)

        pm.setParent(parent_layout)

    def _add_header_image(self, parent_layout):
        """
        """
        # Creat rowLayout to hold out header image. This is done to get the proper
        #logo alignment and response to window size adjustments
        pm.rowLayout(height=50,
                     backgroundColor=[0.2, 0.2, 0.2],
                     numberOfColumns=2,
                     adjustableColumn=1,
                     columnAlign=(2, 'right'),
                     columnAttach=[(2, 'right', 5)],
                     rowAttach=[(2, 'top', 15)] )
        pm.text('')
        pm.image(image=self.__LOGO_NAME)
        
        pm.setParent(parent_layout)

    def _add_control_tabs(self, parent_layout):
        """
        """
        # Creat a tabLayout for our contorl tabs
        controls_tab_layout = self._create_control_tabs()

        tabs = []

        controllers = self.controllers

        if controllers:
            for controller in controllers:
                ctrl = controller.ctrl
                # Strip "_CTRL" from transform name for tab name
                tab_name = str(ctrl).replace('_CTRL', '')

                # Build the contents of each tab
                program_tab = self._build_program_tab(controller, tab_name, parent_layout=controls_tab_layout)
                tabs.append((program_tab, tab_name))

        setup_tab = self._build_setup_tab(parent_layout=controls_tab_layout)
        tabs.append((setup_tab, "Setup"))
        
        # Assign the tabs to the tabLayout
        self._assign_tabs(tabs, controls_tab_layout)
        self.controls_tab_layout = controls_tab_layout

        pm.setParent(parent_layout)

    def _create_control_tabs(self):
        """
        """
        control_tabs_formLayout = pm.formLayout()
        controls_tab_layout = pm.tabLayout(changeCommand=self._tab_changed)
        pm.formLayout(control_tabs_formLayout,
                      edit=True,
                      attachForm=[(controls_tab_layout, "top", 5),
                                  (controls_tab_layout, "bottom", 0),
                                  (controls_tab_layout, "left", 0),
                                  (controls_tab_layout, "right", 0)])

        return controls_tab_layout

    def _add_output_field(self, parent_layout):
        """
        """
        output_field_formLayout = pm.formLayout()
        output_field_scrollField = pm.scrollField('output_field_scrollField', height=5)
        pm.formLayout(output_field_formLayout,
                            edit=True,
                            attachForm=[(output_field_scrollField, "top", 0),
                                        (output_field_scrollField, "bottom", 5),
                                        (output_field_scrollField, "left", 3),
                                        (output_field_scrollField, "right", 3)])
        
        pm.setParent(parent_layout)

    # Program Tabs #
    def _build_program_tab(self, controller, tab_name, parent_layout, parent=None):
        """
        """
        # TO-DO: Break this into smaller utility functions
        # Strip "_CTRL" from transform name for tab name

        ctrl = controller.ctrl
        ctrl_name = str(ctrl)

        if not parent:
            program_tab_columnLayout = pm.columnLayout(tab_name, adj=True)
        else:
            program_tab_columnLayout = pm.columnLayout(tab_name, adj=True, parent=parent)

        ## CONNECT FRAME ##
        # Define dynamic names based on ctrl input
        motor_api_optionMenu_name = '{}{}'.format(ctrl_name, MOTOR_API_OPTIONMENU_EXT)
        device_name_optionMenu_name = '{}{}'.format(ctrl_name, DEVICE_NAME_OPTION_MENU_EXT)

        connect_frameLayout = pm.frameLayout(label='Connect')
        pm.columnLayout(adj=True)
        pm.separator(height=5, style='none')

        TEXT_COL_WIDTH = 63

        # API Selector Row
        pm.rowLayout(numberOfColumns=2,
                     # columnAttach=[1, 'left', 3],
                     columnWidth=[1, TEXT_COL_WIDTH],
                     adjustableColumn2=2)
        pm.text('Motor API:')
        motor_api_optionMenu = pm.optionMenu(motor_api_optionMenu_name)
        
        # Get supported Motor APIs from the config and assign them to the option menu
        supported_apis = mFIZ_config.SUPPORTED_MOTOR_APIS
        for api in supported_apis:
            pm.menuItem(api)
        pm.setParent('..')


        # Device Name Selector Row
        devices = serial_utils.get_device_names()

        pm.rowLayout(numberOfColumns=5,
                     columnAttach=[2, 'right', 3],
                     columnWidth=[1, TEXT_COL_WIDTH],
                     adjustableColumn=2)
        pm.text('Serial Port:')
        device_name_optionMenu = pm.optionMenu(device_name_optionMenu_name)

        for device in devices:
            pm.menuItem(device, label=device)

        pm.symbolButton(image='refresh_icon.png',
                        width=20,
                        height=20,
                        command=self._refresh_port_optionMenus)
        connection_icon = pm.symbolButton(image=CONNECTION_ICON_NAMES[0],
                                          width=20,
                                          height=20,
                                          command=pm.Callback(self.connect, tab_name))
        
        connection_indicator_field = pm.textField('connection_indicator_field',
                                                   editable=False,
                                                   height=20,
                                                   width=10,
                                                   backgroundColor=CONNECTION_INDICATOR_COLORS[0])        
        
        pm.setParent('..')
        pm.separator(height=5, style='none')


        pm.setParent(program_tab_columnLayout)
        pm.separator(height=5, style='none')

        ## CONTROL FRAME ##
        # Define dynamic names based on ctrl input
        control_frameLayout = pm.frameLayout(label='Control')
        pm.columnLayout(adj=True)
        pm.separator(height=5, style='none')

        BUTTON_COL_WIDTH = 21
        FIZ_CONTROL_COL_HEIGHT = 70

        # Creat a row layout that will hold two columns
        # First column will have the main FIZ controls and the second column
        # Will hold the "Keyfram All" command
        fiz_controls_rowLayout = pm.rowLayout(
                     numberOfColumns=2,
                     columnAttach=[2, 'left', -5],
                     rowAttach=[2, 'top', 0],
                     adjustableColumn=1)

        fiz_controls_columnLayout_1 = pm.columnLayout(adj=True)

        attrs = ['focus', 'iris', 'zoom']

        for attr in attrs:
            # Create row layout for attribute slider group and "set keyfram" button
            attr_abbrev = attr[0].capitalize()

            pm.rowLayout(numberOfColumns=2,
                         #columnAttach=[2, 'right', 3],
                         columnWidth=[2, BUTTON_COL_WIDTH],
                         adjustableColumn=1)
            pm.attrFieldSliderGrp(tab_name + '_attrFieldSliderGrp_' + attr_abbrev,
                                  l=attr_abbrev,
                                  min=0,
                                  max=1,
                                  columnAlign=[1, 'center'],
                                  columnWidth3=[15, 50, 0],
                                  adjustableColumn=3,
                                  attribute='{}.{}'.format(ctrl, attr))
            pm.symbolButton(image='set_keyframe_icon.png',
                            command=pm.Callback(self._set_keyframe, [attr]))
            pm.setParent('..')

        pm.setParent(fiz_controls_rowLayout)

        # Key All button
        fiz_controls_columnLayout_2 = pm.columnLayout( 
                                            adj=True,
                                            width=BUTTON_COL_WIDTH,
                                            columnAlign='left')

        pm.symbolButton(image='keyframe_all_icon.png',
                        width=BUTTON_COL_WIDTH,
                        height=FIZ_CONTROL_COL_HEIGHT,
                        command=self._set_keyframe)

        pm.setParent(parent_layout)


        # Add an OpenMaya.MMessage attributeChanged callback to handle UI stat
        # if a device becomes connected/disconnected
        node_name = str(controller.node)
        self._add_attribute_changed_callback(node_name)

        ## Save the tab data to the self.controls_tab_data dict
        tab_data = CONTROLS_TAB_DATA(controller,
                                     connection_indicator_field,
                                     connection_icon,
                                     motor_api_optionMenu,
                                     device_name_optionMenu)

        self.controls_tab_data[tab_name] = {'tab_data': tab_data, 'connected': False}

        return program_tab_columnLayout

    # Setup Tab #
    def _build_setup_tab(self, parent_layout):
        """
        """
        layout = pm.columnLayout(adj=True)

        TEXT_COL_WIDTH = 40
        pm.separator(height=5, style='none')

        pm.rowLayout(numberOfColumns=2,
                     columnAttach=[1, 'left', 3],
                     columnWidth=[1, TEXT_COL_WIDTH],
                     adjustableColumn2=2)
        pm.text('Name:')
        pm.textField(ADD_CONTROLLER_TEXTFIELD_NAME, text='mFIZ')
        pm.setParent('..')

        # Create checkbox to set the stop playback on disconnect stat
        pm.columnLayout(adjustableColumn=True, columnAttach=['left', 43])
        self.stop_playback_checkBox = pm.checkBox(label='Stop Playback on Disconnect',
                                                  value=mFIZ_config.DEFAULT_STOP_PLAYBACK_ON_DISCONNECT)
        pm.setParent('..')

        pm.separator(height=5, style='none')

        pm.button('add_controller_button',
                  label='Add mFIZ Controller',
                  command=self._add_mFIZ_controller_to_scene)

        pm.setParent(parent_layout)  

        return layout  

    # --------------------- #
    #   Graph Editor Pane   #
    # --------------------- #
    def _build_graph_editor_pane(self, parent_layout):
        """
        """
        garph_editor_formLayout = pm.formLayout()
         
        pm.scriptedPanel(self.graph_editor, type='graphEditor')
        
        # Initialize custom selectionConnection for only FIZ nodes
        outliner_selectionConnection = pm.selectionConnection()


        # Create a custom outlineEditor and assign our mainListConnection
        # This way, the mFIZ outliner will only show mFIZ nodes
        oulineEditor_name = self.graph_editor + 'OutlineEd'
        pm.outlinerEditor(oulineEditor_name,  # scriptedPanel name + 'OutlineEd' found with pm.lsUI(editors=True)
                          edit=True,
                          mainListConnection=outliner_selectionConnection)
        
        pm.formLayout(garph_editor_formLayout,
                      edit=True,
                      attachForm=[(self.graph_editor, "top", 3),
                                  (self.graph_editor, "bottom", 3),
                                  (self.graph_editor, "left", 3),
                                  (self.graph_editor, "right", 3)])

        pm.setParent(parent_layout)

        # Set a 'keyable' filter on the outlineEditor to only show keyable attributes
        keyable_attr_filter = pm.itemFilterAttr(KEYABLE_ATTR_FILTER_NAME, keyable=True)
        pm.outlinerEditor(oulineEditor_name, edit=True, attrFilter=keyable_attr_filter)

        # Create a selectionConnection
        # sel_con = pm.selectionConnection(activeList=True, mainListConnection=

        # Store the selectionConnections to an instance attribute
        self.outliner_selection_connection = outliner_selectionConnection

    # --------------------- #
    #   Utility Functions   #
    # --------------------- #
    def _assign_tabs(self, tabs, tab_layout):
        """
        """
        for tab in tabs:
            pm.tabLayout(tab_layout,
                     edit=True,
                     tabLabel=[(tab[0], tab[1])])

    def _get_tab_ctrl(self, tab_name=None):
        """
        Gets the Transform of the mFIZ locator assigned to the tab
        If no tab tab_name is passed, returns controller of the active tab
        Returns None if the active tab is the 'Setup' tab
        """
        # Get controller associated with tab. We do this so as not to assume the
        # tab name is the same as the controller object (locator transform)

        tab_layout = self.controls_tab_layout
        tab_labels = pm.tabLayout(tab_layout, query=True, tabLabel=True)

        # If no tab is passed, get the name of the currently selected tab
        if not tab_name:
            tab_name = pm.tabLayout(tab_layout, query=True, selectTab=True)

        try:
            tab_ctrl = self.controls_tab_data[tab_name]['tab_data'].controller.ctrl 
        except KeyError:  # Setup tab has no tab_data
            tab_ctrl = None

        return tab_ctrl

    def _get_tab_name(self, ctrl=None):
        """
        Gets the name of the tab that the active controller is assigned to
        """
        tab_layout = self.controls_tab_layout
        
        # Get all of the tab labels
        tab_labels = pm.tabLayout(tab_layout, query=True, tabLabel=True)
        if 'Setup' in tab_labels:
            tab_labels.remove('Setup')  # Remove the setup tab

        if not ctrl:
            # We can get the name of the selected tab directly
            tab_name = pm.tabLayout(tab_layout, query=True, selectTab=True)
        else:
            # Get the controller for each tab
            for tab_name in tab_labels:
                tab_ctrl = self._get_tab_ctrl(tab_name)

                # If the selected controller matches the i-th tab controller,
                # select the tab
                if ctrl == tab_ctrl:
                    break 

        return tab_name

    def _add_mFIZ_controller_to_scene(self, *args):
        """
        """
        # Get the user input name and filter out special characters
        name = get_textField_input(ADD_CONTROLLER_TEXTFIELD_NAME, filter=True)

        ## Create a new tab in the mFIZ UI for the new controller
        controller = mFIZ_utils.add_mFIZ_controller_to_scene(name)

        # Set the state of the Stop Playback on Disconnect attribute on the node
        # based on user input in the Setup Tab
        stop_on_disconnect = pm.checkBox(self.stop_playback_checkBox,
                                         query=True,
                                         value=True)
        controller.node.setAttr('stopPlaybackOnDisconnect',
                                 stop_on_disconnect,
                                 lock=True)

        ## Assign the controller to the controls tabLayout
        tab_layout = self.controls_tab_layout

        ctrl = controller.ctrl
        ctrl_name = str(ctrl)
        tab_name = ctrl_name.replace('_CTRL', '')

        tab = self._build_program_tab(controller, tab_name, tab_layout, tab_layout)
        self._assign_tabs([(tab, tab_name)], tab_layout)

        ## Move the "Setup" tab to the end
        tab_labels = pm.tabLayout(tab_layout, query=True, tabLabel=True)
        num_tabs = len(tab_labels)
        setup_tab_index = tab_labels.index('Setup') + 1  # Tabs are 1-based indeces

        pm.tabLayout(tab_layout, edit=True, moveTab=[setup_tab_index, num_tabs])

    def _set_keyframe(self, attrs=None):
        """
        """
        ctrl = self._get_tab_ctrl()
        ctrl_name = str(ctrl)

        if not attrs:
            attrs = FIZ_ATTRS

        for attr in attrs:

            # Check to see if an animCurve already exists for the attribute
            # If not, mark it for setting its color afterwards
            attr_curve_name = '{}_{}'.format(ctrl_name, attr)  # animCurves are created with the naming convention {tranformName}_{attribute}
            new_curve = mFIZ_utils.anim_curve_exists(attr_curve_name)

            pm.setKeyframe(ctrl_name, attribute=attr)

            # If this was the first keyframe set on the attribute, assign
            # the new curve its default color
            if new_curve:
                mFIZ_utils.set_curve_color(attr_curve_name, attr)        

    def _refresh_port_optionMenus(self, *args):
        """
        """
        # Get the list of available devices
        devices = serial_utils.get_device_names()

        if not devices:
            pm.warning('mFIZ: No devices connected')

        for tab_name in self.controls_tab_data:
            device_name_optionMenu = self.controls_tab_data[tab_name]['tab_data'].device_name_optionMenu

            # Clear the existing menu list
            device_name_items = pm.optionMenu(device_name_optionMenu, query=True, itemListLong=True)
            

            if device_name_items:
                pm.deleteUI(device_name_items)

            # Add the new devices to optionMenu
            if devices:
                for device in devices:
                    pm.menuItem(device, label=device, parent=device_name_optionMenu)

    def _tab_changed(self, *args):
        """
        """
        ctrl = self._get_tab_ctrl()
        ctrl_name = str(ctrl)

        # Update the selectionConnection by removing previous selection(s), 
        # then adding the selected tab's controller
        pm.selectionConnection(self.outliner_selection_connection,
                               edit=True,
                               clear=True)
   
        if ctrl:
            pm.selectionConnection(self.outliner_selection_connection,
                                   edit=True,
                                   select=ctrl_name)

            pm.select(ctrl_name)

    def _get_connection_inputs(self, tab_name):
        """
        """
        # Get the optionMenu objects for the input tab
        motor_api_optionMenu = self.controls_tab_data[tab_name]['tab_data'].motor_api_optionMenu
        device_name_optionMenu = self.controls_tab_data[tab_name]['tab_data'].device_name_optionMenu

        # Query each tab for the user data
        api = pm.optionMenu(motor_api_optionMenu, query=True, value=True)
        device_name = pm.optionMenu(device_name_optionMenu, query=True, value=True)

        # Create a namedtuple to store the data
        connection_inputs = namedtuple('connection_inputs', ['api', 'device_name'])

        return connection_inputs(api, device_name)

    # --- Callbacks ---------------------------- #
    def _add_selection_changed_callback(self):
        """
        """
        callback_id = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.active_selection_changed)

        self.selection_changed_callback_id = callback_id

    def _add_attribute_changed_callback(self, node_name):
        """
        Adds an AttributeChangedCallback to the input node to trigger UI state
        changes when an attribute value on the node is changed interactively

        This uses the OpenMaya 2.0 Python instead of PyMel
        :param node_name: str; string representation of the Node
        """
        # Using the OpenMaya 2.0 Pyhton
        sel = OpenMaya.MSelectionList()
        sel.add(node_name)
        obj = sel.getDependNode(0)

        callback_id = OpenMaya.MNodeMessage.addAttributeChangedCallback(obj, self.mFIZ_node_attribute_changed)

        # Add the callback ID to the running list for deletion control later
        self.attribute_changed_callback_ids.append(callback_id)

    def _add_time_changed_script_job(self):
        """
        Adds a timeChanged scriptJob to the scene trigget UI state changes when
        node is computed during playback or timeline scrubbing
        """

        self.time_change_scriptJob_id = pm.scriptJob(timeChange=self.set_ui_connection_state,
                                                     killWithScene=True)
    
    def _delete_attribute_changed_callbacks(self):
        """
        """
        callback_ids = self.attribute_changed_callback_ids

        for callback_id in callback_ids:
            try:
                OpenMaya.MMessage.removeCallback(callback_id)
                self.attribute_changed_callback_ids = []
            except:
                pass
    # ------------------------------------------ #

    def select_tab(self, tab_ctrl):
        """
        """
        tab_layout = self.controls_tab_layout
        
        # Get all of the tab labels
        tab_labels = pm.tabLayout(tab_layout, query=True, tabLabel=True)
        tab_labels.remove('Setup')  # Remove the setup tab

        # Get the controller for each tab
        for tab_name in tab_labels:
            tab_ctrl_i = self._get_tab_ctrl(tab_name)

            # If the selected controller matches the i-th tab controller,
            # select the tab
            if tab_ctrl == tab_ctrl_i:
                pm.tabLayout(tab_layout, edit=True, selectTab=tab_name)

    def active_selection_changed(self, *args):
        """
        """
        # Check if the window assigned to the callback still exists
        # If not, delete the callback and exit
        if not pm.window(self.win, exists=True):
            OpenMaya.MMessage.removeCallback(self.selection_changed_callback_id)
            return

        # Get the current active selection
        active_sel = pm.ls(sl=True, type='transform')

        # Get a list of the mFIZ controllers
        # Controller = (ctrl, node)
        all_controllers = mFIZ_utils.get_all_controllers()
        # Get only a list the ctrls
        all_ctrls = [controller[0] for controller in all_controllers]
        
        selected_ctrls = []
        for each in active_sel:
            if each in all_ctrls:
                selected_ctrls.append(each)

        # We can only have one UI tab selected, so we prioritize the most recently
        # selected controller
        if selected_ctrls:
            selected_ctrl = selected_ctrls[-1]

            try:
                self.select_tab(selected_ctrl)
            except:
                pass

    def mFIZ_node_attribute_changed(self, msg, plug, otherplug, *clientData):
        """
        """
        
        # Check if the tabLayout attached to the object exists,
        # If not, delete the callbacks as they're unnecessary
        if not pm.layout(self.controls_tab_layout, exists=True):
            # Delete all node Attribute Changed callback IDs
            # pm.evalDeferred(pm.Callback(self._delete_attribute_changed_callbacks))
            return
        
        # Only run if the message is from an Attribute on the mFIZ ndoe being evaluated
        if msg & OpenMaya.MNodeMessage.kAttributeEval:
    
            # Get the name of the attribute being evaluate
            attribute_name = str(plug.partialName())
        
            # Only run if the attribute being evaluated is the 'dataSent' attribute
            if attribute_name == 'dataSent':
                self.set_ui_connection_state()

    def set_ui_connection_state(self, tab_names=[], connected=None):
        """
        """
        
        tab_layout = self.controls_tab_layout

        # Check if the window attached to the object exists,
        # If not, delete the callbacks as they're unnecessary
        if not pm.layout(tab_layout, exists=True):
            # If the scriptJob still exists, delete the scriptJob   
            if self.time_change_scriptJob_id:
                pm.evalDeferred('import pymel.core as pm; pm.scriptJob(kill={})'.format(self.time_change_scriptJob_id))
            return

        # If no tab is passed, set the state of every tab
        # Check the connected state by querrying the tab's associated node state
        # This combonation should always be passed together, otherwise, a single
        # tab_name and single connceted state should be passed
        if not tab_names:
            tab_names = pm.tabLayout(tab_layout, query=True, tabLabel=True)
            if 'Setup' in tab_names:
                tab_names.remove('Setup')  # Remove the setup tab

        for tab_name in tab_names:
            tab = self.controls_tab_data[tab_name]

            # If no connection state is passed, check the dataSent attribute on the 
            # associated mFIZ node
            if connected is None:
                node = self.controls_tab_data[tab_name]['tab_data'].controller.node

                # Get attribute value using OpenMaya and not getAttr() as the latter
                # causes recursion problems with the callback in some Maya versions
                sel = OpenMaya.MSelectionList()
                sel.add(str(node))
                obj = sel.getDependNode(0)

                node_state = OpenMaya.MFnDependencyNode(obj).findPlug('dataSent', True).asBool()

            else:
                node_state = connected

            # Get the current state of the tab
            tab_state = tab['connected']

            # If the tab and note state are different, update the tab state
            if tab_state != node_state:
                # Set the connection state in the tab data dict
                tab['connected'] = node_state

                # Set the color of the connection indicator field
                connection_indicator_field = tab['tab_data'].connection_indicator_field
                pm.textField(connection_indicator_field, edit=True, backgroundColor=CONNECTION_INDICATOR_COLORS[node_state])

                # Set the connect/disconnect icon
                connection_icon = tab['tab_data'].connection_icon
                pm.symbolButton(connection_icon,
                                edit=True,
                                image=CONNECTION_ICON_NAMES[node_state])

                # If the node is disconnected, refresh the list of devices to remove
                # disconnected devices
                if not node_state:
                    self._refresh_port_optionMenus()

    def connect(self, tab_name):
        """
        """
        controller = self.controls_tab_data[tab_name]['tab_data'].controller
        node = controller.node

        # Invert the current connection state of the tab
        # i.e. if tab (and therefore the device) is connected, this function should
        #      disconnect the device, and vice versa
        connect = not self.controls_tab_data[tab_name]['connected']

        ## Connect to device
        if connect:
            user_inputs = self._get_connection_inputs(tab_name)

            device_name = user_inputs.device_name

            if not device_name:
                device_name = 'none'

            port_name = serial_utils.format_port_name(device_name)
            api = user_inputs.api

            # Set the port name and api attributes on the mFIZ node

            node.setAttr('portName', port_name)
            node.setAttr('api', api)

        ## Disconnect device
        else:
            # Remove the port name and api from the node attributes
            # Note: might end up leaving these and have the UI set to the last-used options
            node.setAttr('portName', '')
            node.setAttr('api', '')            

        # Set the 'live' attribute of the mFIZ node to establish connection
        node.setAttr('live', connect)

# General utility functions
def get_textField_input(field_name, filter=False):
    """
    """
    text = pm.textField(field_name, query=True, text=True)

    if filter:
        text = _filter_text_input(text)

    return text


def _filter_text_input(text):
    """
    """
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Remove special characters
    text = ''.join(re.findall(r"[_a-zA-Z0-9]+", text))

    return text
