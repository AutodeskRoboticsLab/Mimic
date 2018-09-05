# Mimic

### Contributing

*Woohoo! Thanks for your help!*

The code in this repository was generally written and tested in Python 2.7.14.
We have used a number of different coding styles, however in the interest of
consistency, use [PEP8](https://www.python.org/dev/peps/pep-0008/) conventions
for Python code.

When in doubt, consult the [Zen of Python](https://www.python.org/dev/peps/pep-0020/).


### Dependencies

It is highly recommended that you use the standard library when possible! Ideally,
this repository has no external dependencies and can be easily installed in *one
step* by anyone. To that end, users should not be expected to install external
dependencies.

If necessary, however, packages can be added to the `/scripts/extern` directory.
See `/scripts/extern.md` for more details.

Don't worry about this section unless you're using something other than Maya to
interface this repository. The following dependencies are accessible only through
Maya; use [mayapy](http://help.autodesk.com/cloudhelp/2016/CHS/Maya-Tech-Docs/PyMel/standalone.html)
or handle any `ImportError` as needed in your IDE.

- [pymel](https://help.autodesk.com/cloudhelp/2016/ENU/Maya-Tech-Docs/PyMel/)
- [maya.api](https://help.autodesk.com/view/MAYAUL/2018/ENU/?guid=__py_ref_index_html)
  
  
### Adding packages

Packages, such as the *postproc* package, should function independently
of Mimic and Maya. Packages may be integrated with this repository via the following
structure. Note the use of `__init__.py` throughout this repository.

```
|-- mimic
    |-- __init__.py
    |-- scripts
        |-- __init__.py
        |-- package
            |-- __init__.py
            |-- ...
        |-- ...
    |-- ...
```


### Repository guidelines

- This repository is organized with respect to what Maya expects to see in its
  [modules](http://help.autodesk.com/view/MAYAUL/2018/ENU/?guid=__files_GUID_CB76E356_753B_4837_8C5B_3296C14872CA_htm) directory. Directories within Mimic, such as *scripts* and *icons*
  are named accordingly. Do not change them!

- Do not add IDE and temp files to the global `.gitignore`. Instead, add them
  to a local gitignore (added to `~/.gitconfig`). Alternatively, the folder
  `ignore` is ignored and may be used however you'd like.

- Make sure your code compiles before submitting pull requests or pushing to
  the repository. For each commit, provide a briefly rationalized changelist.
  
- This repository supports branching, however, the main branch should be treated
  as such; it should always contain the most stable and generalized codebase.


### Programming guidelines

- Try to follow naming conventions. At time of writing, the only exceptions to
  this rule are the Maya-Python libraries and Maya attributes.
    - Variables and functions use `snake_case`
    - Classes and class-like objects (i.e. namedtuple) use `CapWords`
    - Global variables use `UPPERCASE_WORDS`
    - Protected variables and functions are `_prefixed` by one underscore.
    - Private variables and functions are `__prefixed` by two underscores.

- Favor descriptive, accurate, and clear names; avoid abbreviations.

- Never import anything using `*`! This makes it super difficult for anyone
  else to read, debug, and trace functionality throughout the repository.

- Favor specific exceptions over broad exceptions. Custom exceptions should
  be avoided and, otherwise, clearly indicate the nature of the exception.

- Document everything!
    - Some documentation may require a full readme.
      If the documentation is for Mimic itself, place it in *mimic/docs*. If it's
      for a package (such as *postproc*), place it in the package directory and
      provide both a description of it and a link to it in *docs/package_index.md*.
    - Use inline comments where an implementation is unclear or a notable.
    - Use complete docstrings for modules, classes, and functions.

- Try to avoid lines that exceed 80 characters in length. Don't worry if a few
  lines break this rule to preserve clarity.

- When using flags for Maya PyMel functions, use the flag's Long Name.

- Use `__private`, `_protected`, and `GLOBAL` variables responsibly!
 

### User Interface (UI) guidelines

- The Mimic UI naming conventions are as follows:
    - Use `Capitalized Letters` for tab titles, section titles, or buttons. 
    - Use `Capitalized first word only` for radios, checkboxes, or descriptions.
    - Use `lowercase` for parameter types suggested by text boxes, ex: `deg`.
    - You may use abbreviations for special, well-known parameters, ex: `A1`.
    - You may use `UPPERCASE` for special, well-known parameters, ex: `KUKA`.
    - Avoid `lowercase`, `UPPERCASE`, or `Abbrev.` elsewhere unless necessary.

- Prefer common UI elements and avoid unique UI elements. Elements such as text
  or button colors, decorative separators, and unusual windows and icons should
  be implemented if *functionally requisite*.
  
- Prefer common dimensions of UI elements, such as separators, and maintain the
  existing dimensions and proportions of the Mimic window.


### Pro tips
 
- Most of Mimic, except for anything UI or Maya dependent, may be written, run,
  and debugged in an external IDE. This will save *hours* of development time as
  compared to developing directly within Maya. To take advantage of this, call
  `reload(*)` after `import *` so changes you make to your code can be loaded by
  Mimic when it reopens without having to reopen Maya all the time.
  
- To avoid creating PYCs -- compiled Python files -- implement this at the very
  top of your highest level Python script (really helpful for tests):
  
    ```
    import sys
    sys.dont_write_bytecode = True
    ```
    
  
#
