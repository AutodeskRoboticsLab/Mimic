# Mimic

### Rigs

*Acquire your rigs from the latest release of Mimic.*

If you decide to build your own rigs, add them to this directory using the
following structure:

```
|-- mimic
    |-- rigs
        |-- rigs.md
        |-- <type of robot>
            |-- <robot name>.ma
            |-- ...
        |-- ...
```

### Notes

The *mimic/rigs* directory may contain any number of robot type directories
and a robot type directory may contain any number of robot rigs (though users
should try to maintain this organization).

Note that the folder structure depends on the parameters `<type of robot>` and
`<robot name>`, which are used to effectively *name* the rig itself in the form
`<type of robot> <robot name>` (for example `ABB IRB-120`). When accessed in Mimic,
the rigs are sorted alphabetically. A default rig can be configured using
*mimic_config.py*. Rig names should be simple and descriptive.


#
