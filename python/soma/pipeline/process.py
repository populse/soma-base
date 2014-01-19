# -*- coding: utf-8 -*-
import os
try:
    from traits.api import ListStr,HasTraits,File,Float,Instance,Enum,Str
except ImportError:
    from enthought.traits.api import ListStr,HasTraits,File,Float,Instance,Enum,Str

from soma.sorted_dictionary import SortedDictionary
from soma.controller import Controller,add_trait
from soma.application import Application
from soma.fom import PathToAttributes,AttributesToPaths,DirectoryAsDict
from soma.path import split_path
from soma_workflow.client import Job, Workflow, Group, Helper,WorkflowController
import subprocess
from soma.global_naming import GlobalNaming
from soma.pipeline.study import Study

class Process( Controller ):
    def __init__( self ):
        super( Process, self ).__init__()
        id = self.__class__.__module__ + '.' + self.__class__.__name__
        self.id = id
        self.name = self.__class__.__name__
        self.viewers={}
      
    def set_viewer( self, parameter, viewer, **kwargs ):
        self.viewers[ parameter ] = ( viewer, kwargs )
      
    def call_viewer( self, controller_widget,name ):
        viewer, kwargs = self.viewers[ name ]
        if not kwargs:
            liste=[]
            liste.append(getattr(controller_widget.controller,name))
            p = GlobalNaming().get_object( viewer)(*liste)
        else:          
            dico_parameter={}
            #dico_parameter[name]=value
            #get all traits name of the process
            trait_of_process=controller_widget.controller.user_traits().keys()
            #Get parameters in the kwargs and complete value of traits needed
            for key,value in kwargs.iteritems():
                dico_parameter[key]=value
                if value in trait_of_process:
                    dico_parameter[key]=getattr(controller_widget.controller,value)          
            p = GlobalNaming().get_object( viewer)(**dico_parameter)
        return p()

    @staticmethod
    def get_instance( process_or_id, **kwargs ):
        '''
        Return an instance of Process given its identifier. The identifier is
        a string identifying a class derived from Process. It must contain one
        of the following value:
        - The name of a Python module containing a single declaration of class
          derived from Process. e.g 'morphologist.process.morphologist'
        - '<module>.<class>' where <module> is the name of a Python module and
          <class> is the name of a Process derived class defined in this
          module. e.g. 'soma.pipeline.sandbox.SPMNormalization'
        '''
        if isinstance( process_or_id, Process ):
            return process_or_id
        # Try to import a module that must contain a single Process derived class
        try:
          module = __import__( process_or_id, fromlist=[ '' ], level=0 )
        except ImportError:
          module = None
        if module is None:
          process_class = GlobalNaming().get_object( process_or_id )
        else:
          # 
          processes = [ i for i in module.__dict__.itervalues() if isinstance(i,type) and issubclass( i, Process ) and i.__module__ == process_or_id ]
          if not processes:
            raise ImportError( 'No process defined in %s' % process_or_id )
          elif len( processes ) > 1:
            raise ImportError( 'Several processes declared in %s' % process_or_id )
          process_class = processes[ 0 ]
        if process_class is None:
          raise ValueError( 'Cannot find process %s' % repr( process_or_id ) )
        return process_class( **kwargs )

        
    def string_to_parameter( self, parameter, string_value ):
      '''
      Convert a string value to an appropriate value type for the given parameter
      name
      '''
      parameters = parameter.split( '.' )
      object = self
      while parameters:
        trait = object.trait( parameters[ 0 ] )
        if trait is None:
          raise ValueError( '%s is not a valid parameter name for %s' % ( parameter, self.id ) )
        object = getattr( object, parameters.pop( 0 ) )
      evaluate = trait.handler.evaluate
      if evaluate is None:
        return string_value
      else:
        return evaluate( string_value )
    
    
    def set_string_list( self, string_list ):
      '''
      Set parameters values given a list of string, this is mainly used to 
      call a process from a command line. Is is possible to give a list of 
      values without parameter names (e.g. [ '/tmp/a_file.txt', '4' ] but also
      to give the name of a parameter for a value (e.g. [ 'file=/tmp/a_file.txt',
      'value=4' ]). For each parameter, string value is converted to the 
      appropriate type with string_to_parameter.
      '''
      args = []
      kwargs = SortedDictionary()
      for s in string_list:
        i = s.find( '=' )
        if i < 0:
          args.append( s )
        elif i == 0:
          args.append( s[ 1: ] )
        else:
          n = s[ :i ]
          v = s[ i+1: ]
          kwargs[ n ] = self.string_to_parameter( n, v )
      if args:
        for t in self.user_traits():
          if t in kwargs:
            continue
          kwargs[ t ] = self.string_to_parameter( t, args.pop( 0 ) )
          if not args:
            break
        if args:
          raise ValueError( 'Too many parameters given for process %s' % self.id )
      for k, v in kwargs.iteritems():
        v = self.string_to_parameter( k, v )
        ks = k.split( '.' )
        object = self
        while len( ks ) > 1:
          object = getattr( object, ks.pop( 0 ) )
        setattr( object, ks[ 0 ], v )
    

