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
Sorted dictionary behave like a dictionary but keep the item insertion
order.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from UserDict import UserDict
from soma.undefined import Undefined

class SortedDictionary( UserDict, object ):
  '''
  Sorted dictionary behave like a dictionary but keep the item insertion
  order.
    
  Example::
    from SortedDictionary import SortedDictionary
    sd = SortedDictionary( ( 'fisrt', 1 ), ( 'second', 2 ) )
    sd[ 'third' ] = 3
    sd.insert( 0, 'zero', 0 )
    sd.items() == [('zero', 0), ('fisrt', 1), ('second', 2), ('third', 3)]
  '''
  def __init__( self, *args ):
    '''
    Initialize the dictionary with a list of ( key, value ) pairs.
    '''
    super(SortedDictionary, self).__init__()
    #UserDict.__init__(self)
    self.sortedKeys = []
    self.data = {}
    if len(args) == 1 and isinstance(args[0], list):
      elements = args[0] # dict / OrderedDict compatibility
    else:
      elements = args
    for key, value in elements:
      self[ key ] = value
      
  def keys( self ):
    '''
    @rtype: list
    @return: sorted list of keys
    '''
    return self.sortedKeys
  
  def items( self ):
    '''
    @rtype: list
    @return: sorted list of C{( key, value)} pairs
    '''
    return [x for x in self.iteritems()]

  def values( self ):
    '''
    @rtype: list
    @return: sorted list of values
    '''
    return [x for x in self.itervalues()]

  def __setitem__( self, key, value ):
    if not self.data.has_key( key ):
      self.sortedKeys.append( key )
    self.data[ key ] = value

  def __delitem__( self, key ):
    del self.data[ key ]
    self.sortedKeys.remove( key )

  def __getstate__( self ):
    return self.items()
    
  def __setstate__( self, state ):
    SortedDictionary.__init__( self, *state )

  def __iter__( self ):
    '''
    returns an iterator over the sorted keys
    '''
    return iter( self.sortedKeys )

  def iterkeys( self ):
    '''
    returns an iterator over the sorted keys
    '''
    return iter( self.sortedKeys )
  
  def itervalues( self ):
    '''
    returns an iterator over the sorted values
    '''
    for k in self:
      yield self[ k ]

  def iteritems( self ):
    '''
    returns an iterator over the sorted (key, value) pairs
    '''
    for k in self:
      try:
        yield ( k, self[ k ] )
      except KeyError:
        print '!SortedDictionary error!', self.data.keys(), self.sortedKeys
        raise

        
  def insert( self, index, key, value ):
    '''
    insert a ( C{key}, C{value} ) pair in sorted dictionary before position 
    C{index}. If C{key} is already in the dictionary, a C{KeyError} is raised.
    @type  index: integer
    @param index: index of C{key} in the sorted keys
    @param key: key to insert
    @param value: value associated to C{key}
    '''
    if self.data.has_key( key ):
      raise KeyError( key )
    self.sortedKeys.insert( index, key )
    self.data[ key ] = value

  def index(self, key):
   """
   Returns the index of the key in the sorted dictionary, or -1 if this key isn't in the dictionary.
   """ 
   try:
    i=self.sortedKeys.index(key)
   except:
    i=-1
   return i

  def clear( self ):
    '''
    Remove all items from dictionary
    '''
    del self.sortedKeys[:]
    self.data.clear()


  def sort(self, func=None):
    """Sorts the dictionary using function func to compare keys.

    @type func: function key*key->int
    @param func: comparison function, return -1 if e1<e2, 1 if e1>e2, 0 if e1==e2
    """
    self.sortedKeys.sort(func)


  def compValues(self, key1, key2):
    """
    Use this comparaison function in sort method parameter in order to sort the dictionary by values.
    if data[key1]<data[key2] return -1
    if data[key1]>data[key2] return 1
    if data[key1]==data[key2] return 0
    """
    e1=self.data[key1]
    e2=self.data[key2]
    print "comp", e1, e2
    if e1 < e2:
      return -1
    elif e1 > e2:
      return 1
    return 0
  
  
  def setdefault( self, key, value=None ):
    result = self.get( key, Undefined )
    if result is Undefined:
      self[ key ] = value
      result = value
    return result


  def pop( self, key, default=Undefined ):
    if default is Undefined:
      result = self.data.pop(key)
    else:
      result = self.data.pop(key,Undefined)
      if result is Undefined:
        return default
    self.sortedKeys.remove( key )
    return result


  def popitem( self ):
    result = self.data.popitem()
    try:
      self.sortedKeys.remove( result[0] )
    except ValueError:
      pass
    return result

  
  def __repr__( self ):
    return '{' + ', '.join( repr(k)+': '+repr(v) for k, v in self.iteritems() ) + '}'
