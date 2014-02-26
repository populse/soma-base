#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement
import csv
import sys
import os


class Data:
    #-----------
    # Data model
    #-----------
    def __init__(self):
        self.data_filename="data_default.csv"
        self.filenames = []
        self.marks = []
        self.comments = []

           
    #-------------------------
    # LOAD
    #-------------------------
    def load(self,dirname):
        file_data=os.path.join(dirname,self.data_filename)
        try:
            with open(file_data, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                nb_row=0
                for row in myreader:
                    #Just have to check if filename because not the same name of data.csv    
                    if row[0]=="Filename":
                        #already the header
                        pass
                    else:        
                        self.filenames.append(row[0])                      
                        self.marks.append(row[1])   
                        self.comments.append(row[2])
                    nb_row=nb_row+1               
                        
        except IOError:
            pass
            
        except IndexError:
            print 'SOMETHING WRONG (MISS COLOUMN) WITH DATA.CSV IN THIS ROW %s'%row
            print 'PLS DELETE THE ROW IN THE DATA.CSV OR PUT THE ROW IN THE RULES'
            return 0
            #sys.exit()  
    #-------------------------
    # SAVE
    #-------------------------
    def save(self,dirname,images_directory):
        print 'SAVE'
        file_data=os.path.join(dirname,self.data_filename)
        if file_data is not None:
            for i in range (0, len(self.filenames)):
                if self.filenames[i] not in images_directory:  
                    print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                    #sys.exit()    
            
            with open(file_data, 'wb') as csvfile:
                mywriter = csv.writer(csvfile,delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                #write the header
                mywriter.writerow(["Filename","Global grade","Comment"])
                for i in range (0, len(self.filenames)):
                    if self.filenames[i] in images_directory:  
                        try:
                            #mywriter.writerow([ self.filenames[i].encode("utf-8"), self.marks[i],  self.comments[i].encode("utf-8")])
                            mywriter.writerow([unicode(self.filenames[i]),unicode(self.marks[i]),unicode(self.comments[i])])
                        except UnicodeDecodeError: 
                            mywriter.writerow([self.filenames[i],self.marks[i],self.comments[i]])
                    else:
                        print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                        #sys.exit()       
                    

  
    def get_simple_note(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.marks[i]
        return ''
     
     
        
    
    def get_comment(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.comments[i]
        return ''
        
   
 
    def set_simple_note(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks[i] = note
                return 1
        return 0
        
                

    def set_comment(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.comments[i] = comment
                return 1
        return 0
          
    
    
    def add_filename(self, filename):
        print 'add filename'
        self.filenames.append(filename)
        self.marks.append('4')
        self.comments.append('')
        
        
    # Renvoie 1 si le fichier est déjà présent dans le CSV, 0 sinon.
    def is_recorded(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return 1
        return 0
