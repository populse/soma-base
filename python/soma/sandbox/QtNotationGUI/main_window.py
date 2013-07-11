# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import os
import read_csv
from filter_window import MyFilter

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.data=read_csv.Data()   
        self.data_file_name= None
        self.dirname=None
        self.pictures_in_directory=None
        self.index_picture_display=None
        self.image_brain=None
        self.filter_window=MyFilter(self.dirname)
        #self.filter_window.setParent(self)
        
        self.create_actions()
        self.create_gui()
        self.create_menu()

    def create_gui(self):
        self.MainWidget=QtGui.QWidget()
        self.resize(800,600)
        self.vbox = QtGui.QVBoxLayout()
        self.hbox = QtGui.QHBoxLayout()        
        self.button_prev=QtGui.QPushButton('<')
        self.button_next=QtGui.QPushButton('>') 
        self.button_prev.clicked.connect(self.on_prev)
        self.button_next.clicked.connect(self.on_next)
        self.choice_note=QtGui.QComboBox()
        self.choice_note.addItems(['0','1','2','3','4','5'])
        self.choice_note.activated.connect(self.on_marks_change)
        self.choice_note2=QtGui.QComboBox()
        self.choice_note2.addItems(['0','1','2','3','4','5'])
        self.choice_note2.setEnabled(False)
        self.choice_note2.currentIndexChanged.connect(self.on_marks_change2)
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
        self.hbox.addWidget(QtGui.QLabel('Grade Brain Mask')) 
        self.hbox.addWidget(self.choice_note2)   
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
        self.vbox.addWidget(self.view)
        self.mousePressEvent = self.back_focus
        self.MainWidget.setLayout(self.vbox)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCentralWidget(self.MainWidget)
      
    def back_focus(self,event):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  

    def create_menu(self):
        menubar = self.menuBar()
        filemenu=menubar.addMenu('&File')
        filemenu.addAction(self.action_open)
        filemenu.addAction(self.action_open_xls)
        filtermenu=menubar.addMenu('&Filter')
        filtermenu.addAction(self.action_filter)

     
    def create_actions(self):
        #Action filemenu
        self.action_open=QtGui.QAction('Open',self)
        self.action_open.triggered.connect(self.on_open)
        self.action_open_xls=QtGui.QAction('Open Xls',self)
        self.action_open_xls.triggered.connect(self.on_open_xls)
        #Action filtermenu
        self.action_filter=QtGui.QAction('Launch filter',self)
        self.action_filter.triggered.connect(self.on_open_filter)


    def resizeEvent(self,resizeEvent):
        if self.data_file_name is not None:
            self.open_image(self.pictures_in_directory[self.index_picture_display]) 

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
            if (self.index_picture_display+1)==len(self.pictures_in_directory):
                self.index_picture_display=0
            else:
                self.index_picture_display=self.index_picture_display+1    
           
            self.open_image(self.pictures_in_directory[self.index_picture_display]) 
            self.statusBar().showMessage(self.pictures_in_directory[self.index_picture_display])
            self.find_picture_split()
            self.check_data()  
        
    def on_prev(self):
        print 'on prev'   
        if self.data_file_name is not None:
            if (self.index_picture_display-1)==-1:
                self.index_picture_display=len(self.pictures_in_directory)-1
            else:
                self.index_picture_display=self.index_picture_display-1
             
            self.open_image(self.pictures_in_directory[self.index_picture_display])     
            self.statusBar().showMessage(self.pictures_in_directory[self.index_picture_display])             
            self.find_picture_split()
            self.check_data() 
            
    def on_marks_change(self):
        print 'marks change'
        if self.data_file_name is not None:
            if self.choice_note2.isEnabled() is True:
                self.data.set_double_note(self.pictures_in_directory[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
            else:
                self.data.set_simple_note(self.pictures_in_directory[self.index_picture_display],self.choice_note.currentIndex())
        self.setFocusPolicy(QtCore.Qt.StrongFocus)               
                               
    def on_marks_change2(self):
        print 'brain marks change'
        if self.data_file_name is not None:
                self.data.set_double_note(self.pictures_in_directory[self.index_picture_display],self.choice_note.currentIndex(),self.choice_note2.currentIndex())
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        
    def on_comment_change(self):
        print 'comment change'
        if self.data_file_name is not None:
            #print self.comment.toPlainText()
            #print str(self.comment.toPlainText())
            #print self.comment.toPlainText().toUtf8()
            #print type(self.comment.toPlainText()),self.comment.toPlainText()
            self.text_in_comment=self.comment.toPlainText()
            #print type(self.text_in_comment),self.text_in_comment
            self.text_in_comment=self.comment.toPlainText().toUtf8()
            #print type(self.text_in_comment),self.text_in_comment
            self.data.set_comment(self.pictures_in_directory[self.index_picture_display],self.text_in_comment)
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
            self.pictures_in_directory=results
            i=-1
            for picture in self.pictures_in_directory:
                i=i+1
                if picture==fname:
                    self.index_picture_display=i
                    break        
                         
        if self.data_file_name is not None:    
         #Display image       
            self.statusBar().showMessage(self.pictures_in_directory[self.index_picture_display])
            self.data.load(self.data_file_name)
            self.find_picture_split()
            self.check_data()
            self.statusBar().showMessage(self.pictures_in_directory[self.index_picture_display])             

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
            self.data.save(self.data_file_name,self.pictures_in_directory)  
            setattr(self.filter_window,'dirname_snap',self.dirname) 
            self.filter_window.open()
        else:
            print 'PLEASE OPEN AN IMAGE BEFORE USING FILTER'          
    
        #Get back focus 
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)      
            
    def check_brain_exist(self):       
        word_to_find='brain'
        self.image_brain=self.pictures_in_directory[self.index_picture_display].replace('split','brain')
        element=[]
        element+= [image for image in self.pictures_in_directory if image==self.image_brain]
        if not element:
            return 0
        else:
            return 1        
            
    def check_data(self):
        if self.data.is_recorded(self.pictures_in_directory[self.index_picture_display])==0:
            self.data.add_filename(self.pictures_in_directory[self.index_picture_display])
            self.data.save(self.data_file_name,self.pictures_in_directory)          
            if self.choice_note2.isEnabled() is True:
                self.choice_note.setCurrentIndex(self.data.get_double_note(self.pictures_in_directory[self.index_picture_display],False))
                self.choice_note2.setCurrentIndex(self.data.get_double_note(self.pictures_in_directory[self.index_picture_display],True))
            else:
                self.choice_note.setCurrentIndex(self.data.get_simple_note(self.pictures_in_directory[self.index_picture_display]))                        
            self.comment.setPlainText(self.data.get_comment(self.pictures_in_directory[self.index_picture_display]))
        
        else:
            self.text_in_comment=QtCore.QString.fromUtf8(self.data.get_comment(self.pictures_in_directory[self.index_picture_display]))
            if self.choice_note2.isEnabled() is True:
                self.choice_note.setCurrentIndex(self.data.get_double_note(self.pictures_in_directory[self.index_picture_display],False))
                self.choice_note2.setCurrentIndex(self.data.get_double_note(self.pictures_in_directory[self.index_picture_display],True))
            else:   
                self.choice_note.setCurrentIndex(self.data.get_simple_note(self.pictures_in_directory[self.index_picture_display]))   
            self.comment.setPlainText(unicode(self.text_in_comment))
            self.data.save(self.data_file_name,self.pictures_in_directory)    
            
            
    def find_picture_split(self):
        word_to_find='split'
        if word_to_find in self.pictures_in_directory[self.index_picture_display]:
            self.choice_note2.setEnabled(True)
        else:
            self.choice_note2.setEnabled(False)



    def closeEvent(self, event): 
        self.data.save(self.data_file_name,self.pictures_in_directory)    

