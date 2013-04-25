#!/usr/bin/python

#!/usr/bin/python
# -*- coding: utf-8 -*-
# author Mathilde Bouin

from __future__ import division
import wx
import os
import glob
import read_csv
import sys
import xlrd
import xlwt
import re
from filter_window import MyDialog
from snap_options_windows import Dialog_snap


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        
        # Default directory (change it if you want)
        self.dirname=''     
        self.dirname_xls='/home/mb236582'
        #border widget picture
        self.border=25
        #Left widget (all except picture)
        self.size_widget=110       
        self.data_file_name= None
        self.data_file_xls=None
        self.images=None
        self.index=None
        self.image_current=None
        self.image_brain=None
        self.data=read_csv.Data()   
        self.keycode_note=None
        self.keycode_comment=None
        self.zoom_ratio=1
        
        #Windows       
        wx.Frame.__init__(self, parent, id, title, (-1, -1), wx.Size(800, 600+self.size_widget))
               
        self.scroll = wx.ScrolledWindow(self)
        self.panel = wx.Panel(self.scroll,wx.ID_ANY)
        #self.panel = wx.Panel(self,-1)
        
        #self.scroll = wx.ScrollBar(self, -1, (100, 240), (200, 20), wx.SB_HORIZONTAL)
        #self.scroll.SetScrollbar(1, 1, 12, 1, True)

              
        # Setting up the menu.
        filemenu= wx.Menu()
        menuOpen = filemenu.Append(wx.ID_FILE, "&Open"," Open a file to edit")
        menuOpenXls= filemenu.Append(wx.ID_FILE1, "&Open Xls"," Open a file Xls")
        
        # Filter
        filtermenu=wx.Menu()
        filter_open=filtermenu.Append(wx.ID_ANY, 'Launch filter')
        
        optionsmenu=wx.Menu()
        snapshots_options=optionsmenu.Append(wx.ID_ANY, 'Define your snapshots')
              
        self.statusbar = self.CreateStatusBar()

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        menuBar.Append(filtermenu,"&Filter")
        menuBar.Append(optionsmenu,"&Options")
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        
        # Main Box 
        self.box = wx.BoxSizer(wx.VERTICAL)
        
        #Box for right widgets
        self.box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.box3 = wx.BoxSizer(wx.HORIZONTAL)
        self.box4 = wx.BoxSizer(wx.HORIZONTAL)
        self.box5 = wx.BoxSizer(wx.HORIZONTAL)
        self.box6 = wx.BoxSizer(wx.VERTICAL)

        button_prev = wx.Button(self.panel, -1, '<',size=(40, -1))
        button_next = wx.Button(self.panel, -1, '>',size=(40, -1))
        self.box3.Add(button_prev, 0)
        self.box3.Add(button_next, 0)
        self.box2.Add(self.box3)
        
        note=['1','2','3','4','5']
        self.choice_note=wx.Choice(self.panel,-1,size=(60, 30),choices=['0','1','2','3','4','5'] )
        self.box5.Add(self.choice_note)
        self.choice_note2=wx.Choice(self.panel,-1,size=(60, 30),choices=['0','1','2','3','4','5'])
        self.box5.Add(self.choice_note2)
        self.box5.Show(self.choice_note2,False,True)
        self.box5.Layout()
         
        self.box4.Add(wx.StaticText(self.panel, -1, '  Note', size=(60, 30)))
        self.brain_text=wx.StaticText(self.panel, -1, '  Mask', size=(60, 30))
        self.box4.Add(self.brain_text)  
        self.box4.Show(self.brain_text,False,True)
        self.box4.Layout()
        
        #self.box5.Add(self.box4)     
        self.box6.Add(self.box5)  
        self.box6.Add(self.box4)  
        self.box2.Add(self.box6)

        self.comment=wx.TextCtrl(self.panel, size=(300, 50),style=wx.TE_MULTILINE)
        self.box2.Add(self.comment)    
        self.display_xls=wx.Button(self.panel,-1,'Display_xls',(50,50)) 
        self.box2.Add(self.display_xls)
        self.xls_comment=wx.TextCtrl(self.panel, size=(300, 50),style=wx.TE_READONLY | wx.TE_MULTILINE )
        self.box2.Add(self.xls_comment)
        self.box2.Show(self.xls_comment,False,True)
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
        self.box.Add(self.picture, 0)
        #, wx.ALIGN_CENTER| wx.ALL | wx.ADJUST_MINSIZE)     
  
        #Display GUI
        self.panel.SetSizerAndFit(self.box)   
        self.Show()
        
        # Events
        self.Bind(wx.EVT_MENU, self.on_open, menuOpen)
        self.Bind(wx.EVT_MENU, self.on_open_xls, menuOpenXls)
        self.Bind(wx.EVT_MENU, self.on_open_filter, filter_open)
        self.Bind(wx.EVT_MENU, self.on_open_snapshots_options,snapshots_options)
        self.Bind(wx.EVT_BUTTON,self.next_pic_event, button_next)
        self.Bind(wx.EVT_BUTTON,self.prev_pic_event, button_prev)
        self.Bind(wx.EVT_CHOICE,self.sel_note_event,self.choice_note)
        self.Bind(wx.EVT_CHOICE,self.sel_note_brain_event,self.choice_note2)
        self.Bind(wx.EVT_TEXT,self.sel_com,self.comment)
        self.Bind(wx.EVT_BUTTON,self.add_xls_comment,self.display_xls)
        self.Bind(wx.EVT_CLOSE,self.quit_windows)
        #self.Bind(wx.EVT_SIZE, self.on_size_changed)
        #self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        #self.Bind(wx.EVT_KEY_UP, self.on_key_down)
        #self.Bind(wx.EVT_CHAR, self.on_key_down)
        self.panel.Bind(wx.EVT_MOUSEWHEEL,self.on_mouse_wheel)   
   
        self.panel.SetFocus()
        
    ##To resize image
    def size_image(self):      
        self.picture.SetFocus()
        # Get current picture    
        image=wx.Image(os.path.join(self.dirname,self.images[self.index]))
        
        #Windows size
        (frameW,frameH)=self.GetSize()
        frameW=frameW
        frameH=frameH-self.size_widget
        print frameW,frameH
   
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
        
        self.zoom_ratio=ratio                    
        #Rescale picture  
        image = image.Scale(image.GetWidth()*ratio, image.GetHeight()*ratio, wx.IMAGE_QUALITY_HIGH)
        result = wx.BitmapFromImage(image)
        self.picture.SetBitmap(result)
        self.Refresh()
        self.Show()
        
        
    def zoom_image(self):
        image=wx.Image(os.path.join(self.dirname,self.images[self.index]))
        #Rescale picture  
        width_scale=image.GetWidth()*self.zoom_ratio
        height_scale=image.GetHeight()*self.zoom_ratio
        #print width_scale,height_scale
     
        if (30<width_scale<2500) and (30<height_scale<2500):           
            image = image.Scale(width_scale,height_scale, wx.IMAGE_QUALITY_HIGH)
            print image.GetWidth(),image.GetHeight()
            (frameW,frameH)=self.GetSize()
            frameH=frameH-self.size_widget
            if frameW<image.GetWidth():
                self.frmPanelWid, self.frmPanelHgt = self.panel.GetSize()
                self.scroll.SetScrollbars(5,5,image.GetWidth(),image.GetHeight())
            if frameH<image.GetHeight():
                self.frmPanelWid, self.frmPanelHgt = self.panel.GetSize()
                self.scroll.SetScrollbars(5,5,image.GetWidth(),image.GetHeight())      
            result = wx.BitmapFromImage(image)
            self.picture.SetBitmap(result)
            self.Refresh()
            self.Show()        
            print 'end'                          
        else:
            print 'NO MORE ZOOM/DEZOOM'   
            image = image.Scale(width_scale,height_scale, wx.IMAGE_QUALITY_HIGH)     
       
    def on_mouse_wheel(self,e):
        if self.images is not None:       
            rot=e.GetWheelRotation()
            if rot>0:
                self.zoom_ratio=self.zoom_ratio+0.05
                self.zoom_image()
            else:
                self.zoom_ratio=self.zoom_ratio-0.05
                self.zoom_image()


