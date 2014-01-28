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
This module provides a notification system that can be used to register 
callbacks (I{i.e} Python callables) that will all be called by a single
L{notify<Notifier.notify>} call.

@author: Yann Cointepas
@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


# Compatibility with older Python versions
import __builtin__
if not hasattr( __builtin__, 'set' ):
  from sets import Set as set

from soma.translation import translate as _
from soma.functiontools import checkParameterCount, numberOfParameterRange
from soma.undefined import Undefined
from soma.sorted_dictionary import SortedDictionary

#-------------------------------------------------------------------------------
class Notifier:
  '''
  Register a series of functions (or Notifiers instances) which are all called
  whith L{notify} method. The calling order is the registering order. If a
  Notifier is registered, its L{notify} method is called whenever 
  C{self.notify()} is called.
  '''
  def __init__( self, parameterCount=None ):
    '''
    @type  parameterCount: integer
    @param parameterCount: if not None, each registered function must be
    callable with that number of arguments (checking is done on registration).
    '''
    self._listeners = []
    self._parameterCount = parameterCount
    self._delayedNotification = None
    
  def add( self, listener ):
    '''
    Register a callable or a Notifier that will be called whenever L{notify} is
    called. If the notifier has a C{parameterCount}, 
    L{checkParameters.checkParameterCount} is used to verify that C{listener} 
    can be called with C{parameterCount} parameters.
    @type  listener: Python callable (function, method, I{etc.}) or L{Notifier} 
    instance
    @param listener: item to add to the notification list.
    '''
    
    if listener not in self._listeners:
      if self._parameterCount is not None:
        if isinstance( listener, Notifier ):
          if listener._parameterCount is not None and \
             listener._parameterCount != self._parameterCount:
            raise RuntimeError( _( 'Impossible to register a notifier with' \
                                     '%(other)d parameter(s) to a notifier ' \
                                     'with %(self)d parameter(s)' ) \
              % { 'self': self._parameterCount, 
                  'other': listener._parameterCount } )
        else:
          checkParameterCount( listener, self._parameterCount )
      self._listeners.append( listener )
      
  def remove( self, listener ):
    '''
    Remove an item from the notification list. Do nothing if C{listener} is not 
    in the list.
    @type  listener: Python callable or L{Notifier} instance
    @param listener: item previously registered with .L{add}.
    @rtype: bool
    @return; C{True} if a listener has been removed, C{False} otherwise.
    '''
    
    try:
      self._listeners.remove( listener )
      result = True
    except ValueError:
      result = False
    return result
  
  def notify( self, *args ):
    '''
    Calls all the registered items in the notification list. All the parameters 
    given to L{notify} are passed to the items in the list. For items in the 
    list that are L{Notifier} instance, their L{notify} method is called
    @see: L{delayNotification}, L{restartNotification}
    '''
    if self._delayedNotification is None:
      #if self._listeners: print '!notify!', self, ':', args, '(' + str(len( self._listeners )), 'listeners)'
      # Iterate on a copy of self._listeners because this list can be modified
      # by a listener during notification loop.
      for listener in tuple( self._listeners ):
        #print '!notify!  -->', listener
        if isinstance( listener, Notifier ):
          listener.notify( *args )
        else:
          listener( *args )
    else:
      if self._delayedNotificationIgnoreDoubles:
        if args not in self._delayedNotification:
          self._delayedNotification.append( args )
      else:
        self._delayedNotification.append( args )
  
  
  def delayNotification( self, ignoreDoubles=False ):
    '''
    Stop notification until L{restartNotification} is called. After a call to 
    L{delayNotification}, all calls to L{notify} will only store the 
    notification parameters until L{restartNotification} is called.
    @type  ignoreDoubles: C{bool}
    @param ignoreDoubles: If C{True} (the default), all calls to L{notify} with 
    the same parameters as a previous call will be ignored (I{i.e.} 
    notification will be done only once for two identical calls).
    '''
    self._delayedNotification = []
    self._delayedNotificationIgnoreDoubles = ignoreDoubles
  
  
  def restartNotification( self ):
    '''
    Restart notifications that have been delayed by L{delayNotification}. All 
    the calls to L{notify} that has been done between the call to 
    L{delayNotification} and the call to L{restartNotification}, are applied 
    immediately.
    '''
    delayedNotification = self._delayedNotification
    if delayedNotification is not None:
      self._delayedNotification = None
      for args in delayedNotification:
        self.notify( *args )
  
  
#-------------------------------------------------------------------------------
class ReorderedCall( object ):
  '''
  @todo: documentation
  '''
  def __init__( self, function, parametersOrder ):
    self._function = function
    self._order = parametersOrder
  
  
  def __call__( self, *args ):
    return self._function( *[args[i] for i in self._order] )


