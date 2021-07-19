# -*- coding: utf-8 -*-
#
# SOMA - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

# System import
from __future__ import absolute_import
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

# Global parameters
_type_to_trait_id = {
    int: "Int",
    six.text_type: "Unicode",
    str: "Str",
    bytes: "Bytes",
    float: "Float"
}
# In order to convert nipype special traits, we define a dict of
# correspondances
_trait_cvt_table = {
    "InputMultiPath_TraitCompound": "List",
    "InputMultiPath": "List",
    "InputMultiObject": "List",
    "MultiPath": "List",
    "Dict_Str_Str": "DictStrStr",
    "OutputMultiPath_TraitCompound": "List",
    "OutputMultiPath": "List",
    "OutputMultiObject": "List",
    "OutputList": "List",
    "ImageFileSPM": "File",
}


def get_trait_desc(trait_name, trait, def_val=None, use_wrap=True):
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
    use_wrap: bool (optional)
        if True, use text wrapping to 70 columns

    Returns
    -------
    manhelpstr: str
        the trait description.
    """
    # Get the trait description
    desc = trait.desc

    # Get the trait type
    trait_id = trait_ids(trait)

    if trait.output and isinstance(trait.trait_type,
                                   (traits.api.File, traits.api.Directory)):
        if trait.input_filename is False:
            trait_id[0] += ' (filename: output)'
        else:
            trait_id[0] += ' (filename: input)'

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
    #if not trait.output:
    line += " ({0} - {1}{2})".format(trait_id, dtype, def_val)

    # Wrap the string properly
    if use_wrap:
        manhelpstr = wrap(line, 70,
                          initial_indent=manhelpstr[0] + ": ",
                          subsequent_indent="    ")
    else:
        manhelpstr = [manhelpstr[0] + ": " + line]

    # Add the trait description if specified
    if desc:
        for line in desc.split("\n"):
            # line = re.sub("\s+", " ", line)
            if use_wrap:
                indent = ''
                s = line.strip()
                if s:
                    # keep text indentation
                    indent = line[:line.index(s[0])]
                wline = wrap(line, 70, initial_indent="    ",
                            subsequent_indent="    " + indent)
                if len(wline) == 0:
                    # don't skip empty lines
                    wline = ['']
            else:
                wline = ['    ' + line]
            manhelpstr += wline
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
                                          traits.api.TraitCoerceType,
                                          traits.api.TraitHandler)):
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
        if handler.aClass is type(traits.api.Undefined):
            return ['Undefined']
        inner_id2 = _type_to_trait_id.get(handler.aClass)
        if inner_id2:
            return [inner_id2]
        inner_id = handler.aClass.__name__
        mod = handler.aClass.__module__
        if mod not in ("__builtin__", "__builtins__", "builtins"):
            modules.add(mod)
            inner_id = '.'.join((mod, inner_id))
        return [main_id + "_" + inner_id]

    elif handler is type(traits.api.Undefined):
        return ['Undefined']

    # Default case
    else:
        if not hasattr(handler, 'inner_traits'):
            return [main_id]

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

def is_file_trait(trait, allow_dir=False, only_dirs=False):
    """
    Tells if the given trait is a File (and/or dict) or may be a file (for a
    compound trait)
    """
    ids = trait_ids(trait)
    if not only_dirs and any(['File' in x for x in ids]):
        return True
    if allow_dir and any(['Directory' in x for x in ids]):
        return True
    return False

def relax_exists_constraint(trait):
    """ Relax the exist constraint of a trait

    Parameters
    ----------
    trait: trait
        a trait that will be relaxed from the exist constraint
    """
    # If we have a single trait, just modify the 'exists' contrain
    # if specified
    if hasattr(trait.handler, "exists"):
        trait.handler.exists = False

    # If we have a selector, call the 'relax_exists_constraint' on each
    # selector inner components.
    main_id = trait.handler.__class__.__name__
    if main_id == "TraitCompound":
        for sub_trait in trait.handler.handlers:
            sub_c_trait = traits.api.CTrait(0)
            sub_c_trait.handler = sub_trait
            relax_exists_constraint(sub_c_trait)
    elif len(trait.inner_traits) > 0:
        for sub_c_trait in trait.inner_traits:
            relax_exists_constraint(sub_c_trait)
