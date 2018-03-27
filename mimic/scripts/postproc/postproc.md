# Mimic

### Post Processors

This section refers to the Python package *mimic/scripts/postproc*. It contains
several Post Processor modules for interpreting and formatting commands created
in Mimic and, from them, producing usable robot code. 

If you add a new Post Processor to this package make sure to:
- List it as supported in the main README.
- Document it using a markdown (`.md`), docstrings, and inline comments.
- Test it! Verify that it is robust and behaves as expected.


### Dependencies

The Post Processors contained in the directory *postproc* try to use the standard
libraries for all functionality. In some cases, they leverage functions provided
elsewhere in Mimic, such as in *general_utils.py* and *transforms.py*. It may,
later, be decided that these functions should be moved in such a way that this
package may be fully independent of the rest of this repository.


### Organization

Post Processors are contained in Python packages, allowing them to be added,
altered, or removed easily by users. Note the use of `__init__.py` modules
throughout the project. The basic file structure is as follows. Note that the
folder structure depends on the parameters `type of robot`, `type of processor`,
and `type of output file`, which characterize the Post Processor subclass.
The *postproc* directory may contain any number of robot type directories and
a robot type directory may contain any number of Post Processors (though users
should try to maintain organization).

```
|-- postproc
    |-- __init__.py
    |-- postproc.py
    |-- postproc_config.py
    |-- <type of robot>
        |-- __init__.py
        |-- <type of processor>
            |-- __init__.py
            |-- <type of processor>.md
            |-- <type of processor>.py
            |-- <type of processor>_config.py
            |-- template.<output file extension>
            |-- example.*
            |-- ...
        |-- ...
    |-- ...
```

For the purpose of style, the parameter `type of processor` should always be
lowercase. The parameters `type of robot` and `type of processor` are free to
use their own, appropriate naming convention.

The *postproc* directory also contains the files:
- *postproc.md*, which is a readme for this package
- *postproc.py*, which contains PostProcessor object, datatypes, functions
- *postproc_config.py*, which contains configuration parameters
- *postproc_setup.py*, which contains configuration functions


### Implementation

Post Processors are implemented as subclasses of the class `PostProcessor` from
*postproc.py*. The class should be instantiated using the parameters `type_robot`
`type_processor`, and `output_file_extension` *exactly* as above (these parameters are
ultimately used to navigate the above file structure). Note that the subclass
must be initialized as follows (other implementations *may* work in unittests but
*may not* work in Maya and would be inconsistent with those in this repository).
Note that the root `PostProcessor` class is a subclass of `object`.

```
def __init__(self):
    super(SimpleKRLProcessor, self).__init__(*params)
```

The `PostProcessor` is primarily concerned with interfacing the Mimic repository
structure, reading and writing files, and structuring the processing routine for
subclasses. While most of the methods for protected and for internal use only,
public methods for actually running the processor and writing an output file are
available. Note that the content of some methods may differ among subclasses of
and must be defined manually therein (will raise a `NotImplementedError` if left
undefined)

```
# Public methods
PostProcessor.process(self, *args)
PostProcessor.write(self, *args)
PostProcessor.get_formatted_commands(self, *args)

# Methods that must be defined in subclass
PostProcessor._process_command(self, *args)
PostProcessor.get_formatted_commands(self, *args)
```


### Configuration

The *postproc_config.py* contains a method of adding a Post Processor package
to Mimic. Mimic will refer to this file at runtime for supported Post Processors,
so this file must be configured by the user if a new Post Processor is added to
the repository. In order to do this, `import` the Post Processor itself as a
private variable and include it in the private list `__supported_processors` as
follows:

```
# Import your processor as private here:
from KUKA.EntertainTech.postproc_entertaintech \
    import SimpleEntertainTechProcessor \
    as __SimpleEntertainTechProcessor
# ...

# Add your processor to private list here:
__supported_processors = [
    __SimpleEntertainTechProcessor,
    # ...
]
```

