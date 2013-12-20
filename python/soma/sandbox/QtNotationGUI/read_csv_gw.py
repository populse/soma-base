# -*- coding: utf-8 -*-
from read_csv import Data
import csv
import sys
import os

class DataGW(Data):
    def __init__(self):
        #super(DataGW, self).__init__()
        Data.__init__(self)
        self.data_filename="data_gw.csv"
        self.marks_limit_surface_gw= []
        self.marks_limit_surface_pial= []
        self.marks_overflow_meninges_sinus= []
        self.marks_brain_miss= []
        self.locality= []


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
                        self.marks_limit_surface_gw.append(row[1])
                        self.marks_limit_surface_pial.append(row[2])
                        self.marks_overflow_meninges_sinus.append(row[3])
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
                mywriter.writerow(["Filename","Limite surface gris/blanc","Limite surface pial","Debordements meninges/sinus","Bouts manquants","Localite des bouts manquants","Note globale","Commentaires"])
                for i in range (0, len(self.filenames)):
                    if self.filenames[i] in images_directory:  
                        try:
                            #mywriter.writerow([ self.filenames[i].encode("utf-8"), self.marks[i],  self.comments[i].encode("utf-8")])
                            mywriter.writerow([unicode(self.filenames[i]),unicode(self.marks_limit_surface_gw[i]),unicode(self.marks_limit_surface_pial[i]),unicode(self.marks_overflow_meninges_sinus[i]),unicode(self.marks_brain_miss[i]),unicode(self.locality[i]),unicode(self.marks[i]),unicode(self.comments[i])])
                        except UnicodeDecodeError: 
                            mywriter.writerow([self.filenames[i],self.marks_limit_surface_gw[i],self.marks_limit_surface_pial[i],self.marks_overflow_meninges_sinus[i],self.marks_brain_miss[i],self.locality[i],self.marks[i],self.comments[i]])
                    else:
                        print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                        #sys.exit()     

        
    def get_marks_limit_surface_gw(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_limit_surface_gw[i])
        return ''   
        
    def get_marks_limit_surface_pial(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_limit_surface_pial[i])
        return ''  
        
    def get_marks_overflow_meninges_sinus(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_overflow_meninges_sinus[i])
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
        
               
    def set_marks_limit_surface_gw(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_limit_surface_gw[i] = note
                return 1
        return 0    
        
        
    def set_marks_limit_surface_pial(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_limit_surface_pial[i] = note
                return 1
        return 0    
        
      
    def set_marks_overflow_meninges_sinus(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_overflow_meninges_sinus[i] = note
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
        self.filenames.append(filename)
        self.marks_limit_surface_gw.append('0')
        self.marks_limit_surface_pial.append('0')
        self.marks_overflow_meninges_sinus.append('0')
        self.marks_brain_miss.append('0')
        self.locality.append('')
        self.marks.append('4')
        self.comments.append('')    
        
    
    
