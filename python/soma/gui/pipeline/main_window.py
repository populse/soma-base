# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from soma.gui.widget_controller_creation import ControllerWidget
from soma.gui.pipeline.display_bdd import DisplayBDD
from soma.application import Application 
#from soma.gui.simple_process import SimpleProcess
try:
  from capsul.process.process import ProcessWithFom,Process, get_process_instance
  from capsul.pipeline.study import Study
except ImportError:
  from soma.process import Process, get_process_instance
  from soma.pipeline.process_with_fom import ProcessWithFom
  from soma.pipeline.study import Study
from soma.gui.pipeline.process_gui import ProcessGui
from soma.gui.pipeline.iteration_gui import IterationGui,ChoiceParameters
#from morphologistSimp import SimpMorpho
#from attributs import Attributs
from soma.gui.pipeline.selection_widget import Selection
from soma.functiontools import SomaPartial as partial
from soma.gui.pipeline.pipeline_gui import PipelineView
import subprocess        
import os


class MainWindow(QtGui.QMainWindow):
    """Class to create study and to launch Simple or iteration process"""   
    def __init__(self):     
        super(MainWindow, self).__init__()         
        self.main_widget=QtGui.QWidget()
        self.vbox=QtGui.QVBoxLayout()
        
        ##Study
        self.btn_get_study=QtGui.QPushButton('Get .json from study')
        self.vbox.addWidget(self.btn_get_study)
        
        self.vbox.addWidget(QtGui.QLabel('Study Information'))
        # Find foms available
        foms = Application().fom_manager.find_foms()        
        #self.grid=QtGui.QGridLayout()
      
        #Scroll area to show completion
        self.scroll_area = QtGui.QScrollArea( parent=self )
        self.scroll_area.setWidgetResizable( True )
        self.vbox.addWidget( self.scroll_area )

        #Create controller widget for process and object_attribute
        self.controller_widget22 = ControllerWidget( Study.get_instance(), live=True, parent=self.scroll_area )
        self.scroll_area.setWidget( self.controller_widget22 )
      

        #Launch Simple process
        self.btn_run_simple_process=QtGui.QPushButton('GUI Simple Process')
        #Launch Pipeline Process
        self.btn_run_pipeline_process=QtGui.QPushButton('GUI Pipeline Process')
        #Launch Iteration process
        self.btn_run_iteration_process=QtGui.QPushButton('GUI Iteration Process')
        #Launch display BDD
        self.btn_display_bdd=QtGui.QPushButton('Launch BDD')
    
        self.vbox.addWidget(self.btn_run_simple_process)
        self.vbox.addWidget(self.btn_run_pipeline_process)
        self.vbox.addWidget(self.btn_run_iteration_process)
        self.vbox.addWidget(self.btn_display_bdd)
        self.vbox.addStretch(1)
        self.signals()
        self.main_widget.setLayout(self.vbox)
        self.setCentralWidget(self.main_widget)

    """Create widgets signals """   
    def signals(self):
        self.btn_get_study.clicked.connect(self.on_get_study)
        self.btn_run_simple_process.clicked.connect(self.run_simple_process)
        self.btn_run_pipeline_process.clicked.connect(self.run_pipeline_process)
        self.btn_run_iteration_process.clicked.connect(self.run_iteration_process) 
        self.btn_display_bdd.clicked.connect(self.on_display_bdd)

   
    def on_get_study(self):
        name_json = QtGui.QFileDialog.getOpenFileName (self, 'Select a .json study','/home', '*.json')
        if name_json:
            Study.get_instance().load(name_json)
   
   

    def run_simple_process(self):
        """Launch simple process"""
        print 'RUN SIMPLE PROCESS'        
        #FIXME utile je pense pour creer fichier json si existe pas..
        Study.get_instance().save()
        process_specific=self.get_object_process()
        print 'process_specific:', process_specific
        #To have attributes on header
        process_with_fom=ProcessWithFom(process_specific)
        self.process_gui=ProcessGui(process_with_fom,process_specific)
        self.process_gui.open()
        
        
    def run_pipeline_process(self):
        """Launch pipeline process"""
        subprocess.check_call(['python', '-m', 'morphologist.process'])


        

    
    def run_iteration_process(self):
        """Launch iteration process"""
        print 'RUN ITERATION PROCESS' 
        process_specific=self.get_object_process()
        process_with_fom=ProcessWithFom(process_specific)
        self.wizard=QtGui.QWizard()
        self.wizard.setButtonText(3,'Run all')
        self.connect(self.wizard,QtCore.SIGNAL( 'currentIdChanged( int )' ),self.on_page_changed)
        self.first_page=IterationGui()
        self.wizard.addPage(self.first_page)
        self.second_page=ChoiceParameters(process_specific,process_with_fom)
        self.connect(self.wizard.button(3), QtCore.SIGNAL('clicked()'), process_with_fom.iteration_run)
        self.wizard.addPage(self.second_page)
        self.wizard.show()

        
    def on_page_changed(self,ide):
        if ide==1:
            ##Check if subjects have selected
            if not self.second_page.list_subjects_selected:
                self.second_page.list_subjects_selected=self.first_page.list_subjects_selected[:]
                self.second_page.go()
            elif self.second_page.list_subjects_selected == self.first_page.list_subjects_selected:
                print 'NO SUBJECTS ADD'
        
            else:
                self.add_element(self.first_page.list_subjects_selected,self.second_page.list_subjects_selected)
                self.del_element(self.first_page.list_subjects_selected,self.second_page.list_subjects_selected)
                self.second_page.list_subjects_selected=self.first_page.list_subjects_selected[:]
        
        
        
    def add_element(self,new_list,prec_list):
        list_add_element=[x for x in new_list if x not in prec_list]
        if list_add_element:
            self.second_page.add_element_on_table(list_add_element)
           

    def del_element(self,new_list,prec_list):
        list_del_element=[x for x in prec_list if x not in new_list]
        if list_del_element:
            for ele in list_del_element:
                self.second_page.del_element_on_table(ele)
    
        
    
    def on_display_bdd(self):
        print 'on display bdd'
        import morphologistSimp
        process_specific = self.get_object_process()
        self.display_bdd=DisplayBDD(process_specific)
        self.display_bdd.open()
        

    def get_object_process(self):
        """This will be automatic"""
        print 'get_object_process:', type(Study.get_instance().process)
        print 'process:', Study.get_instance().process
        return get_process_instance(str(Study.get_instance().process))

        #if Study.get_instance().process=='morphologist.process.morphologist_simplified.SimplifiedMorphologist':
            #import morphologist.process.morphologist_simplified
            #obj = morphologist.process.morphologist_simplified.SimplifiedMorphologist()
            #print 'process:', obj
            #return obj


