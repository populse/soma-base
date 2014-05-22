# -*- coding: utf-8 -*-
from soma.qt_gui.qt_backend import QtCore, QtGui
from soma.qt_gui.qt_backend.QtCore import QObject, SIGNAL
from soma.qt_gui.qt_backend.QtGui import QWidget, QVBoxLayout

from soma.application import Application
from soma.controller import trait_ids


class WidgetToControllerConnector( object ):
  @staticmethod
  def widget_ids( widget ):
    return [ klass.__name__ for klass in widget.__class__.__mro__ if issubclass( klass, QWidget ) ]
  
  default_factory = {}
  
  
  def __init__( self ):
    self.factory = {}
  
  def get_factory( self, trait_id, widget_id ):
    key = ( trait_id, widget_id )
    factory = self.factory.get( key )
    if factory is None:
      factory = self.default_factory.get( key )
    return factory
  
  
  def connect( self, controller, widget ):
    #print '!connect!', controller, widget
    for trait_name in controller.trait_names():
      #print '!connect! 2', trait_name
      subwidget = getattr( widget, trait_name, None )
      if isinstance( subwidget, QWidget ):
        #print '!connect! 3', subwidget
        for trait_id in trait_ids( controller.trait( trait_name ) ):
          for widget_id in self.widget_ids( subwidget ):
            #print '!connect! 4', trait_id, widget_id
            connector_factory = self.get_factory( trait_id, widget_id )
            if connector_factory is not None:
              connector = connector_factory( controller, trait_name, subwidget )
              #print '!connect! 5', connector
              break



class TraitWidgetConnector( QObject ):
  def __init__( self, controller, attribute_name, widget ):
    super( QObject, self ).__init__( widget )
    self.controller = controller
    self.attribute_name = attribute_name
    self._ignore_update = False
    self.connect_widget()
    self.controller.on_trait_change( self._update_widget, self.attribute_name )
    self.update_widget()
  
  def __del__( self ):
    self.disconnect_widget()
    self.controller.on_trait_change( self._update_widget, self.attribute_name, remove=True )

  def _update_widget( self ):
    if self._ignore_update == False:
      self._ignore_update = True
      try:
        self.update_widget()
      finally:
        self._ignore_update = False

class Connector_Unicode_QLineEdit( TraitWidgetConnector ):
  unicode_to_attribute = lambda x: x
  attribute_to_unicode = unicode
  
  def connect_widget( self ):
    self.connect( self.parent(), SIGNAL( 'textChanged( const QString & )' ), self.update_controller )
  
  def disconnect_widget( self ):
    try:
      self.disconnect( self.parent(), SIGNAL( 'textChanged( const QString & )' ), self.update_controller )
    except RuntimeError:
      pass
  
  def update_widget( self ):
    self.parent().setText( self.attribute_to_unicode( getattr( self.controller, self.attribute_name ) ) )

  def update_controller( self ):
    setattr( self.controller, self.attribute_name, self.unicode_to_attribute( self.parent().text() ) )
WidgetToControllerConnector.default_factory[ ( 'Unicode', 'QLineEdit' ) ] = Connector_Unicode_QLineEdit
WidgetToControllerConnector.default_factory[ ( 'String', 'QLineEdit' ) ] = Connector_Unicode_QLineEdit
WidgetToControllerConnector.default_factory[ ( 'Str', 'QLineEdit' ) ] = Connector_Unicode_QLineEdit


class Connector_Float_QLineEdit( Connector_Unicode_QLineEdit ):
  unicode_to_attribute = float
WidgetToControllerConnector.default_factory[ ( 'Float', 'QLineEdit' ) ] = Connector_Float_QLineEdit


class Connector_Int_QLineEdit( Connector_Unicode_QLineEdit ):
  unicode_to_attribute = int
WidgetToControllerConnector.default_factory[ ( 'Int', 'QLineEdit' ) ] = Connector_Int_QLineEdit


class Connector_Bool_QCheckBox( TraitWidgetConnector ):
  def connect_widget( self ):
    self.connect( self.parent(), SIGNAL( 'stateChanged ( int )' ), self.update_controller )
  
  def disconnect_widget( self ):
    TODO
    self.disconnect( self.parent(), SIGNAL( 'stateChanged ( int )' ), self.update_controller )
  
  def update_widget( self ):
    self.parent().setChecked( getattr( self.controller, self.attribute_name ) )

  def update_controller( self ):
    setattr( self.controller, self.attribute_name, self.parent().isChecked() )
WidgetToControllerConnector.default_factory[ ( 'Bool', 'QCheckBox' ) ] = Connector_Bool_QCheckBox


class Connector_ListFloat_QLineEdit( TraitWidgetConnector ):
  def __init__( self, controller, attribute_name, widget ):
    super( Connector_ListFloat_QLineEdit, self ).__init__( controller, attribute_name, widget )
    self.controller.on_trait_change( self._update_widget, attribute_name + '_items' )
  
  def connect_widget( self ):
    self.connect( self.parent(), SIGNAL( 'textChanged( const QString & )' ), self.update_controller )
    
  def disconnect_widget( self ):
    self.disconnect( self.parent(), SIGNAL( 'textChanged( const QString & )' ), self.update_controller )
    
  def update_widget( self ):
    self.parent().setText( ' '.join( ( str(i) for i in getattr( self.controller, self.attribute_name ) ) ) )

  def update_controller( self ):
    setattr( self.controller, self.attribute_name, [ float(i) for i in self.parent().text().split() ] )
WidgetToControllerConnector.default_factory[ ( 'List_Float', 'QLineEdit' ) ] = Connector_ListFloat_QLineEdit


class Connector_Float_QSlider( TraitWidgetConnector ):
  def connect_widget( self ):
    self.connect( self.parent(), SIGNAL('valueChanged( int )' ), self.update_controller )
    
  def disconnect_widget( self ):
    self.disconnect( self.parent(), SIGNAL( 'valueChanged( int )' ), self.update_controller )
    
  def update_widget( self ):
    self.parent().setValue( getattr( self.controller, self.attribute_name ) )

  def update_controller( self ):
    setattr( self.controller, self.attribute_name, self.parent().value() )
WidgetToControllerConnector.default_factory[ ( 'Float', 'QSlider' ) ] = Connector_Float_QSlider


class Connector_object_QFrame( TraitWidgetConnector ):
  def connect_widget( self ):
    self.layout = QVBoxLayout( self.parent() )
    self.subwidget = Application().gui.create_widget( getattr( self.controller, self.attribute_name ), parent=self.parent(), live=True )
    if self.subwidget is not None:
      self.layout.addWidget( self.subwidget )
  
  def disconnect_widget( self ):
    pass
  
  def update_widget( self ):
    pass

  def update_controller( self ):
    pass
WidgetToControllerConnector.default_factory[ ( 'Instance_object', 'QFrame' ) ] = Connector_object_QFrame
