# Mimic Analysis

This is the analysis module of Mimic; it generally takes a program as animated in Maya, calculates the first, second, and third derivatives of the program (i.e. Velocity, Acceleration, and Jerk), and prepares a graphical representation of that data, along with the program itself.


### Organization

```
|-- scripts
    |-- analysis
        |-- analysis.py
        |-- analysis_utils.py
        |-- analysis_ui.py
        |-- analysis_ui_utils.py *
        |-- analysis_ui_config.py
```

- `analysis.py`
  contains only a single, high-level function which takes a program generated
  by Mimic, and produces a graphical UI to interract with the corresponding data.
  
- `analysis_utils.py`
  contains the majority of the utility functions used for manipulating program
  data, generating derivatives, etc.

- `analysis_ui.py`
  configures and creates the Mimic Anaylsis user interface.

- `analysis_ui_utils.py`
  contains custom UI classes used to create the Mimic analysis UI

- `analysis__ui_config.py`
  contains a few global variables used to configure default options for the 
  analysis UI when launched.


### Dependencies

The Analysis module is dependent on both PyQtGraph and NumPy.
See [extern.md](mimic/scripts/extern.md) for more details about these modules

#