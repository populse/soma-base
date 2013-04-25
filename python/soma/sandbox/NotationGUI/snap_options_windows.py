#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin
import wx
import os

class Dialog_snap(wx.Dialog):
  
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title,size=(800,350))
        #Windows       
        self.panel = wx.Panel(self)
        
        self.number_widget=0
                
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_sub = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_cent = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_mod = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_acqu = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_bdd = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_coh = wx.BoxSizer(wx.HORIZONTAL)
        
        #self.gs=wx.GridSizer(2, 2, 3, 3)
        #self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.choice_corhort=wx.Choice(self.panel,-1,size=(150, 30),choices=['Memento','Add']) 
        self.enter_cohort=wx.TextCtrl(self.panel,-1, '')
        self.hbox_coh.Add(self.choice_corhort)
        self.hbox_coh.Add(self.enter_cohort)
        self.hbox_coh.Show(self.enter_cohort,False,True)
        self.hbox_coh.Layout()


        self.button_file_snap = wx.Button(self.panel, -1, 'Choose SNAPSHOTS file',size=(180, -1))
        #self.hbox2.Add(self.button_file_snap)
        self.snap_file=re=wx.StaticText(self.panel,-1, style= wx.EXPAND|wx.ALIGN_CENTER)
        
        self.read_text_subject=wx.TextCtrl(self.panel,-1, 'Subject',style=wx.TE_READONLY)
        self.hbox_sub.Add(self.read_text_subject)
        self.hbox_sub.Show(self.read_text_subject,False,True)
        self.hbox_sub.Layout()
        self.text_subject=wx.TextCtrl(self.panel,-1,'',size=(600,25))
        self.hbox_sub.Add(self.text_subject)
        self.hbox_sub.Show(self.text_subject,False,True)
        self.hbox_sub.Layout()
        self.read_text_center=wx.TextCtrl(self.panel,-1, 'Center',style=wx.TE_READONLY)
        self.hbox_cent.Add(self.read_text_center)
        self.hbox_cent.Show(self.read_text_center,False,True)
        self.hbox_cent.Layout()
        self.text_center=wx.TextCtrl(self.panel,-1,'',size=(600,25))
        self.hbox_cent.Add(self.text_center)
        self.hbox_cent.Show(self.text_center,False,True)
        self.hbox_cent.Layout()
        self.read_text_modality=wx.TextCtrl(self.panel,-1, 'Modality',style=wx.TE_READONLY)
        self.hbox_mod.Add(self.read_text_modality)
        self.hbox_mod.Show(self.read_text_modality,False,True)
        self.hbox_mod.Layout()
        self.text_modality=wx.TextCtrl(self.panel,-1,'t1mri',size=(600,25))
        self.hbox_mod.Add(self.text_modality)
        self.hbox_mod.Show(self.text_modality,False,True)
        self.hbox_mod.Layout()
        self.read_text_acquisition=wx.TextCtrl(self.panel,-1, 'Acquisition',style=wx.TE_READONLY)
        self.hbox_acqu.Add(self.read_text_acquisition)
        self.hbox_acqu.Show(self.read_text_acquisition,False,True)
        self.hbox_acqu.Layout()
        self.text_acquisition=wx.TextCtrl(self.panel,-1,'default_acquisition',size=(600,25))
        self.hbox_acqu.Add(self.text_acquisition)
        self.hbox_acqu.Show(self.text_acquisition,False,True)
        self.hbox_acqu.Layout()
        self.read_text_bdd=wx.TextCtrl(self.panel,-1, 'BDD',style=wx.TE_READONLY)
        self.hbox_bdd.Add(self.read_text_bdd)
        self.hbox_bdd.Show(self.read_text_bdd,False,True)
        self.hbox_bdd.Layout()
        self.text_bdd=wx.TextCtrl(self.panel,-1,'BDD_DIR/<Subject>/<Modality>/<Acquisition>/<Subject>.nii.gz',size=(600,25))
        self.hbox_bdd.Add(self.text_bdd)
        self.hbox_bdd.Show(self.text_bdd,False,True)
        self.hbox_bdd.Layout()
        self.choice_bdd=wx.Choice(self.panel,-1,size=(150, 30),choices=['BrainVISA','FreeSurfer'])      
        self.instruction=wx.StaticText(self.panel,-1,'Please enter the number of the subject and the center corresponding to the snapshot ', style= wx.EXPAND|wx.ALIGN_CENTER)

        self.vbox.Add(self.hbox_coh)
        self.vbox.Add(self.button_file_snap)
        self.vbox.Add(self.snap_file)
        self.vbox.Add(self.hbox)
        self.vbox.Add(self.hbox2)
        self.vbox.Add(self.instruction)
        self.vbox.Show(self.instruction,False,True)
        self.vbox.Add(self.hbox_sub)
        self.vbox.Add(self.hbox_cent)
        self.vbox.AddSpacer(20)
        self.vbox.Add(self.choice_bdd)
        self.vbox.Show(self.choice_bdd,False,True)
        self.vbox.Add(self.hbox_mod)
        self.vbox.Add(self.hbox_acqu)
        self.vbox.Add(self.hbox_bdd)
       
        self.panel.SetSizerAndFit(self.vbox)
        self.Bind(wx.EVT_BUTTON, self.openfile,self.button_file_snap)
        self.Bind(wx.EVT_CHOICE, self.choice_corhort_event,self.choice_corhort) 
        #Voir si quand on appuie sur entree ou non   
        self.Bind(wx.EVT_TEXT,self.enter_cohort_event,self.enter_cohort)   
        
    def openfile(self, event):
       dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.*", wx.OPEN)
       if dlg.ShowModal() == wx.ID_OK:
                # Remove old widget
                if self.number_widget > 0:
                    print self.hbox.GetChildren()
                    #for index in range(self.number_widget): 
                    for index in range(3):
                        print self.hbox.GetChildren()[index]
                        self.hbox.GetChildren()[index].DetachSizer()
                        self.hbox.GetChildren()[index].Destroy()                       
                        #print index              
                        #print self.hbox.Remove(index)  
  
                        #self.hbox.Remove(index) 
                        #print self.hbox2.Remove(index)                 
                        #self.hbox2.Remove(index)
                    print 'END'    
                    print self.hbox.GetChildren()    
                    self.hbox.Layout()
                    #self.hbox2.Layout()
                    #self.number_widget=0
                path = dlg.GetPath()
                snap_name = os.path.basename(path)
                snap_name = snap_name.split('.')[0]
                self.snap_file.SetLabel(snap_name)
                snap_name=snap_name.split('_')
                print snap_name
                print len(snap_name)   
                
                if self.number_widget==0:
                    print 'heyyyyyyy'
                    for i in range(len(snap_name)):
                        self.number_widget=self.number_widget+1
                        print snap_name[i]
                        new_txt = wx.TextCtrl(self.panel, -1, snap_name[i],style=wx.TE_READONLY | wx.EXPAND )
                        self.hbox.Add(new_txt)
                        new_num = wx.TextCtrl(self.panel, -1, str(i),style=wx.TE_READONLY | wx.EXPAND )
                        self.hbox2.Add(new_num)
        
                        self.hbox.Layout()
                        self.hbox2.Layout()
                        self.vbox.Show(self.instruction,True,True)
                        self.vbox.Show(self.read_text_subject,True,True)
                        self.vbox.Show(self.text_subject,True,True)
                        self.vbox.Show(self.read_text_center,True,True)
                        self.vbox.Show(self.text_center,True,True)
                        self.vbox.Show(self.read_text_modality,True,True)
                        self.vbox.Show(self.text_modality,True,True)
                        self.vbox.Show(self.read_text_acquisition,True,True)
                        self.vbox.Show(self.text_acquisition,True,True)
                        self.vbox.Show(self.read_text_bdd,True,True)
                        self.vbox.Show(self.text_bdd,True,True)
                        self.vbox.Show(self.choice_bdd,True,True)
                        self.vbox.Layout()
       dlg.Destroy()
       
       
       
       
    def choice_corhort_event(self,event):
        if self.choice_corhort.GetString(self.choice_corhort.GetCurrentSelection())=='Add':
            self.vbox.Show(self.enter_cohort,True,True)
            self.vbox.Layout()
    
       
    def enter_cohort_event(self,event):
        print 'enter'    
       
       
       
