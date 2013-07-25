# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import os
import read_csv

#from filter_window import Filter

     
    
class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.data=read_csv.Data()   
        self.data_file_name= None
        self.dirname=None
        self.pictures_absolute_path=None
        self.pictures_relatif_path=None
        self.index_picture_display=None
        self.image_brain=None
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
        self.hbox2= QtGui.QHBoxLayout()   
        self.button_prev=QtGui.QPushButton('<')
        self.button_next=QtGui.QPushButton('>') 
        self.button_prev.clicked.connect(self.on_prev)
        self.button_next.clicked.connect(self.on_next)
        self.choice_note=QtGui.QComboBox()
        self.choice_note.addItems(['0','1','2','3','4','5'])
        self.choice_note.activated.connect(self.on_marks_change)
        #self.choice_note2=QtGui.QComboBox()
        #self.choice_note2.addItems(['0','1','2','3','4','5'])
        #self.choice_note2.setEnabled(False)
        #self.choice_note2.currentIndexChanged.connect(self.on_marks_change2)
        self.comment=QtGui.QTextEdit()
        currentSize = self.comment.size()
        self.comment.setMaximumSize(500,50)
        self.text_in_comment=QtCore.QString()
        self.comment.textChanged.connect(self.on_comment_change)
        
        self.display_xls=QtGui.QPushButton('Display_xls')
        self.xls_comment=QtGui.QTextEdit()
        self.xls_comment.setReadOnly(True)
        self.xls_comment.setVisible(False)     
        self.hbox.addWidget(self.button_prev)
        self.hbox.addWidget(self.button_next)
        self.hbox.addWidget(QtGui.QLabel('Grade Image Display'))         
        self.hbox.addWidget(self.choice_note)
        #self.hbox.addWidget(QtGui.QLabel('Grade Brain Mask')) 
        #self.hbox.addWidget(self.choice_note2)   
        self.hbox.addWidget(self.comment)
        self.hbox.addWidget(self.display_xls)      
        self.vbox.addLayout(self.hbox)
        
         #Image
        self.scene=QtGui.QGraphicsScene()
        self.view=QtGui.QGraphicsView(self.scene)
        self.view.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        
        self.view.wheelEvent = self.wheel_event
        #self.picture_display=QGraphicsPixmapItem()
        #self.scene.addItem(self.picture_display)
        self.hbox2.addWidget(self.view)
        self.create_pre_commmentary()
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
        self.filemenu.addAction(self.action_open_xls)
        self.filtermenu=QtGui.QMenu("Filter")
        #self.filtermenu.setTitle('&Filter')
        self.filtermenu.addAction(self.action_filter)
        self.menuBar().addMenu(self.filemenu)
        self.menuBar().addMenu(self.filtermenu)
        
        
     
    def create_actions(self):
        #Action filemenu
        self.action_open=QtGui.QAction('Open',self)
        self.action_open.triggered.connect(self.on_open)
        self.action_open_xls=QtGui.QAction('Open Xls',self)
        self.action_open_xls.triggered.connect(self.on_open_xls)
        #Action filtermenu
        self.action_filter=QtGui.QAction('Launch filter',self)
        self.action_filter.triggered.connect(self.on_open_filter)


       
       
    def create_pre_commmentary(self):   
        self.group_box=QtGui.QGroupBox("Pre-commentary")
        
        #Debordement
        self.vbox_pre_commentary=QtGui.QVBoxLayout()
        self.label_debordement=QtGui.QLabel("Debordement meninges/sinus")
        self.choice_note_debordement=QtGui.QComboBox()
        self.choice_note_debordement.addItems(['0','1','2'])
        self.layout_debordement=QtGui.QGridLayout()
        self.layout_debordement.addWidget(self.label_debordement,0,0)
        self.layout_debordement.addWidget(self.choice_note_debordement,0,1,QtCore.Qt.AlignRight)
        self.vbox_pre_commentary.addLayout(self.layout_debordement)
           
        #Surface pial surface limit
        self.label_pial=QtGui.QLabel("Limite surface pial")
        self.choice_note_pial=QtGui.QComboBox()
        self.choice_note_pial_items=['-1','0','1']
        self.choice_note_pial.addItems(self.choice_note_pial_items)
        self.choice_note_pial.setCurrentIndex(1)
        self.layout_pial=QtGui.QGridLayout()
        self.layout_pial.addWidget(self.label_pial,0,0)
        self.layout_pial.addWidget(self.choice_note_pial,0,1,QtCore.Qt.AlignRight)
        self.vbox_pre_commentary.addLayout(self.layout_pial)            

        #Cutting HL,HR and cerebellum
        self.label_cutting=QtGui.QLabel("Decoupage HD,HG,cervelet")
        self.choice_note_cutting=QtGui.QComboBox()
        self.choice_note_cutting.addItems(['0','1','2'])
        self.layout_cutting=QtGui.QGridLayout()
        self.layout_cutting.addWidget(self.label_cutting,0,0)
        self.layout_cutting.addWidget(self.choice_note_cutting,0,1,QtCore.Qt.AlignRight)
        self.vbox_pre_commentary.addLayout(self.layout_cutting)        
        
        #Brain_miss
        self.label_brain_miss=QtGui.QLabel("Bouts de cerveau manquant")
        self.choice_note_brain_miss=QtGui.QComboBox()
        self.choice_note_brain_miss.addItems(['0','1','2'])
        self.layout_brain_miss=QtGui.QGridLayout()
        self.layout_brain_miss.addWidget(self.label_brain_miss,0,0)
        self.layout_brain_miss.addWidget(self.choice_note_brain_miss,0,1,QtCore.Qt.AlignRight)
        self.vbox_pre_commentary.addLayout(self.layout_brain_miss) 
        
        self.list_locality=['temporal','frontal','hippocampe','hypersignaux MB','corps calleux','noyaux gris','cervelet']
        for i in range(0,len(self.list_locality)):
            self.check_box_locality[i]=QtGui.QCheckBox(self.list_locality[i])
            self.layout_brain_miss.addWidget(self.check_box_locality[i],i+1,0)
         
        self.group_box.setLayout(self.vbox_pre_commentary)            
        self.hbox2.addWidget(self.group_box)
            
    def set_pre_commmentary(self): 
        self.data.set_marks_debordement(self.pictures_relatif_path[self.index_picture_display],self.choice_note_debordement.currentIndex())
        self.data.set_marks_pial(self.pictures_relatif_path[self.index_picture_display],self.choice_note_pial_items[self.choice_note_pial.currentIndex()])
        self.data.set_marks_cutting(self.pictures_relatif_path[self.index_picture_display],self.choice_note_cutting.currentIndex())
        self.data.set_marks_brain_miss(self.pictures_relatif_path[self.index_picture_display],self.choice_note_brain_miss.currentIndex())
        self.checked_locality=[]
        for i in range(0,len(self.list_locality)):
            if self.check_box_locality[i].isChecked() is True:
                self.checked_locality.append(self.list_locality[i])
        self.data.set_locality(self.pictures_relatif_path[self.index_picture_display],self.checked_locality)        
                


    def resizeEvent(self,resizeEvent):
        if self.data_file_name is not None:
            self.open_image(self.pictures_relatif_path[self.index_picture_display]) 

    def keyPressEvent(self, event):
        if self.data_file_name is not None:
            if event.key() == QtCore.Qt.Key_Left:
                print "Left touch keyboard"
                self.on_prev()
            if event.key() == QtCore.Qt.Key_Right: 
                print "Right touch keyboard"
                self.on_next()
     
   
    def on_next(self):
        print 'on next' 
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            if (self.index_picture_display+1)==len(self.pictures_absolute_path):
                self.index_picture_display=0
            else:
                self.index_picture_display=self.index_picture_display+1    
           
            self.open_image(self.pictures_absolute_path[self.index_picture_display]) 
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])
            #self.find_picture_split()
            self.check_data()  
        
    def on_prev(self):
        print 'on prev'   
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            if (self.index_picture_display-1)==-1:
                self.index_picture_display=len(self.pictures_absolute_path)-1
            else:
                self.index_picture_display=self.index_picture_display-1
             
            self.open_image(self.pictures_absolute_path[self.index_picture_display])     
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])             
            #self.find_picture_split()
            self.check_data() 
            
    def on_marks_change(self):
        print 'marks change'
        if self.data_file_name is not None:
            #if self.choice_note2.isEnabled() is True:
                #self.data.set_double_note(self.pictures_absolute_path[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
            #else:
            self.data.set_simple_note(self.pictures_relatif_path[self.index_picture_display],self.choice_note.currentIndex())
        self.setFocusPolicy(QtCore.Qt.StrongFocus)               
                               
    #def on_marks_change2(self):
        #print 'brain marks change'
        #if self.data_file_name is not None:
                #self.data.set_double_note(self.pictures_absolute_path[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        
    def on_comment_change(self):
        print 'comment change'
        if self.data_file_name is not None:
            self.text_in_comment=self.comment.toPlainText()
            self.text_in_comment=self.comment.toPlainText().toUtf8()
            self.data.set_comment(self.pictures_relatif_path[self.index_picture_display],self.text_in_comment)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

            
                
    def on_open(self):
        print 'in open'      
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file','',self.tr("Images Files (*.png);;(*jpg)"))
        if fname != '':
            #self.picture_display.setPixmap(QPixmap(fname))
            self.open_image(fname)
            self.dirname=os.path.dirname(str(fname))
            self.data_file_name = os.path.join(self.dirname,'data.csv')
            results = [os.path.join(self.dirname,each) for each in os.listdir(self.dirname) if each.endswith('.png')]
            results.sort()
            print self.dirname
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
                         
        if self.data_file_name is not None:    
         #Display image       
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])
            self.data.load(self.data_file_name)
            #self.find_picture_split()
            self.check_data()
            self.statusBar().showMessage(self.pictures_absolute_path[self.index_picture_display])             

        #Get back focus 
        self.setFocusPolicy(QtCore.Qt.StrongFocus)    
            
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

            
            
    def on_open_xls (self):
        print 'on open xls - On working'    
        #Get back focus 
        self.setFocusPolicy(QtCore.Qt.StrongFocus)        
            
            
    def on_open_filter(self):
        print 'on open filter'
        if self.data_file_name is not None:
            #try:
                #from create_bdd import CreateBDD  
                #from filter_window import Filter
                #self.filter_window=Filter(self.dirname)        
                #self.data.save(self.data_file_name,self.pictures_relatif_path)  
                #setattr(self.filter_window,'dirname_snap',self.dirname) 
                #setattr(self.filter_window,'bdd',CreateBDD.get_instance())
                #self.filter_window.choice_studies.addItems(self.filter_window.bdd.studies())

            #except ImportError:
            print 'NO USE DATABASE FOR FILTER'
            from filter_window_basic import FilterBasic
            self.filter_window=FilterBasic(self.dirname)
            self.data.save(self.data_file_name,self.pictures_relatif_path)  
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
        if self.data.is_recorded(self.pictures_relatif_path[self.index_picture_display])==0:
            self.data.add_filename(self.pictures_relatif_path[self.index_picture_display])
            self.data.save(self.data_file_name,self.pictures_relatif_path)  
           
            #if self.choice_note2.isEnabled() is True:
                #self.choice_note.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],False))
                #self.choice_note2.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],True))
            #else:
        self.choice_note.setCurrentIndex(self.data.get_simple_note(self.pictures_relatif_path[self.index_picture_display]))                        
        #self.comment.setPlainText(self.data.get_comment(self.pictures_absolute_path[self.index_picture_display]))
        self.text_in_comment=QtCore.QString.fromUtf8(self.data.get_comment(self.pictures_relatif_path[self.index_picture_display]))
        self.choice_note_debordement.setCurrentIndex(self.data.get_marks_debordement(self.pictures_relatif_path[self.index_picture_display]))     
        self.choice_note_pial.setCurrentIndex(self.data.get_marks_pial(self.pictures_relatif_path[self.index_picture_display])+1)                 
        self.choice_note_cutting.setCurrentIndex(self.data.get_marks_cutting(self.pictures_relatif_path[self.index_picture_display]))      
        self.choice_note_brain_miss.setCurrentIndex(self.data.get_marks_brain_miss(self.pictures_relatif_path[self.index_picture_display]))     

        self.list_get_locality=self.data.get_locality(self.pictures_relatif_path[self.index_picture_display]) 
        for i in range(0,len(self.list_locality)):
            if self.list_locality[i] in self.list_get_locality:
                self.check_box_locality[i].setCheckState(QtCore.Qt.Checked)
            else:
                self.check_box_locality[i].setCheckState(QtCore.Qt.Unchecked)
                    

        
        #else:
            ##self.text_in_comment=QtCore.QString.fromUtf8(self.data.get_comment(self.pictures_absolute_path[self.index_picture_display]))
            ##if self.choice_note2.isEnabled() is True:
                ##self.choice_note.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],False))
                ##self.choice_note2.setCurrentIndex(self.data.get_double_note(self.pictures_absolute_path[self.index_picture_display],True))
            ##else:   
            #self.choice_note.setCurrentIndex(self.data.get_simple_note(self.pictures_absolute_path[self.index_picture_display]))   
            #self.comment.setPlainText(unicode(self.text_in_comment))
            
            
            
            
            #self.data.save(self.data_file_name,self.pictures_absolute_path)    
            
            
    #def find_picture_split(self):
        #word_to_find='split'
        #if word_to_find in self.pictures_absolute_path[self.index_picture_display]:
            #self.choice_note2.setEnabled(True)
        #else:
            #self.choice_note2.setEnabled(False)



    def closeEvent(self, event): 
        if self.data_file_name is not None:
            self.set_pre_commmentary()
            self.data.save(self.data_file_name,self.pictures_relatif_path)    

