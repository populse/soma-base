#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin
from __future__ import with_statement
import csv
import sys


class Data:
    #-----------
    # Data model
    #-----------
    def __init__(self):
        self.filenames = []
        self.marks = []
        self.comments = []
        self.marks_debordement= []
        self.marks_pial= []
        self.marks_cutting= []
        self.marks_brain_miss= []
        self.locality= []
        
        
        #self.DATA_FILE_NAME = "data.csv"
           
    #-------------------------
    # LOAD
    #-------------------------
    def load(self,data_file_name):
        try:
            with open(data_file_name, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                nb_row=0
                for row in myreader:
                    #Check compatibility with between old and new .csv
                    if len(row) != 8:
                        print 'WARNING THIS IS A OLD DATA.CSV, you have %d col and the data.csv must countains 8 columns'%(len(row))
                        return 0
                    elif nb_row==0 and row[7] != 'Comment':
                        print" WARNING THIS IS A OLD DATA.CSV, the last column is not 'Comment' "
                        return 0  
                    elif row[0]=="Filename":
                        #already the header
                        pass
                    else:        
                        self.filenames.append(row[0])                      
                        self.marks_debordement.append(row[1])
                        self.marks_pial.append(row[2])
                        self.marks_cutting.append(row[3])
                        self.marks_brain_miss.append(row[4])
                        self.locality.append(row[5])
                        self.marks.append(row[6])   
                        self.comments.append(row[7])
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
    def save(self,data_file_name,images_directory):
        print 'SAVE'
        if data_file_name is not None:
            for i in range (0, len(self.filenames)):
                if self.filenames[i] not in images_directory:  
                    print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                    #sys.exit()    
            
            with open(data_file_name, 'wb') as csvfile:
                mywriter = csv.writer(csvfile,delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                #write the header
                mywriter.writerow(["Filename","Debordements meninges/sinus","Limite surface pial","Decoupage HD, HG et cervelet","Bouts de cerveau manquant","Localite Bouts de cerveau manquant","Global grade","Comment"])
                for i in range (0, len(self.filenames)):
                    if self.filenames[i] in images_directory:  
                        try:
                            #mywriter.writerow([ self.filenames[i].encode("utf-8"), self.marks[i],  self.comments[i].encode("utf-8")])
                            mywriter.writerow([unicode(self.filenames[i]),unicode(self.marks_debordement[i]),unicode(self.marks_pial[i]),unicode(self.marks_cutting[i]),unicode(self.marks_brain_miss[i]),unicode(self.locality[i]),unicode(self.marks[i]),unicode(self.comments[i])])
                        except UnicodeDecodeError: 
                            mywriter.writerow([self.filenames[i],self.marks_debordement[i],self.marks_pial[i],self.marks_cutting[i],self.marks_brain_miss[i],self.locality[i]],self.marks[i],self.comments[i])
                    else:
                        print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                        #sys.exit()       
                    

  
    def get_simple_note(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.marks[i]
        return ''
     
     
     
     
    #def get_double_note(self,filename,bool_brain):
        #for i in range (0, len(self.filenames)):
            #if (self.filenames[i] == filename):    
                #if bool_brain is True:
                    #if len(self.marks[i])>1:
                        #return int(self.marks[i].split(' ')[1])
                    ##To be compatible with old version  
                    #else:
                        #self.marks[i] = self.marks[i]+' 0'
                        #return int(self.marks[i].split(' ')[1])
                #else:
                    #if len(self.marks[i])>1:
                        #return int(self.marks[i].split(' ')[0])
                    ##To be compatible with old version  
                    #else:
                        #self.marks[i] = self.marks[i]+' 0'
                        #return int(self.marks[i].split(' ')[0])
        #return ''
            

        
    
    def get_comment(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.comments[i]
        return ''
        
    
    def get_marks_debordement(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_debordement[i])
        return ''
        
    def get_marks_pial(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_pial[i])
        return ''   
        
   
    def get_marks_cutting(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_cutting[i])
        return ''   
        
    def get_marks_brain_miss(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_brain_miss[i])
        return ''  
        
    def get_locality(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return self.locality[i]
        return ''   
         
           

#self.locality.append(row[7])
        
        
 
    def set_simple_note(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks[i] = note
                return 1
        return 0
        
        
    #def set_double_note(self,filename,note,note_brain):
        #for i in range (0, len(self.filenames)):
            #if(self.filenames[i] == filename):          
                #self.marks[i]=str(note)+' '+str(note_brain)
                #print self.marks[i]
                #return 1
        #return 0             
                

    def set_comment(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.comments[i] = comment
                return 1
        return 0
          
        
    def set_marks_debordement(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_debordement[i] = note
                return 1
        return 0    
        
        
    def set_marks_pial(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_pial[i] = note
                return 1
        return 0    
        
      
    def set_marks_cutting(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_cutting[i] = note
                return 1
        return 0    
                
     
    def set_marks_brain_miss(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_brain_miss[i] = note
                return 1
        return 0    
    
    
    def set_locality(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.locality[i] = comment
                return 1
        return 0
    
    
            
    
    def add_filename(self, filename):
        print 'add filename'
        self.filenames.append(filename)
        self.marks_debordement.append('0')
        self.marks_pial.append('0')
        self.marks_cutting.append('0')
        self.marks_brain_miss.append('0')
        self.locality.append('')
        self.marks.append('0')
        self.comments.append('')
        
        
    # Renvoie 1 si le fichier est déjà présent dans le CSV, 0 sinon.
    def is_recorded(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return 1
        return 0
