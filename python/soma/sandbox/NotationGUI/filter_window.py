#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin
from __future__ import with_statement
import wx
import csv
import re
import glob
import os
class MyDialog(wx.Dialog):
        
    
    def __init__(self, parent, id, title,dirname):
        wx.Dialog.__init__(self, parent, id, title,size=(500,350))
        #Windows       
        self.panel = wx.Panel(self)
                
        self.dirname_bdd='/neurospin/cati/Memento/MEMENTO_fevrier2013/geoCorrected'
        self.dirname_snap=dirname
        print self.dirname_snap
        #self.dirname_snap='/volatile/bouin/source/soma/soma-base/trunk/python/soma/sandbox/NotationGUI'
        self.list_subject=''
        
        #Files and marks in the data.csv  
        self.filenames = []
        self.marks = []  
        self.nb_subject=0
        
        #To write in the .txt
        self.sign_filter_str=''
        self.number=0
        self.word_to_find=''
          
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3= wx.BoxSizer(wx.HORIZONTAL)
        
        self.btnCancel = wx.Button(self.panel, wx.ID_CANCEL)  
        self.btnOk = wx.Button(self.panel, wx.ID_OK)      
        
        self.btnSizer = wx.StdDialogButtonSizer()
        self.btnSizer.AddButton(self.btnCancel)
        self.btnSizer.AddButton(self.btnOk)
        self.btnSizer.Realize()

        self.button_dir_bdd = wx.Button(self.panel, -1, 'Choose BDD Directory',size=(200, -1))
        self.hbox.Add(self.button_dir_bdd)
                
        self.bdd=wx.TextCtrl(self.panel, value=self.dirname_bdd, size=(300, 40),style=wx.TE_MULTILINE,)
        self.hbox.Add(self.bdd)
        
        
        self.button_dir_snap = wx.Button(self.panel, -1, 'Choose SNAPSHOTS Directory',size=(200, -1))
        self.hbox2.Add(self.button_dir_snap)
                
        self.snap=wx.TextCtrl(self.panel, value=self.dirname_snap,size=(300, 40),style=wx.TE_MULTILINE,)
        self.hbox2.Add(self.snap)
        
        self.choice_type=wx.Choice(self.panel,-1,size=(80, 30),choices=['split','GW','hemi']) 
        self.hbox3.Add(self.choice_type)
        self.hbox3.AddSpacer(20)       
        self.choice_sign=wx.Choice(self.panel,-1,size=(60, 30),choices=['<','<=','=','>=','>']) 
        self.hbox3.Add(self.choice_sign)
        self.hbox3.AddSpacer(20)
        self.choice_number=wx.Choice(self.panel,-1,size=(60, 30),choices=['0','1','2','3','4','5'])
        self.hbox3.Add(self.choice_number) 
        self.hbox3.AddSpacer(20)
        self.textres=re=wx.StaticText(self.panel,-1,'Results filter', style= wx.EXPAND|wx.ALIGN_CENTER)
        self.hbox3.Add(self.textres) 
        self.hbox3.AddSpacer(20)
        self.res=re=wx.StaticText(self.panel,-1,'', style= wx.EXPAND|wx.ALIGN_CENTER)
        self.hbox3.Add(self.res) 
        self.vbox.Add(self.hbox)
        self.vbox.AddSpacer(20)
        self.vbox.Add(self.hbox2)
        self.vbox.AddSpacer(20)
        self.vbox.Add(self.hbox3)
        self.vbox.AddSpacer(40)
        self.vbox.Add(self.btnSizer)
        
        self.panel.SetSizerAndFit(self.vbox)

        self.Bind(wx.EVT_BUTTON, self.opendir_bdd,self.button_dir_bdd)
        self.Bind(wx.EVT_BUTTON, self.opendir_snap,self.button_dir_snap)
        self.Bind(wx.EVT_CHOICE,self.filter_event,self.choice_sign)
        self.Bind(wx.EVT_CHOICE,self.filter_event,self.choice_number)
        self.Bind(wx.EVT_CHOICE,self.filter_event,self.choice_type)


    def opendir_bdd(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname_bdd = dlg.GetPath()
            self.bdd.SetValue(self.dirname_bdd)
            dlg.Destroy()
        
    def opendir_snap(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname_snap = dlg.GetPath()
            self.snap.SetValue(self.dirname_snap)
            self.get_files_and_marks()
            dlg.Destroy()
            
    def filter_event(self,event):
        self.filter_process()
    

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
        self.list_subject=''
        self.nb_subject=0
        self.word_in_the_file=self.choice_type.GetString(self.choice_type.GetCurrentSelection())
        if not self.filenames:
            print 'OPEN CSV'
            #if data.csv has not been opened
            self.get_files_and_marks()
        compteur=0 
        index=0
        for file in self.filenames:
            if self.word_in_the_file in file:
                compteur=compteur+1
                sign=str(self.choice_sign.GetString(self.choice_sign.GetCurrentSelection()))
                self.number=self.choice_number.GetCurrentSelection()
                
                if self.comparison(sign,self.number,int(self.marks[index]))==1:
                    self.raw_data(file)
            index=index+1 
  
        print self.list_subject
        print 'nb_subject',self.nb_subject
        self.res.SetLabel(str(self.nb_subject))
    
    def write_results(self):
        with open(os.path.join(self.dirname_snap,'results_filter_%s_%s_%d'%(self.word_in_the_file,self.sign_filter_str,self.number)), 'w') as f:
            f.write(self.list_subject)       
        

    def raw_data(self,file):     
        filename=file.split('.')[0]
        expresion=r"([0-9]{7})([A-Za-z]{4})"
        m=re.search(expresion, filename)
        if m is not None:
            subject=m.group(0)
            filespliter=filename.split('_')
            for i in range(0,len(filespliter)):
                if filespliter[i]==subject:
                    index=i
                    break                     
            nom_center=filespliter[index-1]
            if nom_center.isdigit():
                nom_center=filespliter[index-2]+'_'+filespliter[index-1]
        
        path=glob.glob(os.path.join(self.dirname_bdd,'%s' % nom_center,'%s' %subject,'*','*','%s.nii.gz'%subject))
        if len(path)==0:
            print 'ERROR NO RAW DATA FIND'
            return           
        else:
            if len(path)>1:
                print 'WARNING MORE THAN ON RAW DATA HAVE BEEN FOUND BY DEFAULT IT S %s'%path[0]
            self.list_subject=self.list_subject+"'"+path[0]+"'"+' '   
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
        
                 
        
