# Mimic

### SimpleKRLProcessor

The SimpleKRLProcessor is a Post Processor for Mimic designed to program KUKA
robots using the KRL programming language and SRC output file extension. No
installation options are required for use of this package. This processor IS NOT
time-based.

```
Name: SimpleKRLProcessor
Robot type: KUKA
Processor language: KRL
Output file extension: SRC
Required installation options: None
Time-based: False
```


### Contents

This package contains the following directories and/or files:

```
|-- KRL
    |-- __init__.py
    |-- krl.md
    |-- krl.py
    |-- krl_config.py
    |-- template.src
```


### Warning!

- This Post Processor serves a method of programming robots that IS NOT
  fundamentally time-based. Robot motion seen in Maya may and likely will differ
  from robot motion seen in the real world. 
- DO NOT modify or mutate the value of parameters that are either `__private`,
  `_protected`, or located in `krl.py` unless you intend to extend the core
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
krl_config.py
template.src
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
DEF example()
  BAS(#INITMOV, 0)
  ; Go to start position
  PTP {{A1 0, A2 -90, A3 90, A4 0, A5 90, A6 0}}
  ; Go to programmed positions
{}
  ; Go to end position
  PTP {{A1 0, A2 -90, A3 90, A4 0, A5 90, A6 0}}
END
```


#
