# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
#
# This software is governed by the CeCILL license version 2 under 
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
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
# knowledge of the CeCILL license version 2 and that you accept its terms.

'''
L{BufferAndFile} instances are used to read data from a file (for instance
for identification) and "put back" the data on the file. 

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

#------------------------------------------------------------------------------
class BufferAndFile( object ):
  '''
  This class is a read only file-like object that allows to read ahead and
  push data back into the stream. All pushed back data are stored in a buffer
  that is "read" by all subsequent read acces until it is empty. When the
  buffer is empty, reading is done directly on the attached file object.
  
  Example:
  
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
    elif start == '\x89HDF\r':
      # Use the file in an HDF5 parser
      ...
  '''
  def __init__( self, fileObject ):
    '''
    Create a file-like object that adds an L{unread} method to an opened C{fileObject}. 
    '''
    super( BufferAndFile, self).__init__()
    self.__buffer = ''
    self.__file = fileObject
    self.name = getattr( fileObject, 'filename', getattr( fileObject, 'name', '<unknown>' ) )
  
  
  def unread( self, stringValue ):
    '''
    Adds data at the begining of the internal buffer. Data in the internal
    buffer will be returned by all subsequent read acces until the buffer is empty.
    '''
    self.__buffer = stringValue + self.__buffer 
  
  
  def changeFile( self, fileObject ):
    '''
    Change the internal file object (keeps the internal buffer untouched).
    '''
    self.__file = fileObject
  
  
  def clone( self ):
    '''
    Return a new L{BufferAndFile} instance with the same internale buffer and
    the same internal file object as C{self}.
    '''
    result = BufferAndFile( self.__file )
    result.__buffer = self.__buffer
    return result
  
  def read( self, size=None ):
    if size is None:
      result = self.__buffer + self.__file.read()
    else:
      bufferSize = len( self.__buffer )
      if bufferSize >= size:
        result = self.__buffer[ :size ]
        self.__buffer = self.__buffer[ size: ]
      else:
        result = self.__buffer + self.__file.read( size - bufferSize )
        self.__buffer = ''
    return result
  
  
  def readline( self, size=None ):
    bufferEndOfLine = self.__buffer.find( '\n' )
    if size is None:
      if bufferEndOfLine < 0:
        result = self.__buffer + self.__file.readline()
        self.__buffer = ''
      else:
        bufferEndOfLine += 1
        result = self.__buffer[ :bufferEndOfLine ]
        self.__buffer = self.__buffer[ bufferEndOfLine: ]
    else:
      if bufferEndOfLine < 0:
        bufferSize = len( self.__buffer )
        if bufferSize >= size:
          result = self.__buffer[ :size ]
          self.__buffer = self.__buffer[ size: ]
        else:
          result = self.__buffer + self.__file.readline( size - bufferSize )
          self.__buffer = ''
      else:
        size = min( size, bufferEndOfLine + 1 )
        result = self.__buffer[ :size ]
        self.__buffer = self.__buffer[ size: ]
    return result
  
  
  def __iter__( self ):
    return self
  
  
  def next( self ):
    line = self.readline()
    if not line: raise StopIteration
    return line


  def tell( self ):
    return self.__file.tell() - len( self.__buffer )
  
  
  def seek( self, offset, whence=0 ):
    '''
    If C{whence} is 0 or 2 (absolute seek positioning) or if offset is
    negative, internal buffer is cleared and seek is done directly on the
    internal file object. Otherwise (relative seek with a positive offset),
    internal buffer is taken into account.
    '''
    if whence == 2 or whence == 0 or offset < 0:
      self.__buffer = ''
      return self.__file.seek( offset, whence )
    else:
      lb = len( self.__buffer )
      if offset > lb:
        self.__buffer = ''
        return self.__file.seek( offset - lb, whence )
      else:
        self.__buffer = self.__buffer[ offset: ]
  
  
  def open( *args, **kwargs ):
    '''
    Open a file with built-in C{open} and create a L{BufferAndFile} instance.
    '''
    return BufferAndFile( open( *args, **kwargs ) )
  open = staticmethod( open )
