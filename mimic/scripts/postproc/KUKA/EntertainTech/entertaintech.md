# Mimic

### SimpleEntertainTechProcessor

The SimpleEntertainTechProcessor is a Post Processor for Mimic designed to program KUKA
robots using the EntertainTech programming language and EMILY output file extension. The
KUKA.EntertainTech installation option is required for use of this package. This processor
IS time-based.

```
Name: SimpleEntertainTechProcessor
Robot type: KUKA
Processor language: EntertainTech
Output file extension: EMILY
Required installation options: KUKA.EntertainTech
Time-based: True
```


### Contents

This package contains the following directories and/or files:

```
|-- EntertainTech
    |-- __init__.py
    |-- entertaintech.md
    |-- entertaintech.py
    |-- entertaintech_config.py
    |-- template.emily
```


### Warning!

- In Mimic, set `Sample rate` to  `0.012` and `s` for this Post Processor!
  The KUKA.EntertainTech installation option requires that your commands
  adhere to the MGMO cycle time; see KUKA.EntertainTech documentation!
  *This package will not work correctly if you choose other parameters!*
- DO NOT modify or mutate the value of parameters that are either `__private`,
  `_protected`, or located in `rapid.py` unless you intend to extend the core
  functionality of this package.
- It is highly recommended that you test your robot-control code in a safety
  certified simulator and implement such monitoring in your workcell prior to
  running it.


### Mimic options

At time of writing, this Post Processor uses following User Options in Mimic:

```
|-- Motion options
    |-- Nonlinear
|-- Include in outut
    |-- Axes
    |-- Checksum
```


### Configuration

This package comes with functional default parameters and configuration
parameters that must be modified to suit user and application requirements.
User parameters can be found in the following files:

```
entertaintech_config.py
template.emily
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
[HEADER]
  GEAR_NOMINAL_VEL = 1.000000
[RECORDS]
{}
[END]
```


#
