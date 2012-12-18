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
This module contains all the framework necessary to customize, read and
write minf files. A minf file is composed of structured data saved in
XML or Python format. The minf framework provides tools to read and write
minf files but also to customize the way Python objects are read an written.

There are several submodules in this package but main functions and classes
can be imported from C{soma.minf.api}:
  - for reading minf files: L{iterateMinf}, L{readMinf}
  - for writing minf files: L{createMinfWriter}, L{writeMinf}
  - for customizing minf files: L{createReducerAndExpander}, L{registerClass}, L{registerClassAs}

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "restructuredtext en"


import gzip


from soma.translation import translate as _
from soma.minf.error import MinfError
from soma.bufferandfile import BufferAndFile
from soma.minf.reader import MinfReader
from soma.minf.writer import MinfWriter
from soma.minf.tree import createReducerAndExpander, registerClass, \
                            registerClassAs, createMinfExpander, \
                            EndStructure, MinfReducer, MinfExpander, \
                            listStructure, dictStructure
from soma.undefined import Undefined
defaultReducer = MinfReducer.defaultReducer


#------------------------------------------------------------------------------
def minfFormat( source ):
  '''
  Return a pair C{( format, reduction )} identifying the minf format. If
  C{source} is not a minf file, C{( None, None )} is returned. Otherwise,
  C{format} is a string representing the format of the minf file: C{'XML'} or
  C{'python'}. C{reduction} is the name of the reducer used to write the minf
  file or C{None} if format is C{'python'}.

  Example::
    from soma.minf.api import minfFormat
    format, reduction = minfFormat( '/home/me/test.minf' )

  If C{source} is a L{BufferAndFile} instance, this call behave as if nothing
  has been read from the file. This can be useful if you have an opened file
  that cannot be seeked backward:

  Example::
    from soma.bufferandfile import BufferAndFile
    from soma.minf.api import minfFormat, readMinf

    bf = BufferAndFile( stream_file_object )
    format, reduction = minfFormat( bf )
    if format is not None:
      minfContent = readMinf( bf )


  @param source: Input file name or file object. If it is a file name, it is
    opened with C{open( source )}.
  '''
  if not hasattr( source, 'readline' ):
    source = BufferAndFile( open( source ) )
  elif not isinstance( source, BufferAndFile ):
    source.seek(0)
    source = BufferAndFile( source )

  # Check first non white character to see if the minf file is XML or not
  start = source.read( 5 )
  if start == 'attri':
    source.unread( start )
    return ( 'python', None )
  elif start != '<?xml':
    # Try gzip compressed file
    gzipSource = source.clone()
    gzipSource.unread( start )
    gunzipSource = gzip.GzipFile( source.name ) 
    try:
      start = gunzipSource.read( 5 )
    except IOError:
      start = ''
    if start != '<?xml':
      raise MinfError( _( 'Invalid minf file: %s' ) % ( source.name, ) )
    source.change_file( gunzipSource )
    source.unread( start )
  else:
    source.unread( start )

  r = MinfReader.createReader( 'XML' )
  reduction, buffer = r.reduction( source )
  source.unread( buffer )
  return( 'XML', reduction )


#------------------------------------------------------------------------------
def _setTarget( target, source ):
  from soma.signature.api import HasSignature
  if isinstance( source, dict ):
    if isinstance( target, dict ):
      target.update( source )
      return True
    elif isinstance( target, HasSignature ):
      for k, v in source.iteritems():
        attrTarget = getattr( target, k, Undefined )
        if attrTarget is Undefined:
          setattr( target, k, v )
        else:
          if not _setTarget( attrTarget, v ):
            setattr( target, k, v )
      return True
  return False
  
  
#------------------------------------------------------------------------------
def iterateMinf( source, targets=None, stop_on_error=True, exceptions=[] ):
  '''
  Returns an iterator over all objects stored in a minf file.

  Example::
    from soma.minf.api import iterateMinf

    for item in iterateMinf( 'test.minf' ):
      print repr( item )

  @param source: Input file name or file object. If it is a file name, it is
    opened with C{open( source )}.
  '''
  if targets is not None:
    targets = iter( targets )
  if not hasattr( source, 'readline' ):
    source = BufferAndFile( open( source ) )
  elif not isinstance( source, BufferAndFile ):
    source.seek(0)
    source = BufferAndFile( source )

  # Check first non white character to see if the minf file is XML or not
  start = source.read( 5 )
  source.unread( start )
  if start == 'attri':
    try:
      import numpy
      d = { 'nan' : numpy.nan }
    except:
      d = { 'nan' : None }
    try:
      exec source.read().replace("\r\n", "\n") in d
    except Exception, e:
      x = source
      if hasattr( source, '_BufferAndFile__file' ):
        x = source._BufferAndFile__file
      x = 'Error in iterateMinf while reading ' + str(x) + ': '
      msg = x + e.message
      # e.message = msg
      # e.args = ( x + e.args[0], ) + e.args[1:] 
      print x
      raise
    minf = d[ 'attributes' ]
    if targets is not None:
      result = targets.next()
      _setTarget( result, minf )
      yield result
    else:
      yield minf
    return
  elif start != '<?xml':
    # Try gzip compressed file
    gzSource = gzip.GzipFile( source.name )
    if gzSource.read( 5 ) != '<?xml':
      raise MinfError( _( 'Invalid minf file: %s' ) % ( source.name, ) )
    source = BufferAndFile( gzSource )
    source.unread( '<?xml' )

  r = MinfReader.createReader( 'XML' )
  iterator = r.nodeIterator( source )
  minfNode = iterator.next()
  expander = createMinfExpander( minfNode.attributes[ 'reduction' ] )
  count = 0
  for nodeItem in iterator:
    count += 1
    if isinstance( nodeItem, EndStructure ):
      break
    target = None
    if targets is not None:
      try:
        target = targets.next()
      except StopIteration:
        targets = None
    yield expander.expand( iterator, nodeItem, target=target, stop_on_error=stop_on_error, exceptions=exceptions )

