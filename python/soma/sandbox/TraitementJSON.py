# -*- coding: utf-8 -*-
#class qui va définir les attributs selon la hiérarichie brainVISA 3.1.0
from traits.api import Str,Int
from string import strip
import os
import json
import simplejson
import re


# Récupération des données du .json
def DataJSON(name): 
    with open(name, "r") as fichier:
        data= json.load(fichier)
    return data
  
  
# Extension fichiers sorties entrees?
def Extension(name_extension,data,cond):
        if cond==0:
            return data["Extension"][name_extension][0]
        else:
            return data["Extension"][name_extension]
    

# Création des chemins pour entrées/sorties
def Completion(data,out_directory,the_process):
    dir={}
    path={}
    ext={}
    directories_exist=False
    dir_find=False
    if data.has_key('Directories'):
        directories_exist=True
        for key2 in (data['Directories'].keys()):
            data2=data['Directories'][key2]
            for key in sorted(data['Attributs'].keys()):
                p=re.compile('<'+key+'>')
                data2=p.sub(data['Attributs'][key],str(data2))      
                dir[key2]=out_directory+data2                    
    # Parcours des sorties pour le process
    for key2 in (data[the_process].keys()):
        # on met le chemin dans data2
        data2=data[the_process][key2][0]      
        if directories_exist==True:
            for key in sorted(data['Directories'].keys()):
                d=re.compile('{'+key+'}')
                ho=d.findall(str(data2))
                if len(ho) > 0 :
                    dir_find=True    
                    data2=d.sub(dir[key],str(data2))
                else:
                    dir_find=False                       
        for key in sorted(data['Attributs'].keys()):
            # recherche attributs définis <>
            p=re.compile('<'+key+'>')
            data2=p.sub(data['Attributs'][key],str(data2))
            # le chemin est crée avec les attributs entrés par l'utilisateur   
            # création des chemins de données
            #Si un chemin de sortie
            if dir_find==True: 
                ext[key2]=Extension(data[the_process][key2][1],data,1)   
                path[key2]=data2+Extension(data[the_process][key2][1],data,0)   
            else:
                path[key2]=out_directory+data2+Extension(data[the_process][key2][1],data,1)  
                ext[key2]=Extension(data[the_process][key2][1],data,0)                     
    return path,ext
