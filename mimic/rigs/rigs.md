# Mimic

### Currently supported robots

```
|-- ABB
    |-- IRB 120-3-58
    |-- IRB 140-6-81
    |-- IRB 1100-4-58
    |-- IRB 1200-5-90
    |-- IRB 1200-7-70
    |-- IRB 1600-6-145
    |-- IRB 1600-10-145
    |-- IRB 2600-20-165
    |-- IRB 4400-45-196
    |-- IRB 4400-60-196
    |-- IRB 4600-20-250
    |-- IRB 4600-40-255
    |-- IRB 6640-180-255
    |-- IRB 6640-235-255
    |-- IRB 6700-150-320
    |-- IRB 6700-205-280
    |-- IRB 6700-245-300
    |-- IRB 8700-475-420
    |-- IRBT 4004-9000
|-- Kawasaki
    |-- RS010N-A
    |-- RS010N-B
    |-- RS020N
|-- KUKA
    |-- KL 100 6125
    |-- KL 1500-3 6000
    |-- KL 4000 5000
    |-- KR 3
    |-- KR 3 AGILUS
    |-- KR 5 R1400
    |-- KR 5-arc
    |-- KR 6 R700 sixx AGILUS
    |-- KR 6 R900 sixx AGILUS
    |-- KR 10 R900 sixx AGILUS
    |-- KR 10 R1100 sixx AGILUS
    |-- KR 10 R1100-2
    |-- KR 10 R1420
    |-- KR 12 R1800
    |-- KR 12 R1800-2
    |-- KR 16-2
    |-- KR 16 L6-2
    |-- KR 16 R1610
    |-- KR 16 R2010
    |-- KR 16 R2010-2
    |-- KR 16-arc HW
    |-- KR 20 R1810
    |-- KR 20 R1810-2
    |-- KR 20 R3100
    |-- KR 22 R1610
    |-- KR 30-3
    |-- KR 30 R2100
    |-- KR 50 R2100
    |-- KR 60-3
    |-- KR 60 L30-3
    |-- KR 70 R2100
    |-- KR 120 R2500 Pro
    |-- KR 120 R2700 HA
    |-- KR 120 R2700 press C
    |-- KR 150 R3100 Prime
    |-- KR 150
    |-- KR 150-2
    |-- KR 150 L110-2
    |-- KR 150 R3100 Prime
    |-- KR 180 R2900 Prime
    |-- KR 200 L140-2
    |-- KR 210-2
    |-- KR 210-2 K
    |-- KR 210 R2700 Prime
    |-- KR 210 R3100
    |-- KR 210 R3300 Ultra K-F
    |-- KR 240-2
    |-- KR 240 L180-2
    |-- KR 240 R2900 Ultra
    |-- KR 240 R2900 Ultra C
    |-- KR 250 R2700-2
    |-- KR 300 R2500 Ultra
    |-- KR 300 R2700-2
    |-- KR 300 R2700-2 C
    |-- KR 360-3
    |-- KR 500-2
    |-- KR 500-2 RC
    |-- KR 500 L340-3
    |-- KR 600 R2830
    |-- KR 1000 TITAN
|-- Motoman *
    |-- GP20HL
    |-- MH6
    |-- MH20 II-20
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
