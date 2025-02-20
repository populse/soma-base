"""
Writing of XML minf format.
"""

__docformat__ = "restructuredtext en"

import codecs
from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import quoteattr as xml_quoteattr
from soma.translation import translate as _
from soma.minf.tree import createMinfReducer
from soma.minf.writer import MinfWriter
from soma.minf.tree import minfStructure, listStructure, dictStructure, \
    StartStructure, EndStructure
from soma.minf.error import MinfError
from soma.undefined import Undefined
import sys
import gc

from soma.minf.error import MinfError
from soma.minf.tree import (
    EndStructure,
    StartStructure,
    createMinfReducer,
    dictStructure,
    listStructure,
)
from soma.minf.writer import MinfWriter

# This module only contains a definition of XML tags and attributes.
# It is designed to allow "import *".
from soma.minf.xml_tags import *
from soma.translation import translate as _
from soma.undefined import Undefined

#: Replacement table for characters that are not allowed in XML
xml_replacement = dict(
    [(eval('"\\x' + ("0" + hex(i)[2:])[-2:] + '"'), "") for i in range(32)]
)
del xml_replacement["\x09"]
del xml_replacement["\x0a"]
del xml_replacement["\x0d"]


# ------------------------------------------------------------------------------
class MinfXMLWriter(MinfWriter):
    """
    Specialization of L{MinfWriter} class for writing XML minf format.
    """

    name = "XML"

    def __init__(self, file, reducer,
                 encoding='utf-8',
                 level=0,
                 append=False,
                 close_file=False):
        self.__file = file
        self.reducer = createMinfReducer(reducer)
        self.encoder = codecs.getencoder(encoding)
        self.level = level
        self.indentString = '  '
        self.__close_file = close_file
        if not append:
            self._writeLine(
                '<?xml version="1.0" encoding=' + xml_quoteattr(encoding) + " ?>"
            )
            self._encodeAndWriteLine(
                "<"
                + minfTag
                + " "
                + expanderAttribute
                + "="
                + xml_quoteattr(reducer)
                + ">"
            )

    def close(self):
        """Close the Minf syntax tree. The underlying file is NOT closed."""
        if self.__file is not None:
            self.__file.flush()
            self._encodeAndWriteLine('</' + minfTag + '>')
            if self.__close_file:
                self.__file.close()
            self.__file = None

    def write(self, value):
        minfNodeIterator = self.reducer.reduce(value)
        for minfNode in minfNodeIterator:
            self._write(minfNodeIterator, minfNode, 0, None)

    def _write(self, minfNodeIterator, minfNode, level, name):
        if minfNode is Undefined:
            minfNode = next(minfNodeIterator)
        attributes = {}
        if name is not None:
            attributes[nameAttribute] = name
        if isinstance(minfNode, StartStructure):
            if minfNode.type == listStructure:
                naming = False
                stringNaming = False
                length = minfNode.attributes.get("length")
                if length:
                    attributes[lengthAttribute] = length
                tag = listTag
            elif minfNode.type == dictStructure:
                naming = True
                stringNaming = False
                length = minfNode.attributes.get("length")
                if length:
                    attributes[lengthAttribute] = length
                tag = dictionaryTag
            else:
                naming = True
                stringNaming = True
                tag = factoryTag
                attributes[objectTypeAttribute] = minfNode.type
            if attributes:
                attributes = " " + " ".join(
                    [n + "=" + xml_quoteattr(str(v)) for n, v in attributes.items()]
                )
            else:
                attributes = ""
            self._encodeAndWriteLine("<" + tag + attributes + ">", level)
            ntype = minfNode.type
            for minfNode in minfNodeIterator:
                if isinstance(minfNode, EndStructure):
                    if ntype != minfNode.type:
                        raise MinfError(
                            _(
                                "Wrong Minf structure ending, expecting %(exp)s instead of %(rcv)s"
                            )
                            % {"exp": ntype, "rcv": minfNode.type}
                        )
                    self._encodeAndWriteLine("</" + tag + ">", level)
                    break
                elif naming:
                    if isinstance(minfNode, str):
                        self._write(minfNodeIterator, Undefined, level + 1, minfNode)
                    elif minfNode is None:
                        if not stringNaming:
                            self._write(minfNodeIterator, minfNode, level + 1, None)
                        self._write(minfNodeIterator, Undefined, level + 1, None)
                    else:
                        self._write(minfNodeIterator, minfNode, level + 1, None)
                        self._write(minfNodeIterator, Undefined, level + 1, None)
                else:
                    self._write(minfNodeIterator, minfNode, level + 1, None)
        elif isinstance(minfNode, EndStructure):
            raise MinfError(
                _("Unexpected Minf structure ending: %s") % (minfNode.type,)
            )
            level -= 1
        else:
            if attributes:
                attributesXML = " " + " ".join(
                    [n + "=" + xml_quoteattr(str(v)) for n, v in attributes.items()]
                )
            else:
                attributesXML = ""
            if minfNode is None:
                self._encodeAndWriteLine("<" + noneTag + attributesXML + "/>", level)
            elif isinstance(minfNode, bool):
                if minfNode:
                    self._encodeAndWriteLine(
                        "<" + trueTag + attributesXML + "/>", level
                    )
                else:
                    self._encodeAndWriteLine(
                        "<" + falseTag + attributesXML + "/>", level
                    )
            elif isinstance(minfNode, (float, int)):
                self._encodeAndWriteLine(
                    "<"
                    + numberTag
                    + attributesXML
                    + ">"
                    + str(minfNode)
                    + "</"
                    + numberTag
                    + ">",
                    level,
                )
            elif isinstance(minfNode, (str, bytes)):
                if isinstance(minfNode, bytes):
                    try:
                        minfNode = minfNode.decode("utf-8")
                    except UnicodeDecodeError:
                        minfNode = minfNode.decode("iso-8859-1")
                self._encodeAndWriteLine(
                    "<"
                    + stringTag
                    + attributesXML
                    + ">"
                    + xml_escape(minfNode, xml_replacement)
                    + "</"
                    + stringTag
                    + ">",
                    level,
                )
            elif hasattr(minfNode, "__minfxml__"):
                minfNode.__minfxml__(self, attributes, level)
            else:
                raise MinfError(
                    _("Cannot save an object of type %s as an XML atom")
                    % (str(type(minfNode)),)
                )

    def _encodeAndWriteLine(self, line, level=0):
        self._writeLine(self.encoder(line)[0], level=level)

    def _writeLine(self, line, level=0):
        if self.level is None:
            indent = ""
            nl = ""
            level = None
        else:
            indent = self.indentString * (self.level + level)
            nl = "\n"
        if isinstance(line, bytes):
            line = line.decode("utf8")
        try:
            self.__file.write(indent + line + nl)
        except TypeError:
            # in python3 writing in a binary stream needs to write byte
            # objects, not strings.
            # however there is no [obvious] way to know if the file object
            # is open in string or binary mode, and thus what it expects.
            # if you want my opinion, it's completely crazy...
            self.__file.write((indent + line + nl).encode())

    def flush(self):
        self.__file.flush()

    def change_file(self, file):
        self.__file = file
