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
Qt4GUI implementation for L{Sequence<soma.signature.api.Sequence>}
data type.

@author: Dominique Geffroy

@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys
from PyQt4 import QtGui, QtCore

from soma.translation import translate as _
from soma.qt4gui.api import ApplicationQt4GUI, Qt4GUI
from soma.signature.api import HasSignature

#-------------------------------------------------------------------------------
class Sequence_Qt4GUI( Qt4GUI ):
  _definedQt4GUI = {}
  
  def __new__( cls, dataTypeInstance, *args, **kwargs ):
    # print '!Sequence_Qt3GUI!', type( dataTypeInstance.elementType )
    qtGUI = ApplicationQt4GUI.classQt4GUI( dataTypeInstance.elementType.__class__, _prefix='Sequence_', 
      _definedGUI=Sequence_Qt4GUI._definedQt4GUI )
    if qtGUI is None:
      return super( Sequence_Qt4GUI, cls ).__new__( cls, dataTypeInstance, *args, **kwargs )
    else:
      return qtGUI( dataTypeInstance )
  
  def __init__( self, dataTypeInstance, horizontal=True ) :
    Qt4GUI.__init__( self, dataTypeInstance )
    
    self._widget = None
    self._elementsGUI = []
    self._sequenceObject = None
    if horizontal:
      self.__containerLayoutClass = QtGui.QHBoxLayout
    else:
      self.__containerLayoutClass = QtGui.QVBoxLayout
  
  
  def editionWidget( self, sequenceObject, parent=None, name=None, live=False ):
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._live = live
    self._elementsGUI = []
    
    # Create the widget and set its layout
    self._widget = QtGui.QWidget( parent )
    self._layout=self.__containerLayoutClass( self._widget )
    self._layout.setMargin( 0 )
    self._layout.setSpacing( 5 )
    
    # This call initializes the widget with sequence content
    self.updateEditionWidget( self._widget, sequenceObject )
    
    return self._widget


  def closeEditionWidget( self, editionWidget ):
    for elementQtgui, elementWidget in self._elementsGUI:
      if self._live :
        elementQtgui.onWidgetChange.remove( self._elementWidgetChanged )
      elementQtgui.closeEditionWidget( elementWidget )
    editionWidget.close()
    editionWidget.deleteLater()
    self._widget = None
    self._elementsGUI = []
    self._sequenceObject = None


  def setObject( self, editionWidget, sequenceObject ):
    for index in xrange( len( self._elementsGUI ) ) :
      self._setElement( sequenceObject, index )
  
  
  def _setElement( self, sequenceObject, index ):
    elementQtgui, elementWidget = self._elementsGUI[ index ]
    if elementQtgui.dataTypeInstance.mutable:
      elementQtgui.setObject( elementWidget, sequenceObject[ index ] )
    else:
      sequenceObject[ index ] = \
        elementQtgui.getPythonValue( elementWidget )


  def _elementWidgetChanged( self, editionWidget ):
    index = editionWidget._indexOfElementInSequence
    try:
      self._setElement( self._sequenceObject, index )
    except ValueError:
      pass
    

  def updateEditionWidget( self, editionWidget, sequenceObject ):
    if ( self._sequenceObject is not sequenceObject ) or \
      ( len( sequenceObject ) != len( self._elementsGUI ) ):
      # delete current elements GUI
      for elementQtgui, elementWidget in self._elementsGUI:
        if self._live :
          elementQtgui.onWidgetChange.remove( self._elementWidgetChanged )
        elementQtgui.closeEditionWidget( elementWidget )
      self._elementsGUI = []
      
      # Compute the new number of elements GUI
      elementsCount = len( sequenceObject )
      
      # Create new elements GUI
      for i in xrange( elementsCount ):
        elementQtgui = \
          ApplicationQt4GUI.instanceQt4GUI( self.dataTypeInstance.elementType )
        elementWidget = elementQtgui.editionWidget( sequenceObject[i], 
          parent = self._widget, live = self._live )
        self._layout.addWidget(elementWidget)
        if self._live :
          elementWidget._indexOfElementInSequence = i
          elementQtgui.onWidgetChange.add( self._elementWidgetChanged )
        self._elementsGUI.append( ( elementQtgui, 
                                    elementWidget ) )
        elementWidget.show()
      self._sequenceObject = sequenceObject
    else:
      # Update all element widgets
      itSequenceObject = iter( sequenceObject )
      for elementQtgui, elementWidget in self._elementsGUI:
        elementQtgui.updateEditionWidget( elementWidget,
                                          itSequenceObject.next() )
