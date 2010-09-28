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


import types
from soma.translation import translate as _
from soma.sorted_dictionary import SortedDictionary
from soma.notification import Notifier, VariableParametersNotifier, \
                               ObservableAttributes
from soma.singleton import Singleton
from soma.undefined import Undefined

import copy 

#-------------------------------------------------------------------------------
class DataType( object ):
  """
  C{DataType} derived classes manage the behaviour of all attributes defined in 
  a signature of an object (most often a L{HasSignature} instance). In order to 
  define a new type of parameter, one must derive from C{DataType} and define 
  at least the L{checkValue} method. See C{DataType} methods documentation for 
  more information on how to customize a type.
  """

  def __init__( self ):
    super( DataType, self ).__init__()
    # Some inherited class forbid attribute modification, therefore __dict__
    # is accessed directly
    
    #: Indicate wether the value of this type are mutable (I{i.e.} can be 
    #: modified) or not. By default, C{mutable} is set to C{True}.For more 
    #: information about mutable or immutable objects, see 
    #: U{Python documentation<http://docs.python.org/>}.
    self.mutable = True
    #: Name of this C{DataType}, by default, it is the class name without the 
    #: module(s) prefix (I{i.e.} as defined in the C{class} statement).
    self.name = self.__class__.__name__.split( '.' )[ -1 ]
  
  
  def dataTypeInstance( value ):
    """
    Static method to create a L{DataType} instance from a user defined value. 
    The C{value} argument must be one of the following:
      - B{A DataType instance}: C{value} is returned untouched.
      - B{A class deriving from L{DataType}}: C{value()} is returned.
      - B{A class not deriving from DataType}: returns 
        C{L{ClassDataType}( value )}.
    Any other value lead to a C{TypeError} exception.
    """
    if isinstance( value, type ) or type( value ) is types.ClassType:
      if issubclass( value, DataType ):
        value = value()
      else:
        value = ClassDataType( value )
    elif not isinstance( value, DataType ):
      raise TypeError( _( 'Expected a DataType instance or a class but got %s' ) % (repr(value),) )
    return value
  dataTypeInstance = staticmethod( dataTypeInstance )
  
  
  def checkValue( self, value ):
    """
    Verify that C{value} is valid for this type of attribute. Raises a 
    C{ValueError} if the value is not valid. Must be overloaded in derived 
    classes.
    @return: the real value that will be used for the attribute. It is
      recomended to return C{value} here unless you know what you are doing.
    """
    raise RuntimeError( _( 'checkValue method has not be defined for %s' ) %\
                        ( self.__class__.__name__, ) )
    
  def createValue( self ):
    '''
    Create a default value for this type of attribute.
    '''
    raise RuntimeError( _( 'createValue method has not be defined for %s' ) %\
                        ( self.__class__.__name__, ) )
  
  
  def _getAttribute( self, hasSignatureObject, name ):
    """
    This method allow to customize attribute read acces of L{HasSignature} 
    instances for all attributes declared as a specific C{DataType} in the 
    signature. 
    If not overloaded, it returns the value of attribute C{name} of 
    C{hasSignatureObject}, or raises an C{AttributeError} if this attribute is 
    not defined.
    @param hasSignatureObject: object containing an attribute to read.
    @type hasSignatureObject: L{HasSignature} instance
    @param name: name of the attribute to read
    @type  name: C{string}
    @return: value of C{getattr( hasSignatureObject, name )}
    """
    return super( HasSignature, hasSignatureObject ).__getattribute__( name )


  def _setAttribute( self, hasSignatureObject, name, value ):
    """
    This method allow to customize attribute write acces of L{HasSignature} 
    instances for all attributes declared as a specific C{DataType} in the 
    signature. 
    If not overloaded, if calls C{self.L{checkValue}( value )} and set the 
    attribute with the value returned.
    @param hasSignatureObject: object where an attribute must be set.
    @type  hasSignatureObject: L{HasSignature} instance
    @param name: name of the attribute to set.
    @type  name: C{string}
    @param value: value to set to the attribute.
    @return: the new value of the attribute
    """
    checkValue = getattr( hasSignatureObject, '_check_' + name + '_value',
                          self.checkValue )
    newValue = checkValue( value )
    super( HasSignature, hasSignatureObject ).__setattr__( name, newValue )
    return newValue


  def _deleteAttribute( self, hasSignatureObject, name ):
    """
    This method allow to customize attribute deletion of L{HasSignature} 
    instances for all attributes declared as a specific C{DataType} in the 
    signature. 
    If not overloaded, it raises C{TypeError} because attributes declared in 
    the signature cannot be deleted.
    @param hasSignatureObject: object containing an attribute to delete
    @type hasSignatureObject: L{HasSignature} instance
    @param name: name of the attribute to delete
    @type  name: C{string}
    """
    raise TypeError( _( 'Cannot delete signature attribute %s' ) % ( name, ) )


  def _checkValueError( self, value ):
    """
    Raises a C{ValueError} with a message saying that C{value} is not a valid 
    value for this data type. This method is used in several classes
    derived from C{DataType}.
    """
    raise ValueError( _( '%(value)s is not a valid value for data type ' \
                          '%(type)s' ) \
                     % { 'type': str(self), 'value': repr(value) } )


  def _convertError( self, value ):
    """
    Raises a C{ValueError} with a message saying that C{value} cannot be 
    converted into this data type. This method is used in several classes
    derived from C{DataType}.
    """
    raise ValueError( _( 'cannot convert %(value)s into %(type)s' ) % \
                     { 'type': str(self), 'value': repr(value) } )


  def convert( self, value, checkValue=None ):
    """
    Convert a given value in a valid value for this data type. If not 
    overloaded, it raises a C{TypeError} by calling L{_convertError}.
    C{checkValue} if the function used to check valid values, if it
    is C{None}, C{self.checkValue} is used.
    """
    self._convertError( value )


  def convertAttribute( self, hasSignatureObject, name, value=Undefined ):
    """
    @param hasSignatureObject: object where an attribute must be converted.
    @type  hasSignatureObject: L{HasSignature} instance
    @param name: name of the attribute to convert.
    @type  name: C{string}
    @param value: value to convert (optional).
    @return: the converted value
    """
    checkValue = getattr( hasSignatureObject, '_check_' + name + '_value',
                          self.checkValue )
    if value is Undefined:
      value = getattr( hasSignatureObject, name )
    try:
      newValue = checkValue( value )
    except:
      newValue = self.convert( value, checkValue=checkValue )
    return newValue


  def copy( self ):
    """
    Return a copy of C{self}. If not overloaded, it creates a new instance by 
    passing the result of 
    C{self.L{__getinitkwargs__<DataType.__getinitkwargs__>}()} to the constructor.
    """
    args, kwargs = self.__getinitkwargs__()
    return apply( self.__class__, args, kwargs )
  
    
  def __getinitkwargs__( self ):
    """
    Returns all the parameters that have been passed to the constructor to 
    create this instance. This method must be overloaded by derived classes 
    that overload C{__init__}. See L{Number} class for an example.
    @return: a pair C{( args, kwargs )} where C{args} is a tuple containing the 
    unnamed parameters and C{kwargs} is a dictionary containing named 
    parameters.
    """
    return (), {}

    
  def __str__( self ):
    return self.name
  
  
  def __repr__( self ):
    args, kwargs = self.__getinitkwargs__()
    if args:
      strArgs = ', '.join( [repr(i) for i in args] )
    else:
      strArgs = ''
    if kwargs:
      if strArgs: strArgs += ', '
      strArgs += ', '.join( [n+'='+repr(v) for n,v in kwargs.iteritems()] )
    if strArgs:
      return self.name + '( ' + strArgs + ' )'
    else:
      return self.name + '()'


