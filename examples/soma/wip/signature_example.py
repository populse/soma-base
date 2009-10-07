#! /env/bin python
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


import sys, qt

from soma.functiontools import partial
from soma.signature.api import Signature, VariableSignature, HasSignature, \
     Unicode, Choice, Number, Integer, Boolean, Undefined, Sequence, \
     ClassDataType, Bytes, FileName
from soma.qt3gui.api import ApplicationQt3GUI, Qt3GUI, TimeredQLineEdit
from soma.signature.qt3gui.signature_qt3gui import HasSignature_Qt3GUI


#------------------------------------------------------------------------------
class Coordinate3D( HasSignature ):
  '''
  A simple coordinate in 3D referential.
  '''
  signature = Signature(
    'x', Number,
    'y', Number,
    'z', Number,
  )

  def __init__( self, x = 0, y = 0, z = 0 ):
    HasSignature.__init__( self )
    self.x, self.y, self.z = x, y, z
  
  
#------------------------------------------------------------------------------
class Box3D( HasSignature ):
  '''
  A bounding box composed of two Coordinate3D.
  '''
  signature = Signature(
    'corner1', Coordinate3D,
    'corner2', Coordinate3D,
  )
  
  def __init__( self, corner1=None, corner2=None ):
    HasSignature.__init__( self )
    if corner1 is None:
      corner1 = Coordinate3D()
    if corner2 is None:
      corner2 = Coordinate3D()
    self.corner1 = corner1
    self.corner2 = corner2
  
  
#------------------------------------------------------------------------------
class Sphere( HasSignature ):
  '''
  A sphere composed of one Coordinate3D and one radius.
  '''
  signature = Signature(
    'center', Coordinate3D, dict( defaultValue=Coordinate3D( 0,0,0 ) ),
    'radius', Number( minimum=0 ), dict( defaultValue=1 ),
  )
  
  
  #def __init__( self, **kwargs ):
    #HasSignature.__init__( self )
    #self.initializeSignatureAttributes( **kwargs )
  
  #def __init__( self, center=None, radius=1 ):
    #HasSignature.__init__( self )
    #if center is not None:
      #self.center = center
    #else:
      #self.center = Coordinate3D()



#------------------------------------------------------------------------------
class ROIAnalysis( HasSignature ):
  signature = Signature( 
    'image', FileName( readOnly=True ), dict( defaultValue=None, doc='Input image' ),
    'roiType', Choice( ( 'Box3D', Box3D ) , ( 'Sphere', Sphere ) ),
    'roiVisible', Boolean, dict( defaultValue=True ),
    'roi', Box3D, dict( doc='Type parameters of the ROI here' ),
  )
  
  
  def __init__( self ):
    HasSignature.__init__( self )
    self.signature = VariableSignature( self.signature )
    #for i in xrange( 50 ):
      #n = 'test_%03d' % ( i, )
      #self.signature[ n ] = Unicode
      #setattr( self, n, '' )
    #self.images = [ 'firstImage', 'secondImage', 'thirdImage' ]
    self.roiType = Box3D
    self.roi = Box3D()
    self.onAttributeChange( 'roiType', self._roiTypeChanged )
    self.onAttributeChange( 'roiVisible', self._roiVisibilityChanged )
    self.bytes = ''
  
  def _roiVisibilityChanged( self, visible ):
    self.signature[ 'roi' ].visible = visible
  
  
  def _roiTypeChanged( self, newType, oldType ):
    if newType is not oldType:
      self.delayAttributeNotification( ignoreDoubles=True )
      self.signature[ 'roi' ].type = newType
      self.roi = newType()
      self.restartAttributeNotification()


#------------------------------------------------------------------------------
class Coordinate3D_Qt3GUI( Qt3GUI ):
  '''
  This class redefine completely the GUI for Coordinate3D
  '''
  def __init__( self, instance ):
    Qt3GUI.__init__( self, instance )
    
  def editionWidget( self, value, parent=None, name=None, live=False ):
    self._live = live
    if live:
      widget = TimeredQLineEdit( parent, name )
      self._widget = widget
      if value is not None:
        widget.startInternalModification()
        self.updateEditionWidget( widget, value )
        widget.stopInternalModification()
      widget.connect( widget, qt.PYSIGNAL( 'userModification' ),
                      self._userModification )
    else:
      widget = qt.QLineEdit( parent, name )
      if value is not None:
        self.updateEditionWidget( widget, value )
    return widget
  
  
  def closeEditionWidget( self, editionWidget ):
    if self._live:
      editionWidget.disconnect( editionWidget, 
                                qt.PYSIGNAL( 'userModification' ),
                                self._userModification )
      self._widget = None
    editionWidget.close()
    editionWidget.deleteLater()
  
  
  def _userModification( self ):
    print '!_userModification!'
    self.onWidgetChange.notify( self._widget )
  
  
  def _containerAttributeChanged( self, value ):
    self._widget.startInternalModification()
    self.updateEditionWidget( self._widget, value )
    self._widget.stopInternalModification()
  
  
  def setObject( self, editionWidget, value ):
    value.x, value.y, value.z = [ value.signature['x'].type.convert(i) \
                                  for i in str( editionWidget.text() ).split() ]


  def updateEditionWidget( self, editionWidget, value ):
    self._widget.startInternalModification()
    self._widget.setText( str( value.x ) + ' ' + str( value.y ) + ' ' + \
                          str( value.z ) )
    self._widget.stopInternalModification()



#-------------------------------------------------------------------------------
class Box3D_Qt3GUI( HasSignature_Qt3GUI ):
  def _create_corner2_Qt3GUI( self, dataType, object, attributeName ):
    '''
    This method is called for creating the Qt3GUI of 'corner2' attribute.
    '''
    print 'Box3D_Qt3GUI._create_corner2_Qt3GUI', attributeName
    return HasSignature_Qt3GUI( dataType )

  def _createAttributeQt3GUI( self, dataType, object, attributeName ):
    '''
    This method is called for creating the Qt3GUI of any attribute.
    '''
    print 'Box3D_Qt3GUI._createAttributeQt3GUI', attributeName, dataType
    result = HasSignature_Qt3GUI._createAttributeQt3GUI( self, dataType,
                    object, attributeName )
    print 'Box3D_Qt3GUI._createAttributeQt3GUI done'
    return result
    

print 'Creating QApplication'
qApp = qt.QApplication( sys.argv )
print 'Creating ApplicationQt3GUI'
appGUI = ApplicationQt3GUI()

def printObject( o, indent=0 ):
  it = iter( o.signature )
  it.next()
  for a in it:
    v = getattr( o, a, Undefined )
    if isinstance( v, HasSignature ):
      print '  ' * indent + a + ':'
      printObject( v, indent+1 )
    else:
      print '  ' * indent + a, '=', repr(v)
    

print 'Creating ROIAnalysis'
o = ROIAnalysis()
print 'Creating show object widget'
callback = partial( printObject, o )
showObjectPanel = qt.QVBox( None, None, qt.Qt.WGroupLeader )
showObjectbutton = qt.QPushButton( 'Show object', showObjectPanel )
showObjectbutton.connect( showObjectbutton, qt.SIGNAL( 'clicked()' ), callback )
showObjectPanel.show()

printObject( o )
print 'Editing object'
appGUI.edit( o, live=True )
printObject( o )

