#! /bin/env python
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

#
# This sample can be launched using the following syntax :
#     python <DIRECTORY_PATH>/signature_tg_example.py
# or directly calling :
#    <DIRECTORY_PATH>/signature_tg_example.py
# where <DIRECTORY_PATH> is the directory path that contains the current file
# Then access the url : http://localhost:8080/index
#
# Status : Work in progress ...

import sys, os, urllib, base64
import pkg_resources
pkg_resources.require("TurboGears>=1.0.4.4")

import turbogears, cherrypy
from cherrypy import request

from turbogears import controllers
from turbogears import validators
from turbogears.widgets.base import Widget, WidgetsList
from turbogears.widgets import CompoundWidget, CompoundFormField, \
                               CSSSource, JSSource, \
                               FieldSet, TextField, \
                               CheckBox, SingleSelectField, \
                               RadioButtonList, TableForm, \
                               RemoteForm

from soma.functiontools import partial
from soma.signature.api import Signature, VariableSignature, HasSignature, \
     Unicode, Choice, Number, Integer, Boolean, Undefined, Sequence, \
     ClassDataType, Bytes, FileName
from soma.tggui         import tools
from soma.tggui.api     import ApplicationTgGUI, TgGUI, TgRemoteForm, TgTextField, TgCheckBox, TgSingleSelectField, TgWindowsManager
from soma.signature.tggui.signature_tggui import HasSignature_TgGUI

#------------------------------------------------------------------------------
class Coordinate3D( HasSignature ):
  '''
  A simple coordinate in 3D referential.
  '''
  signature = Signature(
    'x', Number,
    'y', Number,
    'z', Number,
  )

  def __init__( self, x = 0, y = 0, z = 0 ):
    HasSignature.__init__( self )
    self.x, self.y, self.z = x, y, z
  
  
#------------------------------------------------------------------------------
class Box3D( HasSignature ):
  '''
  A bounding box composed of two Coordinate3D.
  '''
  signature = Signature(
    'corner1', Coordinate3D,
    'corner2', Coordinate3D,
  )
  
  def __init__( self, corner1=None, corner2=None ):
    HasSignature.__init__( self )
    if corner1 is None:
      corner1 = Coordinate3D()
    if corner2 is None:
      corner2 = Coordinate3D()
    self.corner1 = corner1
    self.corner2 = corner2
  
  
#------------------------------------------------------------------------------
class Sphere( HasSignature ):
  '''
  A sphere composed of one Coordinate3D and one radius.
  '''
  signature = Signature(
    'center', Coordinate3D, dict( defaultValue=Coordinate3D( 0,0,0 ) ),
    'radius', Number( minimum=0 ), dict( defaultValue=1 ),
  )

#------------------------------------------------------------------------------
class ROIAnalysis( HasSignature ):
  signature = Signature(
    #'image', FileName( readOnly=True ), dict( defaultValue=None, doc='Input image' ),
    'roiType', Choice( ( 'Box3D', Box3D ) , ( 'Sphere', Sphere ) ),
    'roiVisible', Boolean, dict( defaultValue=True ),
    'roi', Box3D, dict( doc='Type parameters of the ROI here' ),
  )
  
  
  def __init__( self ):
    HasSignature.__init__( self )
    self.signature = VariableSignature( self.signature )
    #self.images = [ 'firstImage', 'secondImage', 'thirdImage' ]
    self.roiType = Box3D
    self.roi = Box3D()
    self.onAttributeChange( 'roiType', self._roiTypeChanged )
    self.onAttributeChange( 'roiVisible', self._roiVisibilityChanged )
    self.bytes = ''
  
  def _roiVisibilityChanged( self, visible ):
    self.delayAttributeNotification( ignoreDoubles=True )
    self.signature[ 'roi' ].visible = visible
    self.restartAttributeNotification()

  
  def _roiTypeChanged( self, newType, oldType ):
    if newType is not oldType:
      self.delayAttributeNotification( ignoreDoubles=True )
      self.signature[ 'roi' ].type = newType
      self.roi = newType()
      self.restartAttributeNotification()