class ProcessWithFom(Controller):
    """Class who create attributs and create completion"""
    #name = 'morphologistSimp.SimplifiedMorphologist'   
    def __init__(self,process_specific):   
        HasTraits.__init__(self) 
        self.process_specific=process_specific
        self.list_process_iteration=[]
        #self.fom=fom
        self.attributes={}
        self.Study=Study.get_instance()
        self.directories={}
        self.directories['spm']=self.Study.spm_directory
        self.directories['shared']=self.Study.shared_directory
        self.directories[ 'input' ] = self.Study.input_directory
        self.directories[ 'output' ] = self.Study.output_directory
        self.input_fom = Application().fom_manager.load_foms( self.Study.input_fom)
        self.output_fom = Application().fom_manager.load_foms( self.Study.output_fom )
        self.create_attributes_with_fom()
        #self.find_attributes('t1mri',None)
        self.completion_ongoing = False
        
    """Function use when new file add on table"""        
    def iteration(self,process,newfile):
        self.list_process_iteration.append(process)
        pwd=ProcessWithFom(process)
        #process.t1mri=newfile
        #process_with_fom.output_directory=self.study_directory
        pwd.create_attributes_with_fom()
        #pwd.find_attributes('t1mri',newfile,{'spm' : '/here/is/spm','shared' : os.environ[ 'BRAINVISA_SHARE' ] + '/brainvisa-share-4.5' })
        pwd.create_completion()
        return pwd
        
    def iteration_run(self):
        print 'ITERATION RUN'
        self.jobs={}
        i=0        
        for process in self.list_process_iteration:
            self.jobs['job'+str(i)]= Job(command=process.command())
            i=i+1
        
        wf=Workflow(jobs=[value for value in self.jobs.itervalues()],name='test')
        Helper.serialize('/tmp/test_wf',wf)
        controller=WorkflowController()
        controller.submit_workflow(workflow=wf,name='test run')


    """To get useful attributes by the fom"""   
    def create_attributes_with_fom(self):
        #self.attributes=self.foms.get_attributes_without_value()
        ## Create an AttributesToPaths specialized for our process        
        formats=tuple(getattr(self.Study,key) for key in self.Study.user_traits() if key.startswith('format'))

        self.input_atp = AttributesToPaths( self.input_fom, selection=dict( fom_process=self.process_specific.name_process ),
                             directories=self.directories,prefered_formats=set((formats)) )
                              
        self.output_atp = AttributesToPaths( self.output_fom, selection=dict( fom_process=self.process_specific.name_process ),
                             directories=self.directories,prefered_formats=set((formats)) )

        
        #Get attributes in input fom
        process_specific_attributes=set()
        for parameter in self.input_fom.patterns[self.process_specific.name_process]:
            process_specific_attributes.update(self.input_atp.find_discriminant_attributes(fom_parameter=parameter))
            
        for att in process_specific_attributes:
            if not att.startswith( 'fom_' ):
                default_value = self.input_fom.attribute_definitions[ att ].get( 'default_value' )
                self.attributes[att]=default_value
                add_trait(self,att,Str(self.attributes[att]))                         
        
        #Only search other attributes if fom not the same (by default merge attributes of the same foms)        
        if self.Study.input_fom != self.Study.output_fom:
            #Get attributes in output fom
            process_specific_attributes2=set()
            for parameter in self.output_fom.patterns[self.process_specific.name_process]:
                process_specific_attributes2.update(self.output_atp.find_discriminant_attributes(fom_parameter=parameter))

            for att in process_specific_attributes2:
                if not att.startswith( 'fom_' ):
                    default_value = self.output_fom.attribute_definitions[ att ].get( 'default_value' )
                    if att in process_specific_attributes and  default_value != self.attributes[att]:
                        print 'same attribute but not same default value so nothing displayed'
                    else:        
                        self.attributes[att]=default_value
                        add_trait(self,att,Str(self.attributes[att]))                         
        
        


    """By the path, find value of attributes"""
    def find_attributes(self,value):        
        print 'FIND ATTRIBUTES'
        #By the value find attributes        
        pta = PathToAttributes( self.input_fom, selection=dict( fom_process=self.process_specific.name_process)) #, fom_parameter=name ) )        
                

        # Extract the attributes from the first result returned by parse_directory
        liste=split_path(value)        
        len_element_to_delete=1
        for element in liste:
          if element != os.sep:
            len_element_to_delete=len_element_to_delete+len(element)+1
            new_value=value[len_element_to_delete:len(value)]
            try:
              #import logging
              #logging.root.setLevel( logging.DEBUG ) 
              #path, st, self.attributes = pta.parse_directory( DirectoryAsDict.paths_to_dict( new_value), log=logging ).next()
              path, st, attributes = pta.parse_directory( DirectoryAsDict.paths_to_dict( new_value) ).next()
              break
            except StopIteration: 
              if element == liste[-1]:
                raise ValueError( '%s is not recognized for parameter "%s" of "%s"' % ( new_value,None, self.process_specific.name_process ) )
                
        for att in attributes:
            if att in self.attributes:
                setattr(self,att,attributes[att])
        
        
        
    def create_completion(self):  
        print 'CREATE COMPLETION'              
        #Create completion    
        completion={}
        #for i in self.process_specific.user_traits():
            #parameter = self.output_fom.patterns[ self.process_specific.name_process ].get( i )
        for parameter in self.output_fom.patterns[self.process_specific.name_process]:
        #if parameter is not None:
            # Select only the attributes that are discriminant for this parameter
            # otherwise other attibutes can prevent the appropriate rule to match
            if parameter in self.process_specific.user_traits():
                #print 'parameter',parameter
                if self.process_specific.trait( parameter ).output:
                    atp=self.output_atp
                else:   
                    #print 'input ',parameter
                    atp=self.input_atp           
                parameter_attributes = [ 'fom_process' ] + atp.find_discriminant_attributes( fom_parameter=parameter )
                d = dict( ( i, self.attributes[ i ] ) for i in parameter_attributes if i in self.attributes )
                d['fom_parameter'] = parameter
                d['fom_format']='fom_prefered'
                for h in atp.find_paths(d):          
                    setattr(self.process_specific,parameter,h[0])         
                        
        
    def attributes_changed(self,object,name,old,new):
        print 'attributes changed',name
        print self.completion_ongoing
        if  name != 'trait_added' and name != 'user_traits_changed' and self.completion_ongoing is False:        
            #setattr(self,name,new)
            #print 'here attributes change',name
            self.attributes[name]=new
            self.completion_ongoing = True  
            self.create_completion()
            #print 'end completion'
            self.completion_ongoing = False 
        


      
