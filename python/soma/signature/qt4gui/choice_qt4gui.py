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
Qt4GUI implementation for L{Choice<soma.signature.api.Choice>}
data type.

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from soma.translation import translate as _
from soma.signature.api import Undefined
from soma.qt4gui.api import Qt4GUI
from PyQt4 import QtGui, QtCore


#-------------------------------------------------------------------------------
class Choice_Qt4GUI( Qt4GUI ):  
  def __init__( self, instance ):
    Qt4GUI.__init__( self, instance )
    self._widget = None
    self.__ignoreModification = False
  
  
  def editionWidget( self, value, parent=None, name=None, live=False, editable=False ):
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._widget = QtGui.QComboBox( parent )
    if name:
      self._widget.setObjectName(name)
    self._widget.setEditable( editable )
    for i in self.dataTypeInstance.labels:
      self._widget.addItem( i )
    if value is not Undefined:
      index = self.dataTypeInstance.findIndex( value )
      if index == -1:
        if editable:
          self._widget.setEditText( unicode( value ) )
        else:
          label = unicode( value )
          self._widget.addItem( label )
          self.dataTypeInstance.labels.append( label )
          self.dataTypeInstance.values.append( value )
          index = len( self.dataTypeInstance.labels ) - 1
    else:
      index = 0
    if index >= 0:
      self._widget.setCurrentIndex( index )
    self._live = live
    if live:
      self._widget.connect( self._widget, QtCore.SIGNAL( 'activated( int )' ), 
                            self._userModification )
    return self._widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.disconnect( self._widget, QtCore.SIGNAL( 'activated( int )' ), 
                               self._userModification )
    editionWidget.close()
    editionWidget.deleteLater()
    self._widget = None
    
  
  def getPythonValue( self, attributeWidget ):
    return self.dataTypeInstance.values[ attributeWidget.currentIndex() ]


  def _userModification( self ):
    self.onWidgetChange.notify( self._widget )
  
  
  def updateEditionWidget( self, editionWidget, value ):
    index = self.dataTypeInstance.findIndex( value )
    if index != editionWidget.currentIndex():
      editionWidget.setCurrentIndex( index )