#-------------------------------------------------------------------------------
class VariableParametersNotifier( Notifier ):
  '''
  This class is a notifier that can register functions with various arguments
  count.
  '''
  def __init__( self, mainParameters, *otherParameters ):
    '''
    @see: L{Notifier.__init__}
    @todo: documentation
    '''
    Notifier.__init__( self, len( mainParameters ) )
    self.__parameters = {
      len( mainParameters ): range( len( mainParameters ) )
    }
    self.__min = len( mainParameters )
    self.__max = len( mainParameters )
    # Converting to list because it has the index method (which tuple has not)
    mainParameters = list( mainParameters )
    main = set( mainParameters )
    for p in otherParameters:
      other = set( p )
      if other - main:
        raise RuntimeError( _( 'Invalid parameters definition (%(other)s is' \
                                 ' not a subset of %(main)s)' ) % \
                            { 'other': str(other), 'main': str(main) } )
      if len( p ) in self.__parameters:
        raise RuntimeError( _( 'Invalid parameters definition (several sets' \
                                 ' of %d parameters defined)' ) % (len(p),) )
      self.__parameters[ len( p ) ] = [ mainParameters.index( i ) for i in p ]
      self.__min = min( self.__min, len( mainParameters ) )
  
  
  def add( self, listener ):
    '''
    @see: L{Notifier.add}
    @todo: documentation
    '''
    if isinstance( listener, Notifier ):
      realListener = listener
    else:
      min, max = numberOfParameterRange( listener )
      if max is None:
        paramCount = self.__max
      else:
        paramCount = max
      paramOrder = self.__parameters.get( paramCount )
      if paramOrder is None:
        raise RuntimeError( _( '%(f)s has an invalid parameter count ' \
                                 '(%(c)d)' ) % \
                            { 'f': str( listener ), 'c': paramCount } )
      realListener = ReorderedCall( listener, paramOrder )
    Notifier.add( self, realListener )
  
  
  def remove( self, listener ):
    '''
    @see: L{Notifier.remove}
    @todo: documentation
    '''
    
    for i in xrange( len( self._listeners ) ):
      c = self._listeners[ i ]
      if ( isinstance( c, ReorderedCall ) and c._function == listener ) or \
          c == listener:
        del self._listeners[ i ]
        return True
    return False


#-------------------------------------------------------------------------------
class ObservableAttributes( object ):
  '''
  L{ObservableAttributes} allow to track modification of attributes at 
  runtime. By registering callbacks, it is possible to be warn of the 
  modification (setting and deletion) of any attribute of the instance.
  '''
    
    
  def __init__( self, *args, **kwargs ):
    
    #: L{VariableParametersNotifier} instance notified whenever any attribute 
    #: is modified. Use L{self.onAttributeChange} to register a function on 
    #: this notifier.
#    self.__dict__[ '_onAnyAttributeChange' ] = \
#      self._createAttributeNotifier()
    super( ObservableAttributes, self ).__setattr__( '_onAnyAttributeChange',
                                                        self._createAttributeNotifier() )
    
    #: Dictionary whose keys are attribute names and values are 
    #: L{VariableParametersNotifier} instances. Whenever an attribute is 
    #: modified, the corresponding L{VariableParametersNotifier} is notified. 
    #: Use L{self.onAttributeChange} to register a function on these notifiers.
