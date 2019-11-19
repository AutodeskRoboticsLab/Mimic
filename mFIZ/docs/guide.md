# mFIZ Developer Guide

This document is meant to provide an overview of the mFIZ codebase so that
its easier for programmers to start modifying or contributing to it. While it
isn't meant to replace more detailed documentation that can be found throughout
the repository, think of it as a sort of *quickstart* guide to the repository
itself and to how mFIZ works under the hood.

If you're looking for developer notes and programming guidelines, check out
*mFIZ/docs/CONTRIBUTING.md*.


### Design goals




### Organization

```
|-- mFIZ
    |-- docs
    |-- icons
    |-- plug-ins
    |-- scripts
    |-- shelves
    |-- ...
```

- `docs`
  contains all of the *general* documentation that you might need in order to
  navigate or contribute to this repository. This directory also contains the files
  `AUTHORS.md` and `LICENSE.md`. Files preceded with an underscore, `_`, provide
  an index and sometimes basic descriptions of mFIZ content.
  
- `icons`
  contains logos, graphics, and button icons used throughout the mFIZ
  documentation and user interface.

- `plug-ins`
  contains plug-in scripts that are used by mFIZ and loaded by Maya at runtime.
  The name of this directory follows a Maya convention and shouldn't be modified.

- `scripts`
  contains the actual mFIZ codebase and any supplementary Python packages.
  The name of this directory follows a Maya convention and shouldn't be modified.

- `shelves`
  contains a user interface button for mFIZ that is loaded by Maya at runtime.
  The name of this directory follows a Maya convention and shouldn't be modified.


### Things to notice right away

- There are initialization files named `__init__.py` throughout the repository,
  allowing mFIZ to be imported as one, big Python package. Notice that every
  directory that contains Python code also contains such a file. Notice also
  that these files are blank and need only be present to work.
  
- Look out for markdown files with the extension `.md` throughout mFIZ. These
  provide tons of documentation specific to nearby Python modules and files and
  will help to clarify any questions you have about how mFIZ works.
  
- The most *important* Python modules in the mFIZ repository are prefixed by
  `mFIZ` and are located in the `scripts` directory. For documentation on these,
  see `mFIZ.md`; inline and functional comments are included throughout.


#
