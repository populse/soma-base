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
        #self.dirname_snap='/volatile/bouin/source/soma/soma-base/trunk/python/soma/sandbox/NotationGUI'
        self.list_subject=''
          
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
        
        
        self.choice_sign=wx.Choice(self.panel,-1,size=(60, 30),choices=['<','<=','=','>=','>']) 
        self.hbox3.Add(self.choice_sign)
        self.hbox3.AddSpacer(20)
        self.choice_number=wx.Choice(self.panel,-1,size=(60, 30),choices=['0','1','2','3','4','5'])
        self.hbox3.Add(self.choice_number) 
        
        
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
        #self.Bind(wx.EVT_BUTTON, self.opendir,self.button_dir)
        #self.Bind(wx.EVT_BUTTON, self.opendir,self.button_dir)
        


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
            dlg.Destroy()
        
        
    def filter_process(self):
        self.filenames = []
        self.marks = []
        print 'directory',self.dirname_snap
        data_file_name = os.path.join(self.dirname_snap,'data.csv')
        try:
            with open(data_file_name, 'rb') as csvfile:
                myreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                for row in myreader:
                    self.filenames.append(row[0])
                    self.marks.append(row[1])
        except IOError:
            print 'IOERROR'
            pass

        index=0
        print self.filenames[0]
        for file in self.filenames:
            if 'split' in file:
                sign=str(self.choice_sign.GetString(self.choice_sign.GetCurrentSelection()))
                if self.comparison(sign,self.choice_number.GetCurrentSelection(),int(self.marks[index]))==1:
                    #self.list_subject.append(file)
                    self.raw_data(file)
            index=index+1    
        #print self.list_subject
        
        
        
        
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
        
        path=os.path.join(self.dirname_bdd,nom_center,subject,'t1mri','M000',subject+'*.nii.gz')       
        self.list_subject=self.list_subject+str(glob.glob(path))[1:-1]+' '
        with open('results_filter', 'wb') as f:
            f.write(self.list_subject)
    
                
    def comparison(self,sign,number,number_file):
 
        if sign == '<':
            print 'hoooo'
            if number_file < number:
                print 'return 1'
                return 1
            else:
                return 0
        elif sign == '<=':
            if number_file <= number:
                return 1
            else:
                return 0
                
        elif sign == '=':
            if number_file == number:
                return 1
            else:
                return 0     
                  
        elif sign == '>=':
            if number_file >= number:
                return 1
            else:
                return 0    
            
        elif sign == '>':
            if number_file > number:
                return 1
            else:
                return 0               
        
                 
        
