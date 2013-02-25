# -*- coding: utf-8 -*-


import os
#os.environ['ETS_TOOLKIT'] = 'qt4'
#from traits.etsconfig.api import ETSConfig
#ETSConfig.toolkit = 'qt4'
from traits.api import HasTraits,Button, Str, Event, Int,Float, Enum, \
Instance, Property, Bool, List
from traitsui.api import View,Group,Label,Item,InstanceEditor, \
FileEditor, DirectoryEditor, UItem
from string import strip
import TraitementJSON
import glob
#from process.BiasCorrection import BiasCorrection
#from process.HistogramAnalysis import HistogramAnalysis
from Traitement import Traitement
       
class GestionView(HasTraits):
    
    # Une vue contenant tous les traits editables (sauf genView)
    genView = Property(Instance(View))
    
    def _get_genView(self):
        # Crée une vue qui est une liste de traits éditables
        trait_names = self.editable_traits()
        trait_names.remove('genView')    
        return View(trait_names)

        

class GestionInterface (HasTraits): 

    def __init__( self, *args, **kwargs ):
        super( GestionInterface, self ).__init__( *args, **kwargs )
        HasTraits.__init__(self,**kwargs)
        
        # Objet traitement pour la création des traits etc...
        self.traitement=Traitement()
        
        # Booléen pour indiquer initialisation des traits dynamiques
        self.update_param_enable=False
        self.update_attributs_enable=False

        
        # Camera Attributs de la MOF
        # Camera2 Paramètres du process choisi
        # Camera3 Complétion
        # Savoir si les traits dynamiques ont été modifiés
        self.camera2.on_trait_change(self.update_parametre)
        self.camera.on_trait_change(self.update_attributs)
        self.camera3.on_trait_change(self.update_path)
                  
        # Données du JSON
        self.data=None
        self.parameters=None
        self.attributs=None
        self.process=None
        self.extension_dictionnary=None
        self.extension_path=None
        self.path_input=None
                
        # Chemins de données (path) dépend des attributs entrés
        self.path=Property(depends_on=[self.attributs,self.output_directory], cached = False )    
        
        # Choix MOF 
        li=glob.glob('*.json')
        li.insert(0,' ')
        self.list_mof=Enum(li)
        self.add_trait('list_mof', self.list_mof)

        # Choix Process
        lis_pro=[]
        lis=glob.glob('process/*.py')
        for i in range (len(lis)):
            lis_pro.append(os.path.basename(lis[i]))  
            lis_pro[i]=lis_pro[i].split('.')[-2]                
        lis_pro.remove('__init__')           
        lis_pro.insert(0,' ')
        self.list_process=Enum(lis_pro)
        self.add_trait('list_process', self.list_process)
                              
    ###DEFINITION DES TRAITS CONSTANTS  
    # Dossier de sortie
    output_directory = Str
    
    # Dossier d'entrée
    input_directory=Str
    
    input=Str
    
    # Bouton lancement process
    run=Button('RUN')
    
    # Afficher completion des fichiers sortie process
    display_hide_completion=Button('Display/Hide Completion')
    bool_display_hide_completion=Bool(False)
    
    #Booléen pour autoriser choix MOF (donc quand process choisi)
    mof_enable=Bool(False)
    extension_change=Bool(True)
    use_OK=Bool(False)
    
    
    ###FONCTIONS POUR TRAITS        
    # Dossier de sortie
    def _output_directory_fired(self):
        if self.update_attributs_enable:
            # Met à jour les chemins de données avec le nouveau dossier de sortie
            self.path=TraitementJSON.Completion(self.data,self.output_directory,self.list_process)
            # Mise à jour nouveaux chemins de données graphiquement
            for key in sorted(self.path.keys()):    
                setattr(self.camera3,key,self.path[key])
                self.camera3.trait_property_changed('genView', None, self.camera3.genView)


    # Choix du process/Affichage parametre  
    def _list_process_fired(self):  
        # Booléen pour indiquer que le choix de la mof est dispo ou non
        self.mof_enable=True
        # Création objet du process choisi      
        self.process=self.traitement.getObject(self.list_process)
       
        # Récupération des paramètres
        #Fonction pour différencier les paramètres/entrées/sorties      
        self.parameters,self.path_input,self.path=self.traitement.data_process(self.process)      
        #Boucle pour mettre les paramètres à leurs valeurs par défaut (si l'utilisateur ne les modifie pas)
        for trait in self.parameters:
            setattr( self.process, trait, getattr(self.process,trait).default_value)
                    
        # Création et affichage des paramètres
        self.traitement.create_traits(self.camera2,self.parameters)  
        # Booléen pour indiquer que paramètres créés et que si changement appel de la fonction update OK
        self.update_param_enable=True

                                            
    def _list_mof_fired(self):      
       # Si le choix de la MOF a changé et que une mof avait déjà été choisie    
        if self.data is not None:
            self.update_attributs_enable=False
            self.traitement.delete_traits(self.camera,self.attributs)
            self.traitement.delete_traits(self.camera3,self.path)     
         
        # Choix de la mof            
        if self.list_mof is not None and self.list_mof!=' ':                             
            # Récupération des données du JSON correspondant à la MOF
            self.data=TraitementJSON.DataJSON(self.list_mof)
            # Récupération des attributs et on les mets daans l'attributs de classe correspondant
            self.attributs=self.data['Attributs']
            self.extension_dictionnary=self.data['Extension']
            # Affichage des Attributs
            self.traitement.create_traits(self.camera,self.attributs)           
            # Récupération des Attributs completés par l'utilisateur (enlève espace)
            self.attributs=self.traitement.save_attributs(self.camera,self.attributs)
            # Création des chemins de données
            self.path,self.extension_path=TraitementJSON.Completion(self.data,self.output_directory,self.list_process)
            # Affichage des chemins de données
            self.traitement.create_traits(self.camera3,self.path)
            
            self.traitement.create_traits(self.camera4,self.extension_path)
            
            self.update_attributs_enable=True
    
    def _display_hide_completion_fired(self):
        self.bool_display_hide_completion = not self.bool_display_hide_completion
    
    
    # Mettre a jour les paths quand les attributs sont modifiés
    def update_attributs(self,object,name,old,new):
        # Si initialisation OK
        if self.update_attributs_enable:
            # Récupération de la valeur de l'attribut
            self.attributs[name]=new
            # Enlève espace invoulu
            self.attributs=self.traitement.save_attributs(self.camera,self.attributs)
            # Retourne un dictionnaire avec les chemins pour chaque sortie
            self.path,self.extension_path=TraitementJSON.Completion(self.data,self.output_directory,self.list_process)
            # Mise à jour des traits correspondant aux paths            
            for key in sorted(self.path.keys()):    
                setattr(self.camera3,key,self.path[key])
                self.camera3.trait_property_changed('genView', None, self.camera3.genView)
                
                
    def update_path(self,object,name,old,new):
        setattr( self.process, name, new)
        if self.update_attributs_enable:
            if old is not None and new is not None:
                ext_old='.'+old.split('.')[-1]
                ext_new='.'+new.split('.')[-1]
                if ext_old != ext_new:
                    self.traitement.check_extension(ext_new,self.extension_path,name)
                    if self.traitement.check_extension(ext_new,self.extension_path,name)==1:
                        print 'ERROR'
                        extension_change=False
                    else:
                        extension_change=True
                        
                
        
    def update_parametre(self,object,name,old,new):
        if self.update_param_enable:
            # Mise à jour des paramètres du process            
            setattr( self.process, name, new)
            
               
    def _run_fired(self):
        print 'EXECUTION'
        # Créer les chemins de données
        self.traitement.create_path(self.path)
        # Lancement du process choisi
        self.process.run(self.path,self.input)
                                                
    # Création de la vue
    view = View(
        Group( 
            Group(      
                Item('output_directory',editor=DirectoryEditor()),
                Item('input_directory',editor=DirectoryEditor()),
                #Item('input',editor=FileEditor()), 
                show_border=True,
                ),
                
            Group(
                Item('list_process',enabled_when='output_directory'),    
                Group(      
                    UItem('camera2',
                        editor=InstanceEditor(view_name='object.camera2.genView',droppable=False),
                        style='custom'),
                    scrollable=True,    
                    ),
                show_border=True,
                ),

      
            Group( 
                Item('list_mof',enabled_when='mof_enable'),  
                UItem('camera',
                    editor=InstanceEditor(view_name='object.camera.genView',cachable=False), 
                    style='custom'),             
                show_border=True,
                scrollable=True
                 ),
       
            UItem('display_hide_completion'), 
            Group(     
                UItem('camera3', 
                    editor=InstanceEditor(view_name='object.camera3.genView'),
                    invalid='use_OK',
                    style='custom'),             
   
                show_labels=False,
                show_border=True,
                scrollable=True,
                visible_when='bool_display_hide_completion',
                ), 

            orientation = 'vertical'
                 ),
        UItem('run'),
        title='Traitement',     
        buttons=['OK','Cancel'],
        resizable=True,
        width= 800, height=800
     )
                    


if __name__ == "__main__":
    Camera = GestionView()
    Camera2 = GestionView()
    Camera3 = GestionView()
    Camera4=GestionView()
    camera_wrapper = GestionInterface(camera=Camera,camera2=Camera2,camera3=Camera3,camera4=Camera4)
    camera_wrapper.configure_traits()

