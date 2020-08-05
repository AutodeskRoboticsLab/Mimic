# Mimic | Extern

### Overview

When possible, we try to minimize dependencies on external packages/modules; however, in some cases, it becomes unavoidable.

The `/extern` directory contains such open-source packages/modules that are
leveraged by Mimic.

The directory is added to Maya's `PYTHONPATH` path variable when the Mimic
module file `mimic.mod` is loaded by Maya. This allows for direct import of
modules and packages.

**Example**
```python
import pyqtgraph as pg 
```

When possible, use the most recent release from the package/module's repository
If, for some reason, the most recent release is not used, or the package/module 
has been modified, make note of it here.


### Modules

* **Qt.py** [version: 1.2.0.b2 ][[source](https://github.com/mottosso/Qt.py)][[license](https://github.com/mottosso/Qt.py/blob/master/LICENSE)] 
_Used for creating back-compatible UIs with PySide 2_


### Packages
* **PyQtGraph** [version: GitHub Master origin/HEAD 07/16/2018*][[source](https://github.com/pyqtgraph/pyqtgraph)][[license](https://github.com/pyqtgraph/pyqtgraph/blob/develop/LICENSE.txt)] [[website](http://www.pyqtgraph.org/)] 
A pure-Python graphics library for PyQt/PySide 
_Used for graphing in Mimic's Analysis package_
**Notes:**  
	- At the time of this writing, the most recent PyQtGraph release (0.10.0) lacked features necessary for Mimic's Analysis graphing module, so the main branch head was used 
	- Fixed small bug in PyQtGraph that caused misalignment of legend items [see: `mimic/scripts/extern/pyqtgraph/graphicsItems/LegendItem.py` [`commit`](https://github.com/AutodeskRoboticsLab/Mimic/commit/67a8389a707bd8e1d5a0619a93cc150b5237d01b#diff-a1a34d87a522bc6af94dae6db694521c)] 
	- Reorded libOrder in pyqtgraph/Qt.py to fix an [import error](https://github.com/AutodeskRoboticsLab/Mimic/issues/3) some users were facing
	- Fixed small bug in pyqtgraph/widgets/GraphicsView.py that caused an error in Maya2020 due to mismatching type signature during a MouseMoveEvent [`commit`](https://github.com/AutodeskRoboticsLab/Mimic/commit/b2d38031cf2c6d34e412ff76469cb6168de3c169)]
> 
* **NumPy** [version*][[source](https://github.com/numpy/numpy)][[license](http://www.numpy.org/license.html#license)][[website](http://www.numpy.org/)] 
the fundamental package for scientific computing with Python 
_Used by PyQtGraph_
**Notes:**
	- NumPy is only included as a dependency of PyQtGraph. It should not be used by other modules to avoid dependency issues with the rest of Mimic 
	- *NumPy is a library that must be compiled; as such, the version used is specific to the operating system, so we have included pre-compiled versions for each operating system
