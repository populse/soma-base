# -*- coding: utf-8 -*-

'''This module enables to create automatic links between an object and a traits based controller.'''

from __future__ import absolute_import

from weakref import WeakKeyDictionary
from functools import partial
try:
  from traits.api import HasTraits
except ImportError:
  from enthought.traits.api import HasTraits
from soma.sorted_dictionary import SortedDictionary
from soma.factory import Factories


class ControllerFactories( Factories ):
  '''Holds association between an object and its controller'''
  def __init__( self ):
    super( ControllerFactories, self ).__init__()
    self._controllers = WeakKeyDictionary()


  def get_controller( self, instance ):
    '''Returns the Controller class associated to an object.'''
    controller = self._controllers.get( instance )
    if controller is None:
      factory = self.get_factory( instance )
      if factory is not None:
        controller = factory( instance )
        self._controllers[ instance ] = controller
    return controller

ControllerFactories.register_global_factory( HasTraits, lambda instance: instance )



class MetaController( HasTraits.__metaclass__ ):
  '''This metaclass allows for automatic registration of a Controller derived
  class for ControllerFactories (if the new class defines register_class_controller)
  and WidgetFactories (if the new class defines create_widget_from_ui)'''
  def __new__( mcs, name, bases, dictionary ):
    cls = super( MetaController, mcs ).__new__( mcs, name, bases, dictionary )
    
    controlled_class = dictionary.get( 'register_class_controller' )
    if controlled_class is not None:
      ControllerFactories.register_global_factory( controlled_class, cls )
    
    gui = dictionary.get( 'create_widget_from_ui' )
    if gui is not None:
      from soma.gui.widget_factory import WidgetFactories, create_widget_from_ui
      WidgetFactories.register_global_factory( cls, partial( create_widget_from_ui, gui ) )
    
    return cls


class Controller( HasTraits ):
  '''
  A Controller is a HasTraits that is connected to ControllerFactories and
  idgetFactories and provides some methods to inspect user defined traits.
  '''
  __metaclass__ = MetaController
  
  def user_traits( self, *args, **kwargs ):
    '''
    Returns a dictionnary containing class traits and instance traits defined by
    user  (i.e.  the traits that are not automatically defined by traits 
    module). Returned values are sorted according to the "order" trait attribute.
    '''
    traits = dict( (i, j) for i, j in self.class_traits().iteritems() if not i.startswith( 'trait_' ) )
    traits.update( self._instance_traits() )
    for name in traits.keys():
      if name.endswith( '_items' ) and name[ :-6 ] in traits:
        del traits[ name ]
    sorted_keys = [ t[1] for t in sorted( ( getattr( trait, 'order', '' ), name ) for name, trait in traits.iteritems() ) ]
    return SortedDictionary( *[ ( name, traits[ name ] ) for name in sorted_keys ] )

    
_type_to_trait_id = {
  int: 'Int',
  unicode: 'Unicode',
  str: 'Str',
  float: 'Float'
}

def trait_ids( trait ):
  main_id = trait.handler.__class__.__name__
  inner_ids = []
  if main_id == 'TraitCoerceType':
    real_id = _type_to_trait_id.get( trait.handler.aType )
    if real_id:
      main_id = real_id
  else:
    inner_id = '_'.join( ( trait_ids( i )[0] for i in trait.handler.inner_traits() ) )
    if not inner_id:
      klass = getattr( trait.handler, 'klass', None )
      if klass is not None:
        inner_ids = [ i.__name__ for i in klass.__mro__  ]
      else:
        inner_ids = []
    else:
      inner_ids = [ inner_id ]
  if inner_ids:
    return [ main_id + '_' + i for i in inner_ids ]
  else:
    return [ main_id ]
    
if __name__ == '__main__':
  from traits.api import *
  from soma.controller import *
  class C( Controller ):
      d = Dict( Str, Int )
      d2 = DictStrStr
      d3 = Dict( Str, Directory )
  o = C()
  print trait_ids(o.trait('d'))
  print trait_ids(o.trait('d2'))
  print trait_ids(o.trait('d3'))
