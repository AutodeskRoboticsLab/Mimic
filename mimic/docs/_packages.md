# Mimic Packages

### Package index

This is a simple index of packages installed in this repository. For each
package are provided a brief description and link to documentation. Note that,
typically, a documentation markdown, `*.md`, is provided within the package.

Packages contained in Mimic are as follows:

```
|-- mimic
    |-- scripts
        |-- postproc
        |-- rigging *
        |-- robotmath
        |-- analysis
        |-- extern
            |-- Qt.py
            |-- pyqtgraph
            |-- numpy
        |-- ...
    |-- ...
```


### postproc

Several Post Processor modules for interpreting and formatting commands created
in Mimic and, from them, producing usable robot code.

Documentation may be found in:
[postproc.md](mimic/scripts/postproc/postproc.md).

Subpackages contained in `postproc` are as follows:


```
|-- postproc
    |-- ABB
        |-- RAPID
        |-- ...
    |-- KUKA
        |-- EntertainTech
        |-- KRL
        |-- ...
    |-- ...
```


### rigging *

Tools for assisted-rigging of robots in Autodesk Maya for use with Mimic.

Documentation may be found in:
[rigging.md](mimic/scripts/rigging/rigging.md).


### analysis

Tools for analyizing intended robot motion; primarily through graphical representations

Documentation may be found in:
[analysis.md](mimic/scripts/analysis/analysis.md).


### extern

External libraries leveraged by Mimic

Documentation may be found in:
[extern.md](mimic/scripts/extern/extern.md).

Subpackages contained in `extern` are as follows:


```
|-- extern
    |-- Qt.py
    |-- pyqtgraph
        |-- ...
    |-- numpy **
        |-- ...
```

### robotmath

Algorithms for control of 6 DOF industrial robots including those for inverse
kinematics, forward kinematics, matrix transforms, and more.

Documentation may be found in:
[references](mimic/scripts/robotmath/references).


#

\* *Not integrated at time of writing*

#
