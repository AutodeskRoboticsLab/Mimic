# Mimic

### SimpleCSVProcessor

The SimpleCSVProcessor is a Post Processor for Mimic designed to export paths as CSVs.

```
Name: SimpleCSVProcessor
Robot type: All
Processor language: General
Output file extension: CSV
Time-based: N/A
```


### Contents

This package contains the following directories and/or files:

```
|-- CSV
    |-- __init__.py
    |-- comma_separated_vals.md
    |-- comma_separated_vals.py
    |-- comma_separated_vals_config.py
    |-- template.emily
    |-- example.src
    |-- example.dat
    |-- example.emily
```


### Warning!

- DO NOT modify or mutate the value of parameters that are either `__private`,
  `_protected`, or located in `comma_separated_vals.py` unless you intend to extend the core
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
comma_separated_vals_config.py
template.csv
```

This package comes with a functional default program that must be modified to
suit user and application requirements.
The default program template used by this package is as follows:

```
Time, Axis 1, Axis 2, Axis 3, Axis 4, Axis 5, Axis 6
{}
```


#
