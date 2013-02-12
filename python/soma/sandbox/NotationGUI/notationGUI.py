#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin

from __future__ import division
import wx
import os
import glob
import read_csv
import sys

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        
        # Default directory (change it if you want)
        self.dirname=''
        #/neurospin/cati/CATI_MIRROR/freeshare/Projet_X_050213/snapshots'     

        #border widget picture
        self.border=50
        #Left widget (all except picture)
        self.size_left_widget=100       
        self.data_file_name= None
        self.images=None
        self.indice=None  
        self.image_current=None
        self.data=read_csv.Data()   
        
        #Windows       
        wx.Frame.__init__(self, parent, id, title, (-1, -1), wx.Size(800+self.size_left_widget, 600))
        self.panel = wx.Panel(self, -1,)
  
    
        # Setting up the menu.
        filemenu= wx.Menu()
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open"," Open a file to edit")
        
        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        
        # Main Box 
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        
        #Box for right widgets
        self.box2 = wx.BoxSizer(wx.VERTICAL)
        self.box3= wx.BoxSizer(wx.HORIZONTAL)
        button_next=wx.Button(self.panel, -1, '<',size=(40, -1))
        button_prev=wx.Button(self.panel, -1, '>',size=(40, -1))
        self.box3.Add(button_next, 0)
        self.box3.Add(button_prev, 0)
        self.box2.Add(self.box3)      
        self.box2.Add(wx.StaticText(self.panel, -1, 'Note', (45, 25), style=wx.ALIGN_CENTRE))
        self.choice_note=wx.SpinCtrl(self.panel,-1,size=(60, -1),min=0,max=5)
        self.box2.Add(self.choice_note)
        self.comment=wx.TextCtrl(self.panel, -1,size=(100, 100),style=wx.TE_MULTILINE)
        self.box2.Add(self.comment)     
        self.box.Add(self.box2)
        
        #Widget picture
        screenSizeX, screenSizeY = wx.DisplaySize()        
        bitmap=wx.EmptyBitmap(screenSizeX ,screenSizeY,-1) 
        
        #To have an empty bitmap 
        memory=wx.MemoryDC()
        memory.SelectObject(bitmap)
        
        #Decomment if you want ~grey color background
        #mask=wx.Color(self.GetBackgroundColour()[0],self.GetBackgroundColour()[1],self.GetBackgroundColour()[2])
        #memory.SetBackground(wx.Brush(mask))
        memory.Clear()
        memory.SelectObject(wx.NullBitmap)
        self.picture = wx.StaticBitmap(self.panel, bitmap=bitmap)
        self.box.Add(self.picture, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL | wx.ADJUST_MINSIZE, 10)     
  
        #Display GUI
        self.panel.SetSizerAndFit(self.box)
        self.Centre()
        self.Show()
        
        # Events
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_BUTTON,self.NextPic, button_next)
        self.Bind(wx.EVT_BUTTON,self.PrevPic, button_prev)
        self.Bind(wx.EVT_SPINCTRL,self.sel_note,self.choice_note)
        self.Bind(wx.EVT_TEXT,self.sel_com,self.comment)
        self.Bind(wx.EVT_CLOSE,self.quit_windows)
        self.Bind(wx.EVT_SIZE, self.OnSizeChanged)

    
    #To resize image
    def size_image(self):      
        self.picture.SetFocus()
        # Get current picture    
        bitmap=wx.Bitmap(os.path.join(self.dirname,self.images[self.indice-1]))
        image = wx.ImageFromBitmap(bitmap)
   
        # Windows size
        (frameW,frameH)=self.GetSize()
        frameW=frameW-self.size_left_widget-self.border
        frameH=frameH-self.border
        
        #Picture size
        W = image.GetWidth()
        H = image.GetHeight()
        
        #Find the best ratio
        ratioW=frameW/W
        ratioH=frameH/H
        if ratioW>ratioH:
            ratio=ratioH
        else:
            ratio=ratioW     
            
        #Rescale picture  
        image = image.Scale(image.GetWidth()*ratio, image.GetHeight()*ratio, wx.IMAGE_QUALITY_HIGH)
        result = wx.BitmapFromImage(image)
        self.picture.SetBitmap(result)
        self.Refresh()
        self.Show()
        
    # Function if windows change size    
    def OnSizeChanged(self, e) :  
        if self.data_file_name is not None: 
            self.size_image()
    
    # Function if comment change                 
    def sel_com(self,e):
        if self.data_file_name is not None:
            self.data.set_comment(self.images[self.indice-1],self.comment.GetValue())  
        
    # Function if not change
    def sel_note(self,e):
        if self.data_file_name is not None:
            self.data.set_note(self.images[self.indice-1],self.choice_note.GetValue())   
     
    #If click on button '>' , display next picture in the folder 
    def NextPic(self,e):    
        if self.data_file_name is not None:
            self.indice=self.indice+1  
            print self.images[self.indice-1]
            self.check_data() 
            # Display image                   
            self.size_image()
 
    # If click on button '<' , display previous picture in the folder    
    def PrevPic(self,e):
        if self.data_file_name is not None:
            self.indice=self.indice-1       
            print self.images[self.indice-1]     
            self.check_data()
            # Display image                 
            self.size_image()

    # Function for open a file
    def OnOpen(self,e):      
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = open(os.path.join(self.dirname, self.filename), 'r')
            self.data_file_name = os.path.join(self.dirname,'data.csv')
            results=[]
            results += [each for each in os.listdir(self.dirname) if each.endswith('.png')]
            results.sort()     
            self.images=results
            i=0
            for im in results:
                i=i+1
                if im==self.filename:
                    self.indice=i
                    break                                                    
            f.close() 
        dlg.Destroy()    
        
        
        if self.data_file_name is not None:    
        # Display image    
            print self.images[self.indice-1]
            self.size_image()      
            self.data.load(self.data_file_name)
            self.check_data()
                
   
    def check_data(self):
        if self.data.is_recorded(self.images[self.indice-1])==0:
            self.data.add_filename(self.images[self.indice-1])
            self.data.save(self.data_file_name)
            self.choice_note.SetValue(self.data.get_note(self.images[self.indice-1]))
            self.comment.SetValue(self.data.get_comment(self.images[self.indice-1]))
        else:
            self.choice_note.SetValue(self.data.get_note(self.images[self.indice-1]))
            self.comment.SetValue(self.data.get_comment(self.images[self.indice-1]))
            
        
    #Function if quit windows  
    def quit_windows(self,e):
        print 'SAVE/QUIT'       
        self.data.save(self.data_file_name)    
        self.Destroy()
 
     
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'Note.py')
        frame.Show(True)
        return True

app = MyApp(0)
app.MainLoop()
        
 