#-------------------------------------------------------------------------------
class ClassDataType( DataType ):
  """
  This class is used internally to allow the use of classes that do not derive 
  from L{DataType} in L{Signature} constructor. When such a class (let's call 
  it C{C}) is used for the type of an attribute, it is replaced by 
  C{ClassDataType( C )}. This data type only check that only C{C} instances are 
  used as attribute value.
  """
  def __init__( self, cls ):
    DataType.__init__( self )
    #: Store the class used as attribute type in a L{Signature}.
    self.cls = cls
  
  def __getinitkwargs__( self ):
    args, kwargs = DataType.__getinitkwargs__( self )
    return (self.cls,), kwargs

  def checkValue( self, value ):
    """
    Check that C{value} is an instance of L{self.cls}.
    """
    if not isinstance( value, self.cls ):
      raise TypeError( _( '%(instance)s is no an instance of %(class)s' ) %\
        { 'instance': str( value ),
          'class': str( self.cls )
        } )
    return value


  def createValue( self ):
    return self.cls()


#-------------------------------------------------------------------------------
class Signature( DataType ):
  """
  A C{Signature} instance contains type definition for a series of attributes, 
  it is mainly used to define attributes for L{HasSignature} derived class. It 
  behave like a L{SortedDictionary} where keys are attribute names and values 
  are attribute types (I{i.e.} L{DataType} instances). Since the order of the 
  attribute is user defined, it is not possible to use any syntax or data 
  structure that use a Python dictionary (because dictionaries keys are sorted 
  according to their values). Therefore, a signature instance is created by 
  using a list containing attribute names followed by attribute types.
  
  Example::
    from soma.signature.api import HasSignature, Signature
    from soma.signature.api import Unicode, Number, Integer
    
    class ZooAnimal( HasSignature ):
      signature = Signature(
        'identifier', Integer( minimum=0 ),
        'race', Unicode,
        'name', Unicode,
        'gender', Choice( 'male', 'female' ),
      )
  
  The first element of a signature is always an attribute named C{signature} 
  and whose type is the C{Signature} instance (this attribute B{must not} be 
  defined in the constructor). Hence, a L{HasSignature} instance has always a 
  C{signature} attribute that can be managed like any other user-defined 
  attributes (especially for modification notification).
  
  @see: L{HasSignature}, L{soma.signature.api}, L{SortedDictionary}
  """
  
  class Item( ObservableAttributes ):
    """
    @todo: documentation
    """
    def setType( self, dataType ):
      newValue = DataType.dataTypeInstance( dataType )
      self.__dict__[ 'type' ] = newValue
    
    def getType( self ):
      try:
        return self.__dict__[ 'type' ]
      except KeyError:
        raise AttributeError( 'type' )
    
    type = property( getType, setType, None )
    
    
    def __init__( self, name, type, 
                  defaultValue=Undefined, 
                  doc=None,
                  readOnly=False,
                  visible=True,
                  collapsed=False ):
      """
      @todo: documentation
      """
      ObservableAttributes.__init__( self )
      #: Name of the attribute
      self.name = str( name )
      #: Type the attribute
      self.type = type
      #: Default attribute value
      self.defaultValue = defaultValue
      #: Documentation of the attribute
      if doc:
        self.doc = unicode( doc )
      else:
        self.doc = None
      #: If set to C{True}, the attribute value cannot be modified
      self.readOnly = bool( readOnly )
      #: If set to C{False}, the attribute is not visible on graphical interface
      self.visible = bool( visible )
      #: If set to C{True}, the attribute is reduced on graphical interface (when possible)
      self.collapsed = bool( collapsed )
    
    
    def copy( self ):
      args, kwargs = self.__getinitkwargs__()
      return self.__class__( *args, **kwargs )
  
    def __getinitkwargs__( self ):
      d = {}
      if self.defaultValue is not Undefined:
        d[ 'defaultValue' ] = self.defaultValue
      if self.doc:
        d[ 'doc' ] = self.doc
      if self.readOnly:
        d[ 'readOnly' ] = self.readOnly
      if not self.visible:
        d[ 'visible' ] = self.visible
      if self.collapsed:
        d[ 'collapsed' ] = self.collapsed
      return ( self.name, self.type ), d
  
  
  _msgCannotModify = 'Cannot modify read-only signature'


  def __init__( self, *args ):
    super( Signature, self ).__init__()
    # Notifier is created on read-only Signature because listeners registration
    # can be done on Signature and copied when Signature is changed to
    # VariableSignature
    self.on_change = Notifier( 1 )
    self.__dict__[ '_signature_data' ] = \
      SortedDictionary( ( 'signature', self.Item( 'signature', self ) ) )

    i = 0
    while i < len( args ):
      name = args[ i ]
      i += 1
      if isinstance( name, Signature ):
        for n, item in name.iteritems():
          if n == 'signature': continue
          self._insertElement( len(self), n, item.copy() )
      else:
        dataType = args[ i ]
        if i+1 < len( args ) and isinstance( args[ i+1 ], dict ):
          i += 1
          options = args[ i ]
        else:
          options = {}
        self._insertElement( len( self ), name, dataType, options )
        i += 1


  def _copyItem( self, item ):
    args, kwargs = item.__getinitkwargs__()
    return self.Item( *args, **kwargs )


  def _insertElement( self, index, name, dataType, options={} ):
    if self.has_key( name ):
      raise KeyError( _( 'Element "%s" is defined twice' % ( name, ) ) )
    if isinstance( dataType, Signature.Item ):
      item = self._copyItem( dataType )
    else:
      dataType = DataType.dataTypeInstance( dataType )
      item = self.Item( name, dataType, **options )
    self._signature_data.insert( index, name, item )


  def has_key( self, key ):
    """
    see L{SortedDictionary.has_key}
    """
    return self.__dict__[ '_signature_data' ].has_key( key )


  def __getitem__( self, key ):
    """
    see L{SortedDictionary.__getitem__}
    """
    return self.__dict__[ '_signature_data' ][ key ]


  def __setitem__( self, key, value ):
    """
    see L{SortedDictionary.__setitem__}
    """
    raise RuntimeError( _( self._msgCannotModify ) )

 
  def __delitem__( self, key ):
    """
    see L{SortedDictionary.__delitem__}
    """
    raise RuntimeError( _( self._msgCannotModify ) )


  def __len__( self ) :
    """
    see L{SortedDictionary.__len__}
    """
    return len( self.__dict__[ '_signature_data' ] )


  def get( self, key, default=None ):
    """
    see L{SortedDictionary.get}
    """
    return self.__dict__[ '_signature_data' ].get( key, default )


  def keys( self ) :
    """
    see L{SortedDictionary.keys}
    """
    return  self.__dict__[ '_signature_data' ].keys()


  def values( self ) :
    """
    see L{SortedDictionary.values}
    """
    return  self.__dict__[ '_signature_data' ].values()


  def items( self ) :
    """
    see L{SortedDictionary.items}
    """
    return  self.__dict__[ '_signature_data' ].items()


  def __iter__( self ) :
    """
    see L{SortedDictionary.__iter__}
    """
    return  iter( self.__dict__[ '_signature_data' ] )


  def iterkeys( self ) :
    """
    see L{SortedDictionary.iterkeys}
    """
    return  self.__dict__[ '_signature_data' ].iterkeys()


  def itervalues( self ) :
    """
    see L{SortedDictionary.itervalues}
    """
    return  self.__dict__[ '_signature_data' ].itervalues()


  def iteritems( self ) :
    """
    see L{SortedDictionary.iteritems}
    """
    return  self.__dict__[ '_signature_data' ].iteritems()


  def insert( self, index, key, value, **kwargs ):
    """
    see L{SortedDictionary.insert}
    """
    raise RuntimeError( _( self._msgCannotModify ) )


  def _setAttribute( self, hasSignatureObject, name, value ):
    """
    This method is called when the C{signature} attribute of an L{HasSignature} 
    instance is modified, it calls 
    C{hasSignatureObject.L{_changeSignature<HasSignature._changeSignature>}} to 
    change the attribute value. The new signature becomes an instance signature 
    (overriding the class signature). Once an instance signature is created, 
    the class signature can be restored by deleting the C{signature} attribute.
    
    @see: L{_deleteAttribute}
    """
    checkValue = getattr( hasSignatureObject, '_check_' + name + '_value',
                          self.checkValue )
    newValue = checkValue( value )
    hasSignatureObject._changeSignature( newValue )
    return newValue


  def _deleteAttribute( self, hasSignatureObject, name ):
    """
    This method is called when the C{signature} attribute of an L{HasSignature} 
    instance is deleted. It tries to restore the class signature if an instance 
    signature has been defined. If no instance signature has been defined, it 
    raises a C{RuntimeError}.
    
    @see: L{_setAttribute}
    """
    if not hasSignatureObject._changeSignature( None ):
      raise RuntimeError( _( 'Signature cannot be deleted' ) )


  def checkValue( self, value ):
    """
    Raises a C{TypeError} if C{value} is not a C{Signature} instance.
    """
    if not isinstance( value, Signature ):
      raise TypeError( _('invalid value type for signature attribute: %s') %\
                       ( type(value), ))
    return value


  def __getinitkwargs__( self ):
    args, kwargs = DataType.__getinitkwargs__( self )
    args = []
    it = self.iteritems()
    it.next() # skip signature
    for name, type in it:
      args.append( name )
      args.append( type )
    return args, kwargs


  def copy( self ):
    args, kwargs = DataType.__getinitkwargs__( self )
    args = []
    it = self.iteritems()
    it.next() # skip signature
    for name, item in it:
      args.append( name )
      args.append( item.copy() )
    return apply( self.__class__, args, kwargs )


  def __repr__( self ):
    result = self.name + '( '
    it = self.itervalues()
    it.next()
    for item in it:
      result += repr( item.name ) + ', ' + repr( item.type ) +', '
      args, kwargs = item.__getinitkwargs__()
      if kwargs:
        result += 'dict( ' + ', '.join( [str(i) + '=' + repr(j) for i,j in kwargs.iteritems()] ) + '), '
    return result + ' )'

