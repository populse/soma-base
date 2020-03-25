# -*- coding: utf-8 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL-B license as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.

'''
This module contains the L{XHTML} class that contains an XHTML tree that
can be saved in minf files.

* author: Yann Cointepas
* organization: `NeuroSpin <http://www.neurospin.org>`_
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import
__docformat__ = "restructuredtext en"

import types
try:
    from cStringIO import StringIO
except ImportError:
    # python3
    from io import StringIO

import six
import sys

from soma.translation import translate as _
from soma.minf.api import readMinf
from soma.minf.xml_tags import minfTag, expanderAttribute, xhtmlTag
from soma.html import lesserHtmlEscape
from xml.sax.saxutils import quoteattr as xml_quoteattr

#------------------------------------------------------------------------------


class XHTML(object):

    '''
    Instances of L{XHTML} contains the structure of an XHTML tree and can be used
    to produce an XML string or an HTML string.
    '''

    def __init__(self, tag, attributes=None, content=None):
        '''
        Construct an XHTML tree composed of a tag name, a dictionary containing
        attributes and a content composed of a series of strings and/or XHTML
        values.
        '''
        if attributes is None:
            attributes = {}
        if content is None:
            content = []
        self.tag = tag
        self.attributes = attributes
        self.content = content

    def __getinitkwargs__(self):
        d = {}
        if self.attributes:
            d['attributes'] = self.attributes
        if self.content:
            d['content'] = self.content
        return (self.tag, ), d

    def _contentXML(content):
        return ''.join([XHTML._itemXML(i) for i in content])
    _contentXML = staticmethod(_contentXML)

    def _itemXML(item):
        if isinstance(item, XHTML):
            if item.tag is None:
                # When tag is None, no tag info is produced
                # This is useful for creating XHTML converters
                # that can remove tags.
                return item._contentXML(item.content)
            else:
                result = '<' + six.text_type(item.tag)
                if item.attributes:
                    result += ' ' + ' '.join(
                        [six.text_type(a) + '="' + six.text_type(v) + '"'
                         for a, v in six.iteritems(item.attributes)])
                if item.content:
                    result += '>' + item._contentXML( item.content ) + '</' + \
                              str(item.tag) + '>'
                else:
                    result += '/>'
                return result
        else:
            return lesserHtmlEscape(item)
    _itemXML = staticmethod(_itemXML)

    def __minfxml__(self, xmlWriter, attributes, level):
        backupAttributes = self.attributes
        self.attributes = self.attributes.copy()
        self.attributes.update(attributes)
        xmlWriter._encodeAndWriteLine(self._itemXML(self), level)
        self.attributes = backupAttributes

    def buildFromHTML(html):
        '''
        Return an XHTML instance build from an HTML string.
        @param html: piece of an HTML file
        @type  html: unicode
        '''
        # html must be an unicode string. if not, we can fail to decode it because we don't know what encoding has been use to encode it.
        # try:
            # if not isinstance( html, unicode ):
                # html = unicode( html) #, 'iso-8859-1' )
        # except: # decoding of the string can fail because it isn't encoded with the default charset
                # pass
        io = StringIO()
        # when unicode string is written in a stream, default encoding is used
        # to encode it :
        html = six.ensure_str(html, 'utf-8')
        io.write(
            '<?xml version="1.0" encoding="utf-8" ?>\n<' + minfTag + ' ' +
            expanderAttribute + '="minf_2.0">\n<' + xhtmlTag + '>' +
            html + '</' + xhtmlTag + '>\n</' + minfTag + '>')
        io.seek(0)
        return readMinf(io)[0]
    buildFromHTML = staticmethod(buildFromHTML)

    def xml(item):
        '''
        Build an XML unicode string based on either an XML string (in that case it
        is returned as is) or an XHTML instance.
        @param item: value to convert in XML.
        @type  item: XHTML instance or unicode containing XML
        '''
        if isinstance(item, six.string_types):
            return item
        elif isinstance(item, XHTML):
            return item._itemXML(item)
        else:
            raise RuntimeError(
                _('Cannot use XHTML converter for %s') % (str(item),))
    xml = staticmethod(xml)

    def html(item):
        '''
        Build an HTML unicode string based on either an HTML string (in that case it
        is returned as is) or an XHTML instance.
        @param item: value to convert in HTML.
        @type  item: XHTML instance or unicode containing HTML
        '''
        if isinstance(item, six.string_types):
            return item
        elif isinstance(item, XHTML):
            return item._contentXML(item.content)
        else:
            raise RuntimeError(
                _('Cannot use XHTML converter for %s') % (six.text_type(item),))
    html = staticmethod(html)
