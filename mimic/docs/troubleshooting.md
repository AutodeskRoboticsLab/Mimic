# Mimic

### Troubleshooting

In case of problems, see the below. If all else fails, copy the error you
receive and send a detailed description to us at [mimic@autodesk.com](mailto:mimic@autodesk.com).

- If you're running Windows and downloaded a release in the form of a zipped
  directory, confirm that the files contained therein are not "blocked". To do
  so, right click a file, select Properties, and look for such a tag. If it
  exists, download the zipped release again and, before unzipping it, unblock it.

- Confirm that the Mimic shelf button is executing the following:

```
import mimic
reload(mimic)
mimic.run()
```

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

- Confirm that the following directories exist:
    - *mimic/rigs*
    - *mimic/plug-ins*
    - *mimic/scripts*
    - *mimic/shelves*
    
- Confirm that *mimic/rigs* contains robots with the file path extension `.ma`.

- Confirm that the version of Mimic in *mimic.mod* and *mimic_config.py* coincide:

```
+ mimic 1.0 ../modules/mimic
``` 

```
MIMIC_VERSION_MAJOR = 1
MIMIC_VERSION_MINOR = 0
```

#
