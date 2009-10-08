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

'''
TgGUI implementation for L{Sequence<soma.signature.api.Sequence>}
data type.

@author: Nicoles Souedet
@author: Yann Cointepas

@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys
import turbogears

from soma.translation import translate as _
from soma.tggui.api import ApplicationTgGUI, TgGUI
from soma.signature.api import HasSignature

#-------------------------------------------------------------------------------
class Sequence_TgGUI( TgGUI ):
  _definedTgGUI = {}
  
  def __new__( cls, dataTypeInstance, *args, **kwargs ):
    tgGUI = ApplicationTgGUI.classTgGUI( dataTypeInstance.elementType.__class__, _prefix='Sequence_', _definedGUI=Sequence_TgGUI._definedTgGUI )

    if tgGUI is None:
      return super( Sequence_TgGUI, cls ).__new__( cls, dataTypeInstance, *args, **kwargs )
    else:
      return tgGUI( dataTypeInstance )
  
  def __init__( self, dataTypeInstance, horizontal=True ) :
    super(Sequence_TgGUI, self).__init__( dataTypeInstance )
    
    self._widget = None
    self._elementsGUI = []
    self._sequenceObject = None

  
  def editionWidget( self, sequenceObject, window, parent=None, name=None, live=False ):
    TgGUI.editionWidget( self, sequenceObject, window, parent, name, live )
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._live = live
    self._elementsGUI = []
    
    # Create the widget and set its layout
    self._widget = parent
    
    # This call initializes the widget with sequence content
    self.updateEditionWidget( self._widget, sequenceObject )
    
    return self._widget


  def closeEditionWidget( self, editionWidget ):
    for elementTggui, elementWidget in self._elementsGUI:
      if self._live :
        elementTggui.onWidgetChange.remove( self._elementWidgetChanged )
      elementTggui.closeEditionWidget( elementWidget )
    editionWidget.close()
    editionWidget.deleteLater()
    self._widget = None
    self._elementsGUI = []
    self._sequenceObject = None


  def setObject( self, editionWidget, sequenceObject ):
    for index in xrange( len( self._elementsGUI ) ) :
      self._setElement( sequenceObject, index )
  
  
  def _setElement( self, sequenceObject, index ):
    elementTggui, elementWidget = self._elementsGUI[ index ]
    if elementTggui.dataTypeInstance.mutable:
      elementTggui.setObject( elementWidget, sequenceObject[ index ] )
    else:
      sequenceObject[ index ] = \
        elementTggui.getPythonValue( elementWidget )


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
      for elementTggui, elementWidget in self._elementsGUI:
        if self._live :
          elementTggui.onWidgetChange.remove( self._elementWidgetChanged )
        elementTggui.closeEditionWidget( elementWidget )
      self._elementsGUI = []
      
      # Compute the new number of elements GUI
      elementsCount = len( sequenceObject )
      
      # Create new elements GUI
      for i in xrange( elementsCount ):
        elementTggui = \
          ApplicationTgGUI.instanceTgGUI( self.dataTypeInstance.elementType )
        elementWidget = elementTggui.editionWidget( sequenceObject[i],
          parent = self._widget, live = self._live )
        if self._live :
          elementWidget._indexOfElementInSequence = i
          elementTggui.onWidgetChange.add( self._elementWidgetChanged )
        self._elementsGUI.append( ( elementTggui,
                                    elementWidget ) )
        #elementWidget.show()
      self._sequenceObject = sequenceObject
    else:
      # Update all element widgets
      itSequenceObject = iter( sequenceObject )
      for elementTggui, elementWidget in self._elementsGUI:
        elementTggui.updateEditionWidget( elementWidget,
                                          itSequenceObject.next() )
