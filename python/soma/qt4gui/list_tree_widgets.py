# -*- coding: iso-8859-1 -*-

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
This module provides widgets L{EditableTreeWidget} L{TreeListWidget} and L{ObservableListWidget} for L{EditableTree}, L{ObservableSortedDictionary of EditableTree} and L{ObservableList} model objects.
These widgets register callback methods to update when the model changes.
They provide user interaction to modify the underlying model (drag&drop, contextual menu...)

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import os
from StringIO import StringIO
from soma.qt_gui.qt_backend.QtGui import QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QPixmap, QDrag, QMenu, QPainter, QPen, QCursor, QSizePolicy, QIcon, qApp, QKeyEvent, QApplication
from soma.qt_gui.qt_backend.QtCore import Qt, QEvent, QMimeData, QObject, QPoint, QRect, QSize, QTimer, SIGNAL
import copy
from soma.notification import ObservableList, EditableTree
from soma.minf.api import defaultReducer, createMinfWriter, iterateMinf, minfFormat
from soma.wip.application.api import findIconFile
from soma.qt4gui.api import defaultIconSize

#----------------------------------------------------------------------------
class EditableTreeWidget(QTreeWidget):
  """A widget to represent a tree represented by an EditableTree object.
  The tree can be modifiable by manipulating items in the widget :
    - add new item
    - copy an item in a branch
    - move an item in a branch
    - delete an item

  It is possible to copy items from one tree widget to another.

  This component is created with a EditableTree object which is the model.

  The graphic component has a reference on the model and methods to control events.
  It registers a callback method on the model notifier.
  On drag&drop of an item in another, the model is updated and notify all its listeners,
  so the view is updated via updateContent method.

  The widgets treats some events :
    - drag&drop events : to copy or move items
    - key events : del to remove an item, shift to set move mode
    - context menu request event: show a popup menu to create new item
    - rename event on modifiable items.

  All items icon are resized to have the same size.

  Inner classes :
    - Item
    - Branch
    - Leaf

  @type MARGIN: int
  @cvar MARGIN: margin width in pixel around items

  @type model: EditableTree
  @ivar model: The tree which this widget is the representation
  @type controller: EditableTreeController
  @ivar controller: the controller is called to proceed model's changes on events.
  @type draggedItems: list of EditableTree.Item
  @ivar draggedItems: list of currently dragged items. Items can come from current tree or from another tree (so it is a copy of the other tree's item). 
  @type draggedItemsParent: list of EditableTree.Item
  @ivar draggedItemsParent: list of currently dragged items' parents (if they are in current tree). Usefull for delete and move functionalities.
  @type dropOn: EditableTree or Item
  @ivar dropOn: draggedItem is currently on this container
  @type dropAfter: Item
  @ivar dropAfter: draggedItem is currently after this item
  @type dropBefore: Item
  @ivar dropBefore: draggedItem is currently before this item
  @type popupMenu: QPopupMenu
  @ivar popupMenu: contextual menu shown on mouse right click
  @type contextMenuTarget: EdtiableTree.Item or EditableTree
  @ivar contextMenuTarget: item on which a context menu is opened
  """
  # margin in pixel around the items
  # it is used for the highlighting of the dropzones
  MARGIN=3

  def __init__(self, treeModel, parent=None, iconSize=defaultIconSize):
    """
    @type treeModel: EditableTree
    @param treeModel: the tree which current widget represents.
    @type parent:QWidget
    @param parent: parent of this widget
    @type iconSize: couple of integers or None
    @param iconSize: force items icon resizing.
    """
    QTreeWidget.__init__( self, parent)
    self.setColumnCount(1)
    self.setColumnWidth(0, self.width())
    self.setRootIsDecorated(True)
    #self.setItemMargin(self.MARGIN)
    #self.setSortingEnabled(False) # disable sort
    self.setSizePolicy( QSizePolicy( QSizePolicy.Preferred, QSizePolicy.Preferred ) )
    self.setIconSize(QSize(*iconSize))
    self.iconDim=iconSize
    # enable several items selection using ctrl and shift keys.
    self.setSelectionMode(QTreeWidget.ExtendedSelection)
    self.setAcceptDrops(True)
    # draggedItems attribute stores the items which are currently dragged
    self.draggedItems=[]
    self.draggedItemParent=[] # and their parents in current tree
    self.dragStartPosition=0
    # current drop zones (used in drawContentsOffset to highlight current dropzone)
    self.dropOn=None # dragged item will be dropped in this item's children
    self.dropAfter=None # dragged item will be dropped after this item (sibling)
    self.dropBefore=None # dragged item will be dropped before this item
    # Popup Menu
    self.popupMenu = QMenu(self)
    self.popupMenu.addAction( "New",  self.menuNewItemEvent )
    self.contextMenuTarget=None
    self.setContextMenuPolicy(Qt.CustomContextMenu)
    # keep a reference to the model for control event and register a listener to be aware of changes
    self.setModel(treeModel)
    
    self.connect(self, SIGNAL("itemChanged( QTreeWidgetItem *, int )"), self.itemRenamed)
    self.connect(self, SIGNAL( 'customContextMenuRequested ( const QPoint & )'), self.openContextMenu)

  def setModel(self, m):
    """Construct the children of the tree reading the model given.
    A listener is added to the model, so when the model change, the method self.updateContents
    is automatically called.
    """
    self.clear()
    self.model=m
    self.controller=EditableTreeController(m)
    if m!=None:
      self.setWindowTitle(m.name)
      self.setHeaderLabel(m.name)
      self.setAcceptDrops(m.modifiable)
      self.model.addListener(self.updateContent)
      self.model.onAttributeChange("name", self.updateName)
      # create child items with data in the tree model
      lastChild=None
      for item in self.model.values():
        if item.isLeaf(): # append item to keep the same order as in the model
          lastChild=EditableTreeWidget.Leaf(self, item, lastChild, self.iconDim)
        else: 
          lastChild=EditableTreeWidget.Branch(self, item, lastChild, self.iconDim)
  
  def itemRenamed(self, item, col):
    if item is not None and hasattr(item, "okRename"):
      item.okRename(col)
    
  def getChild(self, n):
    """Return the nth child item
    If n<=0 return the first child, if n>=nb children, return the last child
    @rtype: EditableTreeWidget.Item
    """
    if n<=0:
      n=0
    else:
      nbItems=self.topLevelItemCount()
      if n>=nbItems:
        n=nbItems-1
    return self.topLevelItem(n)

  def getLastChild(self):
    """Return the last child item.
    @rtype: EditableTreeWidget.Item
    """
    return self.topLevelItem(self.topLevelItemCount()-1)

  def toContentsPoint(self, point):
    """Translates coordinates in the frame in coordinates in the content of the list (without header).
    @rtype: QPoint"""
    #viewportPoint=self.contentsToViewport(point) to get the item at position we need the position in the entire list not in the visible content (viewport)
    return point # - QPoint(0, self.header().height())
  # headerItem().sizeHint().height() ?

  # already implemented in QTreeWidget
  #def selectedItems(self):
    #"""
    #Gets items that are currently selected in the listview (as we are in extended selection mode).
    
    #@rtype: list of EditableTreeWidget.Item
    #@return: items currently selected
    #"""
    #items=[]
    #it = QListViewItemIterator(self, QListViewItemIterator.Selected)
    #while it.current() :
        #items.append( it.current() )
        #it+=1
    #return items
    
  #------ Drag&Drop ------
  def mousePressEvent(self, event):
    if (event.button() == Qt.LeftButton):
      self.dragStartPosition = QPoint(event.pos())
    QTreeWidget.mousePressEvent(self, event)
    
  def mouseMoveEvent(self, event):
    """
    The QDrag object is shown during the drag.
    This method is called when the mouse moves, this can be the beginning of a drag if the left button is clicked and the distance between the current position and the dragStartPosition is sufficient.
    draggedItems attribute is set with selected item's model.
    It constructs a minf (xml) representation of drag objects which will be provided to the target drop zone.
    """
    if (not (event.buttons() & Qt.LeftButton)):
      return
    if ((event.pos() - self.dragStartPosition).manhattanLength()
          < QApplication.startDragDistance()):
      return
    
    items=self.selectedItems()
    # keep a reference to the current dragged item
    d=None
    if items != []:
      self.draggedItems=[]
      self.draggedItemsParent=[]
      for item in items:
        self.draggedItems.append(item.model)
        self.draggedItemsParent.append(item.container().model)
      #create a string containing the minf representation of items
      itemMinfBuf=StringIO()
      # find minf format to use for item's class
      firstItem=items[0].model
      reducer = defaultReducer( firstItem ) # supposing that all items needs the same reducer
      itemMinf=""
      if reducer != None:
        writer = createMinfWriter( itemMinfBuf, "XML", reducer )
        for item in items:
          writer.write( item.model )
        itemMinf=itemMinfBuf.getvalue()
        writer.close()
      #else: itemMinf=item.name
      # create a QTextDrag object with mime type text/xml containing the minf string
      d=QDrag(self)
      icon = findIconFile( firstItem.icon )
      if icon is not None: # adding an icon which will be visible on drag move, it will be the first item's icon
        d.setPixmap(QPixmap(icon))
      mimeData = QMimeData()
      mimeData.setText(itemMinf)
      d.setMimeData(mimeData);
      dropAction = d.exec_();
    #QTreeWidget.mouseMoveEvent(self, event)
      
  def dragEnterEvent(self, event):
    """This method is called when a drag enter in the widget. The source of the drag can be this widget or antoher.
    The event contains the encoding of the drag object.
    If the event's source is the current window, the event is always accepted.
    Else, try to decode text event as minf representation of an item and set self.draggedItem.
    """
    # if source of event is this widget, draggedItem is already set.
    if event.source()==self:
      event.accept()
    else: #must decode the event. If it is minf format, read it and initialize draggedItem
      self.draggedItems=[]
      self.draggedItemsParent=[]
      if event.mimeData().hasText():
        textEvent=event.mimeData().text()
        textEventBuf=StringIO(textEvent)
        # check if it is the expected minf format
        format, reduction=minfFormat(textEventBuf)
        if format=="XML":
          textEventBuf.seek(0)
          for value in iterateMinf( textEventBuf ):
            if isinstance(value, EditableTree.Item):
              event.accept()
              self.draggedItems.append(value)
            else: event.ignore()
          textEventBuf.close()
        else: event.ignore()
      else: event.ignore()

  def dragLeaveEvent(self, event):
    """The drag leave the widget, there's no more dropzones to highlight."""
    self.dropOn=None
    self.dropAfter=None
    self.dropBefore=None
    self.viewport().update()

  def dragMoveEvent(self, event):
    """When the drag moves, the current dropzone can change.
    According to cursor position (on, before, after an item),
    attributes that store current dropzone are updated (dropBefore, dropAfter, dropOn).
    Method update is called in order to refresh painting with dropzone highlighting.
    """
    # draggedItem must be set, otherwise it isn't a correct drag
    dropzonesChanged=False
    if self.draggedItems==[]:
      event.ignore(self.contentsRect())
      dropzonesChanged=self.setDropzones(None, None, None)
    else:
      cursorPos=self.toContentsPoint(event.pos())
      currentItem=self.itemAt(cursorPos) #item under the mouse cursor
      if currentItem!=None: #cursor on an item
        currentItemContainer=currentItem.container()
        rect = self.visualItemRect(currentItem)
        if currentItem.model not in self.draggedItems: #the item under the mouse isn't one of dragged items
          # if the cursor is in the top margin of item, insert before item
          if (cursorPos.y() < rect.top()+self.MARGIN):
            if currentItemContainer.acceptDrops(): # container must accept drop
              # in theory, it is possible to pass to accept method a rectangle for which the event is accepted,
              # in order to speed up the process event but this doesn't work :
              # when using this hint, dropzones highlighting is not always updated...
              #event.accept(QRect(rect.left(), rect.top(), rect.width(), self.MARGIN))
              event.accept()
              dropzonesChanged=self.setDropzones(currentItemContainer, currentItem, None)
            else:
              #event.ignore(QRect(rect.left(), rect.top(), rect.width(), self.MARGIN))
              event.ignore()
              dropzonesChanged=self.setDropzones(None, None, None)
          #if the cursor is in the bottom margin of the item -> drop after this item
          elif (cursorPos.y()>rect.bottom()-self.MARGIN):
            if currentItemContainer.acceptDrops():
              #event.accept(QRect(rect.left(), rect.bottom()-self.MARGIN, rect.width(), self.MARGIN))
              event.accept()
              dropzonesChanged=self.setDropzones(currentItemContainer, None, currentItem)
            else:
              #event.ignore(QRect(rect.left(), rect.bottom()-self.MARGIN, rect.width(), self.MARGIN))
              event.ignore()
              dropzonesChanged=self.setDropzones(None, None, None)
          # else if the cursor is on an item which accept drop
          elif currentItem.acceptDrops():
            #event.accept(QRect(rect.left(), rect.top()+self.MARGIN, rect.width(), rect.height()-2*self.MARGIN))
            event.accept()
            dropzonesChanged=self.setDropzones(currentItem, None, None)
          else:
            #event.ignore(QRect(rect.left(), rect.top()+self.MARGIN, rect.width(), rect.height()-2*self.MARGIN))
            event.ignore()
            dropzonesChanged=self.setDropzones(None, None, None)
        else: # item dragged on itself : ignore the event
          #event.ignore(rect)
          event.ignore()
          dropzonesChanged=self.setDropzones(None, None, None)
      elif self.acceptDrops(): #if the cursor is not on an item, the dropzone is the listview (at the end of the list)
        event.accept()
        dropzonesChanged=self.setDropzones(self, None, self.getLastChild())
      else:
        event.ignore()
        dropzonesChanged=self.setDropzones(None, None, None)
      if dropzonesChanged:
        self.viewport().update()

  def setDropzones(self, dropOn, dropBefore, dropAfter):
    """Sets dropOn, dropBefore and dropAfter attributes with parameter values.
    Return true if the dropzones have changed."""
    change=(self.dropOn != dropOn) or (self.dropBefore != dropBefore) or (self.dropAfter != dropAfter)
    if change:
      self.dropOn=dropOn
      self.dropBefore=dropBefore
      self.dropAfter=dropAfter
    return change

  def dropEvent( self, event):
    """When an item is dropped in another, a deep copy of the item is added in the dropzone item"""
    # current dropzone is stored in dropOn
    if self.dropOn!=None:
      dropAfterModel=None
      dropBeforeModel=None
      if self.dropAfter!=None: dropAfterModel=self.dropAfter.model
      if self.dropBefore!=None: dropBeforeModel=self.dropBefore.model
      self.controller.drop(event.source(), self, self.draggedItems, self.draggedItemsParent, self.dropOn.model, dropAfterModel, dropBeforeModel, ((event.keyboardModifiers() & Qt.ControlModifier) == Qt.ControlModifier) )
    self.draggedItems = []
    self.draggedItemsParent=[]
    self.dropOn=None
    self.dropAfter=None
    self.dropBefore=None
    self.viewport().update()

  def deleteDraggedItems(self):
    """Called when the item have been moved in another tree widget (drop+moveMode)"""
    i=0
    for draggedItem in self.draggedItems:
      self.controller.delete(draggedItem, self.draggedItemsParent[i])
      i+=1
    self.draggedItems = []
    self.draggedItemsParent=[]

  #------ Key events ------
    
  def keyPressEvent(self, event):
    """
    This method is called when a key is pressed during a few seconds or when a key is released
    If the user keep the key pressed, the event occurs however;
    same as pressing several times the key. It doesn't seems to be parametrable...
    If the key pressed is delete, the selected items are deleted.
    """
    if (event.key() == Qt.Key_Delete):
      # delete current selected item
      items = self.selectedItems()
      for item in items:
        self.controller.delete(item.model, item.container().model)
    else: event.ignore() # the event could be handled by a parent component

  #------ context menu events ------
  def openContextMenu(self, point):
    """On right click on the mouse, a context menu opens.
    With this menu, it is possible to create a new branch.
    """
    self.contextMenuTarget=None
    cursorPos=self.toContentsPoint(point)
    currentItem=self.itemAt(cursorPos) #item under the mouse cursor
    accept=False
    if currentItem is not None:
      if currentItem.model.modifiable and not currentItem.model.isLeaf():
        self.contextMenuTarget=currentItem.model
        accept=True
    else:
      if self.model is not None and self.model.modifiable:
        self.contextMenuTarget=self.model
        accept=True
    #items=self.selectedItems()
    #if len(items)==1:
      #if items[0].model.modifiable:
        #event.accept()
      #else: event.ignore()
    #elif self.model!=None and self.model.modifiable:
      #event.accept()
    #else: event.ignore()
    if accept:
      self.popupMenu.exec_(QCursor.pos())

  def menuNewItemEvent(self):
    """
    Called when user selects New in context menu in order to create a new item in the tree.
    """
    #items=self.selectedItems()
    #if len(items) == 1:
      #target=items[0].model
    #else: target=self.model
    #self.controller.newItem(target)
    self.controller.newItem(self.contextMenuTarget)

  #------ Update on model changes ------
  def updateContent(self, action, items, position=None):
    """This method is called when the model notifies a change :
    The action has been done at position, with items.
    The view should update its content to reflect the changes.
    """
    if action==ObservableList.INSERT_ACTION:
      self.insert(items, position)
    elif action==ObservableList.REMOVE_ACTION:
      self.remove(items, position)
    elif action==ObservableList.MODIFY_ACTION:
      # some model items have been modified,
      # widget items are replaced by new items with new model items
      # from position, all items must be replaced with new value
      # ->remove and then insert new
      i=position+1
      for modelItem in items:
        self.takeTopLevelItem(i)
        i+=1
      self.insert(items, position)
    #else: print action, "unknown action"

  def updateName(self, newName):
    self.setWindowTitle(newName)
    self.setHeaderLabel(newName)

  def insert(self, items, position=None):
    """Insertion of items at position in the model
    -> create view items for all items and insert them at position in self.
    Inserted item becomes the selected item."""
    #insert at position = insert before item at position = insert after item at position-1
    for item in items:
      if item.isLeaf(): # append item to keep the same order as in the model
        itemBefore=EditableTreeWidget.Leaf(None, item, None, self.iconDim)
      else: itemBefore=EditableTreeWidget.Branch(None, item, None, self.iconDim)
      self.insertTopLevelItem(position, itemBefore)
      if item.unamed and self.hasFocus(): 
        self.editItem(itemBefore, 0)
        item.unamed=False
    #print "current item : ", self.currentItem()
    #print "set current item : ", itemBefore, itemBefore.text(0)
    self.setCurrentItem(itemBefore, 0)
    itemBefore.setSelected(True)

  def remove(self, items, position):
    """Removes items in the list from position.
    If the list is empty, one item is removed.
    If position is undefined, removes items whose model is in the list"""
    if position is None:
      position=0
    if len(items)==0:
      self.takeTopLevelItem(position)
    else:
      for modelItem in items:
        found=False
        i=0
        while not found and i<self.topLevelItemCount():
          item=self.topLevelItem(i)
          if item.model is modelItem:
            self.takeTopLevelItem(i)
            found=True
          i+=1

  #------ Refresh painting ------
  def paintEvent(self, event):
    """This method is called to paint the tree.
    To refresh the view, call self.update.
    It is redefined in order to highlight drop zone during the drag of an item
    Three types of dropzone are defined :
      - before an item (cursor is in the top of the item's rectangle) -> draw a line on top
      - after an item (cursor is in the bottom of the item's rectangle) -> draw a line on bottom
      - on an item -> draw a rectangle around item
    """
    QTreeWidget.paintEvent(self, event)
    painter=QPainter()
    painter.begin(self.viewport())
    if self.dropBefore!=None: # draw a line in the top of the item
      rect=self.visualItemRect(self.dropBefore)
      # offset of the item = depth * offset in relation to parent
      #offset=self.indentation()
      painter.setBrush(Qt.black)
      # the line has the same offset as the item
      painter.drawRect(rect.left(), rect.top(), rect.width(), self.MARGIN)
    elif self.dropAfter!=None: # draw a line in the bottom of the item and its visible content
      rect=self.visualItemRect(self.dropAfter) # this rect only contains the item, not its content
      # inc the height to include item's content
      #rect.setHeight( (min( self.dropAfter.totalHeight(), self.viewport().height() - rect.y() ) ) ) # stay in the viewport to keep the line visible
      #offset=self.indentation()
      painter.setBrush(Qt.black)
      #print "draw drop after", self.dropAfter.getText(), rect.left(), rect.top(), rect.width(), rect.height()
      painter.drawRect(rect.left(), rect.bottom()-self.MARGIN+1, rect.width(), self.MARGIN)
    elif self.dropOn!=None: #draw the rectangle containing the item
      if self.dropOn!=self:
        rect=self.visualItemRect(self.dropOn)
      else: #ajout dans le listview alors qu'il est vide
        rect=QRect(0, 0, self.columnWidth(0), self.MARGIN)
      #print "draw drop on", self.dropOn.getText(), rect.left(), rect.top(), rect.width(), rect.height()
      painter.setPen(QPen(Qt.black, self.MARGIN, Qt.SolidLine))
      painter.drawRect(rect)
    painter.end()
    
    
  #----------------------------------------------------------------------------
  class Item(QTreeWidgetItem):
    """Item is the base class for elements of EditableTreeWidget. """
    def __init__( self, parent, treeItemModel, after=None, iconSize=defaultIconSize):
      """
      @type parent: tree or branch
      @param parent: container of the item
      @type treeItemModel: EditableTree.Item
      @param treeItemModel: model which this widget is the representation
      @type after: item
      @param after: the item after which current item must be added in the parent
      """
      QTreeWidgetItem.__init__( self, parent, [treeItemModel.name] )
      if treeItemModel.icon:
        iconPath = findIconFile( treeItemModel.icon )
        if iconPath is not None:
          self.setIcon(0, QIcon(iconPath))
      if not treeItemModel.copyEnabled:
        self.setFlags(self.flags() & ~Qt.ItemIsDragEnabled)
      if not treeItemModel.modifiable:
        self.setFlags(self.flags() & ~Qt.ItemIsDropEnabled)
      # rename is enabled only if the item is modifiable
      if treeItemModel.modifiable:
        self.setFlags(self.flags() | Qt.ItemIsEditable)
      treeItemModel.onAttributeChange("name", self.updateName)
      treeItemModel.onAttributeChange("visible", self.updateVisibiliy)
      self.setHidden(not treeItemModel.visible)
      self.setDisabled(not treeItemModel.enabled)
      self.model=treeItemModel

    def acceptDrops(self):
      return ((self.flags() & Qt.ItemIsDropEnabled) == Qt.ItemIsDropEnabled)

    def getText(self):
      return self.text(0)

    def container(self):
      """Return the parent item or the listview that contains the element if it is a top level element
      @rtype: EditableTreeWidget.Branch or EditableTreeWidget"""
      parent = self.parent()
      if parent is None:
        parent = self.treeWidget()
      return parent

    def okRename(self, col):
      """It is the called associated to the signal QTreeWidget.itemChanged(item, col). It is called when user renames the item.
      The name must be changed in the model."""
      if getattr(self, "model", None) is not None:
        newText=unicode(self.getText())
        if self.model.name != newText:
          if self.model.name == self.model.tooltip:
            self.model.tooltip=newText
          self.model.name=newText
    
    def updateName(self, newName):
      """
      Called when the model notifies that its name attribute value has changed.
      """
      self.setText(0, newName)

    def updateVisibiliy(self, newValue):
      """
      Called when the model notifies that its visible attribute value has changed.
      """
      #pass
      self.setHidden(not newValue)
      #self.setText(0, self.getText()+"-hid")
      #print "change visibility to ", newValue, " for ", self.getText()
  #----------------------------------------------------------------------------
  class Branch( Item ):
    """Item that represents a tree branch.
    It can have children."""
    def __init__( self, parent, treeItemModel, after=None, iconSize=defaultIconSize):
      EditableTreeWidget.Item.__init__(self, parent, treeItemModel, after, iconSize)
      self.iconDim=iconSize
      treeItemModel.addListener(self.updateContent)
      #create child items
      lastChild=None
      for item in treeItemModel.values():
        if item.isLeaf():
          lastChild=EditableTreeWidget.Leaf(self, item, lastChild, iconSize)
        else: lastChild=EditableTreeWidget.Branch(self, item, lastChild, iconSize)

    def getChild(self, n):
      """Return the nth child item
      If n<=0 return the first child, if n>=nb children, return the last child
      @rtype: EditableTreeWidget.Item
      """
      if n<0:
        n=0
      elif n>=self.childCount():
        n=self.childCount()-1
      return self.child(n)

    #------ Update on model changes ------
    def updateContent(self, action, items, position=None):
      """This method is called when the model notifies a change :
      The action has been done at position, with items.
      The view should update its content to reflect the changes"""
      if action==ObservableList.INSERT_ACTION:
        self.insert(items, position)
      elif action==ObservableList.REMOVE_ACTION:
        self.remove(items, position)
      elif action==ObservableList.MODIFY_ACTION:
        # some model items have been modified,
        # widget items are replaced by new items with new model items
        # from position, all items must be replaced with new value
        #remove and then insert new
        for modelItem in items:
          self.takeChild(position) # when an item is removed, position becomes the index of the next item
        self.insert(items, position)
      #else: print "unknown action"
      #print str(self.listView())

    def insert(self, items, position):
      """Insertion of items at position in the model
      -> create view items for all items and insert them at position in self
      insert at position = insert before item at position = insert after item at position-1"""
      i=position
      for item in items:
        if item.isLeaf(): # append item to keep the same order as in the model
          newItem=EditableTreeWidget.Leaf(None, item, None, self.iconDim)
        else: newItem=EditableTreeWidget.Branch(None, item, None, self.iconDim)
        self.insertChild(i, newItem)
        i+=1
        if item.unamed and self.treeWidget().hasFocus(): 
          self.editItem(newItem, 0)
          item.unamed=False
      self.setExpanded(True)
      #print "current item : ", self.treeWidget().currentItem()
      #print "set current item : ", newItem, newItem.text(0)
      self.treeWidget().setCurrentItem(newItem, 0)
      newItem.setSelected(True)
      
    def remove(self, items, position):
      """Remove items in the list from position
      if the list is empty, remove one item
      if position is undefined, remove items whose model is in the list"""
      if position is None:
        position=0
      if len(items)==0:
        self.takeChild(position)
      else:
        for modelItem in items:
          found=False
          i=position
          while not found and i<self.childCount():
            item=self.child(i)
            if item.model is modelItem:
              self.takeChild(i)
              found=True
            else: # if we remove an item, the index stay the same, no need to increment it
              i+=1

  #----------------------------------------------------------------------------
  class Leaf( Item ):
    """Item that represents a tree leaf. It doesn't have children."""
    def __init__( self, parent, treeItemModel, after=None, iconSize=defaultIconSize):
      EditableTreeWidget.Item.__init__(self, parent, treeItemModel, after, iconSize)
      #self.setExpandable(False)
      #self.setDropEnabled(False)
      self.setFlags( self.flags() & ~Qt.ItemIsDropEnabled )
    # This method could be used to change text color of items : 
    #def paintCell(self, painter, colorGroup, column, width, alignment ):
      #cg=qt.QColorGroup(colorGroup)
      #c=qt.QColor(cg.text())
      #cg.setColor( qt.QColorGroup.Text, Qt.red)
      #QListViewItem.paintCell(self,  painter, cg, column, width, alignment )
      #cg.setColor( qt.QColorGroup.Text, c )

