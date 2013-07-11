from PyQt4 import QtGui
from PyQt4 import QtCore
from create_bdd import CreateBDD
import csv
import re
import glob
import os

class MyFilter(QtGui.QDialog):
    def __init__(self,dirname):
        super(MyFilter, self).__init__()
        self.dirname_bdd='/neurospin/cati/Memento/MEMENTO_fevrier2013/geoCorrected'
        self.dirname_snap=dirname
        self.list_subject=''
        #Files and marks in the data.csv  
        self.filenames = []
        self.marks = []  
        self.nb_subject=0
        #To write in the .txt
        self.sign_filter_str=''
        self.number=0
        self.word_to_find=''
        
        self.hbox = QtGui.QHBoxLayout()
        self.hbox2=QtGui.QHBoxLayout()
        self.vbox = QtGui.QVBoxLayout()    
          
        self.display_dirnam=QtGui.QLabel(self.dirname_snap)
        self.choice_type=QtGui.QComboBox()
        self.choice_type.addItems(['split','GW','hemi'])
        self.choice_sign=QtGui.QComboBox()
        self.choice_sign.addItems(['<','<=','=','>=','>'])
        self.choice_number=QtGui.QComboBox()
        self.choice_number.addItems(['0','1','2','3','4','5'])
        self.hbox.addWidget(self.display_dirnam)
        self.hbox.addWidget(self.choice_type)
        self.hbox.addWidget(self.choice_sign)
        self.hbox.addWidget(self.choice_number)
        self.hbox2.addWidget(QtGui.QLabel('    Results filter'))
        self.text_res=QtGui.QLabel()
        self.hbox2.addWidget(self.text_res)
        self.vbox.addLayout(self.hbox)
        self.vbox.addLayout(self.hbox2)
        self.button_save_quit=QtGui.QPushButton('Save&Quit')
        self.vbox.addWidget(self.button_save_quit)
        self.vbox.setAlignment(QtCore.Qt.AlignLeft)  
        self.setLayout(self.vbox)
        self.signals()
        
        
     
    def signals(self):    
       self.choice_type.currentIndexChanged.connect(self.filter_process)   
       self.choice_sign.currentIndexChanged.connect(self.filter_process)   
       self.choice_number.currentIndexChanged.connect(self.filter_process)   
       self.button_save_quit.clicked.connect(self.save_quit)
        
  
    def get_files_and_marks(self): 
        print 'IN GET FILE'
        print self.dirname_snap 
        data_file_name = os.path.join(self.dirname_snap,'data.csv')
        print data_file_name
        try:
            with open(data_file_name, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                for row in myreader:
                    self.filenames.append(row[0])
                    self.marks.append(row[1])
        except IOError:
            print 'IOERROR'
            pass

      
    def filter_process(self):
        print 'in filtre_process'
        self.bdd=CreateBDD.get_instance()
        print self.dirname_snap
        self.list_subject=''
        self.nb_subject=0
        self.word_in_the_file=str(self.choice_type.currentText())
        print 'type file',self.word_in_the_file
        if not self.filenames:
            print 'OPEN CSV'
            #if data.csv has not been opened
            self.get_files_and_marks()
        compteur=0 
        index=0
        for file in self.filenames:
            if self.word_in_the_file in file:
                compteur=compteur+1
                sign=self.choice_sign.currentText()
                self.number=self.choice_number.currentIndex()
                if len(self.marks[index])>2:
                    if self.comparison(sign,self.number,int(self.marks[index].split(' ')[0]))==1:
                        self.raw_data(file)
                else:
                    if self.comparison(sign,self.number,int(self.marks[index]))==1:
                        self.raw_data(file)
                            
            index=index+1 
        self.text_res.setText(str(self.nb_subject))
    
    def write_results(self):
        with open(os.path.join(self.dirname_snap,'results_filter_%s_%s_%d'%(self.word_in_the_file,self.sign_filter_str,self.number)), 'w') as f:
            f.write(self.list_subject)       
        

    def raw_data(self,file):  
        filename=file.split('.')[0]
        expresion=r"([0-9]{7})([A-Za-z]{4})"
        m=re.search(expresion, filename)

        if m is not None:
            subject=m.group(0)
            subject=subject[0:7]+'_'+subject[7:11]
            image_t1=self.bdd.T1_images(subject)
            if not image_t1:
                print 'NO IMAGE T1 FIND'
            elif len(image_t1)>1:
                print 'WARNING MORE THAN ON RAW DATA HAVE BEEN FOUND BY DEFAULT IT S   %s'%image_t1[0] 
                self.list_subject=self.list_subject+"'"+image_t1[0]+"'"+' '  
                self.nb_subject=self.nb_subject+1
            else:
                self.list_subject=self.list_subject+"'"+image_t1[0]+"'"+' '  
                self.nb_subject=self.nb_subject+1


    def comparison(self,sign,number,number_file):
        if sign == '<':
            self.sign_filter_str='inf'
            if number_file < number:
                return 1
            else:
                return 0
        elif sign == '<=':
            self.sign_filter_str='inf_equal'
            if number_file <= number:
                return 1
            else:
                return 0
                
        elif sign == '=':
            self.sign_filter_str='equal'
            if number_file == number:
                return 1
            else:
                return 0     
                  
        elif sign == '>=':
            self.sign_filter_str='sup_equal'
            if number_file >= number:
                return 1
            else:
                return 0    
            
        elif sign == '>':
            self.sign_filter_str='sup'
            if number_file > number:
                return 1
            else:
                return 0               
        

    def save_quit(self):
        print 'SAVE AND QUIT FILTER'
        self.write_results()
        self.close()
