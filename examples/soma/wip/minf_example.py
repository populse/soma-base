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

from soma.minf.api import createMinfWriter, iterateMinf, MinfError, \
  createReducerAndExpander, registerClass, readMinf
import os, tempfile


class MyClass( object ):
  '''
  This class is used to illustrate how to write custom class
  instances in a minf file.
  '''
  
  def __init__( self, arg1, arg2, kwarg1=None, kwarg2=None ):
    '''
    The constructor takes several parameters, some of them
    have default values.
    '''
    self.arg1 = arg1
    self.arg2 = arg2
    self.kwarg1 = kwarg1
    self.kwarg2 = kwarg2
  
  
  def __getinitkwargs__( self ):
    '''
    This method return the arguments to pass to self.__init__
    to get a copy of self. It returns a tuple ( args, kwargs ) where
    args is a tuple (possibly empty) containing arguments values
    and kwargs is a dictionary (possibly empty) containing named 
    arguments values.
    '''
    kwargs = {}
    if self.kwarg1 is not None:
      kwargs[ 'kwarg1' ] = self.kwarg1
    if self.kwarg2 is not None:
      kwargs[ 'kwarg2' ] = self.kwarg2
    return ( ( self.arg1, self.arg2 ), kwargs )
  
  
  def __repr__( self ):
    '''
    Print instances as they have been created. For instance: 'MyClass( 1, 2, kwarg2=3 )'
    '''
    args, kwargs = self.__getinitkwargs__()
    result = 'MyClass('
    if args or kwargs:
      result += ' ' + \
        ', '.join( ( ', '.join( (repr(i) for i in args) ),
                     ', '.join( (n+'='+repr(v) for n,v in kwargs.iteritems()) ) ) ) + \
        ' '
    result += ')'
    return result


# Create a temporary file that will be deleted at the
# end of the try: ... finally: statement.
minfFileName = tempfile.mkstemp()[ 1 ]
try:
  # Default minf format allow to save items composed
  # of the following objects:
  #   - number: instance of int, long or float
  #   - string: instance of str or unicode
  #   - boolean: instance of bool
  #   - None
  #   - list: instance of list or tuple
  #   - dictionary: instance of dict
  writer = createMinfWriter( minfFileName )
  writer.write( 'This is written in the minf file' )
  writer.write( { None: 'Nothing', 1: 'one', 2: 'two' } )
  writer.close()
  
  # Values stored in a minf file can be retrieved through
  # an iterator (or in a tuple with minf.api.readMinf).
  for value in iterateMinf( minfFileName ):
    print repr( value )
  print '-' * 70
  
  # By default custom class instances cannot be stored
  # in minf file.
  myClassInstance = MyClass( 1, 2, 3 )
  writer = createMinfWriter( minfFileName )
  try:
    writer.write( myClassInstance )
  except MinfError, e:
    print 'Intercepted error:', e
    print '-' * 70
  writer.close()
  
  # To write (respectively read) custom class instances in a minf file, 
  # the class must be registered in a reducer (respectively expander).
  # Instead of modifying the default expander and reducer (called 'minf_2.0'),
  # we create a new one (called 'example_1.0') and register our class
  # in it.
  
  # Register a new 'example_1.0' reducer and expander that is based on
  # 'minf_2.0' (and therefore will store/retreive all the values accepted
  # by this syntax).
  createReducerAndExpander( 'example_1.0', 'minf_2.0' )
  # Registration of a new class in 'example_1.0':
  #  The first parameter is the name of the reducer/expander
  #  The second parameter is the class to register
  #  The third parameter is a string that will identify the
  #  class in the minf file.
  #
  # It is possible to customize the way custom class instances are
  # stored and retrieved from a minf file. By default, writing
  # is done by using __getinitkwargs__ or __getinitargs__ method
  # of the instance and reading is done by calling the class 
  # constructor with the parameters returned by __getinitkwargs__
  # or __getinitargs__.
  registerClass( 'example_1.0', MyClass, 'MyClass' )
  
  # Now it is possible to write/read custom class instances
  writer = createMinfWriter( minfFileName, reducer='example_1.0' )
  writer.write( myClassInstance )
  writer.close()
  print readMinf( minfFileName )
  
finally:
  os.remove( minfFileName )

