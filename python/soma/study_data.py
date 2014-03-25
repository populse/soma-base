# -*- coding: utf-8 -*-
import json
import os
import collections 

class StudyData():
    _instance=None
    """Class to write and save informations about process in the json"""
    def __init__(self):
        self.name_study = "Study"
        self.study_directory = ""
        self.compteur_run_process={}
        self.runs=collections.OrderedDict()

    @staticmethod
    def get_instance():
        if StudyData._instance is None:
            StudyData._instance=StudyData()
            return StudyData._instance
        else:
            return StudyData._instance

    """Save on json with OrderedDict"""
    def save(self):
        self.dico=collections.OrderedDict([('name_study',self.name_study),('study_directory',self.study_directory),('compteur_run_process',self.compteur_run_process),('runs',self.runs)])
        json_string = json.dumps(self.dico, indent=4, separators=(',', ': '))
        with open(os.path.join(self.study_directory,self.name_study+'.json'), 'w') as f:
            f.write(unicode(json_string))

    """Load and put on self.__dict__ OrderedDict"""
    def load(self):
        try:
            with open(os.path.join(self.study_directory,self.name_study+'.json'), 'r') as json_data:
                self.__dict__ = json.load(json_data,object_pairs_hook=collections.OrderedDict)        
        #No file to load
        except IOError:
            pass

    """Get number of run process and iterate"""
    def inc_nb_run_process(self,process_name):
        if self.compteur_run_process.has_key(process_name):
            valeur=self.compteur_run_process[process_name]
            self.compteur_run_process[process_name]=valeur+1
        else:
            self.compteur_run_process[process_name]=1

