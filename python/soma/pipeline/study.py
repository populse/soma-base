# -*- coding: utf-8 -*-
import json
import os
import collections 
import datetime
import glob
from soma.sorted_dictionary import SortedDictionary
from soma.controller import Controller
try:
    from traits.api import HasTraits,Str,Enum,Directory,File
except ImportError:
    from enthought.traits.api import HasTraits,Str,Enum,Directory,File
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
        self.add_trait('input_directory',Directory)
        #self.add_trait('input_directory',Directory('/nfs/neurospin/cati/cati_shared'))
        self.add_trait('input_fom',Enum(foms))
        self.add_trait('output_directory',Directory)   
        self.add_trait('output_fom',Enum(foms))
        self.add_trait('shared_directory',Directory)
        self.add_trait('spm_directory',Directory)
        self.add_trait('format_image',Str)
        self.add_trait('format_mesh',Str)
        self.add_trait('process',Enum(
            '   ',
            'morphologist.process.morphologist_simplified.SimplifiedMorphologist',
            'morphologist.process.morphologist.Morphologist',
            'morpho.morphologist.morphologist',
            'morphologist.process.customized.morphologist.CustomMorphologist'))
        #self.process_specific=None
        self.compteur_run_process={}
        self.runs=collections.OrderedDict()
        
    #def _input_fom_changed(self, old, new):
        #print 'input fom changed'
        ##Get list format
        #self.add_trait(œ'coucou',Str)
        
        
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
        self.dico=collections.OrderedDict([('name_study',self.name_study),('input_directory',self.input_directory),('input_fom',self.input_fom),('output_directory',self.output_directory),('output_fom',self.output_fom),('shared_directory',self.shared_directory),('spm_directory',self.spm_directory),('format_image',self.format_image),('format_mesh',self.format_mesh),('process',self.process)])
        json_string = json.dumps(self.dico, indent=4, separators=(',', ': '))
        with open(os.path.join(self.output_directory,self.name_study+'.json'), 'w') as f:
            f.write(unicode(json_string))

    """Load and put on self.__dict__ OrderedDict"""        
    def load(self,name_json):
        try:
            with open(name_json, 'r') as json_data:
                self.__dict__ = json.load(json_data,object_pairs_hook=collections.OrderedDict)        
            for element in self.__dict__:
                setattr(self,element,self.__dict__[element])
        
        #No file to load
        except IOError:
            pass
        
        
    #"""Get number of run process and iterate"""        
    #def inc_nb_run_process(self,process_name):
        #print 'process_name',process_name
        #if self.compteur_run_process.has_key(process_name):
            #valeur=self.compteur_run_process[process_name]
            #print 'valeur',valeur
            #self.compteur_run_process[process_name]=valeur+1
        #else:
            #self.compteur_run_process[process_name]=1


    def save_run(self,attributes,process):
        print 'save run'
        #Create date directory
        date=datetime.datetime.now()
        date_directory=str(date.day)+'_'+str(date.month)+'_'+str(date.year)
        directory=os.path.join(self.output_directory,date_directory)
        if not os.path.exists(directory):
            name_run=process.name+str(1)
            os.makedirs(directory)
            self.compteur_run_process[process.name]=1
        
        else:
            list_json=glob.glob(directory+os.sep+'*.json')
            inc=1
            number=len(list_json)+inc
            name_run=process.name+str(number)
            while os.path.exists(os.path.join(directory,name_run+'.json')) is True:
                inc=inc+1
                number=len(list_json)+inc
                name_run=process.name+str(number)
            self.compteur_run_process[process.name]=number
        
        run=collections.OrderedDict()
        run['process_name']='morphologist.process.morphologist_simplified.SimplifiedMorphologist'
        #self.inc_nb_run_process(process.name )
        run['attributes']={}
        for key in attributes:
            run['attributes'][key]=attributes[key]
        run['parameters']=collections.OrderedDict()
        run['input']=collections.OrderedDict()
        run['output']=collections.OrderedDict()
        #dicti_sorted=SortedDictionary(*[(key,a[key]) for key in a])

        for name, trait in process.user_traits().iteritems():
            if trait.is_trait_type( File ) is False:
                run['parameters'][name]=getattr(process,name)
            elif trait.output is False:
                run['input'][name]=getattr(process,name)
            elif trait.output is True:
                run['output'][name]=getattr(process,name)

        dico=collections.OrderedDict([('name_study',self.name_study),('input_directory',self.input_directory),('input_fom',self.input_fom),('output_directory',self.output_directory),('output_fom',self.output_fom),('shared_directory',self.shared_directory),('spm_directory',self.spm_directory),('format_image',self.format_image),('format_mesh',self.format_mesh),('run',run)])
        json_string = json.dumps(dico, indent=4, separators=(',', ': '))
        
        with open(os.path.join(directory,name_run+'.json'), 'w') as f:
            f.write(unicode(json_string)) 

        #To incremente compteur runs
        self.save()
