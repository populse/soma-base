# -*- coding: utf-8 -*-

import sys

from .Str import StrControlWidget
from .Bytes import BytesControlWidget
from .Float import FloatControlWidget
from .Int import IntControlWidget
from .Enum import EnumControlWidget
from .List import ListControlWidget
from .List_File_offscreen import OffscreenListFileControlWidget
from .Bool import BoolControlWidget
from .File import FileControlWidget
from .Directory import DirectoryControlWidget
from .Dict import DictControlWidget
from .Controller import ControllerControlWidget
from .Compound import CompoundControlWidget
from .non_editable import NonEditableControlWidget


# Define a structure that will contain the mapping between the string trait
# descriptions and the associated control classes
controls = {}


def range_editor(trait):
    t = type(trait.default)
    if t is int:
        return IntControlWidget
    if sys.version_info[0] >= 3:
        long = int  # this is only a trick to fool flake8
    elif t is long:
        return IntControlWidget
    return FloatControlWidget


# Register all control class
controls["str"] = StrControlWidget
controls["bytes"] = BytesControlWidget
controls["any"] = StrControlWidget
controls["float"] = FloatControlWidget
controls["int"] = IntControlWidget
controls["literal"] = EnumControlWidget
controls["bool"] = BoolControlWidget
controls["file"] = FileControlWidget
controls["directory"] = DirectoryControlWidget
controls["list"] = ListControlWidget
controls["controller"] = ControllerControlWidget
controls["dict"] = DictControlWidget
controls["union"] = CompoundControlWidget
controls["list[file]"] = OffscreenListFileControlWidget
controls["range"] = range_editor
controls["unknown"] = NonEditableControlWidget
