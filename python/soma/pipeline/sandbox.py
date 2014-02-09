import tempfile
from subprocess import check_call
from PyQt4 import QtGui
try:
  from traits.api import File, Float, Int, String
except ImportError:
  from enthought.traits.api import File, Float, Int

from soma.process import Process
from soma.pipeline import Pipeline


class EchoProcess( Process ):  
  def __call__( self ):
    print self.id + ':'
    for parameter in self.user_traits():
      print ' ', parameter, '=', repr( getattr( self, parameter ) )
    
    
class SPMNormalization( EchoProcess ):
  def __init__( self ):
    super( SPMNormalization, self ).__init__()
    self.add_trait( 'image', File() )
    self.add_trait( 'template', File() )
    self.add_trait( 'normalized', File( output=True ) )

    
class BiasCorrection( EchoProcess ):
  def __init__( self ):
    super( BiasCorrection, self ).__init__()
    self.add_trait( 't1mri', File() )
    self.add_trait( 'field_rigidity', Float() )
    self.add_trait( 'nobias', File( output=True ) )

    
class HistoAnalysis( EchoProcess ):
  def __init__( self ):
    super( HistoAnalysis, self ).__init__()
    self.add_trait( 'image', File() )
    self.add_trait( 'histo_analysis', File( output=True ) )

    
class BrainMask( EchoProcess ):
  def __init__( self ):
    super( BrainMask, self ).__init__()
    self.add_trait( 't1mri', File() )
    self.add_trait( 'histo_analysis', File() )
    self.add_trait( 'brain_mask', File( output=True ) )

    
class SplitBrain( EchoProcess ):
  def __init__( self ):
    super( SplitBrain, self ).__init__()
    self.add_trait( 't1mri', File() )
    self.add_trait( 'histo_analysis', File() )
    self.add_trait( 'brain_mask', File() )
    self.add_trait( 'split_brain', File( output=True ) )

    
class GreyWhiteClassification( EchoProcess ):
  def __init__( self ):
    super( GreyWhiteClassification, self ).__init__()
    self.add_trait( 't1mri', File() )
    self.add_trait( 'label_image', File() )
    self.add_trait( 'label', Int() )
    self.add_trait( 'gw_classification', File( output=True ) )


class GreyWhiteSurface( EchoProcess ):
  def __init__( self ):
    super( GreyWhiteSurface, self ).__init__()
    self.add_trait( 't1mri', File() )
    self.add_trait( 'gw_classification', File() )
    self.add_trait( 'hemi_cortex', File( output=True ) )
    self.add_trait( 'white_mesh', File( output=True ) )

    
class SphericalHemisphereSurface( EchoProcess ):
  def __init__( self ):
    super( SphericalHemisphereSurface, self ).__init__()
    self.add_trait( 'gw_classification', File() )
    self.add_trait( 'hemi_cortex', File() )
    self.add_trait( 'hemi_mesh', File( output=True ) )


class GreyWhite( Pipeline ):
  def pipeline_definition( self ):    
    self.add_process( 'gw_classification', GreyWhiteClassification() )
    self.export_parameter( 'gw_classification', 't1mri' )
    
    self.add_process( 'gw_surface', GreyWhiteSurface() )
    self.add_link( 't1mri->gw_surface.t1mri' )
    self.add_link( 'gw_classification.gw_classification->gw_surface.gw_classification' )
    self.export_parameter( 'gw_classification', 'gw_classification' )
    
    self.add_process( 'hemi_surface', SphericalHemisphereSurface() )
    self.add_link( 'gw_classification.gw_classification->hemi_surface.gw_classification' )
    self.add_link( 'gw_surface.hemi_cortex->hemi_surface.hemi_cortex' )
    self.export_parameter( 'gw_surface', 'hemi_cortex' )



