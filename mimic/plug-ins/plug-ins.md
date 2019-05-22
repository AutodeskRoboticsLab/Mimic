# Mimic Plug-ins

Scipts in this folder are Maya
[Depend Graph Plug-ins](https://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__files_GUID_A9070270_9B5D_4511_8012_BC948149884D_htm)
and [Command Plug-ins](https://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__files_GUID_A9FA6DEF_4E48_45A7_AC65_A69E8A55F62D_htm)
and will be loaded in Maya at runtime. They are required for robot rigs to
function correctly, regardless of whether or not the Mimic UI is in use.

The contents of this directory are as follows:

```
|-- plug-ins
    |-- plug-ins.md
    |-- robotIK.py
    |-- robotLimitBlender.py
    |-- snapTransforms.py
```


### Notes

- Changes to these files *require* a restart of Autodesk Maya to work.

- You can confirm that the plugin has loaded properly, in Maya, check
  *Windows > Settings > Plug-in Manager*
  
  
- *robotIK* is a Dependency Graph plug-in and the heart of Mimic's robot rig.
  It performs the Inverse Kinematic solve, along with handling IK-FK switching,
  and more.

- *robotLimitBlender* is a Dependency Graph plug-in that is used in the shader
  network that determines if an axis is near a limit.

- *snapTransforms* is a Command plug-in that allows for the robust snapping of
  one objects transforms to another in world space. It is a modified version of a
  the SnapRuntime Command plug-in developed by Mark Jackson for the
  [Red9 Studio Pack](https://www.highend3d.com/maya/script/red9-studio-pack-for-maya)


#
