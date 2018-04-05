# Mimic

### Troubleshooting

In case of problems, see the below. If all else fails, copy the error you
receive and send a detailed description to us at [mimic@autodesk.com](mailto:mimic@autodesk.com).


### General tips

- Try closing and reopening Mimic and/or Autodesk Maya.

- If you get an error, launch the Maya Script Editor to track it down. Follow the
  instructions provided [here](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-7C861047-C7E0-4780-ACB5-752CD22AB02E-htm.html).
  If you still have trouble, contact us using info provided above.
  
- Some elements in the Mimic UI will give you details about what they do.
  Hover your cursor over an element to view these details. *At time of writing,
  this kind of documentation is not yet implemented for all UI elements.*


### Having trouble installing  Mimic?

- If the `modules` directory below does not exist, create it. 
    
    ```
    macOS   ~/Library/Preferences/Autodesk/maya/modules
    Windows ~/Documents/maya/modules
    ```

- *If you're using Maya 2017 update 3 or earlier, you must
  [manually load the Mimic shelf](https://youtu.be/bc3SqEXcE5Q?t=1m46s).
  
- If you cloned this repository, download the latest robot rigs from
  [releases](https://github.com/AutodeskRoboticsLab/Mimic/releases). Once you do,
  replace the directory *mimic/rigs* with the one you downloaded after unzipping it.
  If you're using Windows, confirm that the directory is unblocked before you unzip
  it!
  
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
    
- Confirm that the version of Mimic in *mimic.mod* and *mimic_config.py* coincide
  such as in the following.

    ```
    + mimic 1.0 ../modules/mimic
    ``` 
    
    ```
    MIMIC_VERSION_MAJOR = 1
    MIMIC_VERSION_MINOR = 0
    ```


#
