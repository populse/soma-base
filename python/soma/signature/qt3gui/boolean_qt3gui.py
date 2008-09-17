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
Qt3GUI implementation for L{Boolean<soma.signature.api.Boolean>}
data type.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import qt

from soma.translation import translate as _
from soma.qt3gui.api import Qt3GUI


#-------------------------------------------------------------------------------
class Boolean_Qt3GUI( Qt3GUI ):
  def __init__( self, instance ):
    Qt3GUI.__init__( self, instance )
    self._widget = None
  
  def editionWidget( self, value, parent=None, name=None, live=False ):
    if self._widget is not None:
      raise RuntimeError( _( 'editionWidget() cannot be called twice without'\
                               'a call to closeEditionWidget()' ) )
    self._widget = qt.QCheckBox( parent, name )
    if value is not None :
      self._widget.setChecked( value )
    else:
      self._widget.setState( qt.QButton.NoChange )
    self._live = live
    if live:
      self._widget.connect( self._widget, qt.SIGNAL( 'clicked()' ), 
                            self._userModification )
    return self._widget


  def closeEditionWidget( self, editionWidget ):
    if self._live:
      self._widget.disconnect( self._widget, qt.SIGNAL( 'clicked()' ), 
                               self._userModification )
    editionWidget.close()
    editionWidget.deleteLater()
    self._widget = None


  #def multipleEditionWidget( self, objects, container=None, attributeName=None,
                     #parent=None, name=None, live=False ):
    #objects = tuple( objects )
    #if len( objects ) == 0:
      #return self.editionWidget( self, None, parent=parent, name=name, live=False )
    #elif len( objects ) == 1:
      #return self.editionWidget( self, objects[0], container=container, 
                                 #attributeName=attributeName, parent=parent, 
                                 #name=name, live=live )
    #else:
      #value = objects[ 0 ]
      #for otherValue in objects[ 1: ]:
        #if otherValue != value:
          #value = None
          #break
      #return self.editionWidget( self, value, parent=parent, 
                                 #name=name, live=live )
  
  
  #def closeMultipleEditionWidget( self, multipleEditionWidget ):
    #return self.closeEditionWidget( multipleEditionWidget )
    
  
  def getPythonValue( self, editionWidget ):
    return bool( editionWidget.isChecked () )


  def updateEditionWidget( self, editionWidget, value ):
    editionWidget.setChecked( value )


  def _userModification( self ):
    self.onWidgetChange.notify( self._widget )