#------------------------------------------------------------------------------
class Coordinate3D_TgGUI( TgGUI ):
  '''
  This class redefine completely the GUI for Coordinate3D
  '''
  def __init__( self, instance ):
    super( Coordinate3D_TgGUI, self ).__init__( instance )
    
  def editionWidget( self, value, window, parent=None, name=None, live=False ):
    TgGUI.editionWidget( self, value, window, parent, name, live )
    widget = TgTextField( label = name )
    
    self._live = live
    self._name = name
    self._widget = widget
    if live:
      if value is not None:
        widget.startInternalModification()
        self.updateEditionWidget( widget, value )
        widget.stopInternalModification()
      self._widget.onAttributeChange( 'default', self._userModification )

    elif value is not None:
      self.updateEditionWidget( widget, value )

    return widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      editionWidget.removeOnAttributeChange( 'default' )
    
    editionWidget.close()

  def _userModification( self ):
    self.onWidgetChange.notify( self._widget ) 
  
  def _containerAttributeChanged( self, value ):
    self._widget.startInternalModification()
    self.updateEditionWidget( self._widget, value )
    self._widget.stopInternalModification()

  def setObject( self, editionWidget, value ):
    value.x, value.y, value.z = [ value.signature['x'].type.convert(i) \
                                  for i in str( editionWidget.default ).split() ]

  def updateEditionWidget( self, editionWidget, value, notifyObject = False ):
    if editionWidget is None :
      editionWidget = self._widget
    
    editionWidget.startInternalModification()
    editionWidget.setText( str( value.x ) + ' ' + str( value.y ) + ' ' + \
                          str( value.z ) )
    editionWidget.stopInternalModification()

  def unserializeEditionWidgetValue( self, value, notifyObject = False ):
    self._widget.startInternalModification()
    widgetid = self._widget.widgetid
    if ( isinstance( value, dict ) ):
      if ( widgetid in value ) :
       self._widget.setText( unicode( value[ widgetid ] ) )
      else :
        self._widget.setText( '' )
    else :
      self._widget.setText( unicode( value ) )
    self._widget.stopInternalModification()

#-------------------------------------------------------------------------------
class Box3D_TgGUI( HasSignature_TgGUI ):
  def _create_corner2_TgGUI( self, dataType, object, attributeName ):
    '''
    This method is called for creating the Qt3GUI of 'corner2' attribute.
    '''
    print 'Box3D_TgGUI._create_corner2_TgGUI', attributeName
    return HasSignature_TgGUI( dataType )

  def _createAttributeTgGUI( self, dataType, object, attributeName ):
    '''
    This method is called for creating the Qt3GUI of any attribute.
    '''
    print 'Box3D_TgGUI._createAttributeTgGUI', attributeName, dataType
    result = HasSignature_TgGUI._createAttributeTgGUI( self, dataType,
                    object, attributeName )
    print 'Box3D_TgGUI._createAttributeTgGUI done'
    return result

def printObject( o, indent = 0 ):
  it = iter( o.signature )
  it.next()
  for a in it:
    v = getattr( o, a, Undefined )
    if isinstance( v, HasSignature ):
      print '  ' * indent + a + ':'
      printObject( v, indent+1 )
    else:
      print '  ' * indent + a, '=', repr(v)

class ConfigurationError(Exception):
    pass

