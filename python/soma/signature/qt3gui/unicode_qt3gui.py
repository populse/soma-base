# -*- coding: iso-8859-1 -*-

# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
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
Qt3GUI implementation for L{Unicode<soma.signature.api.Unicode>}
data type.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from soma.translation import translate as _
from soma.qt3gui.api import Qt3GUI, TimeredQLineEdit
import qt


#-------------------------------------------------------------------------------
class Unicode_Qt3GUI( Qt3GUI ):
  def __init__( self, instance ):
    Qt3GUI.__init__( self, instance )
    self._widget = None
  
  
  def editionWidget( self, value, parent=None, name=None, live=False ):
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._live = live
    if live:
      self._widget = TimeredQLineEdit( parent, name )
      if value is not None:
        self.updateEditionWidget( self._widget, value )
      self._widget.connect( self._widget, qt.PYSIGNAL( 'userModification' ), 
                            self._userModification )
    else:
      self._widget = qt.QLineEdit( parent, name )
      if value is not None:
        self.updateEditionWidget( self._widget, value )
    return self._widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.disconnect( self._widget, qt.PYSIGNAL( 'userModification' ), 
                               self._userModification )
    editionWidget.close()
    editionWidget.deleteLater()
    self._widget = None
  
  
  def getPythonValue( self, editionWidget ):
    return self.dataTypeInstance.convert( unicode( editionWidget.text() ) )


  def updateEditionWidget( self, editionWidget, value ):
    if self._live:
      editionWidget.startInternalModification()
      editionWidget.setText( unicode( value ) )
      editionWidget.stopInternalModification()
    else:
      editionWidget.setText( unicode( value ) )


  def _userModification( self, ):
    self.onWidgetChange.notify( self._widget )


#-------------------------------------------------------------------------------
class Sequence_Unicode_Qt3GUI( Unicode_Qt3GUI ):
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
