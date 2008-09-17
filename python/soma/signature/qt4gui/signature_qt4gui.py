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
Qt4GUI implementation for
L{HasSignature<soma.signature.api.HasSignature>}
data type.

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from PyQt4 import QtGui, QtCore
from soma.functiontools import partial
from soma.qt4gui.api import ApplicationQt4GUI, Qt4GUI

#-------------------------------------------------------------------------------
class HasSignatureEditionWidget( QtGui.QGroupBox ):
  _live = True
  # QPixmap instance cannot be build before a QApplication is being created.
  # (it simply exits the program). But for documentation with epydoc, all
  # modules are loaded without C{QApplication}. Therefore, the creation of
  # the following two static QPixmap instances has been put in __init__.
  _imageDown = None
  _imageUp = None
  
  def __init__( self, qtgui,object,
                parent=None, name=None, live=False ):
    if HasSignatureEditionWidget._imageDown is None:
      HasSignatureEditionWidget._imageDown = QtGui.QPixmap()
      HasSignatureEditionWidget._imageDown.loadFromData( \
        "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
        "\x49\x48\x44\x52\x00\x00\x00\x09\x00\x00\x00\x0b" \
        "\x08\x06\x00\x00\x00\xad\x59\xa7\x1b\x00\x00\x00" \
        "\x4f\x49\x44\x41\x54\x18\x95\x63\x7c\xf6\xec\x19" \
        "\x03\x21\xc0\x04\x63\x48\x49\x49\xfd\x47\x96\x40" \
        "\xe1\x43\x4d\xfa\x8f\x0b\x3f\x7b\xf6\x0c\x62\xd2" \
        "\xb3\x67\xcf\x18\xb1\x59\x03\x13\x67\x42\x17\xc0" \
        "\xc6\x67\xc2\x26\x81\xae\x81\x91\x24\xdf\xe1\x03" \
        "\x2c\x30\xc6\xdd\xbb\x77\xff\xa3\x4b\x2a\x2b\x2b" \
        "\xa3\x3a\x1c\x1f\x20\xca\x4d\x00\x23\x1d\x2b\x53" \
        "\x5e\xdc\x34\x20\x00\x00\x00\x00\x49\x45\x4e\x44" \
        "\xae\x42\x60\x82"
      )
      
      HasSignatureEditionWidget._imageUp = QtGui.QPixmap()
      HasSignatureEditionWidget._imageUp.loadFromData( \
        "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
        "\x49\x48\x44\x52\x00\x00\x00\x09\x00\x00\x00\x0b" \
        "\x08\x06\x00\x00\x00\xad\x59\xa7\x1b\x00\x00\x00" \
        "\x52\x49\x44\x41\x54\x18\x95\x8d\x90\xbb\x0d\x00" \
        "\x31\x08\x43\x0d\xba\x29\xdc\xb2\xff\x48\xb4\x5e" \
        "\x23\x57\xe5\x14\x91\x9c\x02\x15\x9f\x27\x1b\x30" \
        "\x49\xb8\xc5\x33\x93\xcc\x1c\x75\x18\x11\x06\x00" \
        "\x7e\x95\x01\x60\x1d\xbb\x96\xd2\x06\x91\xdc\x76" \
        "\xf3\x13\x50\x41\xaf\xc0\xa9\xf6\x3f\x8b\xb5\xff" \
        "\x5d\x47\x72\x48\xb2\x15\x98\x75\xeb\x05\x2f\xc0" \
        "\x1f\x1f\xf8\x34\x49\xac\xa1\x00\x00\x00\x00\x49" \
        "\x45\x4e\x44\xae\x42\x60\x82"
      )
    
    QtGui.QGroupBox.__init__( self, parent )
    if name:
      self.setObjectName(name)
    self._qtgui = qtgui
    self._live = live
    #self.setColumnLayout( 0, qt.Qt.Vertical )
    self._gridLayout = QtGui.QGridLayout()
    self._gridLayout.setAlignment( QtCore.Qt.AlignTop )
    self._gridLayout.setSpacing( 6 )
    self._gridLayout.setMargin( 11 )
    self.setLayout(self._gridLayout)
    
    self.btnExpand = None
    self.setFlat( True )
    #self._gridLayout.setMargin( 0 )
    
    self._createSignatureWidgets( object, live )
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
    self._collapsed = False
    self.btnExpand = QtGui.QPushButton( self )
    self.btnExpand.setIcon( QtGui.QIcon(self._imageUp) )
    self.btnExpand.resize( 20, 20 )
    pos = self.size() - self.btnExpand.size()
    self.btnExpand.move( pos.width(), 0 )
    self.connect( self.btnExpand, QtCore.SIGNAL( 'clicked()' ), 
                  self._expandOrCollapse )
    self.setTitle( label )
    self.setFlat( False )
    #self.setFrameShape( QtGui.QFrame.GroupBoxPanel )
  
  
  def _createSignatureWidgets( self, object, live ):
    self._attributesGUI = {}
    self._attributesGUI2 = {}
    layout = self._gridLayout
    layoutRow = 0
    it = object.signature.iteritems()
    it.next() # skip signature attribute
    for attributeName, signatureItem in it:
      if not signatureItem.visible: continue
      qtgui = self._qtgui._createAttributeQt4GUI( signatureItem.type, object, 
                                                  attributeName )
      attributeWidget = qtgui.editionWidget( getattr( object, attributeName ),
                                             parent=self, name=attributeName,
                                             live=live )
      labelWidget = qtgui.labelWidget( object, attributeName, attributeWidget,
                                       parent=self )
      if signatureItem.collapsed and isinstance( attributeWidget, HasSignatureEditionWidget ):
        attributeWidget._expandOrCollapse()
      if live:
        qtgui.onWidgetChange.add( self._attributeWidgetChanged )
      if labelWidget is None:
        layout.addWidget(attributeWidget, layoutRow, 0, 1, 2)
        #layout.addMultiCellWidget( attributeWidget, layoutRow, layoutRow, 
                                   #0, 1 )
        if signatureItem.doc:
          attributeWidget.setToolTip('<b>' + attributeName + 
                           ':</b> ' + signatureItem.doc)
      else:
        layout.addWidget( labelWidget, layoutRow, 0 )
        layout.addWidget( attributeWidget, layoutRow, 1 )
        if signatureItem.doc:
          tooltip = '<b>' + attributeName + ':</b> ' + \
                    signatureItem.doc
          labelWidget.setToolTip( tooltip )
          attributeWidget.setToolTip( tooltip )
        labelWidget.show()
      attributeWidget.show()
      self._attributesGUI[ attributeWidget ] = ( qtgui, attributeName, 
                                                 labelWidget )
      self._attributesGUI2[ attributeName ] = ( qtgui, attributeWidget, 
                                                 labelWidget )
      layoutRow += 1
  
  
  def _deleteSignatureWidgets( self ):
    for attributeWidget, ( qtgui, attributeName, labelWidget ) in \
        self._attributesGUI.iteritems():
      qtgui.onWidgetChange.remove( self._attributeWidgetChanged )
      qtgui.closeEditionWidget( attributeWidget )
      qtgui.closeLabelWidget( labelWidget )
  
  
  def _signatureChanged( self ):
    self._deleteSignatureWidgets()
    self._createSignatureWidgets( self.__object, True )
    ApplicationQt4GUI().widgetGeometryUpdater.update( self.topLevelWidget() )

  
  def _attributeChanged( self, attributeName, attributeValue, oldValue ):
    x = self._attributesGUI2.get( attributeName )
    if x is not None:
      qtgui, attributeWidget, labelWidget = x
      qtgui.updateEditionWidget( attributeWidget, attributeValue )
    
    
  
  
  def _setObject( self, object ):
    for attributeWidget, ( qtgui, attributeName, labelWidget ) in \
        self._attributesGUI.iteritems():
      if object.signature[ attributeName ].type.mutable:
        qtgui.setObject( attributeWidget, getattr( object, attributeName ) )
      else:
        setattr(object, attributeName, qtgui.getPythonValue( attributeWidget ) )


  def _attributeWidgetChanged( self, attributeWidget ):
    qtgui, attributeName, labelWidget = \
      self._attributesGUI[ attributeWidget ]
    try:
      if qtgui.dataTypeInstance.mutable:
        qtgui.setObject( attributeWidget, 
                        getattr( self.__object, attributeName ) )
      else:
        setattr( self.__object, attributeName,
                 qtgui.getPythonValue( attributeWidget ) )
    except ValueError:
      pass
  
  
  def closeEvent( self, event ):
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
    self._qtgui = None
    return QtGui.QGroupBox.closeEvent( self, event )


  def resizeEvent( self, resizeEvent ):
    result = QtGui.QGroupBox.resizeEvent( self, resizeEvent )
    if self.btnExpand is not None:
      pos = self.size() - self.btnExpand.size()
      self.btnExpand.move( pos.width(), 0 )
    return result
  
  
  def _expandOrCollapse( self ):
    if self._collapsed:
      self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding,
                             QtGui.QSizePolicy.Fixed ) )
      self.setMaximumHeight( 32767 )
      for attributeWidget, ( qtgui, attributeName, labelWidget ) in \
          self._attributesGUI.iteritems():
        attributeWidget.setEnabled( True )
        if labelWidget is not None:
          labelWidget.setEnabled( True )
      self.btnExpand.setIcon( QtGui.QIcon(self._imageUp) )
      self._collapsed = False
    else:
      self.setMaximumHeight( self.btnExpand.size().height() )
      for attributeWidget, ( qtgui, attributeName, labelWidget ) in \
          self._attributesGUI.iteritems():
        attributeWidget.setEnabled( False )
        if labelWidget is not None:
          labelWidget.setEnabled( False )
      self.btnExpand.setIcon( QtGui.QIcon(self._imageDown) )
      self._collapsed = True
    ApplicationQt4GUI().widgetGeometryUpdater.update( self.topLevelWidget() )


