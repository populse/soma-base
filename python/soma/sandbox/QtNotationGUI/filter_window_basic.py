from PyQt4 import QtGui
from PyQt4 import QtCore
import csv
import re
import glob
import os

class FilterBasic(QtGui.QDialog):
    def __init__(self,dirname,data_file_name):
        super(FilterBasic, self).__init__()
        #Dirname
        self.dirname_snap = dirname
        #Filename
        self.data_file_name = data_file_name
        #All path snapshot 
        self.path_data_file_name = os.path.join(self.dirname_snap,self.data_file_name)
        #To know which .csv chose
        self.get_type_snapshot()
        #Hboxs
        self.vbox = QtGui.QVBoxLayout()    
        self.hbox_csv = QtGui.QHBoxLayout()
        self.hbox_filter = QtGui.QHBoxLayout()
        self.hbox_filter.setAlignment(QtCore.Qt.AlignLeft)
        self.hbox_filter.setAlignment(QtCore.Qt.AlignLeft)
        self.choice_sign = QtGui.QComboBox()
        self.choice_sign.addItems(['<','<=','=','>=','>'])
        self.choice_sign.setFixedSize(60,30)
        self.choice_number = QtGui.QComboBox()
        self.choice_number.addItems(['0','1','2','3','4','5'])
        self.choice_number.setFixedSize(60,30)
        self.label_csv = QtGui.QLabel('Current csv : '+self.path_data_file_name)
        self.button_change_csv = QtGui.QPushButton('Get other csv')
        self.hbox_csv.addWidget(self.label_csv)
        self.hbox_csv.addWidget(self.button_change_csv)
        self.hbox_filter.addWidget(self.choice_sign)
        self.hbox_filter.addWidget(self.choice_number)
        self.text_res = QtGui.QLabel('Results filter : ')
        #Add hboxs in vbox
        self.vbox.addLayout(self.hbox_csv)
        self.vbox.addLayout(self.hbox_filter)
        self.vbox.addWidget(self.text_res)
        self.button_save_quit = QtGui.QPushButton('Save&Quit')
        self.button_save_quit.setFixedSize(80,30)
        self.vbox.addWidget(self.button_save_quit)
        self.vbox.setAlignment(QtCore.Qt.AlignLeft)  
        self.setLayout(self.vbox)
        #Signal widgets
        self.signals()
    
    def get_type_snapshot(self):
        ''' With snapshot name get the type of snapshot to chose the corresponding .csv '''
        if 'GW' in self.data_file_name:
            self.type_snap='GW'
        elif 'spm' in self.data_file_name:  
            self.type_snap='spm'
        else:
            self.type_snap='default'  
        
     
    def signals(self):    
       ''' Signals widgets '''
       self.choice_sign.currentIndexChanged.connect(self.filter_process)   
       self.choice_number.currentIndexChanged.connect(self.filter_process)   
       self.button_change_csv.clicked.connect(self.change_csv)
       self.button_save_quit.clicked.connect(self.save_quit)
        
  
    def change_csv(self):
        ''' If user change the .csv to filter'''
        other_csv = str(QtGui.QFileDialog.getOpenFileName(self, 'Select other csv',self.dirname_snap))
        self.path_data_file_name = other_csv
        self.dirname_snap = os.path.dirname(other_csv)
        self.data_file_name = os.path.basename(other_csv)
        self.label_csv.setText('Current csv : '+self.path_data_file_name)
        #The .csv change so update filter
        self.filter_process()

  
    def get_files_and_marks(self): 
        ''' Get filenames and marks of the .csv '''
        self.filenames = []
        self.marks = []  
        try:
            with open(self.path_data_file_name, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                nb_row = 0
                for row in myreader:
                    #if first row = header
                    if nb_row == 0:
                        pass
                    else:    
                        self.filenames.append(row[0])
                        self.marks.append(row[1])
                    nb_row = nb_row+1    
        except IOError:
            print 'IOERROR'
            pass

      
    def filter_process(self):
        ''' Function call if marks or sign changed '''
        self.list_subject = ''
        self.nb_subject = 0
        #Get files and marks of .csv
        self.get_files_and_marks()
        index = 0
        #Loop on snapshot in .csv
        for file_name in self.filenames:
            sign = self.choice_sign.currentText()
            self.number = self.choice_number.currentIndex()
            #If comparison return 1 -> the current snapshot enter in filter
            if self.comparison(sign,self.number,int(self.marks[index])) == 1 :
                self.list_subject = self.list_subject+os.path.join(self.dirname_snap,file_name)+'\n' 
                self.nb_subject = self.nb_subject+1      
            index = index + 1 
        self.text_res.setText('Results filter : '+str(self.nb_subject))
    
    def write_results(self):
        ''' Write results on fitler in  .txt'''
        with open(os.path.join(self.dirname_snap,'results_filter_basic_%s_%s_%d.txt'%(self.type_snap,self.sign_filter_str,self.number)), 'w') as f:
            f.write(self.list_subject)       


    def comparison(self,sign,number,number_file):
        if sign == '<':
            self.sign_filter_str = 'inf'
            if number_file < number:
                return 1
            else:
                return 0
        elif sign == '<=':
            self.sign_filter_str = 'inf_equal'
            if number_file <= number:
                return 1
            else:
                return 0
                
        elif sign == '=':
            self.sign_filter_str = 'equal'
            if number_file == number:
                return 1
            else:
                return 0     
                  
        elif sign == '>=':
            self.sign_filter_str = 'sup_equal'
            if number_file >= number:
                return 1
            else:
                return 0    
            
        elif sign == '>':
            self.sign_filter_str = 'sup'
            if number_file > number:
                return 1
            else:
                return 0               
        

    def save_quit(self):
        ''' User quit the filter window -> save results and close window '''
        print 'SAVE AND QUIT FILTER'
        self.write_results()
        self.close()
