# -*- coding: utf-8 -*-
import os, json, glob, re
from traits.api import ListStr
from soma.singleton import Singleton
from soma.application import Application

'''This File Organization Model (i.e. FOM) module allows the management of runtime customizable automatic generation of file names for processes (i.e. data processing function) with named parameters'''


class FileOrganizationModelManager( object ):
    '''
    Manage the discovery and instanciation of available FileOrganizationModel (FOM). A FOM can be represented as a JSON file (or a series of JSON files in a directory). This class allows to identify these files contained in a predefined set of directories (see find_fom method) and to instanciate a FileOrganizationModel for each identified file (see get_fom method).
    '''
    def __init__( self, paths ):
      '''
      Create a FOM manager that will use the given paths to find available FOMs.
      '''
      self.paths = paths
      self._cache = None
    
    
    def find_fom( self ):
        '''Return a list of FileOrganizationModel names. 
        These names can be used to create FileOrganizationModel instances with
        get_fom method. FOM files (or directories) are looked for in self.paths.'''
        result = []
        self._cache = {}
        for path in self.paths:
            for i in os.listdir( path ):
                full_path = os.path.join( path, i )
                if os.path.isdir( full_path ):
                    if os.path.exists( os.path.join( full_path, i + '.json' ) ):
                        self._cache[ i ] = full_path
                        result.append( i )
                elif i.endswith( '.json' ):
                    name = i[ :-5 ]
                    self._cache[ name ] = full_path
                    result.append( name )
        return result
     
    
    def get_fom( self, name ):
        '''
        Returns the FileOrganizationModel instance corresponding to a name
        obtained by find_fom method.
        '''
        if self._cache is None:
            self.find_fom()
        fom = self._cache[ name ]
        if not isinstance( fom, FileOrganizationModel ):
            fom = FileOrganizationModel( fom )
            self._cache[ name ] = fom
        return fom


class FileOrganizationModel( object ):
    def __init__( self, path ):
        '''
        
        '''
        self.name = os.path.basename ( path )
        if self.name.endswith( '.json' ):
          self.name = self.name[ : -5 ]
          stack = [ [] ]
        else:
          stack = [ [ i ] for i in os.listdir( path ) ]
        self.json_data = {}
        while stack:
            path_list = stack.pop( 0 )
            full_path = os.path.join( path, *path_list )
            if os.path.isdir( full_path ):
                stack.extend( path_list + [ i ] for i in os.listdir( full_path ) )
            elif full_path.endswith( '.json' ):
                parent = self.json_data
                for i in path_list[ :-1 ]:
                    parent = parent.setdefault( i, {} )
                parent.update( json.load( open( full_path ) ) )
        
        # Parse directory patterns and convert them to "Python" patterns
        # usable with % operator
        self._directories = {}
        attributes = self.json_data[ 'attributes' ]
        for dir_name, json_pattern in self.json_data.get( 'directories', {} ).iteritems():
            if dir_name in attributes:
                raise ValueError( 'Directory name "%s" is already used for an attribute' % ( dir_name, ) )
            python_pattern = json_pattern.replace( '<', '%(' ).replace( '>', ')s' )
            self._directories[ dir_name ] = python_pattern

        self._processes = {}
        
    
    def attributes( self, process=None ):
      '''
      Returns a definition of attributes
      '''
      if not process:
          return self.json_data[ 'attributes' ]
      else:
          process_dir = self._get_process_dir( process )
          if process_dir:
            attributes = set()
            cre = re.compile( r'%\(([^)]*)\)s' )
            for i in process_dir.itervalues():
              attributes.update( cre.findall( i ) )
            return dict( ( k, v ) for k, v in self.json_data[ 'attributes' ].iteritems() if k in attributes )
          else:
            return self.json_data[ 'attributes' ]
    
    
    def _get_process_dir( self, process ):
        process_dir = self._processes.get( process )
        if process_dir is None:
            process_json = self.json_data[ 'processes' ].get( process )
            if process_json is None:
                return None
            process_dir = {}
            for parameter, completion in process_json.iteritems():
                json_pattern, extensions = completion
                python_pattern = json_pattern.replace( '{', '%(' ).replace( '}', ')s' ) % self._directories
                python_pattern = python_pattern.replace( '<', '%(' ).replace( '>', ')s' )
                process_dir[ parameter ] = python_pattern
            self._processes[ process ] = process_dir
        return process_dir
        
        
    def process_completion( self, process, attributes ):
        return dict( ( k, v % attributes ) for k, v in self._get_process_dir( process ).iteritems() )
        

                
                
def call_before_application_initialization( application ):
    application.add_trait( 'fom_path', 
      ListStr( descr='Path for finding file organization models' ) )
    if application.install_directory:
        application.fom_path = [ os.path.join( application.install_directory, 
            'share', 'sandbox', 'soma', 'fom' ) ]

            
def call_after_application_initialization( application ):
    application.fom_manager = FileOrganizationModelManager( application.fom_path )
    


if __name__ == '__main__':
    import pprint
    
    # First thing to do is to create an Application with name and version
    app = Application( 'test', '1.0' )
    # Register module to load and call functions before and/or after
    # initialization
    app.plugin_modules.append( 'sandbox.soma.fom' )
    # Application initialization (e.g. configuration file may be read here)
    app.initialize()
    
    # Parse all FOM and print their dictionary created from JSON file(s)
    for fom_name in app.fom_manager.find_fom():
      print fom_name
      print
      fom = app.fom_manager.get_fom( fom_name )
      import pprint
      pprint.pprint( fom.json_data )
      print '-' * 40
    
    # Print attributes from brainvisa-3.1.0. First all possible attributes
    # of the FOM, then attributes used in parameters of a specific process.
    fom = app.fom_manager.get_fom( 'simple' )
    print 'all attributes :'
    pprint.pprint( fom.attributes() )
    print '-' * 40
    print 'BiasCorrection attributes :'
    pprint.pprint( fom.attributes( 'BiasCorrection' ) )
    print '-' * 40

    # Print completion of a process parameters given attributes
    completion = fom.process_completion( 'BiasCorrection',
        dict( protocol='PROTO', 
              acquisition='ACQU', 
              analysis='ANAL', 
              modality='MODAL', 
              subject='SUBJ' ) )
    pprint.pprint( completion )
