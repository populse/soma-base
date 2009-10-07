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
Base classes for writing various minf formats (XML, HDF5, Python's pickle, etc.)

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

__docformat__ = "epytext en"

from soma.translation import translate as _


#------------------------------------------------------------------------------
class RegisterMinfWriterClass( type ):
  '''
  RegisterMinfWriterClass is used as metaclass of L{MinfWriter} to automatically
  register all classes derived from L{MinfWriter}.
  '''
  def __init__( cls, name, bases, dict ):
    if cls.name is not None:
      MinfWriter._allWriterClasses[ cls.name ] = cls


#------------------------------------------------------------------------------
class MinfWriter( object ):
  '''
  Class derived from MinfWriter are responsible of writing a specific format of
  minf file. This version only support XML format but other formats may 
  be added later (such as HDF5).
  All classes derived from L{MinfWriter} must define a L{name} class attribute
  the following methods:
    - L{__init__} to construct writer instances.
    - L{write} to write objects in minf file.
    - L{close} to terminate writing and close the min file.
  '''
  
  __metaclass__ = RegisterMinfWriterClass
  
  #: all classes derived from L{MinfWriter} are automatically stored in that
  #: dictionary (keys are formats name and values are class objects).
  _allWriterClasses = {}
  
  #: class derived from L{MinfWriter} must set a format name in this attribute.
  name = None
  
  
  def __init__( self, file, reducer ):
    '''
    Constructor of classes derived from L{MinfWriter} must be callable with two
    parameters.
    @param file: file object (opened for writing) where the minf file is 
      written.
    @type  file: any object respecting Python file object API
    @param reducer: name of the reducer to use (see L{soma.minf.tree} for 
      more information about reducers).
    @type  reducer: string
    '''
  
  
  def write( self, value ):
    '''
    Write an object into the minf file.
    @param value: any value that can be written in this minf file.
    '''
    
    
  def close( self ):
    '''
    Close the writer, further calls to L{write} method will lead to an error.
    '''
  
  
  def createWriter( destFile, format, reducer ):
    '''
    This static method create a L{MinfWriter} instance by looking for a 
    registered L{MinfWriter} derived classe named C{format}. Parameters
    C{destFile} and C{reducer} are passed to the derived class constructor. 
    @param format: name of the minf format.
    @type  format: string
    @returns: L{MinfWriter} derived class instance.
    @param file: file name or file object (opened for writing) where the minf
      file is written. If it is a file name, it is opened with
      C{open( destFile, 'wb' )}.
    @type  file: string or any object respecting Python file object API
    @param reducer: name of the reducer to use (see L{soma.minf.tree} for 
      more information about reducers).
    @type  reducer: string
    '''
    writer = MinfWriter._allWriterClasses.get( format )
    if writer is None:
      raise( _( 'No minf writer for format "%(format)s", possible formats are: %(possible)s' ) % \
             { 'format': format, 'possible': ', '.join( ['"' + i + '"' for i in MinfWriter._allWriterClasses ] ) } )
    if not hasattr( destFile, 'write' ):
      destFile = open( destFile, 'w' )
    return writer( destFile, reducer, )
  createWriter = staticmethod( createWriter )