class Morphologist( Pipeline ):
  def pipeline_definition( self ):
    self.add_trait( 't1mri', File() )
    
    self.add_process( 'normalization', 'soma.pipeline.sandbox.SPMNormalization' )
    self.export_parameter( 'normalization', 'normalized', only_if_activated=True )
    self.add_switch( 'select_normalization', [ 'spm', 'none' ], 't1mri' )
    self.add_process( 'bias_correction', BiasCorrection() )

    self.add_link( 'normalization.normalized->select_normalization.spm' )
    self.add_link( 't1mri->select_normalization.none' )
    self.add_link( 't1mri->normalization.image' )

    self.add_link( 'select_normalization.t1mri->bias_correction.t1mri' )
    self.export_parameter( 'bias_correction', 'nobias' )
    
    self.add_process( 'histo_analysis', HistoAnalysis() )
    self.add_link( 'bias_correction.nobias->histo_analysis.image' )
    
    self.add_process( 'brain_mask', BrainMask() )
    self.add_link( 'select_normalization.t1mri->brain_mask.t1mri' )
    self.add_link( 'histo_analysis.histo_analysis->brain_mask.histo_analysis' )
    self.export_parameter( 'brain_mask', 'brain_mask' )
    
    self.add_process( 'split_brain', SplitBrain() )
    self.add_link( 'select_normalization.t1mri->split_brain.t1mri' )
    self.add_link( 'histo_analysis.histo_analysis->split_brain.histo_analysis' )
    self.add_link( 'brain_mask.brain_mask->split_brain.brain_mask' )
    
    self.add_process( 'left_grey_white', GreyWhite(), label=1 )
    self.export_parameter( 'left_grey_white', 'label', None )
    self.add_link( 'select_normalization.t1mri->left_grey_white.t1mri' )
    self.add_link( 'split_brain.split_brain->left_grey_white.label_image' )
    self.export_parameter( 'left_grey_white', 'gw_classification', 'left_gw_classification', set_optional=False )
    self.export_parameter( 'left_grey_white', 'hemi_cortex', 'left_hemi_cortex', set_optional=False  )
    self.export_parameter( 'left_grey_white', 'hemi_mesh', 'left_hemi_mesh', set_optional=False  )
    self.export_parameter( 'left_grey_white', 'white_mesh', 'left_white_mesh', set_optional=False  )
    
    self.add_process( 'right_grey_white', GreyWhite(), label=2 )
    self.export_parameter( 'right_grey_white', 'label', None )
    self.add_link( 'select_normalization.t1mri->right_grey_white.t1mri' )
    self.add_link( 'split_brain.split_brain->right_grey_white.label_image' )
    self.export_parameter( 'right_grey_white', 'gw_classification', 'right_gw_classification' )
    self.export_parameter( 'right_grey_white', 'hemi_cortex', 'right_hemi_cortex' )
    self.export_parameter( 'right_grey_white', 'hemi_mesh', 'right_hemi_mesh' )
    self.export_parameter( 'right_grey_white', 'white_mesh', 'right_white_mesh' )

    self.node_position = {'bias_correction': (620.0, 140.0),
                          'brain_mask': (930.0, 139.0),
                          'histo_analysis': (761.0, 190.0),
                          'inputs': (50.0, 65.0),
                          'left_grey_white': (1242.0, 55.0),
                          'normalization': (278.0, 145.0),
                          'outputs': (1457.0, 103.0),
                          'right_grey_white': (1239.0, 330.0),
                          'select_normalization': (442.0, 65.0),
                          'split_brain': (1089.0, 163.0)}
     
           
class WorkflowViewer( QtGui.QWidget ):
  def __init__( self, pipeline ):
    super( WorkflowViewer, self ).__init__()
    self.pipeline = pipeline
    layout = QtGui.QVBoxLayout( self )
    #self.setLayout( layout )
    self.label =QtGui.QLabel()
    layout.addWidget( self.label )
    self.btn_update = QtGui.QPushButton( 'update' )
    layout.addWidget( self.btn_update )
    self.btn_update.clicked.connect( self.update )
    self.update()
    
  def update( self ):
    image = tempfile.NamedTemporaryFile( suffix='.png' )
    dot = tempfile.NamedTemporaryFile( suffix='.png' )
    self.pipeline.workflow().write( dot )
    dot.flush()
    check_call( [ 'dot', '-Tpng', '-o', image.name, dot.name ] )
    pixmap = QtGui.QPixmap( image.name ).scaledToHeight( 600 )
    self.label.setPixmap( pixmap )
    
                          
if __name__ == '__main__':
  import sys
  from PyQt4 import QtGui
  from soma.gui.widget_controller_creation import ControllerWidget
  from soma.functiontools import SomaPartial as partial
  from soma.gui.pipeline.pipeline_gui import PipelineView
  
  app = QtGui.QApplication( sys.argv )

  morphologist = Morphologist()
  #morphologist.set_string_list( sys.argv[1:] )
  view3 = WorkflowViewer( morphologist )
  view3.show()
  view1 = PipelineView( morphologist )
  view1.show()
  view2 = PipelineView( GreyWhite() )
  view2.show()
  
  cw = ControllerWidget( morphologist, live=True )
  cw.show()
  
  #morphologist.trait( 'nobias' ).hidden = True
  #cw.controller.user_traits_changed = True
  #printer = QtGui.QPrinter( QtGui.QPrinter.HighResolution )
  #printer.setOutputFormat( QtGui.QPrinter.PostScriptFormat )
  #printer.setOutputFileName( sys.argv[ 1 ] )
  #painter = QtGui.QPainter()
  #painter.begin( printer )

  #scale = QtGui.QTransform.fromScale( .5, .5 )
  #painter.setTransform( scale )
  #view1.scene.render( painter )
  #painter.end()
  
  app.exec_()
  morphologist.workflow().write( sys.stdout )
  del view1
  del view2
  del view3