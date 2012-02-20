# -*- coding: utf-8 -*-
from weakref import WeakKeyDictionary
from functools import partial
from enthought.traits.api import HasTraits
from soma.factory import Factories


class ControllerFactories( Factories ):  
  def __init__( self ):
    super( ControllerFactories, self ).__init__()
    self._controllers = WeakKeyDictionary()


  def get_controller( self, object ):
    controller = self._controllers.get( object )
    if controller is None:
      factory = self.get_factory( object )
      if factory is not None:
        controller = factory( object )
        self._controllers[ object ] = controller
    return controller

ControllerFactories.register_global_factory( HasTraits, lambda object: object )



class MetaController( HasTraits.__metaclass__ ):
  def __new__( mcs, name, bases, dict ):
    cls = super( MetaController, mcs ).__new__( mcs, name, bases, dict )
    
    controlled_class = dict.get( 'register_class_controller' )
    if controlled_class is not None:
      ControllerFactories.register_global_factory( controlled_class, cls )
    
    ui = dict.get( 'create_widget_from_ui' )
    if ui is not None:
      from soma.gui.widget_factory import WidgetFactories, create_widget_from_ui
      WidgetFactories.register_global_factory( cls, partial( create_widget_from_ui, ui ) )
    
    return cls


class Controller( HasTraits ):
  __metaclass__ = MetaController
  
  def trait_names( self, *args, **kwargs ):
    return self.class_trait_names( *args, **kwargs )



