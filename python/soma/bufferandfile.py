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
:py:class:`BufferAndFile` instances are used to read data from a file (for 
instance for identification) and "put back" the data on the file. 

- author: Yann Cointepas
- organization: `NeuroSpin <http://www.neurospin.org>`_ and 
  `IFR 49 <http://www.ifr49.org>`_
- license: `CeCILL version 2 <http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>`_
'''
__docformat__ = 'restructuredtext en'

#------------------------------------------------------------------------------
class BufferAndFile( object ):
  '''
  This class is a read only file-like object that allows to read ahead and
  push data back into the stream. All pushed back data are stored in a buffer
  that is "read" by all subsequent read acces until it is empty. When the
  buffer is empty, reading is done directly on the attached file object.
  
  Example::
      
    from soma.bufferandfile import BufferAndFile
    
    # Open a file with a buffer
    f = BufferAndFile.open( fileName )
    # Check that the file content is XML
    start = f.read( 5 )
    # Put back the read characters
    f.unread( start )
    if start == '<?xml':
      # Use the file in an XML parser
      ...
    elif start == '&HDF':
      # Use the file in an HDF5 parser
      ...

  '''
  def __init__( self, file_object):
    '''
    Create a file-like object that adds an :py:meth:`unread` method to an 
    opened ``file_object``.
    '''
    super( BufferAndFile, self).__init__()
    self.__buffer = ''
    self.__file = file_object
    self.name = getattr( file_object, 'filename', 
                         getattr( file_object, 'name', '<unknown>' ) )
  
  
  def unread( self, string_value ):
    '''
    Adds data at the begining of the internal buffer. Data in the internal
    buffer will be returned by all subsequent read acces until the buffer is empty.
    '''
    self.__buffer = string_value + self.__buffer 
  
  
  def change_file( self, file_object ):
    '''
    Change the internal file object (keeps the internal buffer untouched).
    '''
    self.__file = file_object
  
  
  def clone( self ):
    '''
    Return a new L{BufferAndFile} instance with the same internale buffer and
    the same internal file object as C{self}.
    '''
    result = BufferAndFile( self.__file )
    result.__buffer = self.__buffer
    return result
  
  def read( self, size=None ):
    '''
    Read the file
    '''
    if size is None:
      result = self.__buffer + self.__file.read()
    else:
      buffer_size = len( self.__buffer )
      if buffer_size >= size:
        result = self.__buffer[ :size ]
        self.__buffer = self.__buffer[ size: ]
      else:
        result = self.__buffer + self.__file.read( size - buffer_size )
        self.__buffer = ''
    return result
  
  
  def readline( self, size=None ):
    '''
    Read one text line
    '''
    buffer_eol = self.__buffer.find( '\n' )
    if size is None:
      if buffer_eol < 0:
        result = self.__buffer + self.__file.readline()
        self.__buffer = ''
      else:
        buffer_eol += 1
        result = self.__buffer[ :buffer_eol ]
        self.__buffer = self.__buffer[ buffer_eol: ]
    else:
      if buffer_eol < 0:
        buffer_size = len( self.__buffer )
        if buffer_size >= size:
          result = self.__buffer[ :size ]
          self.__buffer = self.__buffer[ size: ]
        else:
          result = self.__buffer + self.__file.readline( size - buffer_size )
          self.__buffer = ''
      else:
        size = min( size, buffer_eol + 1 )
        result = self.__buffer[ :size ]
        self.__buffer = self.__buffer[ size: ]
    return result
  
  
  def __iter__( self ):
    '''
    Iteration protocol
    '''
    return self
  
  
  def next( self ):
    '''
    Iteration protocol
    '''
    line = self.readline()
    if not line:
      raise StopIteration
    return line


  def tell( self ):
    '''
    POsition in file
    '''
    return self.__file.tell() - len( self.__buffer )
  
  
  def seek( self, offset, whence=0 ):
    '''
    If ``whence`` is 0 or 2 (absolute seek positioning) or if offset is
    negative, internal buffer is cleared and seek is done directly on the
    internal file object. Otherwise (relative seek with a positive offset),
    internal buffer is taken into account.
    '''
    if whence == 2 or whence == 0 or offset < 0:
      self.__buffer = ''
      return self.__file.seek( offset, whence )
    else:
      buflen = len( self.__buffer )
      if offset > buflen:
        self.__buffer = ''
        return self.__file.seek( offset - buflen, whence )
      else:
        self.__buffer = self.__buffer[ offset: ]
  
  
  def open( *args, **kwargs ):
    '''
    Open a file with built-in :py:func:`python:open` and create a 
    :py:class:`BufferAndFile` instance.
    '''
    return BufferAndFile( open( *args, **kwargs ) )
  open = staticmethod( open )
