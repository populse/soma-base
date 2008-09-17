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
TgGUI implementation for L{Unicode<soma.signature.api.Unicode>}
data type.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import turbogears
import turbogears.widgets

from soma.translation import translate as _
from soma.tggui.api import TgGUI, TgTextField

#-------------------------------------------------------------------------------
class Unicode_TgGUI( TgGUI ):
  def __init__( self, instance ):
    TgGUI.__init__( self, instance )
    self._widget = None
  
  
  def editionWidget( self, value, window, parent=None, name=None, live=False ):
    TgGUI.editionWidget( self, value, window, parent, name, live )
    
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                             'a call to closeEditionWidget()' ) )
    self._parent = parent
    self._live = live
    self._name = name
    self._widget = TgTextField( label = self._name )
    #self._widget.name = self.widgetid
    #self._widget.label = self._name
    
    if value is not None:
      self.updateEditionWidget( self._widget, value )
      
    if live:
      #self._widget = TimeredQLineEdit( parent, name )
      self._widget.onAttributeChange( 'default', self._userModification )

    return self._widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.removeOnAttributeChange( 'default' )

    editionWidget.close()
  
  
  def getPythonValue( self, editionWidget ):
    foundValue = self.dataTypeInstance.convert( unicode( editionWidget.default ) )
    return foundValue

  def updateEditionWidget( self, editionWidget, value ):
    if self._live:
      editionWidget.startInternalModification()
      editionWidget.setText( unicode( value ) )
      editionWidget.stopInternalModification()
    else:
      editionWidget.setText( unicode( value ) )

  def unserializeEditionWidgetValue( self, value, notifyObject = False ):
    if ( self._widget is not None ) :
      widgetid = self._widget.widgetid
      if ( isinstance( value, dict ) ):
        if ( widgetid in value ) :
          self._widget.setText( unicode( value[ widgetid ] ) )
        else :
          self._widget.setText( '' )
      else :
         self._widget.setText( unicode( value ) )
      
  def _userModification( self, *args, **kwargs ):
    self.onWidgetChange.notify( self._widget )

#-------------------------------------------------------------------------------
class Sequence_Unicode_TgGUI( Unicode_TgGUI ):
  def setObject( self, editionWidget, object ):
    object[:] = list( self.valuesFromText( unicode( editionWidget.text() ) ) )


  def updateEditionWidget( self, editionWidget, value ):
    if self._live:
      editionWidget.startInternalModification()
      editionWidget.setText( ' '.join( ["'" + i.replace( "'", "\\'" ) + "'" for i in value] ) )
      editionWidget.stopInternalModification()
    else:
      editionWidget.setText( ' '.join( value ) )

  @staticmethod
  def valuesFromText( text ):
    while text:
      quote = text[0]
      lastQuote = 0
      if quote in ( '"', "'" ):
        while True:
          lastQuote = text.find( quote, lastQuote+1 )
          if lastQuote == -1:
            yield text[ 1: ]
            text = ''
            break
          elif text[ lastQuote - 1 ] != '\\':
            yield text[ 1 : lastQuote ]
            text = text[ lastQuote+1: ]
            break
      else:
        space = text.find( ' ' )
        if space == -1:
          yield text
          text = ''
        else:
          yield text[ :space ]
          text = text[ space+1: ]
      text = text.strip()
