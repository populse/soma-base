# -*- coding: utf-8 -*-
from traits.api import HasTraits,Int,Str,Enum,File
import json
import os
from string import strip

#Créer un script qui importe automatique les process
from process.BiasCorrection import BiasCorrection
from process.HistogramAnalysis import HistogramAnalysis

class Traitement(HasTraits):
   
   
    def delete_traits(self,camera,traits):
        for key in sorted(traits.keys()):    
            camera.remove_trait(key)
            camera.trait_property_changed('genView', None, camera.genView)

    def save_attributs(self,camera,traits):
        for key in sorted(traits.keys()):    
            traits[key]=strip(str(getattr(camera,key)))      
        return traits
            
    def create_traits(self,camera,traits):
        for key in sorted(traits.keys()):       
            camera.add_trait(key,traits[key])
            getattr(camera,key)
            camera.trait_property_changed('genView', None, camera.genView)
 
    def create_path(self,path): 
        for key in path.keys():
            # On crée le dossier (enlève partie du nom fichier)
            dir=path[key].replace(path[key].split('/')[-1],"")
            if os.path.exists(dir)==False:  
                os.makedirs(dir)

    def data_process(self,process):
        data=process.get()
        input={}
        output={}
        parameters={}
        for key in data.keys():         
            if type(data[key]) is File:
                if data[key].exists==True:
                    input[key]=data[key]
                else:
                    output[key]=data[key]
            else:
                parameters[key]=data[key]
        #Retourne les parametres, entrées,sorties du process (à changer pas très propre)        
        return parameters,input,output

    def check_extension(self,ext_new,extension_enable,name):
        if ext_new not in extension_enable[name]:
            return 1
        return 0
            
        
    def getObject(self,name_process):
        object=globals()[name_process]
        return object()