# Root class exposes http available adresses
class Root(controllers.RootController):
  appGUI = ApplicationTgGUI()

  images = {
  'collapsible' :
      'iVBORw0KGgoAAAANSUhEUgAAAAkAAAALCAYAAACtWacbAAAAUklEQVQYlY2Quw0AMQhDDbop3LL/SLReI1flFJGcAhWfJxswSbjFM5PMHHUYEQYAfpUBYB27ltIGkdx28xNQQa/AqfY/i7X/XUdySLIVmHXrBS/AHx/4NEmsoQAAAABJRU5ErkJggg==',
  'collapsed' :
      'iVBORw0KGgoAAAANSUhEUgAAAAkAAAALCAYAAACtWacbAAAAT0lEQVQYlWN89uwZAyHABGNISUn9R5ZA4UNN+o8LP3v2DGLSs2fPGLFZAxNnQhfAxmfCJoGugZEk3+EDLDDG3bt3/6NLKisrozocHyDKTQAjHStTXtw0IAAAAABJRU5ErkJggg==' }

  javascript = \
      '/**\n' \
      '* Wrapper around document.getElementById().\n' \
      '*/\n' \
      'function $(id) {\n' \
      '  return document.getElementById(id);\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Removes an element from the page\n' \
      '*/\n' \
      'function removeNode(node) {\n' \
      '  if (typeof node == \'string\') {\n' \
      '    node = $(node);\n' \
      ' }\n' \
      '  if (node && node.parentNode) {\n' \
      '    return node.parentNode.removeChild(node);\n' \
      '  }\n' \
      '  else {\n' \
      '    return false;\n' \
      '  }\n' \
      '}\n' \
      '/**\n' \
      '* Emulate PHP\'s ereg_replace function in javascript\n' \
      '*/\n' \
      'function eregReplace(search, replace, subject) {\n' \
      '  return subject.replace(new RegExp(search,\'g\'), replace);\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Returns true if an element has a specified class name\n' \
      '*/\n' \
      'function hasClass(node, className) {\n' \
      '  if (node.className == className) {\n' \
      '    return true;\n' \
      '  }\n' \
      '  var reg = new RegExp(\'(^| )\'+ className +\'($| )\')\n' \
      '  if (reg.test(node.className)) {\n' \
      '    return true;\n' \
      '  }\n' \
      '  return false;\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Adds a class name to an element\n' \
      '*/\n' \
      'function addClass(node, className) {\n' \
      '  if (hasClass(node, className)) {\n' \
      '    return false;\n' \
      '  }\n' \
      '  node.className += \' \' + className;\n' \
      '  return true;\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Removes a class name from an element\n' \
      '*/\n' \
      'function removeClass(node, className) {\n' \
      '  if (!hasClass(node, className)) {\n' \
      '    return false;\n' \
      '  }\n' \
      '  // Replaces words surrounded with whitespace or at a string border with a space. Prevents multiple class names from being glued together.\n' \
      '  node.className = eregReplace(\'(^|\\\\s+)\'+ className +\'($|\\\\s+)\', \' \', node.className);\n' \
      '  return true;\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Toggles a class name on or off for an element\n' \
      '*/\n' \
      'function toggleClass(node, className) {\n' \
      '  if (!removeClass(node, className) && !addClass(node, className)) {\n' \
      '    return false;\n' \
      '  }\n' \
      '  return true;\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Adds a function to the window onload event\n' \
      '*/\n' \
      'function addLoadEvent(func) {\n' \
      '  var oldOnload = window.onload;\n' \
      '  if (typeof window.onload != \'function\') {\n' \
      '    window.onload = func;\n' \
      '  }\n' \
      '  else {\n' \
      '    window.onload = function() {\n' \
      '      oldOnload();\n' \
      '      func();\n' \
      '    }\n' \
      '  }\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Only enable Javascript functionality if all required features are supported.\n' \
      '*/\n' \
      'function isJsEnabled() {\n' \
      '  if (typeof document.jsEnabled == \'undefined\') {\n' \
      '    // Note: ! casts to boolean implicitly.\n' \
      '    document.jsEnabled = !(\n' \
      '    !document.getElementsByTagName ||\n' \
      '    !document.createElement        ||\n' \
      '    !document.createTextNode       ||\n' \
      '    !document.documentElement      ||\n' \
      '    !document.getElementById);\n' \
      '  }\n' \
      '  return document.jsEnabled;\n' \
      '}\n' \
      '\n' \
      'function collapseAutoAttach() {\n' \
      '  var fieldsets = document.getElementsByTagName(\'fieldset\');\n' \
      '  var legend, fieldset;\n' \
      '  for (var i = 0; fieldset = fieldsets[i]; i++) {\n' \
      '    if (!hasClass(fieldset, \'collapsible\')) {\n' \
      '      continue;\n' \
      '    }\n' \
      '    legend = fieldset.getElementsByTagName(\'legend\');\n' \
      '    if (typeof legend == \'undefined\') {\n' \
      '      continue;\n' \
      '    }\n' \
      '    else if (legend.length == 0) {\n' \
      '      continue;\n' \
      '    }\n' \
      '    else if (legend[0].parentNode != fieldset) {\n' \
      '      continue;\n' \
      '    }\n' \
      '    legend = legend[0];\n' \
      '    var span = document.createElement(\'span\');\n' \
      '    span.innerHTML = \'&nbsp;\';\n' \
      '    var a = document.createElement(\'a\');\n' \
      '    a.href =  \'# \';' \
      '    a.onclick = function() {\n' \
      '      toggleClass(this.parentNode.parentNode, \'collapsed\');\n' \
      '      if (!hasClass(this.parentNode.parentNode, \'collapsed\')) {\n' \
      '        collapseScrollIntoView(this.parentNode.parentNode);\n' \
      '      }\n' \
      '      this.blur();\n' \
      '      return false;\n' \
      '    };\n' \
      '    a.appendChild( span );\n' \
      '    a.innerHTML += legend.innerHTML;\n' \
      '    while (legend.hasChildNodes()) {\n' \
      '      removeNode(legend.childNodes[0]);\n' \
      '    }\n' \
      '    legend.appendChild(a);\n' \
      '    //collapseEnsureErrorsVisible(fieldset);\n' \
      '  }\n' \
      '}\n' \
      '\n' \
      'function collapseEnsureErrorsVisible(fieldset) {\n' \
      '  if (!hasClass(fieldset, \'collapsed\')) {\n' \
      '    return;\n' \
      '  }\n' \
      '  var inputs = [];\n' \
      '  inputs = inputs.concat(fieldset.getElementsByTagName(\'input\'));\n' \
      '  inputs = inputs.concat(fieldset.getElementsByTagName(\'textarea\'));\n' \
      '  inputs = inputs.concat(fieldset.getElementsByTagName(\'select\'));\n' \
      '  for (var j = 0; j<3; j++) {\n' \
      '    for (var i = 0; i < inputs[j].length; i++) {\n' \
      '      if (hasClass(inputs[j][i], \'error\')) {\n' \
      '        return removeClass(fieldset, \'collapsed\');\n' \
      '      }\n' \
      '    }\n' \
      '  }\n' \
      '}\n' \
      '\n' \
      'function collapseScrollIntoView(node) {\n' \
      '  var h = self.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 0;\n' \
      '  var offset = self.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;\n' \
      '  var pos = absolutePosition(node);\n' \
      '  if (pos.y + node.scrollHeight > h + offset) {\n' \
      '    if (node.scrollHeight > h) {\n' \
      '      window.scrollTo(0, pos.y);\n' \
      '    } else {\n' \
      '      window.scrollTo(0, pos.y + node.scrollHeight - h);\n' \
      '    }\n' \
      '  }\n' \
      '}\n' \
      '\n' \
      '/**\n' \
      '* Retrieves the absolute position of an element on the screen\n' \
      '*/\n' \
      'function absolutePosition(el) {\n' \
      '  var sLeft = 0, sTop = 0;\n' \
      '  var isDiv = /^div$/i.test(el.tagName);\n' \
      '  if (isDiv && el.scrollLeft) {\n' \
      '    sLeft = el.scrollLeft;\n' \
      '  }\n' \
      '  if (isDiv && el.scrollTop) {\n' \
      '    sTop = el.scrollTop;\n' \
      '  }\n' \
      '  var r = { x: el.offsetLeft - sLeft, y: el.offsetTop - sTop };\n' \
      '  if (el.offsetParent) {\n' \
      '    var tmp = absolutePosition(el.offsetParent);\n' \
      '    r.x += tmp.x;\n' \
      '    r.y += tmp.y;\n' \
      '  }\n' \
      '  return r;\n' \
      '};\n' \
      '\n' \
      'function dimensions(el) {\n' \
      '  return { width: el.offsetWidth, height: el.offsetHeight };\n' \
      '}\n' \
      '\n' \
      'function autoSubmit() {\n' \
      '  var form = document.getElementsByTagName(\'form\');\n' \
      '  if (typeof form[0] != \'undefined\') {\n' \
      '    form[0].submit();\n' \
      '  }\n' \
      '}\n' \
      'function inputSubmitAttach( inputs ) {\n' \
      '  var input;\n' \
      '  for (var i = 0; input = inputs[i]; i++) {\n' \
      '    input.onchange = function() {\n' \
      '      autoSubmit(this);\n' \
      '      return false;\n' \
      '    };\n' \
      '  }\n' \
      '}\n' \
      'function inputAutoAttach() {\n' \
      '  inputSubmitAttach( document.getElementsByTagName(\'input\') );\n' \
      '  inputSubmitAttach( document.getElementsByTagName(\'textarea\') );\n' \
      '  inputSubmitAttach( document.getElementsByTagName(\'select\') );\n' \
      '}\n' \
      '\n' \
      'if (isJsEnabled()) {\n' \
      '  document.documentElement.className = \'js\';\n' \
      '  addLoadEvent(collapseAutoAttach);\n' \
      '  addLoadEvent(inputAutoAttach);\n' \
      '}\n'

  styles = '\n' \
    'html.js fieldset.collapsible legend a span {\n' \
    '  width : 13px;\n' \
    '  height : 13px;\n' \
    '  border-color : #ffffff;\n' \
    '  border-style : double;\n' \
    '  background: url(\'/getimage?imagename=collapsible\');\n' \
    '  background-color : #eff3f7;\n' \
    '  background-repeat : no-repeat;\n' \
    '  background-position : top center;\n' \
    '  margin-right : 3px;\n' \
    '  float : left;\n' \
    '  overflow : hidden;\n' \
    '}\n' \
    'html.js fieldset.collapsible legend a {\n' \
    '  text-decoration : none;\n' \
    '  color : #000000;\n' \
    '}\n' \
    'html.js fieldset.collapsed {\n' \
    '  border-bottom-width: 0;\n' \
    '  border-left-width: 0;\n' \
    '  border-right-width: 0;\n' \
    '  margin-bottom: 0;\n' \
    '}\n' \
    'html.js fieldset.collapsed * {\n' \
    '  display: none;\n' \
    '}\n' \
    'html.js fieldset.collapsed legend,\n' \
    'html.js fieldset.collapsed legend * {\n' \
    '  display: inline;\n' \
    '}\n' \
    'html.js fieldset.collapsed legend a span {\n' \
    '  background-image: url(\'/getimage?imagename=collapsed\');\n' \
    '}\n' \
    '/* Note: IE-only fix due to \'* html\' (breaks Konqueror otherwise). */\n' \
    '* html.js fieldset.collapsible legend a span {\n' \
    '  width : 17px;\n' \
    '  height : 17px;\n' \
    '  border-color : #eff3f7;\n' \
    '  border-width : 3px;\n' \
    '  margin-right : 0px;\n' \
    '}\n'

  @turbogears.expose()
  def index( self, *args, **kwargs ):
    # Get the current session
    session = cherrypy.session

    # Create styles to add to the output
    css = CSSSource( src = self.styles )
    js = JSSource( src = self.javascript )

    if 'roi' not in session :
      o = ROIAnalysis()
      session.acquire_lock()
      session[ 'roi' ] = o
      session.release_lock()
    else :
      o = session[ 'roi' ]

    if 'editionWidget' not in session :
      # Create default object
      editionWidget = self.appGUI.edit( o, live = True )
      session.acquire_lock()
      session[ 'editionWidget' ] = editionWidget
      session.release_lock()
    else :
      # Get objects from session
      editionWidget = session[ 'editionWidget' ]
      if ( len(kwargs) != 0 ) :
        editionWidget.setValues( kwargs )

    printObject(o)

    # Set values from the submitted form
    return css.render( kwargs ) + js.render( kwargs ) + editionWidget.render( kwargs )

  @turbogears.expose()
  def getimage(self, *args, **kwargs ) :

    if ( 'imagename' in kwargs ) :
      imagename = kwargs[ 'imagename' ]
    else :
      imagename = None

    if imagename in self.images :
      image = base64.b64decode( self.images[ imagename ] )
      
    return image

# Launches the web server
if __name__ == "__main__":
    try:
      webserverconfig = os.path.join(os.path.dirname(__file__), 'signature_tg_example.cfg')
      turbogears.update_config( configfile=webserverconfig )
      turbogears.start_server(Root())
  
    except ConfigurationError, exc:
        sys.stderr.write(str(exc))
        sys.exit(1)