These are named and added automatically to a public dictionary, `POST_PROCESSORS`,
such that they may be accessed. Additional functions for getting processor names
are also available. For example:

```
all_names = postproc_config.get_processor_names()
name = postproc_config.construct_processor_name(TYPE_ROBOT, TYPE_PROCESSOR)
if name in all_names:
    processor = postproc_config.POST_PROCESSORS[name]()
    name_check = postproc_config.get_processor_name(processor)
    assert name == name_check
```


### Structures and templates

Commands in Mimic, such as motion commands like *move the robot Phobos linearly
and using poses only*, are programmed via modeling and, occasionally, an option
selected via the Mimic UI. However, in order for Mimic interface any kind of Post
Processor, those parameters are structured using a `namedtuple` depending
on their type. A few generic structures, such as `Axes`, `ExternalAxes`, `Pose`,
`Configuration`, `DigitalOutput`, and `AnalogOutput`, are provided. When a Post
Processor receives a generic datatype as input from Mimic, it is thus able to map
that input to its own expression of it, structure, and template.

The implementation, here, of `namedtuple` allows structure parameters to be
accessed by clear, human-readable names. This behavior is class-like, however,
the parameters of a structure are immutable after it is instantiated. Also, and
unlike a dictionary, the parameters are always ordered. Note that many of the
parameters are marked private, such as `__pose_x`, so as to be clearly indicated
as constants internal to and inaccessible beyond this module.
 
```
POSE = 'pose'
Pose = namedtuple(
    POSE, [
        'pose_x',
        'pose_y',
        'pose_z',
        'pose_ix',
        'pose_iy',
        'pose_iz',
        'pose_jx',
        'pose_jy',
        'pose_jz',
        'pose_kx',
        'pose_ky',
        'pose_kz'
    ]
)
```
 
Specific Post Processors, such as `SimpleKRLPostProcessor`, may have similar
but otherwise application-specific structures. Here, a `__frame_structure` is
functionally equivalent to a `Pose` structure, however, it is not directly
translatable from it. In this case, Euler angles `A`, `B`, `C` must first be
calculated using the principle vectors `i`, `j`, `k` of the `Pose`.

```
FRAME = 'FRAME'
__frame_structure = namedtuple(
    FRAME, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c
    ]
)
```

Note that many of the parameters, such as `__x`, are reusable, such as in
`FRAME` above and `POS` below, and so are implemented once as private variables
higher up in the module.

```
__x = 'X'
__y = 'Y'
__z = 'Z'
__a = 'A'
__b = 'B'
__c = 'C'
__s = 'S'
__t = 'T'
# ... 

POS = 'POS'
__pos_structure = namedtuple(
    POS, [
        __x,
        __y,
        __z,
        __a,
        __b,
        __c,
        __s,
        __t
    ]
)
```

In order to format a structure, a structure-specific template must also exist.
Here, a `__frame_template` contains robot-control code and a placeholder in the
form `{}` for each of the parameters of a `__frame_structure`.

```
__frame_template = \
    '{{' \
    'X {}, Y {}, Z {}, A {}, B {}, C {}' \
    '}}'
```

Note that both `__frame_structure` and `__frame_template` are private in the
above. This is done so to protect them from unwanted mutations and so that they
may be, as a pair, accessible from a public dictionary by the datatype parameter
alone, in this case the parameter `FRAME`. So, once the datatype of an input
command is determined, it is mapped to the appropriate structure and template.

```
STRUCTURES = {
    FRAME: __frame_structure
    # ...
}

TEMPLATES = {
    FRAME: __frame_template
    # ...
}
```


### User options

User options for Post Processors are defined with a `__user_options` structure.
The function `configure_user_options(*opts)` contains descriptions of optional
parameters within the structure (by default, all options are set to False unless
otherwise indicated by the user). Note that these parameters are not reusable and
implemented as strings directly within the tuple. Post Processors should, in
addition to commands, receive as input a completed options structure.

