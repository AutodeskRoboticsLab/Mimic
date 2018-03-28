# Mimic

### Currently supported robots

*Let us know if what you need isn't listed and we'll try to help!*

Mimic currently supports the following robots:

```
ABB
|-- IRB-120
|-- IRB-6700-205-280
KUKA
|-- AGILUS-R900
|-- KR5-R1400
|-- KR5-arc
|-- KR60-3
```

*Get robot rigs from the latest
[release](https://github.com/AutodeskRoboticsLab/Mimic/releases) of Mimic!*


### Adding robot rigs to Mimic

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

- Please provide attributions, credits, and/or sources for your rigs! Include
  these in the *Credits* section below.

- The *mimic/rigs* directory may contain any number of robot type directories
  and a robot type directory may contain any number of robot rigs (though users
  should try to maintain this organization).

- Note that the folder structure depends on the parameters `<type of robot>` and
  `<robot name>`, which are used to effectively *name* the rig itself in the form
  `<type of robot> <robot name>`. For example:
  
    ...a robot with the type and name:
    
    ```
    <type of robot> = ABB
    <robot name> = IRB-120
    ```
    
    ...will appears in Mimic in the form:
    
    ```
    ABB IRB-120
    ```

- When accessed in Mimic the rigs are sorted alphabetically. A default rig can
  be configured using *mimic_config.py*. Rig names should be simple and descriptive.


### Credits

- All ABB robots credited to [ABB](http://new.abb.com/products/robotics).
- All KUKA robots credited [KUKA](https://www.kuka.com/en-us).
- Exceptions to the above credits (`Robot name, attribution or source`):
    ```
    none, none
    ```

#
