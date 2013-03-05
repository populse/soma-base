# -*- coding: utf-8 -*-
import sys, os, glob

#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
try:
  from traits.api import HasTraits,Button, Str, Event, Int,Float, Enum, \
Instance, Property, Bool, List
  from traitsui.api import View,Group,Label,Item,InstanceEditor, \
FileEditor, DirectoryEditor, UItem
except ImportError:
  from enthought.traits.api import HasTraits,Button, Str, Event, Int,Float, Enum, \
Instance, Property, Bool, List
  from enthought.traits.ui.api import View,Group,Label,Item,InstanceEditor, \
FileEditor, DirectoryEditor, UItem

from soma.application import Application
   
   
class EmptyProcess( HasTraits ):
  pass

  
class DynamicView( HasTraits ):
    
    genView = Property( Instance( View ) )
    
    def _get_genView( self ):
        trait_names = self.editable_traits()
        trait_names.remove( 'genView' )    
        return View( trait_names )

    def clear( self ):
      for i in self._instance_traits().keys():
        if i == 'genView': continue
        self.remove_trait( i )

  
class ProcessView( HasTraits ): 

    input_directory=Str( default_value='/tmp',
      descr='Input directory' )
    output_directory = Str( default_value='/tmp',
      descr='Output directory' )

    def __init__( self, *args, **kwargs ):
        super( ProcessView, self ).__init__( *args, **kwargs )
        
        processes = [ os.path.basename( i[ :-3] ) for i in glob.glob( os.path.join( Application().install_directory, 'python', 'sandbox', 'soma', 'processes', '*.py' ) ) if not i.endswith( '__init__.py' ) ]
        self.add_trait( 'process', Enum( [ '' ] + processes ) )
        
        foms = Application().fom_manager.find_fom()
        self.add_trait( 'file_organization_model', Enum( foms ) )
        self.attributes = DynamicView()
        self.process_parameters = DynamicView()

        self._file_organization_model_fired( self.file_organization_model )
        
    def _file_organization_model_fired( self, fom_name ):
      self.attributes.clear()
      fom = Application().fom_manager.get_fom( fom_name )
      for n, d in fom.attributes( self.process ).iteritems():
        self.attributes.add_trait( n, Str( **d ) )
        getattr( self.attributes, n )
      self.attributes.trait_property_changed( 'genView', None, self.attributes.genView )

    
    def _process_fired( self, process ):
      module = 'sandbox.soma.processes.' + process
      __import__( module )
      if process:
        process_class = getattr( sys.modules[ module ], process )
      else:
        process_class = EmptyProcess
      process_instance = process_class()
      self.process_parameters.clear()
      for n, v in process_instance._instance_traits().iteritems():
        self.process_parameters.add_trait( n, v )
        getattr( self.process_parameters, n )
      self.process_parameters.trait_property_changed( 'genView', None, self.process_parameters.genView )
      self._file_organization_model_fired( self.file_organization_model )
    
    
    view = View(
        Group( 
            Group(      
                Item( 'output_directory', editor=DirectoryEditor() ),
                Item( 'input_directory', editor=DirectoryEditor()),
                Item( 'process', ),
                Item( 'file_organization_model', ),
                show_border=True ),
            Group(     
                UItem('attributes', 
                    editor = InstanceEditor( view_name='object.attributes.genView' ),
                    style='custom'),             
                show_border=True,
                scrollable=True ),
           Group(     
                UItem('process_parameters', 
                    editor = InstanceEditor( view_name='object.process_parameters.genView' ),
                    style='custom'),             
                show_border=True,
                scrollable=True ),
            orientation = 'vertical' ),
        title='Processing',     
        buttons=['OK','Cancel'],
        resizable=True,
        width= 800, height=800
     )


if __name__ == "__main__":
    app = Application( 'test_process_traits', '1.0' )
    app.plugin_modules.append( 'sandbox.soma.fom' )
    app.initialize()

    process_view = ProcessView()
    process_view.configure_traits()

