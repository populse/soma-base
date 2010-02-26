# -*- coding: iso-8859-1 -*-

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
Reading of XML minf format.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys, os, operator, codecs, types, gzip
from xml.sax.saxutils import quoteattr as xml_quoteattr
from xml.sax.saxutils import escape as xml_escape
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax.handler import ErrorHandler

from soma.translation import translate as _
from soma.undefined import Undefined
from soma.minf.error import MinfError

from soma.minf.reader import MinfReader
from soma.minf.tree import minfStructure, listStructure, dictStructure, \
                            StartStructure, EndStructure, Reference
from soma.minf.xhtml import XHTML

# This module only contains a definition of XML tags and attributes.
# It is designed to allow "import *".
from soma.minf.xml_tags import *
from cStringIO import StringIO

#------------------------------------------------------------------------------
class MinfXMLReader( MinfReader, ErrorHandler ):
  '''
  Specialization of L{MinfReader} class for reading XML minf format.
  '''
  name = 'XML'
  
  class SaxHandler( ContentHandler ):
    def __init__( self, parser ):
      self.parser = parser
      self.parser._handler = MinfXMLHandler( parser )
      self.parser._stack = []
      
    def startElement( self, name, attrs ):
      # Convert to builtin Python types
      name = unicode( name )
      attrs = dict( [ (unicode(i[0]),unicode(i[1])) for i in attrs.items()  ] )
      self.parser._stack.append( name )
      self.parser._handler.startElement( self.parser, name, attrs )
    
    
    def endElement( self, name ):
      self.parser._handler.endElement( self.parser, unicode( name ) )
      self.parser._stack.pop()
    
    
    def characters( self, content ):
      self.parser._handler.characters( self.parser, unicode( content ) )
  
  
  def reduction( self, source ):
    self._nodesToProduce = []
    self._sax_parser = make_parser()
    self._sax_parser.setContentHandler( MinfXMLReader.SaxHandler( self ) )
    self._sax_parser.setErrorHandler( self )
    self._sax_parser.reset()
    self._minfStarted = False
    self._minfFinished = False
    self._nodeIdentifier = 0
    buffer = []
    while not self._nodesToProduce:
      line = source.readline()
      buffer.append( line )
      if not line:
        # end of file
        break
      self._sax_parser.feed( line )
    if self._nodesToProduce:
      return ( self._nodesToProduce[ 0 ].attributes[ 'reduction' ], ''.join(buffer) )
    return ( None, ''.join(buffer) )


  def nodeIterator( self, source ):
    self._nodesToProduce = []
    self._sax_parser = make_parser()
    self._sax_parser.setContentHandler( MinfXMLReader.SaxHandler( self ) )
    self._sax_parser.setErrorHandler( self )
    self._sax_parser.reset()
    #self._sax_parser.feed( encodingLine )
    self._minfStarted = False
    self._minfFinished = False
    self._nodeIdentifier = 0
    while not self._minfFinished:
      while self._nodesToProduce:
        node = self._nodesToProduce.pop( 0 )
        yield node
      line = source.readline()
      if not line:
        # end of file
        if not self._minfStarted:
          # Log files may be read while not finished, therefore the closing
          # tag is missing. It is append to avoid XML parser error message.
          self._sax_parser.feed( '<' + minfTag + '/>' )
        self._minfFinished = True
        break
      self._sax_parser.feed( line )
    while self._nodesToProduce:
      node = self._nodesToProduce.pop( 0 )
      yield node


  def parseError( self, errorMessage ):
    self.fatalError( errorMessage )
  
  def fatalError( self, error ):
    raise MinfError( _( 'XML parse error: %s' ) % \
                        ( unicode( error ), )  + ' (stack = ' + \
        ','.join( [ '"' + i + '"' for i in self._stack ]) + ')' )


  def checkNoMoreAttributes( self, attributes ):
    if attributes:
      self.parseError( _('Invalid attribute": %(attributes)s') %\
        { 'attributes': ', '.join( ['"' + n + '"' for n in attributes]  ) } )
  

