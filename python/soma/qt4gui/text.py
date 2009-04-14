#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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

from PyQt4 import QtGui, QtCore

class TextEditWithSearch(QtGui.QTextEdit):
  """
  A QTextEdit with search feature to search a piece of text in the QTextEdit content.
  """
  def __init__(self, *args):
    super(TextEditWithSearch, self).__init__(*args)
    self.searchText=""
  
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
  
  def customMenu(self):
    menu=self.createStandardContextMenu()
    menu.addSeparator()
    menu.addAction("Find", self.search, QtGui.QKeySequence.Find ) # Key_Control
    menu.addAction("Find next", self.searchNext, QtGui.QKeySequence.FindNext)
    return menu
  
  def contextMenuEvent(self, event):
    menu=self.customMenu()
    menu.exec_(event.globalPos());
  
  def search(self):
    (res, ok)=QtGui.QInputDialog.getText(self, "Find", "Text to find :", QtGui.QLineEdit.Normal, self.searchText)
    if ok:
      self.searchText=res
    if self.searchText and ok:
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