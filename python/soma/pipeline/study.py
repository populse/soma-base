# -*- coding: utf-8 -*-
import json
import os
import collections 
from soma.controller import Controller,add_trait
try:
    from traits.api import HasTraits,Str,Enum,Directory
except ImportError:
    from enthought.traits.api import HasTraits,Str,Enum,Directory
from soma.application import Application     

class Study(Controller):
    _instance=None
    """Class to write and save informations about process in the json"""
    def __init__(self):
	super(Study, self).__init__() 
        HasTraits.__init__(self) 
	# Find foms available     
        foms = Application().fom_manager.find_foms()
	foms.insert(0,' ')
	#add_trait(self,'input_directory',Directory('/home/mb236582/datafom'))  
	add_trait(self,'input_directory',Directory('/nfs/neurospin/cati/cati_shared'))  

	add_trait(self,'input_fom',Enum(foms))   
        add_trait(self,'output_directory',Directory('/home/mb236582/my_study'))   
	add_trait(self,'output_fom',Enum(foms))
	add_trait(self,'shared_directory',Directory(os.environ[ 'BRAINVISA_SHARE' ] + '/brainvisa-share-4.5'))
	add_trait(self,'spm_directory',Directory('/here/is/spm'))
        add_trait(self,'format_image',Str('.nii'))
	add_trait(self,'format_mesh',Str('.gifti')) 
        #self.name_study = "Study"
	#self.study_directory = ""
	self.compteur_run_process={}
	self.runs=collections.OrderedDict()
	
    @staticmethod
    def get_instance():
        if Study._instance is None:
            Study._instance=Study()
            return Study._instance
        else:
            return Study._instance
	    
    """Save on json with OrderedDict"""	    
    def save(self):
	self.name_study=str(self.output_directory.split(os.sep)[-1])
	self.dico=collections.OrderedDict([('name_study',self.name_study),('input_directory',self.input_directory),('input_fom',self.input_fom),('output_directory',self.output_directory),('output_fom',self.output_fom),('shared_directory',self.shared_directory),('spm_directory',self.spm_directory),('format_image',self.format_image),('format_mesh',self.format_mesh),('compteur_run_process',self.compteur_run_process),('runs',self.runs)])
        json_string = json.dumps(self.dico, indent=4, separators=(',', ': '))
        with open(os.path.join(self.output_directory,self.name_study+'.json'), 'w') as f:
            f.write(unicode(json_string))

    """Load and put on self.__dict__ OrderedDict"""	 
    def load(self,name_json):
	print 'in load'
	try:
            with open(name_json, 'r') as json_data:
                self.__dict__ = json.load(json_data,object_pairs_hook=collections.OrderedDict)	
	    for element in self.__dict__:
		setattr(self,element,self.__dict__[element])
	        
	#No file to load	
        except IOError:
	    pass
		
    """Get number of run process and iterate"""	    
    def inc_nb_run_process(self,name_process):
	if self.compteur_run_process.has_key(name_process):
	    valeur=self.compteur_run_process[name_process]
	    self.compteur_run_process[name_process]=valeur+1
	else:
	    self.compteur_run_process[name_process]=1 
	
