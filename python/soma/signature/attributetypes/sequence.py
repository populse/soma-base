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

from soma.translation import translate as _
from soma.signature.api import DataType

class Sequence ( DataType ):
  
  def __init__( self, elementType, minSize = 0, maxSize = None ):
    ''' 
    A L{Sequence} is a L{DataType} for Python sequence whose elements are all 
    of the same type.
    
    @type  elementType: any value accepted by L{DataType.dataTypeInstance}
    @param elementType: type of all elements in the sequence
    @type  minSize: positive integer
    @param minSize: minimum number of elements in the sequence (default = 0)
    @type  maxSize: None or positive integer
    @param maxSize: maximum number of elements in the sequence. If value is 
    C{None} (the default), there is no limit on the sequence size.
    '''
    DataType.__init__( self )
    
    if ( ( minSize is None ) or ( minSize < 0 ) ):
      #: minimum number of elements in the sequence
      self.minSize = 0
    else:
      self.minSize = int( minSize )
      
    if ( ( maxSize is None ) or ( maxSize < 0 ) ):
      #: maximum number of elements in the sequence or C{None} for no limit.
      self.maxSize = None
    else:
      self.maxSize = int( maxSize )
    #: Type of the elements of the sequence (L{DataType} instance)
    self.elementType = DataType.dataTypeInstance( elementType )
  
  
  def __getinitkwargs__( self ):
    args, kwargs = DataType.__getinitkwargs__( self )
    if self.minSize > 0:
      kwargs[ 'minSize' ] = self.minSize
    if self.maxSize is not None:
      kwargs[ 'maxSize' ] = self.maxSize
    return ( self.elementType, ), kwargs
  
  
  def checkValue( self, value ):
    '''
    Check the size and the element type of the sequence in C{value}. 
    '''
    if ( self.minSize is not None and len( value ) < self.minSize ) or \
      ( self.maxSize is not None and len( value ) > self.maxSize ):
      raise ValueError( _( 'Size of sequence should be between %(minSize)i '\
                             ' and %(maxSize)i, but got %(len)d element(s)' ) \
                        % { 'minSize': self.minSize, 
                            'maxSize': self.maxSize,
                            'len': len( value ) } )
      
    try :
      # Check datatype for each element of the Sequence
      for element in value :
        self.elementType.checkValue( element )
    except ValueError, e:
      raise ValueError( _('One element of a sequence has an invalid value: %(errorMessage)s') % { 'errorMessage': str( e ) } )
    return value


  def createValue( self ):
    return []


