# Mimic

### SimpleVAL3Processor

The SimpleVAL3Processor is a Post Processor for Mimic designed to program Staubli
robots using the VAL3 programming language and SRC output file extension. No
installation options are required for use of this package. This processor IS NOT
time-based.

```
Name: SimpleVAL3Processor
Robot type: Staubli
Processor language: VAL3
Output file extension: PGX
Required installation options: None
Time-based: False
```


### Contents

This package contains the following directories and/or files:

```
|-- VAL3
    |-- __init__.py
    |-- val3.md
    |-- val3.py
    |-- val3_config.py
    |-- template.pgx
    |-- project
        |-- MoveJoint.pgx
        |-- MoveLine.pgx
        |-- project.dtx
        |-- project.pjx
        |-- start.pgx
        |-- stop.pgx
```


### Warning!

- This Post Processor serves a method of programming robots that IS NOT
  fundamentally time-based. Robot motion seen in Maya may and likely will differ
  from robot motion seen in the real world. 
- DO NOT modify or mutate the value of parameters that are either `__private`,
  `_protected`, or located in `val3.py` unless you intend to extend the core
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
val3_config.py
template.pgx
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
<?xml version="1.0" encoding="utf-8"?>
<Programs xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.staubli.com/robotics/VAL3/Program/2">
  <Program name="main">
    <Code><![CDATA[begin
  close(tCurrentTool)
  pPointRx.config.shoulder = lefty
  pPointRx.config.elbow = epositive
  pPointRx.config.wrist = wpositive
  pPointRx2.config.shoulder = lefty
  pPointRx2.config.elbow = epositive
  pPointRx2.config.wrist = wpositive
  mCurrentSpeed.tvel = 100.00
  mCurrentSpeed.blend = joint
  mCurrentSpeed.reach = 0.010
  mCurrentSpeed.leave = 0.010
  // Program start
  mCurrentSpeed.tvel = 200.000
{}
  
  waitEndMove()
  // Program end
end]]></Code>
  </Program>
</Programs>
```


#
