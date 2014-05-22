# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.

'''

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.qt_gui.qt_backend import QtWebKit

class TextEditWithSearch(QtGui.QTextEdit):
  """
  A QTextEdit with search feature to search a piece of text in the QTextEdit content.
  """
  def __init__(self, *args):
    super(TextEditWithSearch, self).__init__(*args)
    self.searchText=""
  
  def keyPressEvent(self, keyEvent):
    if (keyEvent.matches(QtGui.QKeySequence.Copy)):
      self.copy()
    elif (keyEvent.matches(QtGui.QKeySequence.SelectAll)):
      self.selectAll()
    elif (keyEvent.matches(QtGui.QKeySequence.Find)):
      self.search()
    elif (keyEvent.matches(QtGui.QKeySequence.FindNext) ):
      self.searchNext()
    else:
      QtGui.QAbstractScrollArea.keyPressEvent(self, keyEvent)
       
  def customMenu(self):
    menu=self.createStandardContextMenu()
    menu.addSeparator()
    menu.addAction("Find", self.search, QtGui.QKeySequence.Find) # Key_Control
    menu.addAction("Find next", self.searchNext, QtGui.QKeySequence.FindNext)
    return menu
  
  def contextMenuEvent(self, event):
    menu=self.customMenu()
    menu.exec_(event.globalPos())
  
  def search(self):
    (res, ok)=QtGui.QInputDialog.getText(self, "Find", "Text to find :", QtGui.QLineEdit.Normal, self.searchText)
    if ok:
      self.searchText=res
    if self.searchText and ok:
      self.moveCursor(QtGui.QTextCursor.Start)
      self.find(self.searchText) # not case sensitive, not whole word, forward
      
  def searchNext(self):
    if self.searchText:
      self.find(self.searchText) # not case sensitive, not whole word


class TextBrowserWithSearch(QtGui.QTextBrowser):
  """
  A QTextBrowser with search feature to search a piece of text in the QTextBrowser content.
  """
  def __init__(self, *args):
    super(TextBrowserWithSearch, self).__init__(*args)
    self.searchText=""

  def keyPressEvent(self, keyEvent):
    if (keyEvent.matches(QtGui.QKeySequence.Find)):
      self.search()
    elif (keyEvent.matches(QtGui.QKeySequence.FindNext) ):
      self.searchNext()
    elif (keyEvent.matches(QtGui.QKeySequence.Refresh) ):
      self.reload()
    else:
      QtGui.QTextBrowser.keyPressEvent(self, keyEvent)
  
  def customMenu(self):
    menu=self.createStandardContextMenu()
    menu.addSeparator()
    menu.addAction("Find", self.search, QtGui.QKeySequence.Find ) # Key_Control
    menu.addAction("Find next", self.searchNext, QtGui.QKeySequence.FindNext)
    menu.addAction("Reload", self.reload, QtGui.QKeySequence.Refresh)
    return menu
  
  def contextMenuEvent(self, event):
    menu=self.customMenu()
    menu.exec_(event.globalPos());
  
  def search(self):
    (res, ok)=QtGui.QInputDialog.getText(self, "Find", "Text to find :", QtGui.QLineEdit.Normal, self.searchText)
    if ok:
      self.searchText=res
    if self.searchText and ok:
      self.moveCursor(QtGui.QTextCursor.Start)
      self.find(self.searchText) # not case sensitive, not whole word, forward
      
  def searchNext(self):
    if self.searchText:
      self.find(self.searchText) # not case sensitive, not whole word

  def setSource(self, textUrl):
    """
    @type textUrl : string
    @param textUrl : l'url du fichier source
    """
    QtGui.QTextBrowser.setSource(self, QtCore.QUrl(textUrl))


class WebBrowserWithSearch(QtWebKit.QWebView):
  """
  A QWebView with search feature to search a piece of text in the QWebView content.
  """
  def __init__(self, *args):
    super(QtWebKit.QWebView, self).__init__(*args)
    self.searchText=""
    self.findAction = QtGui.QAction( _t_( 'Find' ), self )
    self.findAction.setShortcut( QtGui.QKeySequence.Find )
    self.connect( self.findAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.search )
    self.findNextAction = QtGui.QAction( _t_( 'Find next' ), self )
    self.findNextAction.setShortcut( QtGui.QKeySequence.FindNext )
    self.connect( self.findNextAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.searchNext )
    self.findPreviousAction = QtGui.QAction( _t_( 'Find previous' ), self )
    self.findPreviousAction.setShortcut( QtGui.QKeySequence.FindPrevious )
    self.connect( self.findPreviousAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.searchPrevious )
    self.zoomInAction = QtGui.QAction( _t_( 'Zoom in' ), self )
    self.zoomInAction.setShortcut( QtCore.Qt.CTRL + QtCore.Qt.Key_Plus )
    self.connect( self.zoomInAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.zoomIn )
    self.zoomOutAction = QtGui.QAction( _t_( 'Zoom out' ), self )
    self.zoomOutAction.setShortcut( QtCore.Qt.CTRL + QtCore.Qt.Key_Minus )
    self.connect( self.zoomOutAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.zoomOut )
    self.zoomOneAction = QtGui.QAction( _t_( 'Reset zoom' ), self )
    self.zoomOneAction.setShortcut( QtCore.Qt.CTRL + QtCore.Qt.Key_Equal )
    self.connect( self.zoomOneAction, QtCore.SIGNAL( 'triggered(bool)' ),
      self.zoomOne )
    self.addAction( self.findAction )
    self.addAction( self.findNextAction )
    self.addAction( self.findPreviousAction )
    self.addAction( self.zoomInAction )
    self.addAction( self.zoomOutAction )
    self.addAction( self.zoomOneAction )

  def customMenu(self):
    menu=QtGui.QMenu(self)
    menu.addAction( self.pageAction( QtWebKit.QWebPage.Back ) )
    menu.addAction( self.pageAction( QtWebKit.QWebPage.Forward ) )
    ra = self.pageAction( QtWebKit.QWebPage.Reload )
    if ra.shortcut() != QtGui.QKeySequence.Refresh:
      ra.setShortcut( QtGui.QKeySequence.Refresh )
    menu.addAction( ra )
    menu.addAction( self.pageAction( QtWebKit.QWebPage.Stop ) )
    menu.addSeparator()
    menu.addAction( self.findAction )
    menu.addAction( self.findNextAction )
    menu.addAction( self.findPreviousAction )
    menu.addSeparator()
    menu.addAction( self.zoomInAction )
    menu.addAction( self.zoomOutAction )
    menu.addAction( self.zoomOneAction )
    return menu

  def contextMenuEvent(self, event):
    menu=self.customMenu()
    menu.exec_(event.globalPos());

  def search(self, void):
    text = self.selectedText()
    if not text:
      text = self.searchText
    (res, ok)=QtGui.QInputDialog.getText(self, _t_( "Find" ), _t_( "Text to find :" ), QtGui.QLineEdit.Normal, text )
    if ok:
      self.searchText=res
    if self.searchText and ok:
      self.findText( self.searchText )

  def searchNext(self, void):
    if self.searchText:
      # not case sensitive, not whole word
      self.findText(self.searchText, QtWebKit.QWebPage.FindWrapsAroundDocument )

  def searchPrevious(self, void):
    if self.searchText:
      self.findText(self.searchText,
        QtWebKit.QWebPage.FindFlags( QtWebKit.QWebPage.FindBackward \
        + QtWebKit.QWebPage.FindWrapsAroundDocument ) )

  def setSource(self, textUrl):
    self.load(QtCore.QUrl(textUrl))

  def zoomIn( self, void ):
    self.setZoomFactor( self.zoomFactor() * 1.1 )
    #self.setTextSizeMultiplier( self.textSizeMultiplier() * 1.1 )

  def zoomOut( self, void ):
    self.setZoomFactor( self.zoomFactor() / 1.1 )
    #self.setTextSizeMultiplier( self.textSizeMultiplier() / 1.1 )

  def zoomOne( self, void ):
    self.setZoomFactor( 1. )
    self.setTextSizeMultiplier( 1. )


