# Mimic

### Overview

This is the core of Mimic; developers should consider all Python modules
located in the `scripts` directory and prefixed with `mimic` as such.


### Organization

```
|-- mimic
    |-- scripts
        |-- mimic.py
        |-- mimic_config.py
        |-- mimic_external_axes.py
        |-- mimic_io.py
        |-- mimic_program.py
        |-- mimic_ui.py
        |-- mimic_utils.py
        |-- ...
```

- `mimic.py`
  contains only a few, high-level functions which load plug-ins, confirm that
  the repository is intact, and, most importantly, create the user interface
  for Mimic.
  
- `mimic_config.py`
  contains a few global variables used to identify the Mimic version and which
  may also define user-settings.
  
- `mimic_external_axes.py`
  provides support for external axes in Mimic.
  
- `mimic_io.py`
  provides support for input/output (I/O) in Mimic.
  
- `mimic_program.py`
  provides support for writing programs in Mimic and interfaces the `postproc`
  package.
  
- `mimic_ui.py`
  configures and creates the Mimic user interface. Ideally, as will eventually
  be the case, this module is the only interface module between Maya and the
  rest of Mimic.
  
- `mimic_utils.py`
  contains the majority of functions on which Mimic runs and, so, is the longest
  Python module in the repository.

#