#----------------------------------------------------------------------------
class EditableTreeController:
  """The controller is called to make changes on the model when events occur."""
  def __init__(self, m):
          self.model=m

  def drop(self, sourceTreeWidget, targetTreeWidget, draggedItems, draggedItemsParent, dropOn, dropAfter, dropBefore, copyMode):
    """
    Called when an item is dropped. It is copied or moved in target model.
    The copy of item will be modifiable even if source item is not.

    @type sourceTreeWidget: EditableTreeWidget
    @param sourceTreeWidget: the widget which dragged item comes from
    @type targetTreeWidget: EditableTreeWidget
    @param targetTreeWidget: the widget in which dragged item is dropped
    @type draggedItems: list of EditableTree.Item
    @param draggedItems: items to move or copy
    @type draggedItemsParent: list of EditableTree.Branch or EditableTree
    @param draggedItemsParent: container of dragged items
    @type dropOn: EditableTree.Branch or EditableTree
    @param dropOn: container in which item is dropped
    @type dropAfter: EditableTree.Item
    @param dropAfter: item after which dragged item is dropped
    @type dropBefore: EditableTree.Item
    @param dropBefore: item before which dragged item is dropped
    """
    insertedItem=None
    insertIndex=None
    if sourceTreeWidget==targetTreeWidget: # inner drop
      i=0
      for draggedItem in draggedItems:
        if copyMode: # if ctrl key is pressed, copy item, else move
          insertedItem, insertIndex=self.copy(draggedItem, dropOn, dropAfter, dropBefore, insertIndex)
        else:
          insertedItem, insertIndex=self.move(draggedItem, draggedItemsParent[i], dropOn, dropAfter, dropBefore, insertIndex)
        i+=1
        if insertedItem!=None:
          dropAfter=insertedItem
          dropBefore=None
          if insertIndex is not None:
            insertIndex+=1
    else: # drop from one widget to another 
      #print "drop on ", targetTreeWidget
      if not copyMode: sourceTreeWidget.deleteDraggedItems()
      for draggedItem in draggedItems:
        draggedItem.setAllModificationsEnabled(True)
        insertedItem, insertIndex=self.insert(draggedItem, dropOn, dropAfter, dropBefore, insertIndex)
        if insertedItem is not None:
          dropAfter=insertedItem
          dropBefore=None
          if insertIndex is not None:
            insertIndex+=1

  def move(self, item, source, target, after, before, index):
    """Move an element of the tree from source to target."""
    insertedItem=None
    insertIndex=index
    if not target.isDescendant(item): # can't move an item in its descendant
      # the item is deleted from its parent
      if source == target: # insertion index can change if the item is moved inside its container
        index=None
      self.delete(item, source)
      if item.copyEnabled and target.modifiable and not target.has_key(item.id): # if the item was not deletable, it is already in the target and can't be moved. 
        itemCopy = copy.deepcopy(item)
        # add this new item in the target item
        insertedItem, insertIndex=self.insert(itemCopy, target, after, before, index)
    return (insertedItem, insertIndex)

  def copy(self, item, target, after, before, index):
    """Recursive copy of an item in another item.
    A copy is completly modifiable, even if the source is not."""
    # create a deepcopy of the dragged item
    # notifiers are not copied, view items will be removed so they shouldn't be notified of changes in the new item
    insertedItem=None
    insertIndex=index
    if item.copyEnabled and target.modifiable:
      itemCopy = copy.deepcopy(item)
      # a copy is completely modifiable, even if the source is not
      itemCopy.setAllModificationsEnabled(True)
      # add this new item in the target item
      insertedItem, insertIndex=self.insert(itemCopy, target, after, before, index)
      #print self.model
    return (insertedItem, insertIndex)

  def insert(self, item, target, after, before, index):
    """Insert item in target, eventually after or before an existing child."""
    insertedItem=item
    insertIndex=index
    if not target.has_key(item.id): # can't copy an item that is already in the target
      if index is not None:
        target.insert(index, item.id, item)
      else:
        if before!=None:
          insertIndex=target.index(before.id)
          target.insert(insertIndex, item.id, item) # inserer le suivant en i+1
        elif after!=None: # insert the item after item "after"
          insertIndex=target.index(after.id)+1
          target.insert(insertIndex, item.id, item) # inserer le suivant en i+2
        else: # if no position, append the item
          #print "model append", self.model.onChangeNotifier._listeners
          target[item.id]=item # rien a preciser on ajoute a la fin
    else:
      newItem=target[item.id]
      if newItem is not after and newItem is not before: # else no move to do, it is already in the right place.
        insertedItem, insertIndex=self.move(newItem, target, target, after, before, None) 
      else: 
        insertedItem=newItem
        insertIndex=target.index(newItem.id)
    return (insertedItem, insertIndex)

  def delete(self, item, source):
    """Delete an item in the tree
    Delete item from source"""
    if item.delEnabled:
      del source[item.id]
      #print self.model

  def newItem(self, target):
    """Creates a new child in target"""
    if target.modifiable: #it is possible to add new item in the target
      # create a new branch item of the model
      # EditableTree class is not used directly because the model could be a derived class
      # class Branch should be able to be called without parameters
      newItem=self.model.__class__.Branch()
      target[newItem.id]=newItem

