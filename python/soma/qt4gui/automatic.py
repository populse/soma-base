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
U{Qt 4<http://www.trolltech.com/products/qt/qt4>} widgets to view or edit any
Python object. This framework is especially designed to work with 
L{soma.signature} module but it can be used in many other contexts.

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


import __builtin__
if not hasattr( __builtin__, 'set' ):
  from sets import Set as set

from soma.translation import translate as _
from soma.signature.api import DataType
from soma.gui.base import ApplicationBaseGUI, GUI

from soma.functiontools import partial
import sys
from PyQt4 import QtGui, QtCore
import sip


#-------------------------------------------------------------------------------
class WidgetGeometryUpdater( object ):
  '''
  Qt does not update layout correctly when widget are changing (i.e. when you
  remove/add widgets in a contener), this class allow to fix this problem. The
  only thing I have found to fix the layout is to:
    1) resize the widget
    2) process Qt events
    3) restore original size
  However, events cannot be processed in all cases without crashing the
  application. Therefore, I use another trick. When the user ask for geometry
  update of a widget (with L{udate} method), the widget is stored and the real
  geometry update is started by a single shot timer event (with 0 as delay).
  During the timer event C{qt.qApp.processEvents()} can be called without
  crashing the application.
  '''
  def __init__( self ):
    self._widgetsToUpdate = []
  
  
  def update( self, widget ):
    '''
    Will update C{widget} geometry next time Qt process timer events. The
    following operations will be done:
      1) Increment width and height of widget by one
      2) Process Qt events
      3) Restore widget initial size
    '''
    self._widgetsToUpdate.append( widget )
    QtCore.QTimer.singleShot( 0, self._updateAllWidgetsGeometry )


  def _updateAllWidgetsGeometry( self ):
    widgetsToUpdate = [widget for widget in self._widgetsToUpdate if not sip.isdeleted(widget)]
    sizes = [widget.size() for widget in widgetsToUpdate] 
    for widget, size in zip( widgetsToUpdate, sizes ): 
      widget.resize( size.width() + 1, size.height() + 1 ) 
    QtGui.qApp.processEvents()
    for widget, size in zip( widgetsToUpdate, sizes ): 
      widget.resize( size )


#------------------------------------------------------------------------------
class EditionDialog( QtGui.QDialog ):
  def __init__( self, object, parent = None, name = None, live=False, modal=False, wflags=QtCore.Qt.WindowFlags() ):
    super( EditionDialog, self ).__init__( parent, wflags )
    if name:
      self.setObjectName(name)
    self.setModal(modal)
    # window modal means that the dialog will block only its parent windows in modal mode, which is set automatically when calling exec_ method
    self.setWindowModality(QtCore.Qt.WindowModal)
    layout = QtGui.QVBoxLayout( )
    layout.setMargin(11)
    layout.setSpacing(6)
    self.setLayout(layout)
    
    self.__qtgui = ApplicationQt4GUI.instanceQt4GUI( object )
    self.__widget = self.__qtgui.editionWidget( object, parent=None, live=live )
    layout.addWidget( self.__widget )
    self.__widget.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding))
    icon = self.__widget.windowIcon()
    if icon is not None:
      self.setWindowIcon( icon )
    
    self.setWindowTitle( self.__widget.windowTitle() )
    
    layout1 = QtGui.QHBoxLayout()
    layout1.setMargin(0)
    layout1.setSpacing(6)
    layout.addLayout( layout1 )
    spacer1 = QtGui.QSpacerItem(31,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
    layout1.addItem(spacer1)

    self.btnOk = QtGui.QPushButton( _( '&Ok' ) )
    self.btnOk.setDefault( True )
    layout1.addWidget( self.btnOk )
    self.connect( self.btnOk, QtCore.SIGNAL( 'clicked()' ), QtCore.SLOT( 'accept()' ) )
    
    self.btnCancel = QtGui.QPushButton( _( '&Cancel' ) )
    layout1.addWidget( self.btnCancel )
    self.connect( self.btnCancel, QtCore.SIGNAL( 'clicked()' ), QtCore.SLOT( 'reject()' ) )


  def cleanup( self, alsoDelete=False ):
    self.__qtgui.closeEditionWidget( self.__widget )
    self.__widget = None
    self.__qtgui = None
  
  def setObject( self, object ):
    self.__qtgui.setObject( self.__widget, object )
  

#-------------------------------------------------------------------------------
class ApplicationQt4GUI( ApplicationBaseGUI ):
  '''
  This class manage the creation of Qt widgets for Python objects edition at
  global (I{i.e.} application) level.
  '''

  instanceQt4GUI = staticmethod( partial( ApplicationBaseGUI.instanceGUI, _suffix = 'Qt4' ) )
  classQt4GUI = staticmethod( partial( ApplicationBaseGUI.classGUI, _suffix = 'Qt4' ) )

  def __singleton_init__( self ):
    self.widgetGeometryUpdater = WidgetGeometryUpdater()
  
  def createEditionDialog( self, object, parent = None, name = None,
                           live=False, modal=False, wflags=QtCore.Qt.WindowFlags() ):
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
    dialog = self.createEditionDialog( object, parent=parent, live=live )
    result = dialog.exec_()
    if result:
      dialog.setObject( object )
    self.closeEditionDialog( dialog )
    return result


#-------------------------------------------------------------------------------
class Qt4GUI( GUI ):
  '''
  This class manage the creation of Qt widgets for Python objects edition at
  object level. 
  '''
  
  def labelWidget( self, object, label, editionWidget=None,
                   parent=None, name=None, live=False ):
    '''
    Create a label widget for displaying a label associated with the edition
    widget. If C{editionWidget} already have the possibility to display the
    label (such as in L{qt.QGroupBox}) it sets the label on C{editionWidget}
    and returns C{None}. Returns a L{QtGui.QLabel} instance by default.
    @todo: C{editionWidget} should be mandatory.
    '''
    return QtGui.QLabel( label, parent )
  
  
  def closeLabelWidget( self, labelWidget ):
    '''
    Close a widget (and free associated ressources) created by
    C{self.L{labelWidget}}.
    '''
    if labelWidget is not None:
      labelWidget.close()
      labelWidget.deleteLater()
  
  
  def __init__( self, dataType ):
    '''
    Constructors of L{Qt4GUI} (and its derived classes) must accept a single
    C{dataType} parameter representing the type of data that can be view or 
    edited by this GUI element.
    @param dataType: type data that this L{Qt4GUI} can handle. This can be any 
    value accepted by L{DataType.dataTypeInstance}.
    '''
    super(Qt4GUI, self).__init__(dataType)  
    