#    self.__dict__[ '_onAttributeChange' ] = {}
    super( ObservableAttributes, self ).__setattr__( '_onAttributeChange', {} )
    super( ObservableAttributes, self ).__init__( *args, **kwargs )

  def _createAttributeNotifier():
    '''
    Static method creating a L{VariableParametersNotifier} instance for 
    attribute modification notification.
    
    @see: L{notifyAttributeChange}
    '''
    return VariableParametersNotifier(
      ( 'object', 'attributeName', 'newValue', 'oldValue' ),
      (),
      ( 'newValue', ),
      ( 'newValue', 'oldValue' ),
      ( 'attributeName', 'newValue', 'oldValue' ),
    )
  _createAttributeNotifier = staticmethod( _createAttributeNotifier )  


  def notifyAttributeChange( self, name, value, oldValue=Undefined ):
    '''
    First, call functions registered for modification of the attribute named 
    C{name}, then call functions registered for modification of any attribute.
    
    @see: L{onAttributeChange}
    '''
    # Notify the change of this attribute
    if hasattr(self, '_onAttributeChange') :
      notifier = self._onAttributeChange.get( name )
      if notifier is not None:
        notifier.notify( self, name, value, oldValue )
        
    if hasattr(self, '_onAnyAttributeChange') :
      # Notify the change of one attribute
      self._onAnyAttributeChange.notify( self, name, value, oldValue )
  
  
  def __setattr__( self, name, value ):
    '''
    Change the value of attribute C{name} then calls L{notifyAttributeChange}.
    '''
    oldValue = getattr( self, name, Undefined )
    super( ObservableAttributes, self ).__setattr__( name, value )
    if value != oldValue:
      self.notifyAttributeChange( name, value, oldValue )
  
  
  def __delattr__( self, name ):
    '''
    Delete the attribute C{name} then calls L{notifyAttributeChange} with 
    C{newValue=L{Undefined}}.
    '''
    oldValue = getattr( self, name, Undefined )
    super( ObservableAttributes, self ).__delattr__( name )
    self.notifyAttributeChange( name, Undefined, oldValue )
    # Delete notifier for the deleted attribute
    self._onAttributeChange.pop( name, None )
  
  
  def onAttributeChange( self, first, second=None ):
    '''
    Register a function to be called when an attribute is modified or 
    deleted. To call the function for any attribute modification, use the 
    following syntax::
      instance.onAttributeChange( function )
    To register a function for a named attribute, use the following syntax::
      instance.onAttributeChange( attributeName, function )
    
    The registered function can have 0 to 4 parameters. Depending on its number 
    of parameters, it will be called with the following values:
      - 4 parameters: C{( object, attributeName, newValue, oldValue )}
      - 3 parameters: C{( attributeName, newValue, oldValue )}
      - 2 parameters: C{( newValue, oldValue )}
      - 1 parameter: C{( newValue )}
    Where:
      - C{object} is the object whose attribute has been modified or deleted.
      - C{attributeName} is the name of the modified or deleted attribute.
      - C{newValue} is the value of the attribute after modification or 
        C{Undefined} if the attribute has been deleted.
      - C{oldValue} is the value of the attribute before modification. If 
        the attribute where not defined, C{oldValue = L{Undefined}}.
    If the function accepts a variable number of parameters, it will be called 
    with the maximum number of arguments possible.
    '''
    if second is None:
      if hasattr(self, '_onAnyAttributeChange') :
        self._onAnyAttributeChange.add( first )
    else:
      if hasattr(self, '_onAttributeChange') :
        notifier = self._onAttributeChange.get( first )
        if notifier is None:
          notifier = self._createAttributeNotifier()
          self._onAttributeChange[ first ] = notifier
        notifier.add( second )
  
  
  def removeOnAttributeChange( self, first, second=None ):
    '''
    Remove a function previously registered with L{onAttributeChange}. To 
    remove a function, the arguments of L{removeOnAttributeChange} must be the 
    same as those passed to L{onAttributeChange} to register the function.
    '''
    if second is None:
      result = self._onAnyAttributeChange.remove( first )
    else:
      result = self._onAttributeChange[ first ].remove( second )
    return result
  
  
  def delayAttributeNotification( self, ignoreDoubles=False ):
    '''
    Stop attribute modification notification until 
    L{restartAttributeNotification} is called. After a call to 
    L{delayAttributeNotification}, all modification notification will only be 
    stored until L{restartAttributeNotification} is called. This call is 
    recursive on all attributes values that are instance of 
    L{ObservableAttributes}.
    
    @type  ignoreDoubles: C{bool}
    @param ignoreDoubles: If C{True} (C{False} is the default), all 
      notification with the same parameters as a previous notification will be 
      ignored (I{i.e.} notification will be done only once for two identical 
      events).
    '''
    self._delayAttributeNotification( ignoreDoubles=ignoreDoubles, checkedObjects = set() )

  def _delayAttributeNotification( self, ignoreDoubles=False, checkedObjects = None ):

    if not checkedObjects == None :
      checkedObjects.add( self )
    
    for name, notifier in self._onAttributeChange.iteritems():
      notifier.delayNotification( ignoreDoubles )
    self._onAnyAttributeChange.delayNotification( ignoreDoubles )

    # Recursively delay notification
    for name in dir( self ):
      value = getattr( self, name, Undefined )

      if isinstance( value, ObservableAttributes ):
        if not checkedObjects is None :
          # This allow to not recursively call _delayAttributeNotification
          if not value in checkedObjects :
            value._delayAttributeNotification( ignoreDoubles=ignoreDoubles, checkedObjects=checkedObjects )
        else :
          value._delayAttributeNotification( ignoreDoubles=ignoreDoubles )

    if not checkedObjects == None :
      checkedObjects.pop()

  def restartAttributeNotification( self ):
    '''
    Restart notifications that have been delayed by 
    L{delayAttributeNotification}. All the modifications that happened between 
    the call to L{delayAttributeNotification} and the call to 
    L{restartAttributeNotification}, are notified immediately.
    '''
    self._restartAttributeNotification( checkedObjects = set() )

  def _restartAttributeNotification( self, checkedObjects = None ):

    if not checkedObjects == None :
      checkedObjects.add( self )
      
    for name, notifier in self._onAttributeChange.iteritems():
      notifier.restartNotification()
    self._onAnyAttributeChange.restartNotification()
    # Recursively restart notification
    for name in dir( self ):
      value = getattr( self, name, Undefined )
      if isinstance( value, ObservableAttributes ):
        if not checkedObjects is None :
          # This allow to not recursively call _delayAttributeNotification
          if not value in checkedObjects :
            value.restartAttributeNotification()
        else :
          value._delayAttributeNotification( ignoreDoubles=ignoreDoubles )

    if not checkedObjects == None :
      checkedObjects.pop()

