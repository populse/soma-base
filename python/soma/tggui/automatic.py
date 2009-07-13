# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
#
# This software is governed by the CeCILL license version 2 under 
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
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
# knowledge of the CeCILL license version 2 and that you accept its terms.

'''
Customizable framework for automatic creation of
U{Turbogears<http://docs.turbogears.org>} widgets to view or edit any
Python object. This framework is especially designed to work with 
L{soma.signature} module but it can be used in many other contexts.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


import __builtin__
if not hasattr( __builtin__, 'set' ):
  from sets import Set as set

import cherrypy, turbogears
import turbogears.widgets
from turbogears.widgets.base import JSLink, js_location, mochikit
from turbogears.widgets import Label, FormFieldsContainer, HiddenField
from turbogears.util import to_unicode

from soma.decorators import synchronized
from soma.gui.base import ApplicationBaseGUI, GUI
from soma.tggui import tools
from soma.tggui.standard_widgets import TgRemoteForm
from soma.translation import translate as _
from soma.notification import Notifier
from soma.undefined import Undefined
from soma.signature.api import DataType
from soma.uuid import Uuid
from soma.functiontools import partial

import sys, os, os.path, urllib
import sip

class TgWindowsManager( object ) :
  '''
  C{TgWindowsManager} class manages opened windows for a session.
  '''
  windows = dict()
  
  def __new__( cls, session = cherrypy.session ):
    '''
    Only instanciates a new C{TgWindowsManager} class if none exists for the current session.
    '''
    if 'windows' in session :
      instance = session[ 'windows' ]
    else :
      instance = None

    if instance is None :
      instance = object.__new__( cls )
      session.acquire_lock()
      session[ 'windows' ] = instance
      session.release_lock()
      
    return instance

  def setWidgetValues( self, values, windowkey = 'windowid' ) :
    '''
    Recursively set widget values from L{dict}.
    Try to retrieve the window id in values L{dict}.
    '''
    if ( windowkey in values ) :
      # Get the window id from values
      windowid = values[ windowkey ]

      if windowid in windows :
        window = windows[ windowid ]
        window.setWidgetValues( values )
    
  __getitem__ = windows.__getitem__
  __setitem__ = windows.__setitem__
  __contains__ = windows.__contains__

class TgWindow( object ) :
  '''
  C{TgWindow} identifies a client browser.
  '''
  
  def __new__( cls, windowid = None ) :
    '''
    Only instanciates a new C{TgWindows} class if none exists for associates L{TgManager}.
    '''
    manager = getattr( cls, 'manager', None )
    if manager is None :
      # It is necessary to manually instanciate a TgWindowsManager
      manager = TgWindowsManager()
      cls.manager = manager

    widgets = getattr( cls, 'widgets', None )
    if widgets is None :
      cls.widgets = list()
    
    if windowid is None :
      # Generate a new unique identifier
      windowid = unicode( Uuid() ).replace( '-', '' )

    if windowid in manager :
      # Get the existing instance
      instance = manager[ windowid ]
    else :
      # Get a new window instance
      instance = object.__new__( cls )
      instance.windowid = windowid
      manager[ windowid ] = instance

    return instance
        
  def addWidget( self, widget ) :
    '''
    Add widget for the L{TgGUI}.
    '''
    self.widgets.append( widget )
    
    # Add delete method
    method = partial( self.removeWidget, widget )
    setattr( widget, '__del__', method )

  def removeWidget( self, widget = None ) :
    if not widget is None :
      self.widgets.remove( widget )

  def setWidgetValues( self, values ) :
    '''
    Recursively set widget values from L{dict}.
    '''
    for widget in self.widgets :
      unserializeMethod = getattr( widget, 'unserializeEditionWidgetValue', None )

      if unserializeMethod is not None :
        unserializeMethod.__call__( values, True )

#------------------------------------------------------------------------------
class EditionDialog( TgRemoteForm ):
  template = """
  <form xmlns:py="http://purl.org/kid/ns#"
      name="${name}"
      action="${action}"
      method="${method}"
      class="tableform"
      py:attrs="form_attrs"
  >
      <div py:for="field in hidden_fields"
          py:replace="field.display(value_for(field), **params_for(field))"
      />
      <table border="0" cellspacing="0" cellpadding="0" py:attrs="table_attrs">
          <tr py:for="i, field in enumerate(fields)"
              class="${i%2 and 'odd' or 'even'}"
          >
              <th py:if="field.label is not None">
                  <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
              </th>
              <td py:attrs="{ 'colspan' : field.label and 1 or 2 }">
                  <span py:replace="field.display(value_for(field), **params_for(field))" />
                  <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                  <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
              </td>
          </tr>
          <tr>
              <td py:content="submit.display(submit_text)" />
              <td>&#160;</td>
          </tr>
      </table>
  </form>
  """
  #form_attrs = { 'onsubmit' : 'return validate()' }
    
  def __init__( self, object, parent = None, name = None, live=False, modal=False, wflags=0 ):
    super( EditionDialog, self ).__init__( name = name, submit_text = 'Ok' )

    self.javascript = [ mochikit, JSLink( 'static', 'js/soma.js' ) ]
    
    # Add a window id hidden field
    self.window = TgWindow()
    windowidfield = HiddenField( name = 'windowid', default = self.window.windowid )

    # Create associated objects
    self.__tggui = ApplicationTgGUI.instanceTgGUI( object )
    self.__widget = self.__tggui.editionWidget( object, self.window, parent=self, live=True )
    self.fields = [ windowidfield, self.__widget ]

    icon = self.__widget.icon()
    if icon is not None:
      self.setIcon( icon )
    
    self.setCaption( self.__widget.caption() )

  def setCaption( self, caption ):
    '''
    @see: L{}
    '''
    self.label = caption

  def caption( self ):
    '''
    @see: L{}
    '''
    return self.label
    
  def setIcon( self, icon ):
    '''
    @see: L{}
    '''
    pass
  
  def icon( self ):
    '''
    @see: L{}
    '''
    return None

  @synchronized
  def cleanup( self, alsoDelete=False ):
    self.__tggui.closeEditionWidget( self.__widget )
    self.__widget = None
    self.__tggui = None
  
  @synchronized
  def setObject( self, object ):
    self.__tggui.setObject( self.__widget, object )

  @synchronized
  def setValues( self, values ):
    self.delayAttributeNotification( ignoreDoubles=True )
    self.window.setWidgetValues( values )
    self.restartAttributeNotification()

  @synchronized
  def __del__( self ):
    if not self.__tggui is None :
      self.__tggui.__del__()
  

#-------------------------------------------------------------------------------
class ApplicationTgGUI( ApplicationBaseGUI ):
  '''
  This class manage the creation of Tg widgets for Python objects edition at
  global (I{i.e.} application) level.
  '''

  instanceTgGUI = staticmethod( partial( ApplicationBaseGUI.instanceGUI, _suffix = 'Tg' ) )
  classTgGUI = staticmethod( partial( ApplicationBaseGUI.classGUI, _suffix = 'Tg' ) )

  def createEditionDialog( self, object, parent = None, name = None,
                           live=False, modal=False, wflags=0 ):
    '''
    Create a QDialog allowing to edit an object.
    '''
    return EditionDialog( object, parent=parent, name=name, live=live, modal=modal, wflags=wflags )

  def closeEditionDialog( self, dialog ):
    '''
    Must be called after a call to createEditionDialog. Properly destroy all 
    children widgets and objects created with a default edition dialog.
    '''
    dialog.cleanup()

  def edit( self, object, live=True, parent=None ):
    return self.createEditionDialog( object, parent=parent, live=live )


#-------------------------------------------------------------------------------

class TgGUI( GUI ):
  '''
  This class manage the creation of Turbogears widgets for Python objects edition at
  object level. 
  '''

  def editionWidget( self, object, window, parent = None, name = None, live = False ):
    '''
    Create a widget for editing an object.
    '''
    self.registerGUI( window )

  def labelWidget( self, object, label, editionWidget=None,
                   parent = None, name = None, live = False ):
    '''
    Create a label widget for displaying a label associated with the edition
    widget. If C{editionWidget} already have the possibility to display the
    label (such as in L{qt.QGroupBox}) it sets the label on C{editionWidget}
    and returns C{None}. Returns a L{qt.QLabel} instance by default.
    @todo: C{editionWidget} should be mandatory.
    '''
    #return Label( label = label, name = name )
    return None
  
  def registerGUI( self, window ) :
    '''
    Register edition widgets for the given L{window<soma.TgWindow>}.
    '''
    if ( window is not None ) :
      self.window = window

    if ( getattr( self, 'window', None ) is not None  ) :
      # Register the current widget for the known window
      self.window.addWidget( self )
      
  def findValueFromParams( self, params, widgetid, widgetname, default = None ) :
      '''
      Get the value for the widget from given parameters.
      @param params: parameters to get widget value from.
      @type widgetid: String
      @param widgetid: id of the widget to find value for.
      @type widgetname: String
      @param widgetname: name of the widget to find value for.
      @return: value for the widget from parameters.
      '''
      if ( isinstance( params, dict ) ):
        if ( widgetid in params ) :
          result = params[ widgetid ]
        elif ( widgetname in params ) : 
          result = params[ widgetname ]
        else :
          result = default
      else :
        result = params
      return result