#----------------------------------------------------------------------------
class ObservableListWidget(QTreeWidget):
  """A widget to represent an ObservableList.
  The list is modifiable by manipulating items in the widget :
    - add new item
    - delete an item
    - rename an item

  The widget is created with an ObservableList as model.

  The graphic component has a reference on the model.
  It registers a callback method on the model notifier.
  On modification events, the model is updated and notify all its listeners,
  so the view is updated via updateContent method.

  Action events are not catched in this class.
  To enable actions, you may attach a popup menu to the signal contextMenuRequested.

  The widget shows tooltips items.
  All items icon are resized to have the same size.

  Inner classes :
    - Item

  Inherits qt component QTreeWidget.

  @type model: ObservableList with an attribute name
  @ivar model: the list which this widget is a graphic representation.
  @type tooltipsViewer: ListViewToolTip
  @ivar tooltipsViewer: this object reimplements QToolTip in order to show tooltip's item when mouse is on an item
  """

  def __init__(self, model, parent=None, iconSize=defaultIconSize):
    """
    @type model: ObservableList
    @param model: the list which this widget is a graphic representation.
    @type parent:QWidget
    @param parent: parent of this widget
    @type iconSize: couple of integers or None
    @param iconSize: force items icon resizing.
    """
    QTreeWidget.__init__( self, parent)
    self.setColumnCount(1)
    self.setHeaderLabels([""])
    self.iconDim=iconSize
    self.setIconSize(QSize(*iconSize))
    self.connect(self, SIGNAL("currentItemChanged (  QTreeWidgetItem *, QTreeWidgetItem * )", self.currentItemRenamed))
    self.setContextMenuPolicy(Qt.CustomContextMenu)
    # keep a reference to the model for control event and register a listener to be aware of changes
    self.setModel(model)

  def setModel(self, m):
    """Construct items of the list reading the model given.
    A listener is added to the model, so when the model change, the method self.updateContents
    is automatically called.
    """
    self.clear()
    self.model=m
    if m is not None:
      self.setHeaderLabels( [m.name] )
      self.model.addListener(self.updateContent)
      # create child items with data in the tree model
      lastChild=None
      for item in self.model:
        lastChild=ObservableListWidget.Item(self, item, lastChild, self.iconDim) # append item to keep the same order as in the model

  def currentItemRenamed(self, current, previous):
    if self.currentItem() is not None:
      self.currentItem().okRename()
    
  def getChild(self, n):
    """Return the nth child item
    If n<=0 return the first child, if n>=nb children, return the last child
    @rtype: ObservableListWidget.Item"""
    if n<0:
      n=0
    elif n>=self.topLevelItemCount():
      n=self.topLevelItemCount()-1
    return self.topLevelItem(n)

  def getLastChild(self):
    """Return the last child item.
    @rtype: ObservableListWidget.Item
    """
    return self.topLevelItem( self.topLevelItemCount() - 1)

  #------ Update on model changes ------
  def updateContent(self, action, items, position=None):
    """This method is called when the model notifies a change :
    The action has been done at position, with items.
    The view should update its content to reflect the changes.
    """
    if action==ObservableList.INSERT_ACTION:
      self.insert(items, position)
    elif action==ObservableList.REMOVE_ACTION:
      self.remove(items, position)
    elif action==ObservableList.MODIFY_ACTION:
      # some model items have been modified,
      # widget items are replaced by new items with new model items
      # from position, all items must be replaced with new value
      # ->remove and then insert new
      if position is None:
        position=0
      for modelItem in items:
        self.takeTopLevelItem(position)
      self.insert(items, position)
    #else: print action, "unknown action"

  def insert(self, items, position=None):
    """insertion of items at position in the model
      -> create view items for all items and insert them at position in self.
      Inserted item becomes the selected item."""
    #insert at position = insert before item at position = insert after item at position-1
    i=position
    for item in items:
      widgetItem=ObservableListWidget.Item(None, item, None, self.iconDim)
      self.insertTopLevelItem( i, item )
      i+=1
      if item.unamed:
        self.editItem(widgetItem)
        item.unamed=False
    self.setCurrentItem(widgetItem)

  def remove(self, items, position):
    """Removes items in the list from position.
    If the list is empty, one item is removed.
    If position is undefined, removes items whose model is in the list"""
    if position is None:
      position =0
    if len(items)==0:
      self.takeTopLevelItem(position)
    else:
      for modelItem in items:
        found=False
        i=position
        while not found and i<=self.topLevelItemcount():
          item=self.topLevelItem(i)
          if item.model is modelItem:
            self.takeTopLevelItem(i)
            found=True
          else:
            i+=1

  #----------------------------------------------------------------------------
  class Item(QTreeWidgetItem):
    """Item is the base class for elements of ObservableListWidget.
    Treats renaming events if the item is modifiable.
    """
    def __init__( self, parent, model, after=None, iconSize=defaultIconSize):
      """
      @type parent: ObservableListWidget
      @param parent: container of the item
      @type model: any object that contains attributes name, icon, tooltip and modifiable, and which is Observable.
      @param model: model which this item is the representation
      @type after: item
      @param after: the item after which current item must be added in the parent
      """
      QTreeWidgetItem.__init__( self, parent )
      if model.icon:
        iconPath = findIconFile( model.icon ) # QIcon
        if iconPath is not None:
          self.setIcon(0, QIcon(iconPath))
      self.setText(0, model.name)
      self.setToolTip(0, model.tooltip)
      # rename is enabled only if the item is modifiable
      if model.modifiable:
        self.setFlags(self.flags() | Qt.ItemIsEditable)
      self.model=model
      self.model.onAttributeChange("name", self.updateName)

    def getText(self):
      return self.text(0)

    def okRename(self):
      """This method is called when user renames the item.
      The name must be changed in the model."""
      if getattr(self, "model", None) is not None:
        newText=unicode(self.text(0))
        if self.model.name != newText:
          if self.model.name==self.model.tooltip:
            self.model.tooltip=newText
          self.model.name=newText

    #------ Update on model changes ------
    def updateName(self, newName):
      """This method is called when the model notifies that its name attribute has changed :
      The view should update its content to reflect the changes"""
      self.setText(0, newName)
      self.setToolTip(0, self.model.tooltip)
      #else: print "unknown action"
      
