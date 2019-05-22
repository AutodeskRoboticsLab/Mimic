# Mimic

### Currently supported robots

```
|-- ABB
    |-- IRB 120-3-58
    |-- IRB 1600-6-145
    |-- IRB 1600-10-145
    |-- IRB 2600-20-165
    |-- IRB 4400-45-196
    |-- IRB 4400-60-196
    |-- IRB 4600-40-255
    |-- IRB 6640-180-255
    |-- IRB 6640-235-255
    |-- IRB 6700-150-320
    |-- IRB 6700-205-280
    |-- IRB 6700-245-300
    |-- IRBT 4004-9000
|-- KUKA
    |-- KL 100 6125
    |-- KL 1500-3 6000
    |-- KL 4000 5000
    |-- KR 3
    |-- KR 3 AGILUS
    |-- KR 5 R1400
    |-- KR 5-arc
    |-- KR 6 R900 sixx AGILUS
    |-- KR 10 R900 sixx AGILUS
    |-- KR 10 R1100 sixx AGILUS
    |-- KR 10 R1420
    |-- KR 16 L6-2
    |-- KR 16 R2010
    |-- KR 16-arc HW
    |-- KR 22 R1610
    |-- KR 60-3
    |-- KR 120 R2700 HA
    |-- KR 150 R3100 Prime
    |-- KR 150-2
    |-- KR 200 L140-2
    |-- KR 210 R3100
    |-- KR 210-2
    |-- KR 240 R2900 Ultra
    |-- KR 240-2
    |-- KR 300 R2500 Ultra
    |-- KR 500-2
    |-- KR 500-2 RC
    |-- KR 600 R2830
    |-- KR 1000 TITAN
|-- Motoman *
    |-- MH6
|-- Staubli *
    |-- RX160
    |-- RX160L
    |-- TX40
    |-- TX60
    |-- TX60L
    |-- TX90
    |-- TX90L
|-- Universal Robots *
    |-- UR3
    |-- UR3e
    |-- UR5
    |-- UR5e
    |-- UR10
    |-- UR10e
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

- You can *ignore* a rigs directory if it is preceded by an underscore, `_`, such
  as for rig templates. For example, the subdirectories `_ABB` or `_templates`
  would not appear in the Mimic UI. Note that directories preceded by a `.` are
  also ignored, but this convention is typically reserved for system and hidden
  files only.

- To change the color of a robot, use the Hypershade to change the color of 
  “J#LowerBase_MAT” and “J#UpperBase_MAT” (these should match)

- To change the limit shader color (the color the robot turns when you’re near a limit),
  change “J#LowerLimit_MAT” and/or “J#UpperLimit_MAT” (you can set upper and lower limits
  to different colors)

### Credits

- All ABB robots credited to [ABB](http://new.abb.com/products/robotics).
- All KUKA robots credited to [KUKA](https://www.kuka.com/en-us).
- All Staubli robots credited to [Staubli](https://www.staubli.com/en-us/robotics/).
- All Universal Robots robots credited to [Staubli](https://www.universal-robots.com/).
- Exceptions to the above credits (`Robot name, attribution or source`):
    ```
    none, none
    ```

#