#------------------------------------------------------------------------------
def readMinf( source, targets=None, stop_on_error=True, exceptions=[] ):
  '''
  Entirerly reads a minf file and returns its content in a tuple.
  Equivalent to C{tuple( iterateMinf( source ) )}.
  @see: L{iterateMinf}
  '''
  return tuple( iterateMinf( source, targets=targets, stop_on_error=stop_on_error, exceptions=exceptions ) )


#------------------------------------------------------------------------------
def createMinfWriter( destFile, format='XML', reducer='minf_2.0' ):
  '''
  Create a writer for storing objects in destFile.
  Example::
    from soma.minf.api import createMinfWriter
    writer = createMinfWriter( '/tmp/test.minf' )
    writer.write( 'A string' )
    writer.write( { 'A dict key': [ 'A list', 'with two elements' ] } )
    writer.close()
  @param format: name of the format to write.
  @type  format: string
  @param reducer: name of the reducer to use (see L{soma.minf.tree} for
    more information about reducers).
  @type  reducer: string
  '''
  return MinfWriter.createWriter( destFile, format, reducer )


#------------------------------------------------------------------------------
def writeMinf( destFile, args, format='XML', reducer=None ):
  '''
  Creates a minf writer with L{createMinfWriter} and write the content
  of C{args} in it.

  @param destFile: see L{createMinfWriter}
  @param args: series of values to write
  @type  args: sequence or iterator
  @param format: see L{createMinfWriter}
  @param reducer: see L{createMinfWriter}
  '''
  it = iter( args )
  try:
    firstItem = it.next()
  except StopIteration:
    firstItem = Undefined
  if reducer is None:
    if firstItem is not Undefined:
      reducer = MinfReducer.defaultReducer( firstItem )
      if reducer is None:
        reducer = 'minf_2.0'
      
  writer = createMinfWriter( destFile, format, reducer )
  if firstItem is not Undefined:
    writer.write( firstItem )
    for item in it:
      writer.write( item )
  writer.close()


#------------------------------------------------------------------------------
# xml_reader and xml_writer are not used directly but importing
# them register the XML minf format
import soma.minf.xml_reader
import soma.minf.xml_writer


#------------------------------------------------------------------------------
from soma.minf.xhtml import XHTML
from soma.uuid import Uuid

minf_2_0_reducer = MinfReducer( 'minf_2.0' )
minf_2_0_reducer.registerAtomType( None.__class__ )
minf_2_0_reducer.registerAtomType( bool )
minf_2_0_reducer.registerAtomType( int )
minf_2_0_reducer.registerAtomType( long )
minf_2_0_reducer.registerAtomType( float )
minf_2_0_reducer.registerAtomType( str )
minf_2_0_reducer.registerAtomType( unicode )
minf_2_0_reducer.registerAtomType( XHTML )
minf_2_0_reducer.registerClass( list, minf_2_0_reducer.sequenceReducer )
minf_2_0_reducer.registerClass( tuple, minf_2_0_reducer.sequenceReducer )
minf_2_0_reducer.registerClass( dict, minf_2_0_reducer.dictReducer )

minf_2_0_expander = MinfExpander( 'minf_2.0' )
minf_2_0_expander.registerStructure( listStructure, minf_2_0_expander.sequenceExpander )
minf_2_0_expander.registerStructure( dictStructure, minf_2_0_expander.dictExpander )

registerClass( 'minf_2.0', Uuid, 'Uuid' )


#------------------------------------------------------------------------------
minf_1_0_reducer = MinfReducer( 'minf_1.0', ( 'minf_2.0', )  )
minf_1_0_expander = MinfExpander( 'minf_1.0', ( 'minf_2.0', )  )