#-------------------------------------------------------------------------------
class HasSignature_Qt4GUI( Qt4GUI ):
  def editionWidget( self, object, parent=None, name=None, live=False ):
    return HasSignatureEditionWidget( self, object, parent, name, live )
  
  
  def closeEditionWidget( self, editionWidget ):
    editionWidget.close()
  
  
  def setObject( self, editionWidget, object ):
    editionWidget._setObject( object )
  
  
  def labelWidget( self, object, label, editionWidget, parent=None, name=None ):
    editionWidget._setLabel( label )
    return None

  
  def updateEditionWidget( self, editionWidget, object ):
    '''
    @todo: not implemented
    '''

  def _createAttributeQt4GUI( self, dataType, object, attributeName ):
    customizedMethod = getattr( self, '_create_' + attributeName + '_Qt4GUI',  
                                None )
    if customizedMethod is not None:
      return customizedMethod( dataType, object, attributeName )
    else:
      return ApplicationQt4GUI.instanceQt4GUI( dataType )
  

#-------------------------------------------------------------------------------
class ClassDataType_Qt4GUI( Qt4GUI ):
  '''
  A GUI for ClassDataType is a proxy on the GUI of the embedded class.
  '''
  def __init__( self, dataTypeInstance ):
    super( ClassDataType_Qt4GUI, self ).__setattr__(  '_ClassDataType_Qt4GUI__qtgui', ApplicationQt4GUI.classQt4GUI( dataTypeInstance.cls )( dataTypeInstance ) )
  
  
  def __getattribute__( self, name ):
    return getattr( super( ClassDataType_Qt4GUI, self ).__getattribute__( '_ClassDataType_Qt4GUI__qtgui' ), name )
  
  
  def __setattr__( self, name, value ):
    setattr( self.__qtgui, name, value )