#----------------------------------------------------------------------------
class TreeListWidget(QTreeWidget):
  """
  This widget represents a list of EditableTree.
  The given model is an ObservableSortedDictionary (trees are referenced by their id).
  
  The widget listens for modifications done on the model :
    - add new item
    - delete an item
    - rename an item
  It registers a callback method on the model notifier.
  On modification events, the model is updated and notify all its listeners,
  so the view is updated via updateContent method.

  Action events are not catched in this class.
  To enable actions, you may attach a popup menu to the signal contextMenuRequested.
  Items accept drop if dropped elements are EditableTree.Item. Dropped element are added in target EditableTree.
  
  The widget shows tooltips items.
  All items icon are resized to have the same size.
  
  Inner classes :
    - Item

  Inherits qt component QTreeWidget.

  @type model: ObservableSortedDictionary
  @ivar model: the EditableTree map which this widget is a graphic representation.
  @type tooltipsViewer: ListViewToolTip
  @ivar tooltipsViewer: this object reimplements QToolTip in order to show tooltip's item when mouse is on an item
  @type draggedItems: list of EditableTree.Item
  @ivar draggedItems: list of elements that are currently dragged on the widget
  @type dropOn: TreeListWidget.Item
  @ivar dropOn: current drop zone (mouse is over this item with dragged items and the drop zone item accepts drop)
  """

  def __init__(self, model, parent=None, iconSize=defaultIconSize):
    """
    @type model: ObservableSortedDictionary
    @ivar model: the EditableTree map which this widget is a graphic representation.
    @type parent:QWidget
    @param parent: parent of this widget
    @type iconSize: couple of integers or None
    @param iconSize: force items icon resizing.
    """
    QTreeWidget.__init__( self, parent)
    self.setColumnCount(1)
    self.iconDim=iconSize
    self.setIconSize(QSize(*iconSize))
    self.setRootIsDecorated(False) # it is not really a tree but a list, keep a QTreeWidget to keep columns
    # enable display of tooltips on items
    # the listview accept drops to enable adding items in trees by dropping items on the item representing the tree
    self.setAcceptDrops(True)
    self.draggedItems=[]
    self.dropOn=None
    self.connect(self, SIGNAL("currentItemChanged ( QTreeWidgetItem *, QTreeWidgetItem * )"), self.currentItemRenamed )
    self.setContextMenuPolicy(Qt.CustomContextMenu)
    # keep a reference to the model for control event and register a listener to be aware of changes
    self.setModel(model)

  def setModel(self, m):
    """
    Construct items of the list reading the model given.
    A listener is added to the model, so when the model change, the method self.updateContents
    is automatically called.
    @type m: ObservableSortedDictionary
    @param m: tree map to show in this widget
    """
    self.clear()
    self.model=m
    if m is not None:
      self.setHeaderLabels([m.name])
      self.model.addListener(self.updateContent)
      # create child items with data in the tree model
      lastChild=None
      for item in self.model.values():
        lastChild=self.Item(self, item, lastChild, self.iconDim) # append item to keep the same order as in the model

  def currentItemRenamed(self, current, previous):
    if self.currentItem() is not None:
      self.currentItem().okRename()
    
  def getChild(self, n):
    """
    Return the nth child item
    If n<=0 return the first child, if n>=nb children, return the last child
    @rtype: TreeListWidget.Item
    """
    if n<0:
      n=0
    elif n>=self.topLevelItemCount():
      n=self.topLevelItemCount() - 1
    return self.topLevelItem(n)

  def getLastChild(self):
    """
    Return the last child item.
    @rtype: TreeListWidget.Item
    """
    return self.topLevelItem(self.topLevelItemCount()-1)
  
  #------ Drag&drop control  ------
  def dragEnterEvent(self, event):
    """
    This method is called when a drag enters in the widget. 
    The event contains the encoding of the dragged objects.
    The method tries to decode text event as minf representation of EditableTree.Item and sets self.draggedItems.
    """
    # accept drag if it contains instances of EditableTree.Item
    self.draggedItems=[]
    if event.mimeData().hasText():
      textEventBuf=StringIO(event.mimeData().text())
      # check if it is the expected minf format
      format, reduction=minfFormat(textEventBuf)
      if format=="XML":
        textEventBuf.seek(0)
        for value in iterateMinf( textEventBuf ):
          if isinstance(value, EditableTree.Item):
            event.accept()
            value.setAllModificationsEnabled(True) # this is a copy of items that comes from another tree, so enable modifications on the copied items
            self.draggedItems.append(value)
          else: event.ignore()
        textEventBuf.close()
      else: event.ignore()
    else: event.ignore()
  
  def toContentsPoint(self, point):
    """
    Translates coordinates in the frame to coordinates in the content of the list (without header).
    @rtype: QPoint
    """
    #viewportPoint=self.contentsToViewport(point) to get the item at position we need the position in the entire list not in the visible content (viewport)
    return point #- QPoint(0, self.header().height())
 
  def dragMoveEvent(self, event):
    """
    When the drag moves, the current dropzone can change.
    According to cursor position, dropOn attribute is updated.
    To have a valid dropzone, mouse must be over a modifiable item.
    When the dragMoveEvent is ignored, a forbidden cursor is shown.
    """
    # draggedItem must be set, otherwise it isn't a correct drag 
    if self.draggedItems==[]:
      event.ignore(self.contentsRect())
      self.dropOn=None
    else:
      cursorPos=self.toContentsPoint(event.pos())
      currentItem=self.itemAt(cursorPos) #item under the mouse cursor
      self.dropOn=currentItem
      if currentItem is not None and currentItem.model.modifiable and event.source().model is not currentItem.model: # not accept dragged items that comes from current tree
        event.accept()
      else: event.ignore()
 
  def dropEvent( self, event):
    """
    When items are dropped, they are added to the dropzone model (an EditableTree)
    """
    # current dropzone is stored in dropOn
    if self.dropOn!=None:
      for item in self.draggedItems:
        self.dropOn.model.add(item)
    self.draggedItems = []
    self.dropOn=None
    
  #------ Update on model changes ------
  def updateContent(self, action, items, position=None):
    """
    This method is called when the model notifies a change :
    The action has been done at position, with items.
    The view should update its content to reflect the changes.
    """
    if action==ObservableList.INSERT_ACTION:
      self.insert(items, position)
    elif action==ObservableList.REMOVE_ACTION:
      self.remove(items, position)
    elif action==ObservableList.MODIFY_ACTION:
      # some model items have been modified,
      # widget items are replaced by new items with new model items
      # from position, all items must be replaced with new value
      # ->remove and then insert new
      for modelItem in items:
        self.takeTopLevelItemItem(position)
      self.insert(items, position)
    #else: print action, "unknown action"

  def insert(self, items, position=None):
    """insertion of items at position in the model
      -> create view items for all items and insert them at position in self.
      Inserted item becomes the selected item."""
    #insert at position = insert before item at position = insert after item at position-1
    i=position
    for item in items:
      newItem=self.Item(None, item, None, self.iconDim)
      self.insertTopLevelItem(i, newItem)
      i+=1
      if item.unamed:
        self.editItem(newItem, 0)
        item.unamed=False
    self.setCurrentItem(newItem)

  def remove(self, items, position):
    """Removes items in the list from position.
    If the list is empty, one item is removed.
    If position is undefined, removes items whose model is in the list"""
    if position is None:
      position =0
    if len(items)==0:
      self.takeTopLevelItem(position)
    else:
      for modelItem in items:
        found=False
        i=position
        while not found and i<self.count():
          item=self.topLevelItem(i)
          if item.model is modelItem:
            self.takeTopLevelItem(i)
            found=True
          else:
            i+=1

  #----------------------------------------------------------------------------
  class Item(QTreeWidgetItem):
    """
    Item is the base class for elements of TreeListWidget.
    Treats renaming events if the item is modifiable.
    """
    def __init__( self, parent, model, after=None, iconSize=defaultIconSize):
      """
      @type parent: TreeListWidget
      @param parent: container of the item
      @type model: any object that contains attributes name, icon, tooltip and modifiable, and which is Observable.
      @param model: model which this item is the representation
      @type after: item
      @param after: the item after which current item must be added in the parent
      """
      QTreeWidgetItem.__init__( self, parent )
      if model.icon:
        iconPath = findIconFile( model.icon )
        if iconPath is not None:
          self.setIcon(0, QIcon(iconPath))
      self.setText(0, model.name)
      self.setToolTip(0, model.tooltip)
      # rename is enabled only if the item is modifiable
      if model.modifiable:
        self.setFlags(self.flags() | Qt.ItemIsEditable)
      if not model.visible:
        self.setHidden(True)
      self.model=model
      self.model.onAttributeChange("name", self.updateName)
      self.model.onAttributeChange("visible", self.updateVisibility)

    def getText(self):
      return self.text(0)

    def okRename(self):
      """
      This method is called when user renames the item.
      The name must be changed in the model.
      """
      if getattr(self, "model", None) is not None:
        newText=unicode(self.text(0))
        if self.model.name != newText:
          if self.model.name==self.model.tooltip:
            self.model.tooltip=newText
          self.model.name=newText # the model will notify the change and updateName will be called

    #------ Update on model changes ------
    def updateName(self, newName):
      """
      This method is called when the model notifies that its name attribute has changed :
      The view should update its content to reflect the changes.
      """
      self.setText(0, newName)
      self.setToolTip(0, self.model.tooltip)
      #else: print "unknown action"
      
    def updateVisibility(self, newValue):
      """
      Called when the model notifies that its visible attribute value has changed.
      """
      #pass
      self.setHidden(not newValue)
