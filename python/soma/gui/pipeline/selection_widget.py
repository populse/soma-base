# -*- coding: utf-8 -*-
from soma.qt_gui.qt_backend import QtCore, QtGui
from soma.qt4gui.api import TimeredQLineEdit

class Selection(QtGui.QWidget):
    def __init__(self,selection_type,label,label_h=120,label_v=40):
	super(Selection, self).__init__()
	#Add a selection file in the constructor
        self.label=QtGui.QLabel(label)
        #self.label.setAlignment(QtCore.Qt.AlignHCenter)
        self.label.setFixedSize(label_h,label_v)
        self.button=QtGui.QPushButton('...')
	self.button.setFixedSize(30,30)
        self.lay=QtGui.QHBoxLayout()
	self.selection_type=selection_type
        self.fname=None
        self.lineedit=TimeredQLineEdit()
        self.button.clicked.connect(self.on_button)
        #self.connect(self.lineedit, QtCore.SIGNAL("textChanged(QString)"),self.on_lineedit)
	self.connect(self.lineedit, QtCore.SIGNAL('userModification'),self.on_lineedit)
	self.lay.addWidget(self.label)
	self.lay.addWidget(self.lineedit)
	self.lay.addWidget(self.button)
	self.setLayout(self.lay)


    def on_button(self):
	if self.selection_type=='File':
            self.fname=QtGui.QFileDialog.getOpenFileName(self, 'Select file', '/home', '')
	elif self.selection_type=='Directory':
             self.fname=QtGui.QFileDialog.getExistingDirectory(self, 'Select Directory','/home','')
	         
	#check if something if fname
	if self.fname !='':
	    self.lineedit.setText(self.fname)


    def on_lineedit(self,text):
        self.fname=text
	self.emit( QtCore.SIGNAL("editChanged(const QString & )"), text)