#----------------------------------------------------------------------------
class ObservableList(list):
  """
  A list that notifies its changes to registred listeners.
  Inherits from python list and contains an instance of L{soma.notification.Notifier} (onChangeNotifier).

  Example::

  l=ObservableList()
  l.addListener(update)
  l.append(e)
  -> calls onChangeNotifier.notify(INSERT_ACTION, [e], len(l))
  -> calls update(INSERT_ACTION, [e], len(l))

  @type INSERT_ACTION: int
  @cvar INSERT_ACTION: used to notify insertion of new elements  in the list
  @type REMOVE_ACTION: int
  @cvar REMOVE_ACTION: used to notify elements deletion
  @type MODIFY_ACTION: int
  @cvar MODIFY_ACTION: used to notify elements modification

  @type onChangeNotifier: Notifier
  @ivar onChangeNotifier: the Notifier's notify method is called when the list has changed.
  """

  # actions to notify
  INSERT_ACTION=0
  REMOVE_ACTION=1
  MODIFY_ACTION=2

  def __init__(self, content=None):
    """
    @type content: list
    @param content: elements to initialize the list's content
    """
    # call a super class method can be done two different ways:
    # - superClass.method(self, ...)
    # - super(superClass, self).method(...)
    # It's better to use the second way because if derived class inherits from several classes,
    # super will try to find the method in other super classes before
    super(ObservableList, self).__init__()
    # views can register update callbacks on this notifier
    # to be aware of any change in the model
    # On change, this object calls Notifier.notify(args)
    # which calls every registred function with args
    # args = action (insert, remove, modify), elems list, position
    self.onChangeNotifier=Notifier()
    if content:
      self.extend(content)

  def __getinitargs__(self):
    """Returns the args to pass to the __init__ method to construct this object.
    It is usefull to save ObservableList object to minf format.
    @rtype: tuple
    @return: arg content to pass to the __init__ method for creating a copy of this object
    """
    content=[]
    content.extend(self)
    return (content)

  def __reduce__( self ):
    """This method is redefined for enable deepcopy of this object (and potentially pickle).
    It gives the arguments to pass to the init method of the object when creating a copy

    @rtype: tuple
    @return: class name, init args, state, iterator on elements to copy, dictionary iterator
    """
    # class name, init args, parameters for setstate, elements iterator, dictionary iterator
    return ( self.__class__, (), None, iter( self ), None )

  def addListener(self, listener):
    """Registers the listener callback method in the notifier.
    The method must take 3 arguments : action, elems list, position
      - INSERT_ACTION : elems have been inserted at position in the list
      - REMOVE_ACTION : elems have been removed [at position] in the list
      - MODIFY_ACTION : at position, some elements have been replaced by elems
    The position given in the notify method will be between 0 and len(self)

    @type listener: function
    @param listener: function to call to notify changes
    """
    self.onChangeNotifier.add(listener)

  def append(self, elem):
    """Adds the element at the end of the list.
    Notifies an insert action.
    """
    index=len(self)
    super(ObservableList, self).append(elem)
    self.onChangeNotifier.notify(self.INSERT_ACTION, [elem], index)

  def extend(self, l):
    """Adds the content of the list l at the end of current list.
    Notifies an insert action. """
    index=len(self)
    super(ObservableList, self).extend(l)
    self.onChangeNotifier.notify(self.INSERT_ACTION, l, index)

  def insert(self, pos, elem):
    """Inserts elem at position pos in the list.
    Notifies an insert action.
    """
    index=self.getPositiveIndex(pos)
    super(ObservableList, self).insert( pos, elem)
    self.onChangeNotifier.notify(self.INSERT_ACTION, [elem], index)

  def remove(self, elem):
    """Removes the first occurence of elem in the list.
    Notifies a remove action. """
    super(ObservableList, self).remove( elem)
    self.onChangeNotifier.notify(self.REMOVE_ACTION, [elem])

  def pop(self, pos=None):
    """Removes the element at position pos or the last element if pos is None.
    Notifies a remove action.
    @return: the removed element"""
    if pos is not None:
      index=self.getPositiveIndex(pos)
      elem=super(ObservableList, self).pop( pos)
    else:
      index=len(self)-1
      elem=super(ObservableList, self).pop()
    self.onChangeNotifier.notify(self.REMOVE_ACTION, [elem], index)
    return elem

  def sort(self, func=None):
    """Sorts the list using function func to compare elements.
    Notifies a modify action.
    @type func: function elem*elem->int
    @param func: comparison function, return -1 if e1<e2, 1 if e1>e2, 0 if e1==e2
    """
    super(ObservableList, self).sort( func)
    # all the elements of the list could be modified
    self.onChangeNotifier.notify(self.MODIFY_ACTION, self, 0)

  def reverse(self):
    """Inverses the order of the list.
    Notifies a modify action."""
    super(ObservableList, self).reverse()
    self.onChangeNotifier.notify(self.MODIFY_ACTION, self, 0)

  def __setitem__(self, key, value):
    """Sets value to element at position key in the list.
    Notifies a modify action.

    C{l[key]=value}
    """
    index=self.getPositiveIndex(key)
    super(ObservableList, self).__setitem__( key, value)
    self.onChangeNotifier.notify(self.MODIFY_ACTION, [value], index)

  def __delitem__(self, key):
    """Removes the element at position key in the list.
    Notifies a remove action.

    C{del l[key]}
    """
    index=self.getPositiveIndex(key)
    super(ObservableList, self).__delitem__( key)
    self.onChangeNotifier.notify(self.REMOVE_ACTION, [], index)

  def __setslice__(self, i, j, seq):
    """Sets values in seq to elements in the interval i,j.

    If i and j are negative numbers, there are converted before this call in index+len(self)
    Notifies a modify action.

    C{l[i:j]=seq}"""
    indexI=self.getIndexInRange(i)
    indexJ=self.getIndexInRange(j)
    super(ObservableList, self).__setslice__( i, j, seq)
    # if the interval is empty, action is insertion at the first position
    if indexI>=indexJ:
      self.onChangeNotifier.notify(self.INSERT_ACTION, seq, indexI)
    else:
      lenSeq=len(seq)
      lenInter=indexJ-indexI
      # if values sequence has same or lower length as the interval in the list,
      # all values are written to the list from the first index
      # the rest of the interval (if interval is longer than sequence) is left unchanged
      if lenInter>=lenSeq:
        self.onChangeNotifier.notify(self.MODIFY_ACTION, seq, indexI)
      else:
        # if the interval is shorter than the sequence of values,
        # values in the interval are used to modify the list,
        # the rest is inserted at indexJ position
        self.onChangeNotifier.notify(self.MODIFY_ACTION, seq[0:lenInter], indexI)
        self.onChangeNotifier.notify(self.INSERT_ACTION, seq[lenInter:lenSeq], indexJ)

  def __delslice__(self, i, j):
    """Removes elements in the interval i,j.

    If i and j are negative numbers, there are converted before this call in index+len(self).
    Notifies a remove action.

    C{del l[i:j]}"""
    indexI=self.getIndexInRange(i)
    indexJ=self.getIndexInRange(j)
    seq=self[indexI:indexJ]
    super(ObservableList, self).__delslice__( i, j)
    # if the interval is empty, the list is not modified
    if indexI<indexJ:
      self.onChangeNotifier.notify(self.REMOVE_ACTION, seq, indexI)

  def __iadd__(self, l):
    """C{list+=l} <=> C{list.extend(l)}

    Notifies insert action."""
    index=len(self)
    newList=super(ObservableList, self).__iadd__( l)
    self.onChangeNotifier.notify(self.INSERT_ACTION, l, index)
    return newList

  def __imul__(self, n):
    """C{list*=n}

    Notifies insert action."""
    index=len(self)
    newList=super(ObservableList, self).__imul__( n)
    self.onChangeNotifier.notify(self.INSERT_ACTION, self[index:], index)
    return newList

  def getPositiveIndex(self, i):
    """Returns an index between 0 and len(self)
      - if i is negative, it is replaced by len(self)+i
      - if index is again negative, it is replaced by 0
      - if index is beyond len(self) it is replaced by len(self)
    """
    l=len(self)
    if i<0:
      index=max(0, l+i)
    else: index=min(i, l)
    return index

  def getIndexInRange(self, i):
    """Returns an index in the range of the list.
    if i<0 return 0, if i>len(self), return len(self)"""
    if i<0:
      index=0
    else:
      l=len(self)
      if i>l:
        index=l
      else: index=i
    return index

  def itemIndex(self, item):
    """
    Returns item's index in the list. It's different from index method that returns index of the first element that has the same value as item.
    """
    i=0
    for it in self:
      if it is item:
        break
      i=i+1
    if i == len(self):
      i=-1
    return i

