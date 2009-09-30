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
TgGUI implementation for L{Boolean<soma.signature.api.Boolean>}
data type.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

from soma.translation import translate as _
from soma.tggui.api import TgGUI, TgCheckBox
from soma.tggui import tools


#-------------------------------------------------------------------------------
class Boolean_TgGUI( TgGUI ):
  def __init__( self, instance ):
    super(Boolean_TgGUI, self).__init__( instance )
    self._widget = None
  
  def editionWidget( self, value, window, parent=None, name=None, live=False ):
    TgGUI.editionWidget( self, value, window, parent, name, live )
    
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._name = name
    self._live = live
    self._widget = TgCheckBox( label = self._name )

    if value is not None:
      self.updateEditionWidget( self._widget, value )
    
    if live:
      self._widget.onAttributeChange( 'default', self._userModification )
    
    return self._widget


  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.removeOnAttributeChange( 'default' )

    editionWidget.close()

  def getPythonValue( self, editionWidget ):
    return bool( editionWidget.default )

  def updateEditionWidget( self, editionWidget, value ):
    tools.unlockWidget( self._widget )
    editionWidget.default = value
    
  def unserializeEditionWidgetValue( self, value, notifyObject = False ):
    if ( self._widget is not None ) :
      tools.unlockWidget( self._widget )

      res = self.findValueFromParams( value, self._widget.widgetid, self._name, default = False )
      self._widget.default = bool( res )
      
  def _userModification( self, newValue, oldValue ):
    self.onWidgetChange.notify( self._widget )
