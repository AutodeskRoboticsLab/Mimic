# Mimic

### SimpleRAPIDProcessor

The SimpleRAPIDProcessor is a Post Processor for Mimic designed to program ABB
robots using the RAPID programming language and PRG output file extension. No
installation options are required for use of this package. This processor IS NOT
time-based.

```
Name: SimpleRAPIDProcessor
Robot type: ABB
Processor language: RAPID
Output file extension: PRG
Required installation options: None
Time-based: False
```


### Contents

This package contains the following directories and/or files:

```
|-- RAPID
    |-- __init__.py
    |-- rapid.md
    |-- rapid.py
    |-- rapid_config.py
    |-- template.prg
    |-- template_use_as_vars.prg
```


### Warning!

- This Post Processor serves a method of programming robots that IS NOT
  fundamentally time-based. Robot motion seen in Maya may and likely will differ
  from robot motion seen in the real world. 
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
    |-- Use motion as variables
|-- Include in outut
    |-- Axes
```


### Configuration

This package comes with functional default parameters and configuration
parameters that must be modified to suit user and application requirements.
User parameters can be found in the following files:

```
rapid_config.py
template.prg
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
MODULE MainModule
	! Main routine
	PROC main()
		ConfL\Off;
		SingArea\Wrist;
		! Go to start position
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		! Go to programmed positions
{}
		! Go to end position
		MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		Stop;
	ENDPROC
ENDMODULE
```

Alternatively, teh default program template for the user option 'Use as variables'
is as follows:

```
MODULE MainModule
	! Pose variables
	CONST num NUMPOSES := {};
	CONST jointtarget poses{{NUMPOSES}} :=
    [
{}
    ];
	! Main routine
	PROC main()
		ConfL\Off;
		SingArea\Wrist;
		! Go to start position
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		! Go to programmed positions
		FOR i FROM 1 TO NUMPOSES DO
			MoveAbsJ poses{{i}}, v100, fine, tool0;
		ENDFOR
		! Go to end position
		MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		Stop;
	ENDPROC
ENDMODULE
```


#
