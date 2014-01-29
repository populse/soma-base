# -*- coding: utf-8 -*-

import os
os.environ['ETS_TOOLKIT'] = 'qt4'


#from enthought.traits.api import HasTraits, Directory

##-------------------------------------------------------------------------------
#class Application( HasTraits ):
  #user_directory = Directory( desc='Base directory where user specific information can be found' )



from soma.api import Application
from soma.api import Controller
from enthought.traits.api import Instance


# An independent class not using soma-traits at all
class AffineTransformation( object ):
  def __init__( self, translation, matrix ):
    self.translation = translation
    self.matrix = matrix

  
  def __repr__( self ):
    return '<' + repr( self.translation ) + ' ' + repr( self.matrix ) + '>'



# The following controller class to manage interaction between AffineTransformation
# and soma-traits could be written in  another module.
from soma.api import Controller
from enthought.traits.api import Float
class AffineTransformationController( Controller ):
  # A shortcut to create an association between AffineTransformationController and AffineTransformation
  register_class_controller = AffineTransformation
  # A shortcut to declare a ui file to be used when creating GUI
  create_widget_from_ui = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), 'affine_transformation.ui' )
  
  tx = Float()
  ty = Float()
  tz = Float()
  rxx = Float()
  rxy = Float()
  rxz = Float()
  ryx = Float()
  ryy = Float()
  ryz = Float()
  rzx = Float()
  rzy = Float()
  rzz = Float()
  
  def __init__( self, transformation ):
    super( AffineTransformationController, self ).__init__()
    self.transformation = transformation
    self.tx, self.ty, self.tz = transformation.translation
    self.rxx, self.rxy, self.rxz = transformation.matrix[ 0 ]
    self.ryx, self.ryy, self.ryz = transformation.matrix[ 1 ]
    self.rzx, self.rzy, self.rzz = transformation.matrix[ 2 ]
    
  
  def _tx_changed( self, value ):
    self.transformation.translation[ 0 ] = value
  
  def _ty_changed( self, value ):
    self.transformation.translation[ 1 ] = value
  
  def _tz_changed( self, value ):
    self.transformation.translation[ 2 ] = value
  
  def _rxx_changed( self, value ):
    self.transformation.matrix[ 0 ][ 0 ] = value
  
  def _rxy_changed( self, value ):
    self.transformation.matrix[ 0 ][ 1 ] = value
  
  def _rxz_changed( self, value ):
    self.transformation.matrix[ 0 ][ 2 ] = value
  
  def _ryx_changed( self, value ):
    self.transformation.matrix[ 1 ][ 0 ] = value
  
  def _ryy_changed( self, value ):
    self.transformation.matrix[ 1 ][ 1 ] = value
  
  def _ryz_changed( self, value ):
    self.transformation.matrix[ 1 ][ 2 ] = value
  
  def _rzx_changed( self, value ):
    self.transformation.matrix[ 2 ][ 0 ] = value
  
  def _rzy_changed( self, value ):
    self.transformation.matrix[ 2 ][ 1 ] = value
  
  def _rzz_changed( self, value ):
    self.transformation.matrix[ 2 ][ 2 ] = value
  


# A class derived from Controller can be its own controller
class CombineTransformations( Controller ):
  transformation1 = Instance( AffineTransformation )
  transformation2 = Instance( AffineTransformation )

  create_widget_from_ui = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), 'combine_transformations.ui' )

if __name__ == '__main__':
  
  application = Application( 'soma-traits-example' )
  application.initialize()
  application.initialize_gui()

  transformation1 = AffineTransformation( [ 0, 0, 0 ], [ [ 1, 0, 0], [ 0, 1, 0 ], [ 0, 0, 1 ] ] )
  transformation2 = AffineTransformation( [ 1, 2, 3 ], [ [ -1, 0, 0], [ 0, -1, 0 ], [ 0, 0, -1 ] ] )
  combine = CombineTransformations( transformation1=transformation1, transformation2=transformation2 )
  
  #controller = application.get_controller( transformation )
  
  #print '!', controller, application.get_controller( transformation )
  #controller.tx = 1
  #controller.ty = 2
  #controller.tz = 3
  #controller.rxx = 4
  #controller.rxy = 5
  #controller.rxz = 6
  #controller.ryx = 7
  #controller.ryy = 8
  #controller.ryz = 9
  #controller.rzx = 10
  #controller.rzy = 11
  #controller.rzz = 12
  #print transformation
  
  from PyQt4.QtGui import QWidget, QApplication
  widget1 = application.gui.create_widget( transformation1, live=True )
  widget1.show()
  widget2 = application.gui.create_widget( transformation2, live=True )
  widget2.show()
  widget3 = application.gui.create_widget( combine, live=True )
  widget3.show()
  application.gui.event_loop()
  print transformation1
  print transformation2
