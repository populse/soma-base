# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import os
import read_csv
import read_csv_spm
import read_csv_gw

#from filter_window import Filter

     
    
class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        #self.data=read_csv.Data()   
        self.data_file_name= None
        self.dirname=None
        self.pictures_absolute_path=None
        self.pictures_relatif_path=None
        self.index_picture_display=None
        self.image_brain=None
        self.type_snap=None
        self.check_box_locality={}
        #self.filter_window=MyFilter(self.dirname)
        #self.filter_window.setParent(self)
        
        self.create_actions()
        self.create_gui()
        self.create_menu()

    def create_gui(self):
        self.MainWidget=QtGui.QWidget()
        self.resize(800,600)
        self.vbox = QtGui.QVBoxLayout()
        self.hbox = QtGui.QHBoxLayout() 
        #self.hbox.setAlignment(QtCore.Qt.AlignLeft)  
        self.hbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)  
        self.hbox2= QtGui.QHBoxLayout()   
        self.button_prev=QtGui.QPushButton('<')
        self.button_prev.setFixedSize(40,30)
        self.button_next=QtGui.QPushButton('>') 
        self.button_next.setFixedSize(40,30)
        self.button_prev.clicked.connect(self.on_prev)
        self.button_next.clicked.connect(self.on_next)
        self.choice_note=QtGui.QComboBox(parent=self)
        self.choice_note.addItems(['0','1','2','3','4'])
        self.choice_note.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.choice_note.setEditable(True)
        self.choice_note.setCurrentIndex(4)
        self.choice_note.setFixedSize(60,30)
        self.choice_note.textChanged.connect(self.on_marks_change)
        #self.choice_note2=QtGui.QComboBox()
        #self.choice_note2.addItems(['0','1','2','3','4','5'])
        #self.choice_note2.setEnabled(False)
        #self.choice_note2.currentIndexChanged.connect(self.on_marks_change2)
        self.comment=QtGui.QTextEdit()
        currentSize = self.comment.size()
        self.comment.setFixedSize(500,50)
        #self.comment.setMaximumSize(10000,50)
        self.text_in_comment=QtCore.QString()
        self.comment.textChanged.connect(self.on_comment_change)
        
        self.number_current_image=QtGui.QLabel()
        
        
        #self.display_xls=QtGui.QPushButton('Display_xls')
        #self.xls_comment=QtGui.QTextEdit()
        #self.xls_comment.setReadOnly(True)
        #self.xls_comment.setVisible(False)     
        self.hbox.addWidget(self.button_prev)
        self.hbox.addWidget(self.button_next)
        self.hbox.addWidget(QtGui.QLabel('Grade Image Display'))         
        self.hbox.addWidget(self.choice_note)
        #self.hbox.addWidget(QtGui.QLabel('Grade Brain Mask')) 
        #self.hbox.addWidget(self.choice_note2)   
        self.hbox.addWidget(self.comment)
        self.hbox.addWidget(self.number_current_image)
        self.hbox.addStretch(1)
        #self.hbox.addWidget(self.display_xls)      
        self.vbox.addLayout(self.hbox)
        
         #Image
        self.scene=QtGui.QGraphicsScene()
        self.view=QtGui.QGraphicsView(self.scene)
        self.view.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        
        self.view.wheelEvent = self.wheel_event
        #self.picture_display=QGraphicsPixmapItem()
        #self.scene.addItem(self.picture_display)
        self.hbox2.addWidget(self.view)
        self.create_pre_commmentary_gw()
        self.create_pre_commmentary_spm()        
        self.vbox.addLayout(self.hbox2)
        self.mousePressEvent = self.back_focus
        self.MainWidget.setLayout(self.vbox)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCentralWidget(self.MainWidget)
      
    def back_focus(self,event):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  


        

    def create_menu(self):
        self.filemenu=QtGui.QMenu("File")
        #self.filemenu.setTitle("&File")
        self.filemenu.addAction(self.action_open)
        #self.filemenu.addAction(self.action_open_xls)
        self.filtermenu=QtGui.QMenu("Filter")
        #self.filtermenu.setTitle('&Filter')
        self.filtermenu.addAction(self.action_filter)
        self.menuBar().addMenu(self.filemenu)
        self.menuBar().addMenu(self.filtermenu)
        
        
     
    def create_actions(self):
        #Action filemenu
        self.action_open=QtGui.QAction('Open',self)
        self.action_open.triggered.connect(self.on_open)
        #self.action_open_xls=QtGui.QAction('Open Xls',self)
        #self.action_open_xls.triggered.connect(self.on_open_xls)
        #Action filtermenu
        self.action_filter=QtGui.QAction('Launch filter',self)
        self.action_filter.triggered.connect(self.on_open_filter)


        

            

       
       
    def create_pre_commmentary_gw(self):   
        self.group_box=QtGui.QGroupBox("Pre-commentaires")
        self.vbox_pre_commentary=QtGui.QVBoxLayout()
        #Create list QgridLayout for hide/show
        self.list_layout_pre_commentary_gw=[]
        
        
        #Limite Surface grey/white
        self.label_limit_gw=QtGui.QLabel(self.trUtf8("Limite surface gris/blanc"))
        self.choice_note_limit_gw=QtGui.QComboBox()
        self.choice_note_limit_gw_items=['-1','0','1']
        self.choice_note_limit_gw.addItems(self.choice_note_limit_gw_items)
        self.choice_note_limit_gw.setCurrentIndex(1)
        self.choice_note_limit_gw.setFixedSize(50,30)
        self.layout_limit_gw=QtGui.QGridLayout()
        self.layout_limit_gw.addWidget(self.label_limit_gw,0,0)
        self.layout_limit_gw.addWidget(self.choice_note_limit_gw,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_limit_gw)  
        self.list_layout_pre_commentary_gw.append(self.layout_limit_gw)  
           
        #Surface pial surface limit
        self.label_pial=QtGui.QLabel("Limite surface pial")
        self.choice_note_pial=QtGui.QComboBox()
        self.choice_note_pial_items=['-1','0','1']
        self.choice_note_pial.addItems(self.choice_note_pial_items)
        self.choice_note_pial.setCurrentIndex(1)
        self.choice_note_pial.setFixedSize(50,30)
        self.layout_pial=QtGui.QGridLayout()
        self.layout_pial.addWidget(self.label_pial,0,0)
        self.layout_pial.addWidget(self.choice_note_pial,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_pial)            
        self.list_layout_pre_commentary_gw.append(self.layout_pial)

        
        #Debordement
        self.label_debordement=QtGui.QLabel(self.trUtf8("Débordement méninges/sinus"))
        self.choice_note_debordement=QtGui.QComboBox()
        self.choice_note_debordement.addItems(['0','1','2'])
        self.choice_note_debordement.setFixedSize(50,30)
        self.layout_debordement=QtGui.QGridLayout()
        self.layout_debordement.addWidget(self.label_debordement,0,0)
        self.layout_debordement.addWidget(self.choice_note_debordement,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_debordement)
        self.list_layout_pre_commentary_gw.append(self.layout_debordement)           
        
        #Brain_miss
        self.label_brain_miss=QtGui.QLabel("Bouts de cerveau manquants")
        self.choice_note_brain_miss=QtGui.QComboBox()
        self.choice_note_brain_miss.addItems(['0','1','2'])
        self.choice_note_brain_miss.setFixedSize(50,30)
        self.layout_brain_miss=QtGui.QGridLayout()
        self.layout_brain_miss.addWidget(self.label_brain_miss,0,0)
        self.layout_brain_miss.addWidget(self.choice_note_brain_miss,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_brain_miss) 
        self.list_layout_pre_commentary_gw.append(self.layout_brain_miss)        
        
        self.list_locality=['temporal','frontal','hippocampe','hypersignaux MB','corps calleux','noyaux gris','cervelet']
        for i in range(0,len(self.list_locality)):
            self.check_box_locality[i]=QtGui.QCheckBox(self.list_locality[i])
            #self.check_box_locality[i].setEnabled(False)
            self.layout_brain_miss.addWidget(self.check_box_locality[i],i+1,0)
         
        ##self.vbox_pre_commentary.addStretch(1)  
        #self.group_box.setLayout(self.vbox_pre_commentary)    
        #self.hbox2.addWidget(self.group_box)
        
         
        self.hide_show_pre_commentary_gw() 
        

        
    def hide_show_pre_commentary_gw(self,state="hide"):
        for lay in self.list_layout_pre_commentary_gw:
            for i in range(0,lay.count()):
                item=lay.itemAt(i)
                if state=="show":
                   item.widget().show() 
                else:
                   item.widget().hide() 
                

            
   


    def create_pre_commmentary_spm(self):   
        #self.group_box=QtGui.QGroupBox("Pre-commentary")
        #self.vbox_pre_commentary=QtGui.QVBoxLayout()
        #Create list QgridLayout for hide/show
        self.list_layout_pre_commentary_spm=[]
        
        #Debordement du blanc
        self.label_overflow_white=QtGui.QLabel(self.trUtf8("Débordement du blanc"))
        self.choice_note_overflow_white=QtGui.QComboBox()
        self.choice_note_overflow_white.addItems(['0','1','2'])
        self.choice_note_overflow_white.setFixedSize(50,30)
        self.layout_overflow_white=QtGui.QGridLayout()
        self.layout_overflow_white.addWidget(self.label_overflow_white,0,0)
        self.layout_overflow_white.addWidget(self.choice_note_overflow_white,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_overflow_white)
        self.list_layout_pre_commentary_spm.append(self.layout_overflow_white)
           
        #Frontière gris/blanc
        self.label_border_gw=QtGui.QLabel(self.trUtf8("Frontière gris/blanc"))
        self.choice_note_border_gw=QtGui.QComboBox()
        self.choice_note_border_gw.addItems(['0','1'])
        self.choice_note_border_gw.setFixedSize(50,30)
        self.layout_border_gw=QtGui.QGridLayout()
        self.layout_border_gw.addWidget(self.label_border_gw,0,0)
        self.layout_border_gw.addWidget(self.choice_note_border_gw,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_border_gw)            
        self.list_layout_pre_commentary_spm.append(self.layout_border_gw)

        #Débordements du gris ds méninges/sinus
        self.label_overflow_grey=QtGui.QLabel(self.trUtf8("Débordemens gris dans méninges/sinus"))
        self.choice_note_overflow_grey=QtGui.QComboBox()
        self.choice_note_overflow_grey.addItems(['0','1','2'])
        self.choice_note_overflow_grey.setFixedSize(50,30)
        self.layout_overflow_grey=QtGui.QGridLayout()
        self.layout_overflow_grey.addWidget(self.label_overflow_grey,0,0)
        self.layout_overflow_grey.addWidget(self.choice_note_overflow_grey,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_overflow_grey)  
        self.list_layout_pre_commentary_spm.append(self.layout_overflow_grey)             
        
        #Frontière LCR/gris
        self.label_border_lcr=QtGui.QLabel(self.trUtf8("Frontière LCR/gris"))
        self.choice_note_border_lcr=QtGui.QComboBox()
        self.choice_note_border_lcr.addItems(['0','1'])
        self.choice_note_border_lcr.setFixedSize(50,30)
        self.layout_border_lcr=QtGui.QGridLayout()
        self.layout_border_lcr.addWidget(self.label_border_lcr,0,0)
        self.layout_border_lcr.addWidget(self.choice_note_border_lcr,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_border_lcr) 
        self.list_layout_pre_commentary_spm.append(self.layout_border_lcr)        
        
        #Débordements du LCR ds méninges/sinus
        self.label_overflow_lcr=QtGui.QLabel(self.trUtf8("Débordements LCR dans méninges/sinus"))
        self.choice_note_overflow_lcr=QtGui.QComboBox()
        self.choice_note_overflow_lcr.addItems(['0','1','2'])
        self.choice_note_overflow_lcr.setFixedSize(50,30)
        self.layout_overflow_lcr=QtGui.QGridLayout()
        self.layout_overflow_lcr.addWidget(self.label_overflow_lcr,0,0)
        self.layout_overflow_lcr.addWidget(self.choice_note_overflow_lcr,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_overflow_lcr) 
        self.list_layout_pre_commentary_spm.append(self.layout_overflow_lcr)   
        
        # Zones de LCR non segmentées 
        self.label_lcr_unsegmented=QtGui.QLabel(self.trUtf8("Zones de LCR non segmentées"))
        self.choice_note_lcr_unsegmented=QtGui.QComboBox()
        self.choice_note_lcr_unsegmented.addItems(['0','1','2'])
        self.choice_note_lcr_unsegmented.setFixedSize(50,30)
        self.layout_lcr_unsegmented=QtGui.QGridLayout()
        self.layout_lcr_unsegmented.addWidget(self.label_lcr_unsegmented,0,0)
        self.layout_lcr_unsegmented.addWidget(self.choice_note_lcr_unsegmented,0,1)
        self.vbox_pre_commentary.addLayout(self.layout_lcr_unsegmented) 
        self.list_layout_pre_commentary_spm.append(self.layout_lcr_unsegmented)             
       
     
     
        #self.vbox_pre_commentary.addStretch(1)  
        self.vbox_pre_commentary.addStretch(1)  
        self.group_box.setLayout(self.vbox_pre_commentary)    
        self.hbox2.addWidget(self.group_box)
        
         
        self.hide_show_pre_commentary_spm() 
        

    def hide_show_pre_commentary_spm(self,state="hide"):
        for lay in self.list_layout_pre_commentary_spm:
            for i in range(0,lay.count()):
                item=lay.itemAt(i)
                if state=="show":
                   item.widget().show() 
                else:
                   item.widget().hide() 


            
                 
                


    def resizeEvent(self,resizeEvent):
        if self.data_file_name is not None:
            self.open_image(self.pictures_absolute_path[self.index_picture_display]) 

    def keyPressEvent(self, event):
        if self.data_file_name is not None:
            if event.key() == QtCore.Qt.Key_Left:
                print "Left touch keyboard"
                self.on_prev()
            if event.key() == QtCore.Qt.Key_Right: 
                print "Right touch keyboard"
                self.on_next()
     
   
    def on_next(self):
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            self.data.save(self.dirname,self.pictures_relatif_path) 
            if (self.index_picture_display+1)==len(self.pictures_absolute_path):
                self.index_picture_display=0
            else:
                self.index_picture_display=self.index_picture_display+1    
                    
            self.open_image(self.pictures_absolute_path[self.index_picture_display]) 
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])
            self.number_current_image.setText("%d/%d"%(self.index_picture_display+1,len(self.pictures_absolute_path)))
            #self.find_picture_split()
            self.get_type_snapshot()       
            self.check_data()  
        
    def on_prev(self):  
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            self.data.save(self.dirname,self.pictures_relatif_path) 
            if (self.index_picture_display-1)==-1:
                self.index_picture_display=len(self.pictures_absolute_path)-1
            else:
                self.index_picture_display=self.index_picture_display-1
             
            self.open_image(self.pictures_absolute_path[self.index_picture_display])     
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])       
            self.number_current_image.setText("%d/%d"%(self.index_picture_display+1,len(self.pictures_absolute_path)))      
            #self.find_picture_split()
            self.get_type_snapshot()       
            self.check_data() 
            
    def on_marks_change(self):
        if self.data_file_name is not None:
            #if self.choice_note2.isEnabled() is True:
                #self.data.set_double_note(self.pictures_absolute_path[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
            #else:
            self.data.set_simple_note(self.pictures_relatif_path[self.index_picture_display],self.choice_note.currentText())
        self.setFocusPolicy(QtCore.Qt.StrongFocus)            
                               
    #def on_marks_change2(self):
        #print 'brain marks change'
        #if self.data_file_name is not None:
                #self.data.set_double_note(self.pictures_absolute_path[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        
    def on_comment_change(self):
        if self.data_file_name is not None:
            self.text_in_comment=self.comment.toPlainText()
            self.text_in_comment=self.comment.toPlainText().toUtf8()
            self.data.set_comment(self.pictures_relatif_path[self.index_picture_display],self.text_in_comment)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

            
                
    def on_open(self):
        print 'in open'      
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','',self.tr("Images Files (*.png);;(*jpg)"))
        if fname != '':
            #self.data=read_csv.Data()  
            #self.picture_display.setPixmap(QPixmap(fname))
            self.dirname=os.path.dirname(str(fname))
            #self.data_file_name = os.path.join(self.dirname,self.data.data_filename)
            #print 'self.data_file name',self.data_file_name
            #if self.data_file_name is not None:    
                ##if something wrong with the current csv
                #if self.data.load(self.data_file_name)== 0:
                    #self.data_file_name= None
                    #self.dirname=None
                #else:    
            self.open_image(fname)
            results = [os.path.join(self.dirname,each) for each in os.listdir(self.dirname) if each.endswith('.png')]
            results.sort()
            self.pictures_absolute_path=results
            results2=[each for each in os.listdir(self.dirname) if each.endswith('.png')]
            results2.sort()
            self.pictures_relatif_path=results2
            i=-1
            for picture in self.pictures_absolute_path:
                i=i+1
                if picture==fname:
                    self.index_picture_display=i
                    break     
            
            self.number_current_image.setText("%d/%d"%(self.index_picture_display+1,len(self.pictures_absolute_path)))
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])        
            self.get_type_snapshot()       
            self.check_data()     

            #Get back focus 
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  
        
        
    def get_type_snapshot(self):
        print 'get type snapshot'
        if 'GW' in self.pictures_relatif_path[self.index_picture_display]:
            new_type_snap='GW'
            self.hide_show_pre_commentary_gw("show")
            self.hide_show_pre_commentary_spm()
        elif 'spm' in self.pictures_relatif_path[self.index_picture_display]:  
            new_type_snap='spm'
            self.hide_show_pre_commentary_gw()
            self.hide_show_pre_commentary_spm("show")
        else:
            new_type_snap='default'
            self.hide_show_pre_commentary_gw()
            self.hide_show_pre_commentary_spm()
        
        #If the first time
        if self.type_snap is None:
            self.type_snap=new_type_snap
            self.data=self.get_data_class() 
            self.dirname=os.path.dirname(self.pictures_absolute_path[self.index_picture_display])
            self.data_file_name = os.path.join(self.dirname,self.data.data_filename)
            if self.data_file_name is not None:    
                #if something wrong with the current csv
                if self.data.load(self.dirname)== 0:
                    self.data_file_name= None
                    self.dirname=None
            
        else:    
            #Check if something change or not    
            if self.type_snap==new_type_snap:
                    print 'same type snap'
            else:
                print 'the snap type change -> an other .csv is created'
                self.type_snap=new_type_snap   
                self.data=self.get_data_class() 
                print self.data.data_filename
                #self.picture_display.setPixmap(QPixmap(fname))
                self.dirname=os.path.dirname(self.pictures_absolute_path[self.index_picture_display])
                self.data_file_name = os.path.join(self.dirname,self.data.data_filename)
                if self.data_file_name is not None:    
                    #if something wrong with the current csv
                    if self.data.load(self.dirname)== 0:
                        self.data_file_name= None
                        self.dirname=None
           
        
        
    def get_data_class(self):
        if self.type_snap=='GW':
            return read_csv_gw.DataGW()
        elif self.type_snap=='spm':
            return read_csv_spm.DataSPM()     
        elif self.type_snap=='default':
            return read_csv.Data()
            
          
            
    def open_image(self, path):
        w_vue, h_vue = self.view.width(), self.view.height() 
        self.current_image = QtGui.QImage(path)
        self.pixmap = QtGui.QPixmap.fromImage(self.current_image.scaled(w_vue, h_vue,
                                    QtCore.Qt.KeepAspectRatio, 
                                    QtCore.Qt.SmoothTransformation)) 
        self.view_current()

    def view_current(self):
        w_pix, h_pix = self.pixmap.width(), self.pixmap.height()
        self.scene.clear()
        self.scene.setSceneRect(0, 0, w_pix, h_pix)
        self.scene.addPixmap(self.pixmap)
        #self.view.setScene(self.scene)
        
    def wheel_event (self, event):
        if self.data_file_name is not None:
            steps = event.delta() / 120.0
            self.event_x=event.x()
            self.event_y=event.y()
            self.zoom(steps)
            event.accept()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)   
    
    def zoom(self, step):
        w_pix, h_pix = self.pixmap.width(), self.pixmap.height()
        w, h = w_pix * (1 + 0.1*step), h_pix * (1 + 0.1*step)
        self.pixmap = QtGui.QPixmap.fromImage(self.current_image.scaled(w, h, 
                                            QtCore.Qt.KeepAspectRatio, 
                                            QtCore.Qt.FastTransformation))
        self.view_current()
        self.view.centerOn(self.view.mapToScene(self.event_x,self.event_y))
            
            
    def on_open_xls (self):
        print 'on open xls - On working'    
        #Get back focus 
        self.setFocusPolicy(QtCore.Qt.StrongFocus)        
            
            
    def on_open_filter(self):
        print 'on open filter'
        if self.data_file_name is not None:
            try:
                from create_bdd import CreateBDD  
                from filter_window import Filter
                self.filter_window=Filter(self.dirname)        
                self.data.save(self.dirname,self.pictures_relatif_path)  
                setattr(self.filter_window,'dirname_snap',self.dirname) 
                setattr(self.filter_window,'bdd',CreateBDD.get_instance())
                self.filter_window.choice_studies.addItems(self.filter_window.bdd.studies())
    

            except ImportError:
                print 'NO USE DATABASE FOR FILTER'
                from filter_window_basic import FilterBasic
                self.filter_window=FilterBasic(self.dirname)
                self.data.save(self.dirname,self.pictures_relatif_path)  
                setattr(self.filter_window,'dirname_snap',self.dirname) 
            
            self.filter_window.open()
                    
                
        else:
            print 'PLEASE OPEN AN IMAGE BEFORE USING FILTER'          
    
        #Get back focus 
        self.setFocusPolicy(QtCore.Qt.StrongFocus)      
            
    #def check_brain_exist(self):       
        #word_to_find='brain'
        #self.image_brain=self.pictures_absolute_path[self.index_picture_display].replace('split','brain')
        #element=[]
        #element+= [image for image in self.pictures_absolute_path if image==self.image_brain]
        #if not element:
            #return 0
        #else:
            #return 1        

            
    def check_data(self):
        #COndtion if precommentray or not
        #if filename doesn't exists in .csv
        print 'check data'
        
        if self.data.is_recorded(self.pictures_relatif_path[self.index_picture_display])==0:
            print self.pictures_relatif_path[self.index_picture_display]
            self.data.add_filename(self.pictures_relatif_path[self.index_picture_display])
            #self.data.save(self.data_file_name,self.pictures_relatif_path)  
            
            #self.choice_note.setEditText(self.data.get_simple_note(self.pictures_relatif_path[self.index_picture_display]))                    
            #self.comment.setPlainText(self.data.get_comment(self.pictures_relatif_path[self.index_picture_display]))
            #self.choice_note_debordement.setCurrentIndex(self.data.get_marks_debordement(self.pictures_relatif_path[self.index_picture_display]))     
            #self.choice_note_pial.setCurrentIndex(self.data.get_marks_pial(self.pictures_relatif_path[self.index_picture_display])+1)                 
            #self.choice_note_cutting.setCurrentIndex(self.data.get_marks_cutting(self.pictures_relatif_path[self.index_picture_display]))      
            #self.choice_note_brain_miss.setCurrentIndex(self.data.get_marks_brain_miss(self.pictures_relatif_path[self.index_picture_display]))  
            #self.list_get_locality=self.data.get_locality(self.pictures_relatif_path[self.index_picture_display]) 
            #for i in range(0,len(self.list_locality)):
                #if self.list_locality[i] in self.list_get_locality:
                    #self.check_box_locality[i].setCheckState(QtCore.Qt.Checked)
                #else:
                    #self.check_box_locality[i].setCheckState(QtCore.Qt.Unchecked)          
            
        #else:
        self.text_in_comment=QtCore.QString.fromUtf8(self.data.get_comment(self.pictures_relatif_path[self.index_picture_display]))
        self.comment.setPlainText(unicode(self.text_in_comment))
        #self.data.save(self.data_file_name,self.pictures_relatif_path)             
        self.choice_note.setEditText(self.data.get_simple_note(self.pictures_relatif_path[self.index_picture_display]))       
        
        if self.type_snap=='GW':     
            print 'chec data gw'        
            self.choice_note_limit_gw.setCurrentIndex(self.data.get_marks_limit_surface_gw(self.pictures_relatif_path[self.index_picture_display])+1)     
            self.choice_note_pial.setCurrentIndex(self.data.get_marks_limit_surface_pial(self.pictures_relatif_path[self.index_picture_display])+1)                 
            self.choice_note_debordement.setCurrentIndex(self.data.get_marks_overflow_meninges_sinus(self.pictures_relatif_path[self.index_picture_display]))      
            self.choice_note_brain_miss.setCurrentIndex(self.data.get_marks_brain_miss(self.pictures_relatif_path[self.index_picture_display]))     
            self.list_get_locality=self.data.get_locality(self.pictures_relatif_path[self.index_picture_display]) 
            for i in range(0,len(self.list_locality)):
                if self.list_locality[i] in self.list_get_locality:
                    self.check_box_locality[i].setCheckState(QtCore.Qt.Checked)
                else:
                    self.check_box_locality[i].setCheckState(QtCore.Qt.Unchecked)
        elif self.type_snap=='spm':     
            print 'check data spm'
            self.choice_note_overflow_white.setCurrentIndex(self.data.get_marks_overflow_white(self.pictures_relatif_path[self.index_picture_display]))     
            self.choice_note_border_gw.setCurrentIndex(self.data.get_marks_border_grey_white(self.pictures_relatif_path[self.index_picture_display]))                 
            self.choice_note_overflow_grey.setCurrentIndex(self.data.get_marks_overflow_grey_meninges_sinus(self.pictures_relatif_path[self.index_picture_display]))      
            self.choice_note_border_lcr.setCurrentIndex(self.data.get_marks_border_lcr_grey(self.pictures_relatif_path[self.index_picture_display]))     
            self.choice_note_overflow_lcr.setCurrentIndex(self.data.get_marks_overflow_lcr_meninges_sinus(self.pictures_relatif_path[self.index_picture_display]))    
            self.choice_note_lcr_unsegmented.setCurrentIndex(self.data.get_marks_area_lcr_unsegmented(self.pictures_relatif_path[self.index_picture_display]))    
        
        
              
        
        self.data.save(self.dirname,self.pictures_relatif_path)  
        
        #else:
            ##self.text_in_comment=QtCore.QString.fromUtf8(self.data.get_comment(self.pictures_absolute_path[self.index_picture_display]))
            ##if self.choice_note2.isEnabled() is True:
                ##self.choice_note.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],False))
                ##self.choice_note2.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],True))
            ##else:   
            #self.choice_note.setCurrentIndex(self.data.get_simple_note(self.pictures_absolute_path[self.index_picture_display]))   
            #self.comment.setPlainText(unicode(self.text_in_comment))
            
            
            
            
            #self.data.save(self.data_file_name,self.pictures_absolute_path)    
        
        
        
    def set_pre_commmentary(self): 
        if self.type_snap=='GW':
            self.data.set_marks_limit_surface_gw(self.pictures_relatif_path[self.index_picture_display],self.choice_note_limit_gw_items[self.choice_note_limit_gw.currentIndex()])
            self.data.set_marks_limit_surface_pial(self.pictures_relatif_path[self.index_picture_display],self.choice_note_pial_items[self.choice_note_pial.currentIndex()])
            self.data.set_marks_overflow_meninges_sinus(self.pictures_relatif_path[self.index_picture_display],self.choice_note_debordement.currentIndex())
            self.data.set_marks_brain_miss(self.pictures_relatif_path[self.index_picture_display],self.choice_note_brain_miss.currentIndex())
            self.checked_locality=[]
            for i in range(0,len(self.list_locality)):
                if self.check_box_locality[i].isChecked() is True:
                    self.checked_locality.append(self.list_locality[i])
            self.data.set_locality(self.pictures_relatif_path[self.index_picture_display],self.checked_locality)       
        elif self.type_snap=='spm':
            self.data.set_marks_overflow_white(self.pictures_relatif_path[self.index_picture_display],self.choice_note_overflow_white.currentIndex())
            self.data.set_marks_border_grey_white(self.pictures_relatif_path[self.index_picture_display],self.choice_note_border_gw.currentIndex())
            self.data.set_marks_overflow_grey_meninges_sinus(self.pictures_relatif_path[self.index_picture_display],self.choice_note_overflow_grey.currentIndex())
            self.data.set_marks_border_lcr_grey(self.pictures_relatif_path[self.index_picture_display],self.choice_note_border_lcr.currentIndex())    
            self.data.set_marks_overflow_lcr_meninges_sinus(self.pictures_relatif_path[self.index_picture_display],self.choice_note_overflow_lcr.currentIndex())
            self.data.set_marks_area_lcr_unsegmented(self.pictures_relatif_path[self.index_picture_display],self.choice_note_lcr_unsegmented.currentIndex())             
        
        


    def closeEvent(self, event): 
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            self.data.save(self.dirname,self.pictures_relatif_path)    

