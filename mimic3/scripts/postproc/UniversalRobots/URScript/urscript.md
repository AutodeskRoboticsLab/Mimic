# Mimic

### SimpleURScriptProcessor

The SimpleURScriptProcessor is a Post Processor for Mimic designed to program Universal Robots
robots using the URScript programming language and SCRIPT output file extension. No
installation options are required for use of this package. This processor IS NOT
time-based.

```
Name: SimpleURScriptProcessor
Robot type: Universal Robots
Processor language: URScript
Output file extension: SCRIPT
Required installation options: None
Time-based: False
```


### Contents

This package contains the following directories and/or files:

```
|-- URScript
    |-- __init__.py
    |-- urscript.md
    |-- urscript.py
    |-- urscript_config.py
    |-- template.script
```


### Warning!

- This Post Processor serves a method of programming robots that IS NOT
  fundamentally time-based. Robot motion seen in Maya may and likely will differ
  from robot motion seen in the real world. 
- DO NOT modify or mutate the value of parameters that are either `__private`,
  `_protected`, or located in `urscript.py` unless you intend to extend the core
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
```


### Configuration

This package comes with functional default parameters and configuration
parameters that must be modified to suit user and application requirements.
User parameters can be found in the following files:

```
urscript_config.py
template.script
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
{}
```


#
