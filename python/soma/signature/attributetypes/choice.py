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

import types

from soma.translation import translate as _
from soma.signature.api import DataType, Undefined

#-------------------------------------------------------------------------------
class Choice( DataType ):
  '''Parameter value is a list of values choosen in a predefined value set.'''

  def __init__( self, *args ):
    '''Each parameter is either a single value which is append in the possible
    values set or a tuple containing a pair of ( label, value ).'''
    DataType.__init__( self )
    self.mutable = False
    self.setChoices( *args ) 
  
  
  def setChoices( self, *args ):
    '''Change the possible choices.'''

    self.values = []
    self.labels = []
    for p in args:
      if type( p ) in ( types.TupleType, types.ListType ) and \
         len( p ) == 2:
        label, value = p
      else:
        label, value = unicode( p ), p
      if label in self.labels:
        raise KeyError( _( 'label "%s" is used twice' ) % ( label, ) )
      i = None
      try:
        i = self.values.index( value )
      except ValueError:
        pass
      if i is not None:
        if label != self.labels[ i ]:
          raise KeyError( _( 'Choice value %(value)s already set with label'\
                               ' %(label)s' ) \
                          % { 'value': str( value ), 
                              'label': self.labels[ i ] } )
      else:
        self.values.append( value )
        self.labels.append( label )
          
    
  def checkValue( self, value ):
    i = self.findIndex( value )
    if i == -1:
      raise ValueError( _('%s is not a valid Choice value') % repr(value) )
    return self.values[ i ]

  
  def findIndex( self, value ):
    try:
      return self.values.index( value )
    except ValueError:
      try:
        return self.labels.index( value )
      except ValueError:
        pass
    return -1

  
  def convert( self, value, checkValue=None ):
    if checkValue is None:
      checkValue = self.checkValue
    try:
      return checkValue( value )
    except ValueError:
      if isinstance( type, basestring ):
        try:
          index = [unicode( i ) for i in self.values].index( value )
          return self.values[ index ]
        except ValueError:
            pass
    self._convertError( value )
  
  
  def __getinitkwargs__( self ):
    args, kwargs = DataType.__getinitkwargs__( self )
    args = [( name, type ) for name, type in zip( self.labels, self.values )]
    return ( args, kwargs )


  def copy( self ):
    return apply( self.__class__, zip( self.labels, self.values ) )


  def createValue( self ):
    return self.values[ 0 ]
