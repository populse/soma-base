# -*- coding: utf-8 -*-
from soma.qt_gui.qt_backend import QtCore, QtGui, getOpenFileName, \
    getExistingDirectory
from soma.qt4gui.api import TimeredQLineEdit

class FileSelectionWidget(QtGui.QWidget):
    ''' A widget with a label and file name field, and a button to select the
    file name.

    Parameters
    ----------
    selection_type: str
        select between file ('File') or directory ('Directory') mode
    label: str
        label displayed on the left
    label_h: int
        horizontal size of the label
    label_v: int
        vertical size of the label
    '''
    def __init__(self, selection_type, label, label_h=120, label_v=40):
        super(FileSelectionWidget, self).__init__()
        #Add a selection file in the constructor
        self.label = QtGui.QLabel(label)
        self.label.setFixedSize(label_h, label_v)
        self.button = QtGui.QPushButton('...')
        self.button.setFixedSize(30, 30)
        self.lay = QtGui.QHBoxLayout()
        self.selection_type = selection_type
        self.fname = None
        self.lineedit = TimeredQLineEdit()
        self.button.clicked.connect(self._on_button)
        self.connect(self.lineedit,
            QtCore.SIGNAL('userModification'), self._on_lineedit)
        self.lay.addWidget(self.label)
        self.lay.addWidget(self.lineedit)
        self.lay.addWidget(self.button)
        self.setLayout(self.lay)


    def _on_button(self):
        if self.selection_type == 'File':
            self.fname = getOpenFileName(self, 'Select file', '', '')
        elif self.selection_type == 'Directory':
            self.fname = getExistingDirectory( self, 'Select Directory', '',
                '')

        #check if something if fname
        if self.fname != '':
            self.lineedit.setText(self.fname)


    def _on_lineedit(self, text):
        self.fname = text
        self.emit(QtCore.SIGNAL("editChanged(const QString & )"), text)
