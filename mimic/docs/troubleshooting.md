# Mimic

### Troubleshooting

In case of problems, see the below. If all else fails, copy the error you
receive and send a detailed description to us at [mimic@autodesk.com](mailto:mimic@autodesk.com).

- Try closing and reopening Mimic and/or Autodesk Maya.
  
- If you're running Windows and downloaded a release in the form of a zipped
  directory, confirm that the files contained therein are not "blocked". To do
  so, right click a file, select Properties, and look for such a tag. If it
  exists, download the zipped release again and, before unzipping it, unblock it.

- Confirm that the plugin has loaded properly, in Maya, check
  *Windows > Settings > Plug-in Manager* for the `REQUIRED_PLUGINS` listed in
  *mimic_config.py*:

    ```
    REQUIRED_PLUGINS = [
        'robotAccumRot',
        'robotIK',
        'robotLimitRot',
        'snapTransforms'
        # ...
        ]
    ```
    
- If you cloned the Mimic repository, you probably won't have robot rigs. In the
  directory *mimic/rigs* you must add directories corresponding with robot-type and,
  in them, named robot rigs with the extension `.ma`. See *mimic/rigs/rigs.md* or
  more information or download the latest robot rigs from
  [releases](https://github.com/AutodeskRoboticsLab/Mimic/releases).

- Confirm that the version of Mimic in *mimic.mod* and *mimic_config.py* coincide
  such as in the following.

    ```
    + mimic 1.0 ../modules/mimic
    ``` 
    
    ```
    MIMIC_VERSION_MAJOR = 1
    MIMIC_VERSION_MINOR = 0
    ```
    
- If you get an error, launch the Maya Script Editor to track it down. Follow the
  instructions provided [here](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-7C861047-C7E0-4780-ACB5-752CD22AB02E-htm.html).
  If you still have trouble, contact us using info provided above.


#