```
# USER OPTIONS
USER_OPTIONS = 'USER_OPTIONS'
__user_options = namedtuple(
    USER_OPTIONS, [
        'use_motion',
        'use_linear_motion',
        'use_nonlinear_motion',
        'include_axes',
        'include_pose',
        'include_external_axes',
        'include_configuration',
        'use_ios',
        'process_ios_first',
        'include_digital_output',
        'include_checksum'
    ]
)
```


### Template files

Mimic will search the Post Processor directory for a template file in the form
`template.*` containing robot-control code and placeholders for commands in the
form `{}`. Programmers should feel free to alter the content of these files
as necessary, keeping in mind to retain the required placeholders. If a template
file cannot be found, Mimic will refer to a default, internal template, which
cannot be altered except in Python. When commands are processed, placeholder
parameters will be replaced with formatted commands. Mimic will output to the
Post Processor directory a file in the form `output.*` containing robot-control
code and formatted commands. In some cases, the directory also contains an
example implementation in the form `example.*` which contains robot-control code.

The template below contains the placeholder parameter `{}`, a few syntactical
elements such as `[HEADER]`, and a user-defined parameter `GEAR_NOMINAL_VEL`.
Note that everything in this template may be altered to the extent that only 
the placeholder parameter remains; while this would not create a complete program,
a Post Processor would still be able to generate an output file.

```
[HEADER]
  GEAR_NOMINAL_VEL = 1.000000
[RECORDS]
{}
[END]
```

When the template is processed (here by `SimpleEntertainTechPostProcessor`),
the placeholder parameter is replaced by several lines of command parameters.
In this case, a time parameter and six axis parameters are defined. Note that
sometimes an additional program is required to run an output file.

```
[HEADER]
  GEAR_NOMINAL_VEL = 1.000000
[RECORDS]
   +0.012000   +0.000000  +90.000000  +10.000000   +0.000000   +0.000000   +1.000000  
   +0.024000   +1.000000  +90.000000  +20.000000   +0.000000   +0.000000   +2.000000  
   +0.036000 -666.666000  +90.000000  +10.000000   +0.000000   +0.000000   +1.000000  
   +0.048000  +33.000000  +90.000000  +20.000000   +0.000000   +0.000000   +2.000000  
   +0.060000   +4.000000  +90.000000  +10.000000   +0.000000   +0.000000   +2.000000  
   +0.072000   +5.000000  +90.000000  +20.000000   +0.000000   +0.000000   +3.000000  
   +0.084000   +6.000000  +90.000000  +10.000000   +0.000000   +0.000000   +5.000000  
   +0.096000   +7.000000  +90.000000  +20.000000   +0.000000   +0.000000   +6.000000  
   +0.108000   +8.000000  +90.000000  +10.000000   +0.000000   +0.000000   +4.000000
[END]
```


### Notes

- It is possible to use a Post Processor of type 'A' to generate robot-control
  code for a Robot of type 'B' (for example, using a KUKA robot with an ABB RAPID
  Post Processor). While this *may* generate usable robot control code, it is
  highly inadvisable and potentially dangerous. Future versions of Mimic may or
  may not limit this functionality.
- It is possible to use a Robot of type 'A' to generate robot-control
  code for a Robot of type 'B' (for example, using an ABB IRB-120 robot to generate
  code for an ABB IRB-6700). While this *may* generate usable robot control code, it is
  highly inadvisable and potentially dangerous. Future versions of Mimic may or
  may not limit this functionality.
- This package is intended for use with a few supported robots, installation
  options which must be installed on same, and user settings. Users are expected
  to understand *how* to use and program their robot and should refer to external
  documentation regarding safety and usage for their application.
- It may be the case a Post Processor serves a method of programming robots that
  IS NOT fundamentally time-based. If so, *clearly* indicate that robot motion seen
  in Maya may and likely will differ from robot motion seen in the real world. 

#
