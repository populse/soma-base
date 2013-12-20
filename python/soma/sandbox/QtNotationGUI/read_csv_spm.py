# -*- coding: utf-8 -*-
from read_csv import Data
import csv
import sys
import os

class DataSPM(Data):
    def __init__(self):
        #super(DataSPM, self).__init__()
        Data.__init__(self)
        self.data_filename="data_spm.csv"
        self.marks_overflow_white=[]
        self.marks_border_grey_white=[]
        self.marks_overflow_grey_meninges_sinus=[]
        self.marks_border_lcr_grey=[]
        self.marks_overflow_lcr_meninges_sinus=[]
        self.marks_area_lcr_unsegmented=[]
        

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
                        self.marks_overflow_white.append(row[1])
                        self.marks_border_grey_white.append(row[2])
                        self.marks_overflow_grey_meninges_sinus.append(row[3])
                        self.marks_border_lcr_grey.append(row[4])
                        self.marks_overflow_lcr_meninges_sinus.append(row[5])
                        self.marks_area_lcr_unsegmented.append(row[6])
                        self.marks.append(row[7])   
                        self.comments.append(row[8])
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
        file_data=os.path.join(dirname,self.data_filename)
        print 'SAVE'
        if file_data is not None:
            for i in range (0, len(self.filenames)):
                if self.filenames[i] not in images_directory:  
                    print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                    #sys.exit()    
            
            with open(file_data, 'wb') as csvfile:
                mywriter = csv.writer(csvfile,delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                #write the header
                mywriter.writerow(["Filename","Débordements du blanc","Frontière gris/blanc","Découpage du gris dans méninges/sinus","Frontière LCR/gris","Débordements du LCR dans méninges/sinus","Zones de LCR non semgnetées","Note globale","Commentaires"])
                for i in range (0, len(self.filenames)):
                    if self.filenames[i] in images_directory:  
                        try:
                            #mywriter.writerow([ self.filenames[i].encode("utf-8"), self.marks[i],  self.comments[i].encode("utf-8")])
                            mywriter.writerow([unicode(self.filenames[i]),unicode(self.marks_overflow_white[i]),unicode(self.marks_border_grey_white[i]),unicode(self.marks_overflow_grey_meninges_sinus[i]),unicode(self.marks_border_lcr_grey[i]),unicode(self.marks_overflow_lcr_meninges_sinus[i]),unicode(self.marks_area_lcr_unsegmented[i]),unicode(self.marks[i]),unicode(self.comments[i])])
                        except UnicodeDecodeError: 
                            mywriter.writerow([self.filenames[i],self.marks_overflow_white[i],self.marks_border_grey_white[i],self.marks_overflow_grey_meninges_sinus[i],self.marks_border_lcr_grey[i],self.marks_overflow_lcr_meninges_sinus[i],self.marks_area_lcr_unsegmented[i],self.marks[i],self.comments[i]])
                    else:
                        print 'ERROR DATA.CSV CONTAINS FALSE DATA---->%s'%self.filenames[i]
                        #sys.exit()     
                        
                            
     
        
    def get_marks_overflow_white(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_overflow_white[i])
        return ''   
        
    def get_marks_border_grey_white(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_border_grey_white[i])
        return ''  
        
    def get_marks_overflow_grey_meninges_sinus(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_overflow_grey_meninges_sinus[i])
        return ''   
        
    def get_marks_border_lcr_grey(self,filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_border_lcr_grey[i])
        return ''
        
    def get_marks_overflow_lcr_meninges_sinus(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_overflow_lcr_meninges_sinus[i])
        return ''   
    
    def get_marks_area_lcr_unsegmented(self, filename):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                return int(self.marks_area_lcr_unsegmented[i])
        return ''   
            
     
               
    def set_marks_overflow_white(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_overflow_white[i] = note
                return 1
        return 0    
        
        
    def set_marks_border_grey_white(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_border_grey_white[i] = note
                return 1
        return 0    
        
      
    def set_marks_overflow_grey_meninges_sinus(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_overflow_grey_meninges_sinus[i] = note
                return 1
        return 0    
                
     
    def set_marks_border_lcr_grey(self, filename,note):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_border_lcr_grey[i] = note
                return 1
        return 0    
    
    
    def set_marks_overflow_lcr_meninges_sinus(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_overflow_lcr_meninges_sinus[i] = comment
                return 1
        return 0
        
        
    def set_marks_area_lcr_unsegmented(self, filename, comment):
        for i in range (0, len(self.filenames)):
            if(self.filenames[i] == filename):
                self.marks_area_lcr_unsegmented[i] = comment
                return 1
        return 0    
        
   
              
        
    def add_filename(self, filename):
        self.filenames.append(filename)
        self.marks_overflow_white.append('0')
        self.marks_border_grey_white.append('0')
        self.marks_overflow_grey_meninges_sinus.append('0')
        self.marks_border_lcr_grey.append('0')
        self.marks_overflow_lcr_meninges_sinus.append('0')
        self.marks_area_lcr_unsegmented.append('0')
        self.marks.append('4')
        self.comments.append('')    
        
    
