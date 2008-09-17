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
TgGUI implementation for
L{HasSignature<soma.signature.api.HasSignature>}
data type.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from turbogears.widgets.base import CSSLink, JSLink, js_location, mochikit
from soma.functiontools import partial
from soma.tggui import tools
from soma.tggui.api import ApplicationTgGUI, TgGUI, TgFieldSet

class HasSignatureEditionWidget( TgFieldSet ):
  _live = True

  def __init__( self, tggui, object,
                parent=None, name=None, live=False ):

    super(HasSignatureEditionWidget, self).__init__()
    self.css = [ CSSLink('static', 'css/hassignature.css') ]
    self.javascript = [mochikit, JSLink( 'static', 'js/library.js' ), JSLink( 'static', 'js/hassignature.js', location = js_location.bodybottom ) ]

    self._tggui = tggui
    self._live = live
    self._createSignatureWidgets( object, live )
    self.legend = name
    self.field_class = 'collapsible'

    if live:
      self.__object = object
      self.__object.onAttributeChange( 'signature', self._signatureChanged )
      self.__object.onAttributeChange(  self._attributeChanged )
      it = self.__object.signature.iteritems()
      it.next() # skip signature attribute
      for attributeName, signatureItem in it:
        signatureItem.onAttributeChange( 'type', self._signatureChanged )
        signatureItem.onAttributeChange( 'visible', self._signatureChanged )
    
  
  def _setLabel( self, label ):
    self.legend = label

  def _createSignatureWidgets( self, object, live ):

    layoutRow = 0
    self.fields = []
    self._attributesGUI = {}
    self._attributesGUI2 = {}

    it = object.signature.iteritems()
    it.next() # skip signature attribute

    for attributeName, signatureItem in it:
      if not signatureItem.visible: continue

      tggui = self._tggui._createAttributeTgGUI( signatureItem.type, object,
                                                  attributeName )
      attributeWidget = tggui.editionWidget( getattr( object, attributeName ), self._tggui.window,
                                             parent=self, name=unicode(attributeName),
                                             live=live )
      labelWidget = tggui.labelWidget( object, unicode(attributeName), attributeWidget,
                                       parent=self )
      if signatureItem.collapsed and isinstance( attributeWidget, HasSignatureEditionWidget ):
        attributeWidget._expandOrCollapse()
        
      if live:
        tggui.onWidgetChange.add( self._attributeWidgetChanged )
        
      if labelWidget is None:
        self.fields.append( attributeWidget )
        if signatureItem.doc :
          tooltip = attributeName + ': ' + \
                    signatureItem.doc

          if hasattr(attributeWidget, 'label_attrs') :
            attributeWidget.label_attrs['title'] = tooltip
            
          if hasattr(attributeWidget, 'attrs') :
            attributeWidget.attrs['title'] = tooltip
          
      else:
        self.fields.append( labelWidget )
        self.fields.append( attributeWidget )
        
        if signatureItem.doc :
          tooltip = attributeName + ': ' + \
                    signatureItem.doc

          if hasattr(labelWidget, 'attrs') :
            labelWidget.attrs['title'] = tooltip
            
          if hasattr(attributeWidget, 'attrs') :
            attributeWidget.attrs['title'] = tooltip

      self._attributesGUI[ attributeWidget ] = ( tggui, attributeName,
                                                 labelWidget )
      self._attributesGUI2[ attributeName ] = ( tggui, attributeWidget,
                                                 labelWidget )
      layoutRow += 1

  def _deleteSignatureWidgets( self ):
    for attributeWidget, ( tggui, attributeName, labelWidget ) in \
        self._attributesGUI.iteritems():

      tggui.onWidgetChange.remove( self._attributeWidgetChanged )
      tggui.closeEditionWidget( attributeWidget )
      tggui.closeLabelWidget( labelWidget )
  
  def _signatureChanged( self ):
    self._deleteSignatureWidgets()
    self._createSignatureWidgets( self.__object, True )

  def _attributeChanged( self, attributeName, attributeValue, oldValue ):
    x = self._attributesGUI2.get( attributeName )
    if x is not None:
      tggui, attributeWidget, labelWidget = x
      tggui.updateEditionWidget( attributeWidget, attributeValue )

  def _setObject( self, object ):
    for attributeWidget, ( tggui, attributeName, labelWidget ) in \
        self._attributesGUI.iteritems():
      if object.signature[ attributeName ].type.mutable:
        tggui.setObject( attributeWidget, getattr( object, attributeName ) )
      else:
        setattr(object, attributeName, tggui.getPythonValue( attributeWidget ) )

  def _attributeWidgetChanged( self, attributeWidget ):
    tggui, attributeName, labelWidget = \
      self._attributesGUI[ attributeWidget ]
    try:
      if tggui.dataTypeInstance.mutable:
        tggui.setObject( attributeWidget,
                        getattr( self.__object, attributeName ) )
      else:
        setattr( self.__object, attributeName,
                 tggui.getPythonValue( attributeWidget ) )
    except ValueError:
      pass
  
  
  def close( self ):
    # Cleanup: remove callbacks and break garbage collection loops
    if self._live:
      self.__object.removeOnAttributeChange( 'signature', self._signatureChanged )
      self.__object.removeOnAttributeChange( self._attributeChanged )

      it = self.__object.signature.itervalues()
      it.next() # skip signature
      for signatureItem in it:
        signatureItem.removeOnAttributeChange( 'type', self._signatureChanged )
        signatureItem.removeOnAttributeChange( 'visible', self._signatureChanged )
      
      
      self.__object = None
    self._deleteSignatureWidgets()
    self._tggui = None
    return None


  def resizeEvent( self, resizeEvent ):
    return None
  
  
  def _expandOrCollapse( self ):
    if self._collapsed:
      self._collapsed = False
    else:
      self._collapsed = True

  def setCaption( self, caption ):
    '''
    @see: L{}
    '''
    self.legend = caption

  def caption( self ):
    '''
    @see: L{}
    '''
    return self.legend
  
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

