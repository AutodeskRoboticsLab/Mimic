

![mimic_logo](mimic/logos/mimic_logo_web.gif)

#

### What is Mimic?

*An open-source Autodesk Maya plugin for controlling Industrial Robots.*

[Mimic](https://www.mimicformaya.com/) is a free and open-source plugin for [Autodesk Maya](https://www.autodesk.com/products/maya/overview) that enables simulation, programming, and control of 6-axis, Industrial Robots. Use Mimic to generate programs without writing any code, or extend Mimic to suit your project's needs. Written in Python 2.7.


### Installation

Download the latest [release](https://github.com/AutodeskRoboticsLab/Mimic/releases) and copy the contents of it to one of the following directories, depending on your operating system:
```
macOS   ~/Library/Preferences/Autodesk/maya/modules
Windows ~/Documents/maya/modules
```
_note: the only difference between the MAC and PC versions is the NumPy build that's included_

-We only include a small set of rigs with the main download to save download size. If you need a rig that is otherwise supported, download the manufacturer-specific rigs, grab the rig you need, and drop it into the appropriate[rigs](mimic/rigs) folder in your mimic directory

When you're done, open Maya, click on the Mimic shelf tab, and click on the Mimic icon; that's it!

**Installation tips:**

- If the `modules` directory above does not exist, create it.
- If you're using Maya 2017 update 3 or earlier, you must [manually load the Mimic shelf](https://youtu.be/bc3SqEXcE5Q?t=1m46s).
- If you're running Windows and downloaded a release and/or rigs archive,  confirm that it isn't "blocked" before unzipping and installing it (right click the archive, select Properties, check Unblock if necessary).
- If you cloned this repository, download the latest robot rigs from  [releases](https://github.com/AutodeskRoboticsLab/Mimic/releases). 
Replace the directory `mimic/rigs`  with the unzipped `rigs` folder.
- See [troubleshooting](mimic/docs/troubleshooting.md) if you have trouble  using or installing Mimic.

You can find tutorials, videos, and other media on our [website](https://www.mimicformaya.com/) and textual documentation in [docs](mimic/docs).


### Currently supported robots

*Let us know if what you need isn't listed and we'll try to help!*
(contact info provided below)

Mimic currently supports the following robots for animation (see [rigs](mimic/rigs)):

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
|-- Kawasaki
    |-- RS020N
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
    |-- KR 12 R1800
    |-- KR 12 R1800-2
    |-- KR 16 L6-2
    |-- KR 16 R1610
    |-- KR 16 R2010
    |-- KR 16-arc HW
    |-- KR 20 R1810
    |-- KR 20 R1810-2
    |-- KR 22 R1610
    |-- KR 30-3
    |-- KR 60-3
    |-- KR 120 R2500 Pro
    |-- KR 120 R2700 HA
    |-- KR 150 R3100 Prime
    |-- KR 150-2
    |-- KR 200 L140-2
    |-- KR 210 R3100
    |-- KR 210-2
    |-- KR 240 L180-2
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

\* *post processor not yet supported*

Mimic currently supports the following post processors
(see [postproc](mimic/scripts/postproc)):

```
|-- ABB
    |-- RAPID
|-- KUKA
    |-- EntertainTech *
    |-- KRL
|-- Staubli
    |-- VAL3
|-- Genral
    |-- CSV
```

\* *external installation option required*


### Join the community!

Help us out and contribute to this repository!
You may submit an issue or open a pull request for any bugs or improvements to
this software. See [CONTRIBUTING](mimic/docs/CONTRIBUTING.md) for programming guidelines.

Join the our [slack channel](https://www.mimicformaya.com/#community-section)!
You may also contact us at [mimic@autodesk.com](mailto:mimic@autodesk.com).

*Mimic was born at the Autodesk Robotics Lab 2018.* It is now developed
and contributed to by a community of animators, designers, engineers, architects,
programmers, and more.
See [AUTHORS](mimic/docs/AUTHORS.md) for details.


### License

Mimic is licensed under the MIT license.
See [LICENSE](mimic/docs/LICENSE.md) for details.


### Notes

- Be careful out there! Mimic is not a safety certified monitoring tool.
  Users of this software are responsible for safe robot programming and operation.
- Developed to work with Autodesk Maya 2016-2020; is not compatible with versions prior to Maya 2016 due to changes in Maya's Python API
- Developed to work with macOS and Windows; Maya is not compatible with other
  operating systems but *most* of the Mimic backend is.
- Do not modify names or hierarchies within robot rigs!
- Use Maya's default units: Centimeters, Degrees
- Use Maya's default coordinate system where the Y-axis points *up*.
- Note this repository does not include robot rigs; download the latest release
  to access the latest rigs.


#
