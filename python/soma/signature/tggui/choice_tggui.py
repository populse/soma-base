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
TgGUI implementation for L{Choice<soma.signature.api.Choice>}
data type.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import turbogears

from soma.translation import translate as _
from soma.signature.api import Undefined
from soma.tggui.api import TgGUI, TgSingleSelectField
from soma.tggui import tools

#-------------------------------------------------------------------------------
class Choice_TgGUI( TgGUI ):
  def __init__( self, instance ):
    TgGUI.__init__( self, instance )
    self._widget = None
    self.__ignoreModification = False

  def editionWidget( self, value, window, parent=None, name=None, live=False, editable=False ):
    TgGUI.editionWidget( self, value, window, parent, name, live )
    
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._name = name
    self._live = live
    self._widget = TgSingleSelectField( label = self._name, validator = turbogears.validators.String )

    #self._widget.setEditable( editable )
    for i in xrange(len(self.dataTypeInstance.labels)):
      label = self.dataTypeInstance.labels[ i ]
      self._widget.options += [ ( unicode( i ), label ) ]
    
    if value is not Undefined:
      index = self.dataTypeInstance.findIndex( value )
      if index == -1:
        if editable:
          label = unicode( value )
          index = len( self.dataTypeInstance.labels )
          self._widget.options += [( index, label )]
          self.dataTypeInstance.labels.append( label )
          self.dataTypeInstance.values.append( value )
    else:
      index = 0
    
    if index >= 0:
      self._widget.default = unicode( index )
      
    if live:
      self._widget.onAttributeChange( 'default', self._userModification )

    return self._widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.removeOnAttributeChange( 'default' )

    editionWidget.close()

  def getPythonValue( self, attributeWidget ):
    return self.dataTypeInstance.values[ int(attributeWidget.default) ]

  def _userModification( self ):
    self.onWidgetChange.notify( self._widget )
  
  def updateEditionWidget( self, editionWidget, value ):
    index = self.dataTypeInstance.findIndex( value )
    tools.unlockWidget( editionWidget )
    editionWidget.delayAttributeNotification(ignoreDoubles=True)
    editionWidget.default = unicode( index )
    editionWidget.restartAttributeNotification()

  def unserializeEditionWidgetValue( self, value, notifyObject = False ):
    if ( self._widget is not None ) :
      tools.unlockWidget( self._widget )
      index = None
      res = self.findValueFromParams( value, self._widget.widgetid, self._name )
      try :
          index = int(res)
      except Exception, e :
          index = self.dataTypeInstance.findIndex( res )
      
      if not index is None :
        self._widget.default = unicode( index )