#-------------------------------------------------------------------------------
class VariableSignature( Signature ):
  """
  This class is a non constant version of C{Signature}. You can add or remove
  elements at run-time on a C{VariableSignature} instance. These changes are 
  taken into account by the notification system.
  """
  def __setitem__( self, key, value ):
    if key == 'signature':
      raise KeyError( _( 'Attribute named "signature" cannot be redefined.') )
    self._insertElement( len(self), key, value )
    self.on_change.notify( key )


  def __delitem__( self, key ):
    if key == 'signature':
      raise KeyError( _( 'Attribute named "signature" cannot be deleted.' ) )
    del self.__dict__[ '_signature_data' ][ key ]
    self.on_change.notify( key )


  def insert( self, index, key, value, **kwargs ):
    self._insertElement( index, key, value, kwargs )
    self.on_change.notify( key )
  
  
  def append( self, key, value, **kwargs ):
    self._insertElement( len( self ), key, value, kwargs )
    self.on_change.notify( key )
    


#-------------------------------------------------------------------------------
class MetaHasSignature( type ):
  def __init__( cls, name, bases, dict ):
    signature = dict.get( 'signature' )
    if signature is not None:
      for c in bases:
        referenceSignature = getattr( c, 'signature', None )
        if referenceSignature is not None: break
      if referenceSignature is not None and not isinstance( signature, referenceSignature.__class__ ):
        raise TypeError( _( 'signature must be an instance of %s' ) % ( unicode( referenceSignature.__class__ ), ) )
    super( MetaHasSignature, cls ).__init__( name, bases, dict )


