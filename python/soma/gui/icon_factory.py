# -*- coding: utf-8 -*-
from soma.qt_gui.qt_backend import QtGui, QtCore
import os

ICON_PATH=os.path.join(os.path.dirname( __file__ ),'icons')


class IconFactory():
    """Class for the differents icon of the GUI"""  
    
    # QPixmap instance cannot be build before a QApplication is being created.
    # (it simply exits the program). But for documentation with epydoc, all
    # modules are loaded without C{QApplication}. Therefore, the creation of
    # the following two static QPixmap instances has been put in __init__.

    _imageExpand = None
    _imageCollapse = None
    _imageViewer=None
    _imageBrowseInput=None
    _imageBrowseOutput=None  
    _imageBrowseDir=None
    _valueModified=None
    
    def __init__(self):

        if IconFactory._imageExpand is None:
            IconFactory._imageExpand = QtGui.QPixmap()
            IconFactory._imageExpand.loadFromData( \
                "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
                "\x49\x48\x44\x52\x00\x00\x00\x09\x00\x00\x00\x0b" \
                "\x08\x06\x00\x00\x00\xad\x59\xa7\x1b\x00\x00\x00" \
                "\x4f\x49\x44\x41\x54\x18\x95\x63\x7c\xf6\xec\x19" \
                "\x03\x21\xc0\x04\x63\x48\x49\x49\xfd\x47\x96\x40" \
                "\xe1\x43\x4d\xfa\x8f\x0b\x3f\x7b\xf6\x0c\x62\xd2" \
                "\xb3\x67\xcf\x18\xb1\x59\x03\x13\x67\x42\x17\xc0" \
                "\xc6\x67\xc2\x26\x81\xae\x81\x91\x24\xdf\xe1\x03" \
                "\x2c\x30\xc6\xdd\xbb\x77\xff\xa3\x4b\x2a\x2b\x2b" \
                "\xa3\x3a\x1c\x1f\x20\xca\x4d\x00\x23\x1d\x2b\x53" \
                "\x5e\xdc\x34\x20\x00\x00\x00\x00\x49\x45\x4e\x44" \
                    "\xae\x42\x60\x82"
                )
        if IconFactory._imageCollapse is None:
            IconFactory._imageCollapse = QtGui.QPixmap()
            IconFactory._imageCollapse.loadFromData( \
                "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
                "\x49\x48\x44\x52\x00\x00\x00\x09\x00\x00\x00\x0b" \
                "\x08\x06\x00\x00\x00\xad\x59\xa7\x1b\x00\x00\x00" \
                "\x52\x49\x44\x41\x54\x18\x95\x8d\x90\xbb\x0d\x00" \
                "\x31\x08\x43\x0d\xba\x29\xdc\xb2\xff\x48\xb4\x5e" \
                "\x23\x57\xe5\x14\x91\x9c\x02\x15\x9f\x27\x1b\x30" \
                "\x49\xb8\xc5\x33\x93\xcc\x1c\x75\x18\x11\x06\x00" \
                "\x7e\x95\x01\x60\x1d\xbb\x96\xd2\x06\x91\xdc\x76" \
                "\xf3\x13\x50\x41\xaf\xc0\xa9\xf6\x3f\x8b\xb5\xff" \
                "\x5d\x47\x72\x48\xb2\x15\x98\x75\xeb\x05\x2f\xc0" \
                "\x1f\x1f\xf8\x34\x49\xac\xa1\x00\x00\x00\x00\x49" \
                "\x45\x4e\x44\xae\x42\x60\x82"
                )
		
	if IconFactory._imageBrowseDir is None:
            IconFactory._imageBrowseDir = QtGui.QPixmap(os.path.join(ICON_PATH,'browse.png'))    
	      
        if IconFactory._imageBrowseInput is None:
            IconFactory._imageBrowseInput = QtGui.QPixmap(os.path.join(ICON_PATH,'database_read.png'))   


        if IconFactory._imageBrowseOutput is None:
            IconFactory._imageBrowseOutput = QtGui.QPixmap(os.path.join(ICON_PATH,'database_write.png'))      


        if IconFactory._imageViewer is None:
            IconFactory._imageViewer = QtGui.QPixmap(os.path.join(ICON_PATH,'eye.png'))
            
            
        if IconFactory._valueModified is None:
            IconFactory._valueModified = QtGui.QPixmap(os.path.join(ICON_PATH,'icons/modified.png'))


