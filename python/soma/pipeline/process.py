# -*- coding: utf-8 -*-
import os
try:
    from traits.api import ListStr,HasTraits,File,Float,Instance,Enum,Str
except ImportError:
    from enthought.traits.api import ListStr,HasTraits,File,Float,Instance,Enum,Str

from soma.controller import Controller,add_trait
from soma.application import Application
from soma.fom import PathToAttributes,AttributesToPaths,DirectoryAsDict
from soma.path import split_path
from soma_workflow.client import Job, Workflow, Group, Helper,WorkflowController
import subprocess
from soma.global_naming import GlobalNaming
from soma.pipeline.study import Study

class Process( Controller ):
    def __init__( self, **kwargs ):
        super( Process, self ).__init__( **kwargs )
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
        if isinstance( process_or_id, Process ):
            return process_or_id
        module = __import__( process_or_id, fromlist=[ '' ], level=0 )
        processes = [ i for i in module.__dict__.itervalues() if isinstance(i,type) and issubclass( i, Process ) and i.__module__ == process_or_id ]
        if not processes:
          raise ImportError( 'No process defined in %s' % process_or_id )
        elif len( processes ) > 1:
          raise ImportError( 'Several processes declared in %s' % process_or_id )
        module = GlobalNaming().get_object( process_or_id )
        process = processes[ 0 ]( **kwargs )
        return process


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
	


      
