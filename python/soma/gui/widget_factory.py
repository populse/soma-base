# -*- coding: utf-8 -*-

try:
    from traits.api import HasTraits
except:
    from enthought.traits.api import HasTraits
from soma.qt_gui.qt_backend import set_qt_backend, loadUi
from soma.factory import Factories
from soma.controller import Controller
from soma.application import Application
from soma.gui.widget_controller_creation import ControllerWidget


class WidgetFactories( Factories ):  
  def get_global_factory( self, key ):
    name = getattr( key, '__name__', None )
    #print '!get_global_factory!', key, name
    #if name:
      #import_feature( 'widget_factory.' + name )
    result = super( WidgetFactories, self ).get_global_factory( key )
    #print '!get_global_factory! ->', result, self._global_factories.keys()
    return result
    
  
  def create_widget( self, object, parent=None, live=False ):
    factory = self.get_factory( object )
    if factory is not None:
      return factory( object, parent=parent, live=live )
    if not isinstance( object, Controller ):
      controller = Application().get_controller( object )
      if controller is not None:
        return self.create_widget( controller, parent=parent, live=live )
    return None


def controller_widget_factory( controller, parent=None, live=False ):
 return ControllerWidget( controller, parent=parent, live=live )
 #trait_view = has_traits.trait_view()
  #trait_view.buttons = []
  #if live:
    #kwargs = { 'kind': 'live' }
  #else:
    #kwargs = {}
  #trait_ui = trait_view.ui( has_traits, **kwargs )
  #if parent is not None:
    #trait_ui.control.setParent( parent )
  #trait_ui.control._trait_ui = trait_ui
  #return trait_ui.control

WidgetFactories.register_global_factory( Controller, traits_widget_factory )


def create_widget_from_ui( ui, controller, parent=None, live=False ):
  set_qt_backend()
  widget = loadUi( ui )
  if parent is not None:
    widget.setParent( parent )
  if live:
    Application().gui.connect_widget( controller, widget )
  return widget