#----------------------------------------------------------------------------
class ObservableSortedDictionary( SortedDictionary ):
  """
  A sorted dictionary that notifies its changes.
  Inherits from python list and contains an instance of L{soma.notification.Notifier} (onChangeNotifier).

  Example::

  d=ObservableSortedDictionary()
  d.addListener(update)
  d.insert(index, key, e)
  -> calls onChangeNotifier.notify(INSERT_ACTION, [e], index)
  -> calls update(INSERT_ACTION, [e], index)

  @type INSERT_ACTION: int
  @cvar INSERT_ACTION: used to notify insertion of new elements  in the dictionary
  @type REMOVE_ACTION: int
  @cvar REMOVE_ACTION: used to notify elements deletion
  @type MODIFY_ACTION: int
  @cvar MODIFY_ACTION: used to notify elements modification

  @type onChangeNotifier: Notifier
  @ivar onChangeNotifier: the Notifier's notify method is called when the dictionaty has changed.
  """

  # actions to notify
  INSERT_ACTION=0
  REMOVE_ACTION=1
  MODIFY_ACTION=2

  def __init__( self, *args ):
    '''
    Initialize the dictionary with a list of ( key, value ) pairs.
    '''
    self.onChangeNotifier=Notifier()
    super(ObservableSortedDictionary, self).__init__(*args)
  
  def __getinitargs__(self):
    """Returns the args to pass to the __init__ method to construct this object.
    It is usefull to save ObservableList object to minf format.
    @rtype: tuple
    @return: arg content to pass to the __init__ method for creating a copy of this object
    """
    content=self.items()
    return (content)
    
  def addListener(self, listener):
    """Registers the listener callback method in the notifier.
    The method must take 3 arguments : action, elems list, position
      - INSERT_ACTION : elems have been inserted at position in the dictionary
      - REMOVE_ACTION : elems have been removed [at position] in the dict
      - MODIFY_ACTION : at position, some elements have been replaced by elems
    The position given in the notify method will be between 0 and len(self)

    @type listener: function
    @param listener: function to call to notify changes
    """
    self.onChangeNotifier.add(listener)
  
  def __setitem__( self, key, value ):
    insertion=not self.data.has_key(key)
    super(ObservableSortedDictionary, self).__setitem__(key, value)
    if insertion:
      self.onChangeNotifier.notify(self.INSERT_ACTION, [value], len(self.data) -1)
    else:
      self.onChangeNotifier.notify(self.MODIFY_ACTION, [value], self.sortedKeys.index(key))

  def __delitem__( self, key ):
    index=self.sortedKeys.index(key)
    super(ObservableSortedDictionary, self).__delitem__(key)
    self.onChangeNotifier.notify(self.REMOVE_ACTION, [], index)

  def insert( self, index, key, value ):
    '''
    insert a ( C{key}, C{value} ) pair in sorted dictionary before position 
    C{index}. If C{key} is already in the dictionary, a C{KeyError} is raised.
    @type  index: integer
    @param index: index of C{key} in the sorted keys
    @param key: key to insert
    @param value: value associated to C{key}
    '''
    super(ObservableSortedDictionary, self).insert(index, key, value)
    self.onChangeNotifier.notify(self.INSERT_ACTION, [value], index)
    
  def clear( self ):
    '''
    Remove all items from dictionary
    '''
    super(ObservableSortedDictionary, self).clear()
    self.onChangeNotifier.notify(self.REMOVE_ACTION, self.values(), 0)
    
  def sort(self, func=None):
    """Sorts the dictionary using function func to compare keys.
    Notifies a modify action.
    @type func: function key*key->int
    @param func: comparison function, return 1 if e1<e2, -1 if e1>e2, 0 if e1==e2
    """
    super(ObservableSortedDictionary, self).sort(func)
    self.onChangeNotifier.notify(self.MODIFY_ACTION, self.values(), 0)

  
