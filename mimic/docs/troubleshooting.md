# Mimic | Troubleshooting

In case of problems, see the below. If all else fails, copy the error you
receive and send a detailed description to us at [mimic@autodesk.com](mailto:mimic@autodesk.com).


### Having trouble installing  Mimic?

- Download the latest release and copy the contents of it to one of the following
  directories, depending on your operating system. When you're done, open Maya,
  click on the Mimic shelf tab, and click on the Mimic icon.

    ```
    macOS   ~/Library/Preferences/Autodesk/maya/modules
    Windows ~/Documents/maya/modules
    ```

- If the `modules` directory above does not exist, create it.

- If you're on a Mac and dont see the path listed above, it's likely that
  your user Library folder is hidden (there are multiple Library folders on Macs).
  The correct Library folder is the user Library folder in Mac HD > Users > User Name, 
  not the one that’s on the main HD
 
  So, to make the user Library folder appear, follow these [instructions](http://osxdaily.com/2013/10/28/show-user-library-folder-os-x-mavericks/)
 
  That will give you the correct folder structure that matches mine in the [tutorial video](https://youtu.be/bc3SqEXcE5Q?t=73).

- If you're using Maya 2017 update 3 or earlier, you must
  [manually load the Mimic shelf](https://youtu.be/bc3SqEXcE5Q?t=1m46s).
  
- If you're running Windows and downloaded a release and/or rigs archive,
  confirm that it isn't "blocked" before unzipping and installing it (right click
  the archive, select Properties, check Unblock if necessary).
  
- If you cloned this repository, download the latest robot rigs from
  [releases](https://github.com/AutodeskRoboticsLab/Mimic/releases). Once you do,
  replace the directory *mimic/rigs* with the one you downloaded after unzipping it.
  
- Confirm that the plugin has loaded properly, in Maya, check
  *Windows > Settings > Plug-in Manager* for the `REQUIRED_PLUGINS` listed in
  *mimic.py*:

    ```
    required_plugins = [
        'robotIK',
        'robotLimitBlender',
        'snapTransforms'
        # ...
        ]
    ```
    
- Confirm that the version of Mimic in *mimic.mod* and *mimic_config.py* coincide
  such as in the following.

    ```
    + mimic 1.3.0 ../modules/mimic
    ``` 
    
    ```
    MIMIC_VERSION_MAJOR = 1
    MIMIC_VERSION_MINOR = 3
    MIMIC_VERSION_PATCH = 0 
    ```


### General tips

- Try closing and reopening Mimic and/or Autodesk Maya after new install.

- If you get an error, launch the Maya Script Editor to track it down. Follow the
  instructions provided [here](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-7C861047-C7E0-4780-ACB5-752CD22AB02E-htm.html).
  If you still have trouble, contact us using info provided above.
  
- Some elements in the Mimic UI will give you details about what they do.
  Hover your cursor over an element to view these details. *At time of writing,
  this kind of documentation is not yet implemented for all UI elements.*

- If you're using Maya 2016, and it continually crashes when you  analyze or 
  save a program , try  changing Maya's evaluation mode from *Parallel* to *DG* by going to: 
  `Windows > Settings/Preferencs > Preferences` > 
  `Settings > Animation` > 
  `Evaluation > Evaluation Mode > DG`

#
