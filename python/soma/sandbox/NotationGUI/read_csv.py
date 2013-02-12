#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin

import csv

class Data:
    #-----------
    # Data model
    #-----------
    def __init__(self):
        self.filenames = []
        self.marks = []
        self.comments = []
        #self.DATA_FILE_NAME = "data.csv"
        
        
       
    #-------------------------
    # LOAD
    #-------------------------
    def load(self,data_file_name):
        try:
            with open(data_file_name, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                for row in myreader:
                    self.filenames.append(row[0])
                    self.marks.append(row[1])
                    self.comments.append(row[2])
        except IOError:
            pass

    #-------------------------
    # SAVE
    #-------------------------
    def save(self,data_file_name):
        if data_file_name is not None:
            with open(data_file_name, 'wb',) as csvfile:
                mywriter = csv.writer(csvfile,delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for i in range (0, len(self.filenames)):               
                    mywriter.writerow([ unicode(self.filenames[i]).encode("utf-8"), self.marks[i],  unicode(self.comments[i]).encode("utf-8")])
    
    
  
    def get_note(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks[i])
        return ''
    
    def get_comment(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.comments[i]
        return ''
    
    def set_note(self, filename, note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks[i] = note
                print self.marks[i]
                return 1
        return 0
    
    def set_comment(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.comments[i] = comment
                return 1
        return 0
    
    def add_filename(self, filename):
        self.filenames.append(filename);
        self.marks.append('0');
        self.comments.append('None');
        
    # Renvoie 1 si le fichier est déjà présent dans le CSV, 0 sinon.
    def is_recorded(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return 1
        return 0
