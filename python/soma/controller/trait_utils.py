#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
import sys
import types
from textwrap import wrap
import re
import logging
import six
import importlib

# Define the logger
logger = logging.getLogger(__name__)

# Trait import
import traits.api

if sys.version_info[0] >= 3:
    unicode = str


# Global parameters
_type_to_trait_id = {
    int: "Int",
    unicode: "Unicode",
    str: "Str",
    float: "Float"
}
# In order to convert nipype special traits, we define a dict of
# correspondances
_trait_cvt_table = {
    "InputMultiPath_TraitCompound": "List",
    "InputMultiPath": "List",
    "MultiPath": "List",
    "Dict_Str_Str": "DictStrStr",
    "OutputMultiPath_TraitCompound": "List",
    "OutputMultiPath": "List",
    "OutputList": "List"
}


def get_trait_desc(trait_name, trait, def_val=None):
    """ Generate a trait string description of the form:

    [parameter name: type (default trait value) string help (description)]

    Parameters
    ----------
    name: string (mandatory)
        the trait name
    trait: a trait instance (mandatory)
        a trait instance
    def_val: object (optional)
        the trait default value
        If not in ['', None] add the default trait value to the trait
        string description.

    Returns
    -------
    manhelpstr: str
        the trait description.
    """
    # Get the trait description
    desc = trait.desc

    # Get the trait type
    trait_id = trait_ids(trait)

    # Add the trait name (bold)
    manhelpstr = ["{0}".format(trait_name)]

    # Get the default value string representation
    if def_val not in ["", None]:
        def_val = ", default value: {0}".format(repr(def_val))
    else:
        def_val = ""

    # Get the paramter type (optional or mandatory)
    if trait.optional:
        dtype = "optional"
    else:
        dtype = "mandatory"

    # Get the default parameter representation: trait type of default
    # value if specified
    line = "{0}".format(trait.info())
    if not trait.output:
        line += " ({0} - {1}{2})".format(trait_id, dtype, def_val)

    # Wrap the string properly
    manhelpstr = wrap(line, 70,
                      initial_indent=manhelpstr[0] + ": ",
                      subsequent_indent="    ")

    # Add the trait description if specified
    if desc:
        for line in desc.split("\n"):
            line = re.sub("\s+", " ", line)
            manhelpstr += wrap(line, 70,
                               initial_indent="    ",
                               subsequent_indent="    ")
    else:
        manhelpstr += wrap("No description.", 70,
                           initial_indent="    ",
                           subsequent_indent="    ")

    return manhelpstr


def is_trait_value_defined(value):
    """ Check if a trait value is valid.

    Parameters
    ----------
    value: type (mandatory)
        a value to test.

    Returns
    -------
    out: bool
        True if the value is valid,
        False otherwise.
    """
    # Initialize the default value
    is_valid = True

    # Check if the trait value is not valid
    if (value is None or value is traits.api.Undefined or
       (isinstance(value, six.string_types) and value == "")):

        is_valid = False

    return is_valid


def is_trait_pathname(trait):
    """ Check if the trait is a file or a directory.

    Parameters
    ----------
    trait: CTrait (mandatory)
        the trait instance we want to test.

    Returns
    -------
    out: bool
        True if trait is a file or a directory,
        False otherwise.
    """
    return (isinstance(trait.trait_type, traits.api.File) or
            isinstance(trait.trait_type, traits.api.Directory))


def trait_ids(trait, modules=set()):
    """Return the type of the trait: File, Enum etc...

    Parameters
    ----------
    trait: trait instance (mandatory)
        a trait instance
    modules: set (optional)
        modifiable set of modules names that should be imported to instantiate
        the trait

    Returns
    -------
    main_id: list
        the string description (type) of the input trait.
    """
    # Get the trait class name
    if hasattr(trait, 'handler'):
        handler = trait.handler or trait
    else:
        # trait is already a handler
        handler = trait
    main_id = handler.__class__.__name__
    if main_id == "TraitCoerceType":
        real_id = _type_to_trait_id.get(handler.aType)
        if real_id:
            main_id = real_id

    # Use the conversion table to normalize the trait id
    if main_id in _trait_cvt_table:
        main_id = _trait_cvt_table[main_id]

    # Debug message
    logger.debug("Trait with main id %s", main_id)

    # Search for inner traits
    inner_ids = []

    # Either case
    if main_id in ["Either", "TraitCompound"]:

        # Debug message
        logger.debug("A coumpound trait has been found %s", repr(
            handler.handlers))

        # Build each trait compound description
        trait_description = []
        for sub_trait in handler.handlers:
            if not isinstance(sub_trait, (traits.api.TraitType,
                                          traits.api.TraitInstance,
                                          traits.api.TraitCoerceType)):
                sub_trait = sub_trait()
            trait_description.extend(trait_ids(sub_trait, modules))
        return trait_description

    elif main_id == "Instance":
        inner_id = handler.klass.__name__
        mod = handler.klass.__module__
        if mod not in ("__builtin__", "__builtins__"):
            modules.add(mod)
            inner_id = '.'.join((mod, inner_id))
        return [main_id + "_" + inner_id]

    elif main_id == "TraitInstance":
        inner_id = handler.aClass.__name__
        mod = handler.aClass.__module__
        if mod not in ("__builtin__", "__builtins__"):
            modules.add(mod)
            inner_id = '.'.join((mod, inner_id))
        return [main_id + "_" + inner_id]

    # Default case
    else:
        # FIXME may recurse indefinitely if the trait is recursive
        inner_id = '_'.join((trait_ids(i, modules)[0]
                             for i in handler.inner_traits()))
        if not inner_id:
            klass = getattr(handler, 'klass', None)
            if klass is not None:
                inner_ids = [i.__name__ for i in klass.__mro__]
            else:
                inner_ids = []
        else:
            inner_ids = [inner_id]

        # Format the output string result
        if inner_ids:
            return [main_id + "_" + inner_desc for inner_desc in inner_ids]
        else:
            return [main_id]
