# Mimic Developer Guide

This document is meant to provide an overview of the Mimic codebase so that
its easier for programmers to start modifying or contributing to it. While it
isn't meant to replace more detailed documentation that can be found throughout
the repository, think of it as a sort of *quickstart* guide to the repository
itself and to how Mimic works under the hood.

If you're looking for developer notes and programming guidelines, check out
*mimic/docs/devnotes.md*.


### Design goals




### Organization

```
|-- mimic
    |-- docs
    |-- icons
    |-- logos
    |-- plug-ins
    |-- rigs
    |-- scripts
    |-- shelves
    |-- ...
```

- `docs`
  contains all of the *general* documentation that you might need in order to
  navigate or contribute to this repository. This directory also contains the files
  `AUTHORS.md` and `LICENSE.md`. Files preceded with an underscore, `_`, provide
  an index and sometimes basic descriptions of Mimic content.
  
- `icons`
  contains logos, graphics, and button icons used throughout the Mimic
  documentation and user interface.
  
- `logos`
  contains a ton of logos that users may feel free to use however they'd like.

- `plug-ins`
  contains plug-in scripts that are used by Mimic and loaded by Maya at runtime.
  The name of this directory follows a Maya convention and shouldn't be modified.

- `rigs`
  contains robot rigs, meaning the robot-geometry and attribute models that Mimic
  allows you to control on screen. Rigs are organized by robot brand.

- `scripts`
  contains the actual Mimic codebase and any supplementary Python packages.
  The name of this directory follows a Maya convention and shouldn't be modified.

- `shelves`
  contains an user interface button for Mimic that is loaded by Maya at runtime.
  The name of this directory follows a Maya convention and shouldn't be modified.


### Things to notice right away

- There are initialization files named `__init__.py` throughout the repository,
  allowing Mimic to be imported as one, big Python package. Notice that every
  directory that contains Python code also contains such a file. Notice also
  that these files are blank and need only be present to work.
  
- Look out for markdown files with the extension `.md` throughout Mimic. These
  provide tons of documentation specific to nearby Python modules and files and
  will help to clarify any questions you have about how Mimic works.

- Most directories contain a Python module of the same name, for example the
  directory `mimic` contains the module `mimic.py`. Nearby modules that provide
  supplementary functionality are prefixed accordingly, for example
  `mimic_utils.py` provides supplementary functionality for `mimic.py`.
  
- The most *important* Python modules in the Mimic repository are prefixed by
  `mimic` and are located in the `scripts` directory. For documentation on these,
  see `mimic.md`; inline and functional comments are included throughout.


#