#-------------------------------------------------------------------------------
class HasSignature_TgGUI( TgGUI ):
  def editionWidget( self, object, window, parent=None, name=None, live=False ):
    TgGUI.editionWidget( self, object, window, parent, name, live )
    widget = HasSignatureEditionWidget( self, object, parent, name, live )

    return widget
  
  
  def closeEditionWidget( self, editionWidget ):
    editionWidget.close()
  
  
  def setObject( self, editionWidget, object ):
    editionWidget._setObject( object )
  
  
  def labelWidget( self, object, label, editionWidget, parent=None, name=None ):
    #editionWidget._setLabel( label )
    return None

  
  def updateEditionWidget( self, editionWidget, object ):
    '''
    @todo: not implemented
    '''

  def _createAttributeTgGUI( self, dataType, object, attributeName ):
    customizedMethod = getattr( self, '_create_' + attributeName + '_TgGUI',
                                None )
    if customizedMethod is not None:
      return customizedMethod( dataType, object, attributeName )
    else:
      return ApplicationTgGUI.instanceTgGUI( dataType )
  

#-------------------------------------------------------------------------------
class ClassDataType_TgGUI( TgGUI ):
  '''
  A GUI for ClassDataType is a proxy on the GUI of the embedded class.
  '''
  def __init__( self, dataTypeInstance ):
    super( ClassDataType_TgGUI, self ).__setattr__(  '_ClassDataType_TgGUI__tggui', ApplicationTgGUI.classTgGUI( dataTypeInstance.cls )( dataTypeInstance ) )
  
  
  def __getattribute__( self, name ):
    return getattr( super( ClassDataType_TgGUI, self ).__getattribute__( '_ClassDataType_TgGUI__tggui' ), name )
  
  
  def __setattr__( self, name, value ):
    setattr( self.__tggui, name, value )
