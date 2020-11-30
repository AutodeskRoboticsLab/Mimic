#!usr/bin/env python
"""
Configuration for post processors
"""

import mimic_config

reload(mimic_config)


# Import your processor as private here:
from ABB.RAPID.rapid \
    import SimpleRAPIDProcessor \
    as __SimpleRAPIDProcessor
from KUKA.EntertainTech.entertaintech \
    import SimpleEntertainTechProcessor \
    as __SimpleEntertainTechProcessor
from KUKA.KRL.krl \
    import SimpleKRLProcessor \
    as __SimpleKRLProcessor
from Staubli.VAL3.val3 \
    import SimpleVAL3Processor \
    as __SimpleVAL3Processor
from GENERAL.CSV.comma_separated_vals \
    import SimpleCSVProcessor \
    as __SimpleCSVProcessor
from GENERAL.TSV.tab_separated_vals \
    import SimpleTSVProcessor \
    as __SimpleTSVProcessor

# Add your processor to private list here:
__supported_processors = [
    __SimpleRAPIDProcessor,
    __SimpleKRLProcessor,
    __SimpleVAL3Processor,
    __SimpleEntertainTechProcessor,
    __SimpleCSVProcessor,
    __SimpleTSVProcessor
]


def construct_processor_name(type_robot, type_processor):
    """
    Construct the name of a single Post Processor.
    :param type_robot: Type of robot.
    :param type_processor: Type of processor.
    :return:
    """
    return '{} {}'.format(type_robot, type_processor)


def get_processor_name(processor):
    """
    Get the name from a given Post Processor
    :param processor: Processor itself.
    :return:
    """
    return construct_processor_name(processor.type_robot, processor.type_processor)


def get_processor_names(pref_level=mimic_config.FILE):
    """
    Get the names of all processors using existing POST_PROCESSORS dict.
    Sorts names alphabetically by default. User-accessible function.
    :param pref_level: str - PREFERENCE LEVEL defined in mimic_config module
    :return: 'ROBOT_TYPE POSTPROCESSOR_TYPE'
    """
    names = POST_PROCESSORS.keys()
    names.sort()

    # Get default from config. This is the processor that should appear first.
    default = mimic_config.Prefs.get('DEFAULT_POST_PROCESSOR', pref_level)

    if default in names:
        names.remove(default)
        names.insert(0, default)
    return names


# All post processors dict!
POST_PROCESSORS = {}

# Configure the dict (don't touch)
for processor in __supported_processors:
    p = processor()
    name = construct_processor_name(p.type_robot, p.type_processor)
    POST_PROCESSORS[name] = processor