#------------------------------------------------------------------------------
class XMLHandler:
  def __init__( self, parser, parent, name, attributes ):
    self.parent = parent
    parser.checkNoMoreAttributes( attributes )
    
  def startElement( self, parser, name, attributes ):
    parser.parseError( _( 'Unexpected tag "%s"') % ( name, ) )


  def endElement( self, parser, name ):
    parser._handler = self.parent
    self.parent = None
  
  
  def characters( self, parser, content ):
    pass


#------------------------------------------------------------------------------
class NoneXMLHandler( XMLHandler ):
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( None )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class TrueXMLHandler( XMLHandler ):
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( True )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class FalseXMLHandler( XMLHandler ):
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( False )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class NumberXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    XMLHandler.__init__( self, parser, parent, name, attributes )
    self._stringValue = []
  
  
  def characters( self, parser, content ):
    self._stringValue.append(content)
  
  
  def endElement( self, parser, name ):
    stringValue=''.join(self._stringValue)
    try: 
      value = int( stringValue )
    except:
      try: 
        value = long( stringValue )
      except:
        value = float( stringValue )
    parser._nodesToProduce.append( value )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class StringXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    XMLHandler.__init__( self, parser, parent, name, attributes )
    self._value = []
  
  
  def characters( self, parser, content ):
    self._value.append(content)
  
  
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( ''.join(self._value) )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class ListXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    length = attributes.pop( lengthAttribute, None )
    identifier = attributes.pop( identifierAttribute, None )
    if length is not None:
      parser._nodesToProduce.append( StartStructure( listStructure, 
                                                     identifier=identifier,
                                                     length=length ) )
    else:
      parser._nodesToProduce.append( StartStructure( listStructure,
                                                     identifier=identifier ) )
    XMLHandler.__init__( self, parser, parent, name, attributes )

  
  def startElement( self, parser, name, attributes ):
    newHandler = MinfXMLHandler.getHandler( parser, self, name, attributes )
    if newHandler is None:
      parser.parseError( _( 'Unexpected tag "%s"' ) % ( name, ) )
    parser._handler = newHandler
  
  
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( EndStructure( listStructure ) )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class DictionaryXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    length = attributes.pop( lengthAttribute, None )
    identifier = attributes.pop( identifierAttribute, None )
    if length is not None:
      parser._nodesToProduce.append( StartStructure( dictStructure,
                                                     identifier=identifier, 
                                                     length=length ) )
    else:
      parser._nodesToProduce.append( StartStructure( dictStructure,
                                                     identifier=identifier ) )
    XMLHandler.__init__( self, parser, parent, name, attributes )

  
  def startElement( self, parser, name, attributes ):
    nameAttr = attributes.pop( nameAttribute, None )
    if nameAttr is not None:
      parser._nodesToProduce.append( nameAttr )
    newHandler = MinfXMLHandler.getHandler( parser, self, name, attributes )
    if newHandler is None:
      parser.parseError( _( 'Unexpected tag "%s"' ) % ( name, ) )
    parser._handler = newHandler
  
  
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( EndStructure( dictStructure ) )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class FactoryXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    self.type = attributes.pop( objectTypeAttribute, None )
    if self.type is None:
      parser.parseError( _( '%s attribute missing' ) % ( objectTypeAttribute, ) )
    identifier = attributes.pop( identifierAttribute, None )
    parser._nodesToProduce.append( StartStructure( self.type, identifier=identifier ) )
    XMLHandler.__init__( self, parser, parent, name, attributes )
  
  
  def startElement( self, parser, name, attributes ):
    nameAttr = attributes.pop( nameAttribute, None )
    parser._nodesToProduce.append( nameAttr )
    newHandler = MinfXMLHandler.getHandler( parser, self, name, attributes )
    if newHandler is None:
      parser.parseError( _( 'Unexpected tag "%s"' ) % ( name, ) )
    parser._handler = newHandler
  
  
  def endElement( self, parser, name ):
    parser._nodesToProduce.append( EndStructure( self.type ) )
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class ReferenceXMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    identifier = attributes.pop( identifierAttribute, None )
    if self.type is None:
      parser.parseError( _( '%s attribute missing' ) % ( identifierAttribute, ) )
    parser._nodesToProduce.append( Reference( identifier=identifier ) )
    XMLHandler.__init__( self, parser, parent, name, attributes )
  
  
  def endElement( self, parser, name ):
    XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class XHTMLHandler( XMLHandler ):
  def __init__( self, parser, parent, name, attributes ):
    self.stack = [ XHTML( name, attributes ) ]
    self._characters = []
    XMLHandler.__init__( self, parser, parent, name, attributes )


  def characters( self, parser, content ):
    self._characters.append(content)
  
  
  def startElement( self, parser, name, attributes ):
    c = ''.join(self._characters)
    if c: self.stack[ -1 ].content.append( c )
    self._characters = []
    newItem = XHTML( name, attributes )
    self.stack[ -1 ].content.append( newItem )
    self.stack.append( newItem )
    
    
  def endElement( self, parser, name ):
    item = self.stack.pop()
    c = ''.join(self._characters)
    self._characters = []
    if c: item.content.append( c )
    if not self.stack:
      parser._nodesToProduce.append( item )
      XMLHandler.endElement( self, parser, name )