#----------------------------------------------------------------------------
class EditableTree(ObservableAttributes, ObservableSortedDictionary):
  """The base class to model a tree of items.
  This class can be derived to change implementation.

  An EditableTree contains items which can be
    - an item branch : it contains other items as children
    - an item leaf : doesn't have children

  The list of items is an ObservableSortedDictionary which notifies its changes to registred listeners.
  If the tree is modifiable, new items can be added.
  Every item is an EditableTree.Item.
  EditableTree is iterable over its items.

  EditableTree also inherits from ObservableAttributes, so registred listeners can be notified of attributes value change.

  To call a method when item list changes::
  C{editableTree.addListener(callbackMethod)}
  To call a method when an item list changes at any depth in the tree::
  C{editableTree.addListenerRec(callbackMethod)}
  To call a method when an attribute of the tree changes::
  C{editableTree.onAttributeChange(attributeName, callbackMethod)}
  To call a method when an attribute changes at any depth in the tree::
  C{editableTree.onAttributeChangeRec(attributeName, callbackMethod)}

  @type defaultName: string
  @cvar defaultName: default name of the tree

  @type name: string
  @ivar name: the name of the tree
  @type modifiable: boolean
  @ivar modifiable: if true, new items can be added, items can be deleted and modified
  @type unamed: boolean
  @param unamed: indicates if name parameter was none, so the tree has the default name.
  :param visible: bool, indicates if the tree is visible (if not it may be hidden in a graphical representation)
  """
  defaultName="tree"
  def __init__( self, name=None, id=None, modifiable=True, content=[], visible=True, enabled=True):
    dictContent=[(i.id, i) for i in content]
    super(EditableTree, self).__init__(*dictContent)
    if name is None:
      self.name = self.defaultName
      self.unamed = True
    else:
      self.name=name
      self.unamed=False
    if id is None:
        self.id=str(hash(self))
    else:
      self.id=id
    self.modifiable=modifiable
    self.visible=visible
    self.enabled=enabled

  def __getinitargs__(self):
    """Returns the args to pass to the __init__ method to construct this object.
    It is usefull in order to save EditableTree object to minf format.
    @rtype: tuple
    @return: arg content to pass to the __init__ method for creating a copy of this object
    """
    # elements in the tuple must be serializable with minf, so the content must be of type list
    content=self.values()
    return (self.name, self.id, self.modifiable, content, self.visible, self.enabled)

  def __str__(self):
    s = self.name + " ("
    for i in self:
      s += str(i)+" "
    s += ")"
    return s

  def add(self, item):
    """
    Add an item in the tree. If this item's id is already present in the tree as a key, add the item's content in the corresponding key. 
    recursive method
    """
    key=item.id
    if self.has_key(key):
      if not item.isLeaf(): # if the item is a leaf and is already in the tree, nothing to do
        for v in item.values(): # item is also a dictionary and contains several elements, add each value in the tree item
          self[key].add(v)
      # also set current name for the current object
      self[key].name = item.name
    else: # new item
      self[key]=item

  def isDescendant(self, item):
    """Return true if current item is a child or a child's child... of the item in parameter
    Always false for the root of the tree"""
    return False
  
  def isLeaf(self):
    return False

  def removeEmptyBranches(self):
    """If a branch item doesn't contain any leaf or branch that contains leaf recursivly,
    the item is removed from the tree. """
    toRemove=[]
    for child in self.values():
      if not child.isLeaf():
        child.removeEmptyBranches()
        if child.values()==[]: # it isn't possible to remove an element during iteration on the list
          toRemove.append(child) # so it's put on a remove list and will be removed from the tree outside the loop
    for item in toRemove:
      del self[item.id]

  def sort(self, func=None):
    """Recursive sort of the tree : items are sorted in all branches.
    """
    ObservableSortedDictionary.sort(self, self.compItems)
    for item in self.values():
      if not item.isLeaf():
        item.sort( func )
        
  def compItems(self, id1, id2):
    """Comparison function
    return 1 if i1 > i2
    -1 if i1 < i2
    0 if they are equal"""
    res=0
    i1=self[id1]
    i2=self[id2]
    if (not i1.isLeaf() and i2.isLeaf()):
      # if one item is a branch and the other is a leaf, the branch must be before the leaf
      res=-1
    elif (i1.isLeaf() and not i2.isLeaf()):
      res=1
    else:
      # names are translated in lowercase to make an alphabetical sort independant of the case
      # by default (uppercase letters are < to lowecase letters)
      n1=i1.name.lower()
      n2=i2.name.lower()
      if n1 < n2:
        res=-1
      elif n1 > n2:
        res=1
    #print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
    return res

  def addListenerRec(self, listener):
    """Add a listener to the tree recursivly at every level.
    The listener is added to the notifier of all branches of the tree."""
    self.addListener(listener)
    for item in self.values():
      if not item.isLeaf():
        item.addListenerRec(listener)

  def onAttributeChangeRec(self, attributeName, listener):
    """Add a listener of the changes of this attribute value in the tree recursivly at every level.
    The listener is added to the attribute change notifier of all branches of the tree."""
    self.onAttributeChange(attributeName, listener)
    for item in self.values():
      if not item.isLeaf():
        item.onAttributeChangeRec(attributeName, listener)

  #----------------------------------------------------------------------------
  class Item(ObservableAttributes):
    """Base element of an EditableTree
    The attributes :
    - icon : filename of the image that can be used to represent the item
    - name : Text representation of the item
    - movable : true if the item can be moved in the tree
    - modifiable : true if the item can change (add children, change text, icon)
    - delEnabled : true if deletion of the item is allowed

    Item inherits from L{ObservableAttributes}, so it can notify registred listener of attributes changes (for example name).

    @type icon: string
    @ivar icon: file name of an icon to represent the item.
    @type name: string
    @ivar name: name of the item
    @type tooltip: string
    @ivar tooltip: description associated to the item
    @type copyEnabled: boolean
    @ivar copyEnabled: indicates if this item can be copied
    @type modifiable: boolean
    @ivar modifiable: indicates if the item can be modified (renamed for example)
    @type delEnabled: boolean
    @ivar delEnabled: indicates if the item can be deleted
    :param visible: bool, indicates if current item is visible (if not it may be hidden in a graphical representation)
    :param enabled: bool, indicates if the item is enabled, it could be visible but disabled
    """
    def __init__( self, name=None, id=None, icon=None, tooltip=None, copyEnabled=True, modifiable=True, delEnabled=True, visible=True, enabled=True, *args):
      super(EditableTree.Item, self).__init__(*args)
      self.icon=icon
      self.name=name
      if id is None:
        self.id=str(hash(self))
      else:
        self.id=id
      self.tooltip=tooltip
      self.copyEnabled=copyEnabled
      self.modifiable=modifiable
      self.delEnabled=delEnabled
      self.visible=visible
      self.enabled=enabled
      self.onChangeNotifier=Notifier()
      self.unamed=False

    def __getinitargs__(self):
      """Returns the args to pass to the __init__ method to construct this object.
      It is usefull to save L{ObservableList} object to minf format.
      @rtype: tuple
      @return: arg content to pass to the __init__ method for creating a copy of this object
      """
      return (self.name, self.id, self.icon, self.tooltip, self.copyEnabled, self.modifiable, self.delEnabled, self.visible, self.enabled)

    def __reduce__( self ):
      """This method is redefined for enable deepcopy of this object (and potentially pickle).
      It gives the arguments to pass to the init method of the object when creating a copy

      @rtype: tuple
      @return: class name, init args, state, iterator on elements to copy, dictionary iterator
      """
      return ( self.__class__, self.__getinitargs__(), None, None, None )

    def __str__(self):
      return self.name

    def isLeaf(self):
      """Must be redefined in subclasses to say if the item is a leaf"""
      pass

    def setAllModificationsEnabled(self, bool):
      """Recursivly enables or disables item's modification."""
      #self.copyEnabled=bool # copy is always enabled. there's no use to have 3 different booleans, an editable should be sufficient
      self.modifiable=bool
      self.delEnabled=bool
      if not self.isLeaf():
        for child in self.values():
          child.setAllModificationsEnabled(bool)

    def isDescendant(self, item):
      """Return true if current item is a child or a child's child... of the item in parameter"""
      found=False
      #print self.name, "is descendant", item.name, "? "
      if not item.isLeaf():
        for child in item.values():
          # search self in item's children and recursively in children's children (deep first search)
          if self==child:
            found=True
          elif not child.isLeaf():
            found=self.isDescendant(child)
          if found:
            break
      return found

  #----------------------------------------------------------------------------
  class Branch( Item, ObservableSortedDictionary ):
    """ A Branch is an item that can contain other items.
    It inherits from L{Item} and from L{ObservableSortedDictionary}, so it can have children items.
    """
    defaultName="new"
    def __init__( self, name=None, id=None, icon=None, tooltip=None, copyEnabled=True, modifiable=True, delEnabled=True, content=[], visible=True, enabled=True ):
      """All parameters must have default values to be able to create new elements automatically"""
      #super(EditableTree.Branch, self).__init__(content)  #, name, icon, tooltip, copyEnabled, modifiable, delEnabled)
      #EditableTree.Item.__init__(self, name, icon, tooltip, copyEnabled, modifiable, delEnabled)
      dictContent=[(i.id, i) for i in content]
      super(EditableTree.Branch, self).__init__(name, id, icon, tooltip, copyEnabled, modifiable, delEnabled, visible, enabled, *dictContent)
      if name is None:
        self.name=self.defaultName
        self.unamed=True
      else:
        self.name=name
        self.unamed=False

    def __getinitargs__(self):
      content=self.values()
      return (self.name, self.id, self.icon, self.tooltip, self.copyEnabled, self.modifiable, self.delEnabled, content, self.visible, self.enabled)

    def __reduce__( self ):
      """This method is redefined for enable deepcopy of this object (and potentially pickle).
      It gives the arguments to pass to the init method of the object when creating a copy
      """
      return ( self.__class__, self.__getinitargs__(), None, None, None )

    def __str__(self):
      s = self.name + " ("
      for i in self:
        s += str(i)+" "
      s += ")"
      return s

    def isLeaf(self):
      return False
  
    def add(self, item):
      """
      Add an item in the tree. If this item's id is already present in the tree as a key, add the item's content in the corresponding key. 
      recursive method
      """
      key=item.id
      if self.has_key(key):
        if not self[key].isLeaf(): # if the item is a leaf and is already in the tree, nothing to do
          for v in item.values(): # item is also a dictionary and contains several elements, add each value in the tree item
            self[key].add(v)
            
        # also set current name for the current object
        self[key].name = item.name
        
      else: # new item
        self[key]=item

    def removeEmptyBranches(self):
      toRemove=[]
      for child in self.values():
        if not child.isLeaf():
          child.removeEmptyBranches()
          if child.values()==[]:
            toRemove.append(child)
      for item in toRemove:
        del self[item.id]

    def sort(self, func=None ):
      """Recursive sort of the tree : items are sorted in all branches.
      """
      ObservableSortedDictionary.sort(self, self.compItems)
      for item in self.values():
        if not item.isLeaf():
          item.sort( func )
  
    def compItems(self, id1, id2):
      """Comparison function
      return 1 if i1 > i2
      -1 if i1 < i2
      0 if they are equal"""
      res=0
      i1=self[id1]
      i2=self[id2]
      if (not i1.isLeaf() and i2.isLeaf()):
        # if one item is a branch and the other is a leaf, the branch must be before the leaf
        res=-1
      elif (i1.isLeaf() and not i2.isLeaf()):
        res=1
      else:
        # names are translated in lowercase to make an alphabetical sort independant of the case
        # by default (uppercase letters are < to lowecase letters)
        n1=i1.name.lower()
        n2=i2.name.lower()
        if n1 < n2:
          res=-1
        elif n1 > n2:
          res=1
      #print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
      return res

    def addListenerRec(self, listener):
      self.addListener(listener)
      for item in self.values():
        if not item.isLeaf():
          item.addListenerRec(listener)

    def onAttributeChangeRec(self, attributeName, listener):
      self.onAttributeChange(attributeName, listener)
      for item in self.values():
        if not item.isLeaf():
          item.onAttributeChangeRec(attributeName, listener)

  #----------------------------------------------------------------------------
  class Leaf( Item ):
    """A tree item that cannot have children items"""
    def __init__( self, name="new", id=None, icon=None, tooltip=None, copyEnabled=True, modifiable=True, delEnabled=True, visible=True, enabled=True):
      super(EditableTree.Leaf, self).__init__(name, id, icon, tooltip, copyEnabled, modifiable, delEnabled, visible, enabled)

    def isLeaf(self):
            return True

  #----------------------------------------------------------------------------