#KEYBOARD EVENTS           
        #if keycode==wx.WXK_LEFT:
            #self.prev_pic_event(e)
        #elif keycode==wx.WXK_RIGHT:
            #self.next_pic_event(e)           
        #elif keycode==wx.WXK_NUMPAD0:
            #self.keycode_note=0
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_NUMPAD1:
            #self.keycode_note=1
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_NUMPAD2:
            #self.keycode_note=2
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_NUMPAD3:
            #self.keycode_note=3
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_NUMPAD4:
            #self.keycode_note=4
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_NUMPAD5:
            #self.keycode_note=5
            #self.sel_note_event(e)
        #elif keycode==wx.WXK_ESCAPE:
            #self.quit_windows(e)
        #else:
            #print 'else'       
            #self.keycode_comment=unichr(keycode)
            #self.comment.AppendText(self.keycode_comment)
  
       
    # Function if windows change size    
    def on_size_changed(self, e) :  
        if self.data_file_name is not None: 
            self.size_image()
    
    # Function if comment change                 
    def sel_com(self,e):
        if self.data_file_name is not None:
            self.data.set_comment(self.images[self.index],self.comment.GetValue())      
        
    # Function if not change
    def sel_note_event(self,e):
        if self.data_file_name is not None: 
            if self.keycode_note is not None:
                self.choice_note.SetSelection(self.keycode_note)
                self.data.set_note(self.images[self.index],self.choice_note.GetCurrentSelection())
                self.keycode_note=None
            else:                      
                self.data.set_note(self.images[self.index],self.choice_note.GetCurrentSelection())
        

    # Function if not change
    def sel_note_brain_event(self,e):
        if self.data_file_name is not None:
            self.data.set_note(self.image_brain,self.choice_note2.GetCurrentSelection())
       
    # If click on button '>' , display next picture in the folder 
    def next_pic_event(self,e):  
        # Hide and clear display xls
        self.xls_comment.Clear()
        self.box2.Show(self.xls_comment,False,True)          
        self.box2.Layout() 
        if self.data_file_name is not None:
            if (self.index+1)==len(self.images):
                self.index=0
            else:
                self.index=self.index+1    
                         
            self.statusbar.SetStatusText(self.images[self.index])             
            self.pict_split() 
            self.check_data() 
            # Display image                   
            self.size_image() 

 
    # If click on button '<' , display previous picture in the folder    
    def prev_pic_event(self,e):
        # Hide and clear display xls
        self.xls_comment.Clear()
        self.box2.Show(self.xls_comment,False,True)          
        self.box2.Layout() 
        if self.data_file_name is not None:
            if (self.index-1)==-1:
                self.index=len(self.images)-1
            else:
                self.index=self.index-1
                               
            self.statusbar.SetStatusText(self.images[self.index])
            self.pict_split()      
            self.check_data()
            # Display image                 
            self.size_image()
    
    def add_xls_comment(self,e):
        if self.box2.IsShown(self.xls_comment) is False:
            self.check_data_xls()
            self.box2.Show(self.xls_comment,True,True)          
            self.box2.Layout() 
        else:
            self.box2.Show(self.xls_comment,False,True)          
            self.box2.Layout()  
       
         
    # Function for open a file
    def on_open(self,e):      
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
            i=-1
            for im in results:
                i=i+1
                if im==self.filename:
                    self.index=i
                    break                                                    
            f.close()    
        dlg.Destroy()    
        
        if self.data_file_name is not None:    
        # Display image    
            self.statusbar.SetStatusText(self.images[self.index])
            self.data.load(self.data_file_name)
            self.pict_split()  
            self.check_data()
            self.size_image()   
            
                
    def on_open_xls(self,e):  
        dlg = wx.FileDialog(self, "Choose a file xls", self.dirname_xls, "", "*.xls", wx.OPEN)     
        if dlg.ShowModal() == wx.ID_OK:           
            self.filename_xls = dlg.GetFilename()
            self.dirname_xls = dlg.GetDirectory()
            self.data_file_xls=xlrd.open_workbook(os.path.join(self.dirname_xls, self.filename_xls))                       
        dlg.Destroy()  
        
        
    def on_open_filter(self,e):
        self.data.save(self.data_file_name,self.images)  
        dia = MyDialog(self, -1, 'Filter',self.dirname)
        if dia.ShowModal() == wx.ID_OK:   
            #Get value of filter
            #dia.filter_process()    
            dia.write_results()       
        else:
            print 'NO FILTER SELECTION'   
        dia.Destroy()
             
             
    def on_open_snapshots_options(self,e):
        dia = Dialog_snap(self, -1, 'Options snap')   
        if dia.ShowModal() == wx.ID_OK:  
            pass      
        dia.Destroy()     
            
    def check_data_xls(self):
        if self.data_file_xls is None:
            self.xls_comment.AppendText('Open a xls file pls')  
        if self.data_file_name is not None and self.data_file_xls is not None:
            suj_find=False
            filename=self.images[self.index].split('.')[0]
            expresion=r"([0-9]{7})([A-Za-z]{4})"
            m=re.search(expresion, filename)
            if m is not None:
                subject=m.group(0)
                filespliter=filename.split('_')
                for i in range(0,len(filespliter)):
                    if filespliter[i]==subject:
                        index=i
                        break
                        
                #Check nom_center                              
                nom_center=filespliter[index-1]
                if nom_center.isdigit():
                    nom_center=filespliter[index-2]   
                subject2=subject[7:11]+subject[0:7]
                res=[]  
                res += [each for each in self.data_file_xls.sheet_names() if nom_center in each]
                if res:
                    good_sheet = self.data_file_xls.sheet_by_name(res[0])
                    good_row=0
                    for row in good_sheet.col_values(0):
                        if row==subject2:
                            suj_find=True
                            break;          
                        good_row=good_row+1 
                    if suj_find is True:   
                        note_xls=good_sheet.cell(good_row,xlwt.Utils.cell_to_rowcol2('AO'+str(good_row))[1]).value
                        comment_xls=good_sheet.cell(good_row,xlwt.Utils.cell_to_rowcol2('AP'+str(good_row))[1]).value        
                        self.xls_comment.AppendText(str(note_xls)+'\n')  
                        self.xls_comment.AppendText(comment_xls)  
                
   
    def check_data(self):
        if self.data.is_recorded(self.images[self.index])==0:
            self.data.add_filename(self.images[self.index])
            self.data.save(self.data_file_name,self.images)
            self.choice_note.SetSelection(self.data.get_note(self.images[self.index]))
            self.comment.SetValue(self.data.get_comment(self.images[self.index]))
        else:
            self.choice_note.SetSelection(self.data.get_note(self.images[self.index]))
            self.comment.ChangeValue(self.data.get_comment(self.images[self.index]))
            self.data.save(self.data_file_name,self.images)

   
    def check_brain_exist(self):       
        word_to_find='brain'
        self.image_brain=self.images[self.index].replace('split','brain')
        element=[]
        element+= [image for image in self.images if image==self.image_brain]
        if not element:
            return 0
        else:
            return 1
   

    def pict_split(self):
        word_to_find='split'
        if word_to_find in self.images[self.index] and self.check_brain_exist()==1: 
            self.box2.Show(self.choice_note2,True,True)
            self.box4.Show(self.brain_text,True,True)
            self.box2.Layout()
            self.box4.Layout()            
        else:
            self.box2.Show(self.choice_note2,False,True)
            self.box4.Show(self.brain_text,False,True)
            self.box2.Layout()
            self.box4.Layout()
           
    #Function if quit windows  
    def quit_windows(self,e):
        print 'SAVE/QUIT'       
        self.data.save(self.data_file_name,self.images)    
        self.Destroy()
 
     
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'Note.py')
        frame.Show(True)
        frame.Centre()
        return True

app = MyApp(0)
app.MainLoop()
        
