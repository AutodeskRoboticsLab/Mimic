

![mFIZ_logo](mFIZ/icons/mFIZ_logo_web.png)

#

### What is mFIZ?

*An open-source [Autodesk Maya](https://www.autodesk.com/products/maya/overview) plugin for automating film lens control systems.*

This plugin can be used on its own; however, it can also be used to integrate lens control into motion control film workflows, like those enabled by our sister plug-in [Mimic](https://www.mimicformaya.com/). Mimic is an Autodesk Maya plugin that provides an animation-based workflow for programming 6-axis, Industrial Robots, and is most commonly used for filmmaking applications.


### Installation

Download the latest Mimic [release](https://github.com/AutodeskRoboticsLab/Mimic/releases) and copy the contents of it to one of the following directories, depending on your operating system:

```
macOS   ~/Library/Preferences/Autodesk/maya/modules
Windows ~/Documents/maya/modules
```

This will create a shelf with an mFIZ button. That's it!

See Mimic Installation instructions for troubleshooting.



### Currently supported lens control systems

mFIZ currently supports the following systems:

```
[Redrock Micros Eclipse](https://shop.redrockmicro.com/eclipse/)
```

### How does mFIZ work?

At the heart of mFIZ is a custom Maya Python MPxNode that sends data out of Maya through a serial API. When an mFIZ "Controller" is added to the scene, two Maya nodes are created, and then connected together. The first is a Locator Transform node, and the second is the custom MPxNode of type "mFIZ", which can be found in `mFIZ/plug-ins`

Using the mFIZ UI, you can set and keyframe Focus, Iris, and Zoom attributes on the Locator Control node. The mFIZ node establishes a connection and sends the motor data to the motors via the APIs in the `mFIZ/scripts/motor_apis`.


### Join the community!

Help us out and contribute to this repository!
You may submit an issue or open a pull request for any bugs or improvements to
this software. See [CONTRIBUTING](mFIZ/docs/CONTRIBUTING.md) for programming guidelines.

Join the our [slack channel](https://www.mimicformaya.com/#community-section)!
You may also contact us at [mimic@autodesk.com](mailto:mimic@autodesk.com).

*mFIZ was born at the Autodesk Robotics Lab in 2019.* 
See [AUTHORS](mFIZ/docs/AUTHORS.md) for details.


### License

mFIZ is licensed under the MIT license.
See [LICENSE](mFIZ/docs/LICENSE.md) for details.


### Acknowledgments

- [Redrock Micro](https://shop.redrockmicro.com/eclipse/) for their support, openness, and motor API contribution
- [Dan Thompson](www.danthompsonsblog.blogspot.com) and his work on [Servo Tools for Maya](https://www.highend3d.com/maya/plugin/servo-tools-for-maya-for-maya). While none of Dan's source code was used, his methodolgy and execution was both informative and inspirational during mFIZ development.


### Notes

- Developed to work with Autodesk Maya 2016-2019; mFIZ may or may not be compatible with other versions.
- Developed to work with macOS and Windows; 
- Do not modify names or hierarchies within the repository!


#