class ObservableNotifier(Notifier):
  """
  This notifier can notify when the first listener is added and when the last listener is removed. 
  It enables to use the notifier only when there's some listeners registred.
  
  @type onAddFirstListener: Notifier
  @ivar onAddFirstListener: register a listener on this notifier to be called when the first listener is registred on ObservableNotifier
  @type onRemoveLastListener: Notifier
  @ivar onRemoveLastListener: register a listener on this notifier to be called when the last listener is removed from ObservableNotifier
  """
  
  def __init__(self, parameterCount=None):
    """
    @type parameterCount: integer
    @param parameterCount: if not None, each registered function must be callable with that number of arguments (checking is done on registration).
    """
    Notifier.__init__(self, parameterCount)
    self.onAddFirstListener=Notifier()
    self.onRemoveLastListener=Notifier()
    
  def add(self, listener):
    nbListenersBefore=len(self._listeners)
    Notifier.add(self, listener)
    if nbListenersBefore == 0: # before add : 0 listener, after : 1 listener -> add first listener
      if len(self._listeners) == 1:
        self.onAddFirstListener.notify()
        
  def remove(self, listener):
    nbListenersBefore=len(self._listeners)
    Notifier.remove(self, listener)
    if nbListenersBefore == 1: # before add : 1 listener, after : 0 listener -> remove last listener
      if len(self._listeners) == 0:
        self.onRemoveLastListener.notify()