#-------------------------------------------------------------------------------
class HasSignature( ObservableAttributes ):
  """
  HasSignature is the base class for all object using the signature system.
  """
  __metaclass__ = MetaHasSignature
  
  #: The default empty signature
  signature = Signature()
  

  def __init__( self, *args, **kwargs ):
    super( HasSignature, self ).__init__( *args, **kwargs )
    for attribute in self.signature:
      self._onAttributeChange[ attribute ] = self._createAttributeNotifier()
  
  
  def initializeSignatureAttributes( self, **attributesValues ):
    """
    Initialize signature attributes according to the values given in
    parameters and the default values given in the signature. Values
    given in parameters takes precedence over signature default values.
    If a parameter name is not in the signature, a TypeError is raised.
    
    Example
    =======
    L{initializeSignatureAttributes} is suitable for using in constructors::
      class Time( HasSignature ):
        signature = Signature(
          'hour', Integer( minimum=0, maximum=23 ), dict( defaultValue=0 ),
          'minute', Integer( minimum=0, maximum=59 ), dict( defaultValue=0 ),
          'second', Integer( minimum=0, maximum=59 à, dict( defaultValue=0 ),
        )
        
        def __init__( self, **kwargs ):
          HasSignature.__init__( self )
          self.initializeSignatureAttributes( **kwargs )

    """
    # Copy the dictionary to allow modification
    it = self.signature.iteritems()
    it.next()
    for attributeName, signatureItem in it:
      value = attributesValues.pop( attributeName, Undefined )
      if value is Undefined:
        value = copy.copy( signatureItem.defaultValue )
      if value is not Undefined:
        setattr( self, attributeName, value )
    if attributesValues:
      raise TypeError( _( "Attribute '%s' is not in the signature" ) % \
                            ( attributesValues.iterkeys().next(), ) )
  
  
  def __getattribute__( self, name ):
    """
    For all attributes that are declared in the signature, calls the 
    L{_getAttribute<DataType._getAttribute>} method of the attribute type.
    Directly return the value of all other attributes.
    """
    signatureItem = \
      super( HasSignature, self ).__getattribute__( 'signature' ).get( name )
    if signatureItem is None:
      return super( HasSignature, self ).__getattribute__( name )
    else:
      try:
        return signatureItem.type._getAttribute( self, name )
      except AttributeError:
        defaultValue = signatureItem.defaultValue
        if defaultValue is Undefined: raise
        defaultValue = copy.copy( defaultValue )
        super( ObservableAttributes, self ).__setattr__( name, defaultValue )
        return defaultValue
  

  def __setattr__( self, name, value ):
    """
    For all attributes that are declared in the signature, calls the 
    L{_setAttribute<DataType._setAttribute>} method of the attribute type
    and then calls L{self.notifyAttributeChange}. Directly change the value of 
    all other attributes.
    """
    signatureItem = self.signature.get( name )
    if signatureItem is None:
      super( HasSignature, self ).__setattr__( name, value )
    else:
      signatureItem.type._setAttribute( self, name, value )


  def __delattr__( self, name ):
    """
    For all attributes that are declared in the signature, calls the 
    L{_deleteAttribute<DataType._deleteAttribute>} method of the attribute type
    and then calls L{self.notifyAttributeChange}. Directly change the value of 
    all other attributes.
    """
    signatureItem = self.signature.get( name )
    if signatureItem is None:
      super( HasSignature, self ).__delattr__( name )
    else:
      signatureItem.type._deleteAttribute( self, name )


  def _changeSignature( self, newSignature ):
    """
    Change or delete the instance signature. C{newSignature} becomes the 
    instance signature. If C{newSignature} is C{None}, the instance signature 
    is deleted and the class signature is restored. Notification for attributes 
    that are in both old and new signature is preserved.
    """
    signatureChanged = True
    oldSignature = self.signature
    if newSignature is None:
      try:
        super( HasSignature, self ).__delattr__( 'signature' )
        newSignature = self.signature
      except AttributeError:
        signatureChanged = False
    else:
      super( HasSignature, self ).__setattr__( 'signature', newSignature )
    if signatureChanged:
      oldSignature.on_change.remove( self._signatureChanged )
      newSignature.on_change.add( self._signatureChanged )

      for attribute in newSignature:
        notifier = self._onAttributeChange.get( attribute )
        if notifier is None:
          self._onAttributeChange[ attribute ] = self._createAttributeNotifier()
      for attribute in oldSignature:
        if not newSignature.has_key( attribute ):
          del self._onAttributeChange[ attribute ]
    return signatureChanged


  def _signatureChanged( self, attributeName ):
    """
    This method is called whenever the signature content is modified.
    """
    if self._onAttributeChange.has_key( attributeName ):
      if not self.signature.has_key( attributeName ):
        del self._onAttributeChange[ attributeName ]
    elif self.signature.has_key( attributeName ):
      self._onAttributeChange[ attributeName ] = self._createAttributeNotifier()
    self._onAttributeChange[ 'signature' ].notify( self, 'signature',
                                                   self.signature,
                                                   self.signature )

  def delayAttributeNotification( self, ignoreDoubles=False ):
    super( HasSignature, self ).delayAttributeNotification( ignoreDoubles )
    for item in self.signature.itervalues():
      item.delayAttributeNotification( ignoreDoubles )


  def restartAttributeNotification( self ):
    super( HasSignature, self ).restartAttributeNotification()
    for item in self.signature.itervalues():
      item.restartAttributeNotification()