#------------------------------------------------------------------------------
class MinfXMLHandler( XMLHandler ):
  _handlers = {
    noneTag: NoneXMLHandler,
    trueTag: TrueXMLHandler,
    falseTag: FalseXMLHandler,
    numberTag: NumberXMLHandler,
    stringTag: StringXMLHandler,
    listTag: ListXMLHandler,
    dictionaryTag: DictionaryXMLHandler,
    factoryTag: FactoryXMLHandler,
    referenceTag: ReferenceXMLHandler,
    xhtmlTag: XHTMLHandler,
  }
  
  def __init__( self, parser ):
    XMLHandler.__init__( self, parser, None, minfTag, {} )
  
  
  def getHandler( parser, parent, name, attributes ):
    handler = MinfXMLHandler._handlers.get( name )
    if handler is not None:
      handler = handler( parser, parent, name, attributes )
    return handler
  getHandler = staticmethod( getHandler )
  
  
  def startElement( self, parser, name, attributes ):
    if parser._minfStarted:
      nameAttr = attributes.pop( nameAttribute, None )
      if nameAttr is None:
        if self._obsoleteFormat:
          parser.parseError( _( '%s attribute required for minf_1.0' ) % ( nameAttribute,) )
      else:
        if self._obsoleteFormat:
          parser._nodesToProduce.append( nameAttr )
        else: 
          parser.parseError( _( 'Unexpected attribute %s' ) % ( nameAttribute, ) )
      newHandler = MinfXMLHandler.getHandler( parser, self, name, attributes )
      if newHandler is None:
        parser.parseError( _( 'Unexpected tag "%s"' ) % ( name, ) )
      parser._handler = newHandler
    else:
      if  name != minfTag:
        # Document is not a minf file
        parser.parseError(
          _( 'Wrong document type, expecting "%(minf)s" instead of ' \
                '"%(other)s>"' ) % { 'minf': minfTag, 'other': name } )
      # Checking minf format
      self._obsoleteFormat = False
      expanderName = attributes.pop( expanderAttribute, None )
      if expanderName is None:
        # Compatibility with obsolete minf 1.0 XML format
        version = attributes.pop( 'version', None )
        if version is None:
          expanderName = 'minf_2.0'
        else:
          if version != '1.0':
            parser.parseError( _( 'Wrong value for attribute "version", found '
                                    '"%s" but only "1.0" is accepted' ) % \
                              ( version, ) )
          self._obsoleteFormat = True
          expanderName = 'minf_1.0'
      parser._nodesToProduce.append( StartStructure( minfStructure, reduction=expanderName ) )
      # Compatibility with obsolete minf 1.0 XML format
      if self._obsoleteFormat:
        parser._nodesToProduce.append( StartStructure( dictStructure ) )
      parser._minfStarted = True
      # Check attributes
      parser.checkNoMoreAttributes( attributes )
  
  
  def endElement( self, parser, name ):
    if  name == minfTag:
      # Compatibility with obsolete minf 1.0 XML format
      if self._obsoleteFormat:
        parser._nodesToProduce.append( EndStructure( dictStructure ) )
      parser._nodesToProduce.append( EndStructure( minfStructure ) )
      parser._minfFinished = True
    else:
      parser._nodesToProduce.append( EndStructure( minfStructure ) )

