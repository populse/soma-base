# -*- coding: iso-8859-1 -*-

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
Facilitation of run-time creation and usage of C{Qt} widgets from C{*.ui} 
files created with 
U{Qt designer<http://doc.trolltech.com/3.3/designer-manual.html>}.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"



import __builtin__
if not hasattr( __builtin__, 'set' ):
  from sets import Set as set

from soma.singleton import Singleton

import os, errno
import qt, qtui


#------------------------------------------------------------------------------
class WidgetFactory( object ):
  '''An C{WidgetFactory} instance is bound to a 
  U{Qt designer<http://doc.trolltech.com/3.3/designer-manual.html>} file 
  (I{i.e.} C{*.ui}) and can be called to create one or several widgets from 
  this file.
  
  Example::
    uiFactory = WidgetFactory( 'settingsDialog.ui' )
    dialog = uiFactory( None, None )
    dialog.exec_loop()
  
  All child widgets of the created widget whose name starts with C{"EXPORT_"} 
  are stored in an attribute of the created widget. The name of the attribute 
  is the name of the child widget without the first seven characters (I{i.e} 
  without C{"EXPORT_"}). In the previous example, if the file 
  C{'settingsDialog.ui'} contains a widget called C{"EXPORT_comboLanguage"}, 
  it will be stored in C{dialog.comboLanguage}.
  
  It is possible to include custom widgets in designer file but special care is
  required to define them in Python (see L{CustomizedQWidgetFactory}).
  
  @see: L{createWidget}
  @see: U{QWidgetFactory<http://doc.trolltech.com/3.3/qwidgetfactory.html>}
  @todo: Document usage of 
  U{Qt linguist<http://doc.trolltech.com/3.3/linguist-manual.html>} with 
  C{WidgetFactory}
  '''
  
  class CustomWidgetError( RuntimeError ):
    '''
    Exception raised when an invalid custom widget is encountered
    '''
    pass
  
  def __init__( self, uiFile,
                translationFile = None,
                ignoreInvalidCustomWidgets = False ):
    '''
    @param uiFile: Name of the 
    U{Qt designer<http://doc.trolltech.com/3.3/designer-manual.html>} file 
    containing the widget to create.
    @type  uiFile: string
    @param translationFile: Name of a
    U{Qt linguist<http://doc.trolltech.com/3.3/linguist-manual.html>} 
    translation file (C{*.qm}) used to translate the created widget.
    @type  translationFile: string
    @param ignoreInvalidCustomWidgets: By default, if the C{*.ui} file 
    contains custom widgets that cannot be created, a L{CustomWidgetError} is 
    raised. If C{ignoreInvalidCustomWidgets} is C{True}, any invalid custom 
    widgets is silently replaced by an empty C{QWidget}.
    @type  ignoreInvalidCustomWidgets: bool
    '''
    if not os.path.exists( uiFile ):
      raise IOError( errno.ENOENT, os.strerror( errno.ENOENT )+': '+ `uiFile` )
    self.uiFile = uiFile

    self.translationFile = translationFile
    if translationFile is None:
      self.translator = None
    else:
      if not os.path.exists( translationFile ):
        raise IOError( errno.ENOENT, 
                       os.strerror( errno.ENOENT )+': '+ `translationFile` )
      self.translator = qt.QTranslator()
      if not self.translator.load( translationFile ):
        raise RuntimeError( 'Invalid translation file: ' + `translationFile` )

    self.ignoreInvalidCustomWidgets = ignoreInvalidCustomWidgets


  def __call__( self, parent, name ):
    '''
    Create a widget from the designer file. The widget is created with U{qtui.QWidgetFactory.create
    <http://doc.trolltech.com/3.3/qwidgetfactory.html#create>} then all its
    subwidgets are processed with L{processChildWidget}.
    
    @param parent: parent of the widget to create
    @type  parent: QWidget or None
    @param name: name of the widget to create
    @type  name: string or QString
    '''
    if self.translator is not None:
     qt.qApp.installTranslator( self.translator )
    try:
      mainWidget = qtui.QWidgetFactory.create( self.uiFile, None, parent, name )
    finally:
      if self.translator is not None:
       qt.qApp.removeTranslator( self.translator )
    if mainWidget is None:
      raise RuntimeError( 'Invalid qtui file:' + `self.uiFile` )
    CustomizedQWidgetFactory._widgetsPostprocessing( mainWidget, 
                                                     self. processChildWidget )
    return mainWidget


  def processChildWidget( self, mainWidget, childWidget ):
    '''
    Child widgets post-processing:
      - Check if C{childWidget} is an invalid custom widget and behave 
        accordingly (possibly raising an exception)
      - If the name of C{childWidget} starts with C{EXPORT_}, set an attribute 
        to C{mainWidget} to access C{childWidget}. The name of the attribute is 
        the name of C{childWidget} without the first seven characters. For 
        example, a widget is called C{EXPORT_saveButton}, it will be accessible 
        with C{mainWidget.saveButton}.
    '''
    name = str( childWidget.name() )
    if not self.ignoreInvalidCustomWidgets and hasattr( childWidget, '_invalid_custom_widget' ):
      raise self.CustomWidgetError( 'Unknown custom widget class: ' + childWidget._invalid_custom_widget )
    if name.startswith( 'EXPORT_' ):
      name = name[ 7: ]
      childWidget.setName( name )
      setattr( mainWidget, name, childWidget )
  

#------------------------------------------------------------------------------
class CustomizedQWidgetFactory( qtui.QWidgetFactory, Singleton ):
  '''
  This class manages the creation of custom widgets embedded in C{*.ui} files.
  In order to work, instance of CustomizedQWidgetFactory must be registered
  once in an C{Qt} global set of QWidgetFactory instances::
    import qt, qtui
    from soma.qt3gui.api import CustomizedQWidgetFactory
    qApp = qt.QApplication( sys.argv )
    customizedQWidgetFactory = CustomizedQWidgetFactory()
    qtui.QWidgetFactory.addWidgetFactory( customizedQWidgetFactory )
  
  Then, all custom widgets are created by factories that must be registered
  with L{addWidgetFactory}::
    class MyWidget( qt.QWidget ):
      pass
    uiFactory = WidgetFactory( 'myDesignerWidget.ui' )
  
    customizedQWidgetFactory.addWidgetFactory( 'CustomWidget1', MyWidget )
    customizedQWidgetFactory.addWidgetFactory( 'CustomWidget2', uiFactory )
  
  Registered class name (such as C{'CustomWidget1'} and C{'CustomWidget2'} in 
  the previous example) can be used in C{*.ui} files that are processed by any
  L{WidgetFactory} instance.
  '''
  
  def __singleton_init__( self ):
    qtui.QWidgetFactory.__init__( self )
    self.__registeredFactories = {}
    # It is mandatory to keep a Python reference to any widget that need
    # to preserve the link between C++ widget and Python widget. These
    # references are kept in self._preservedSipWidgets and must be removed by
    # a call to _widgetsPostprocessing after the call to
    # QWidgetFactory.create().
    self._preservedSipWidgets = set()
  
  
  def addWidgetFactory( self, className, widgetFactory ):
    '''
    Register a Widget factory that will create custom widgets whose class name
    is C{className}. If a factory is already registered for C{className}, 
    C{KeyError} is raised.
    '''
    existingFactory = self.__registeredFactories.get( className )
    if existingFactory is None:
      self.__registeredFactories[ className ] = widgetFactory
    else:
      raise KeyError( 'A WidgetFactory is already registered for widget class ' + className )


  def removeWidgetFactory( self, className ):
    '''
    Remove a factory previously registered with L{addWidgetFactory}. Returns
    the removed factory or C{None} if no factory is registered for C{className}.'''
    return self.__registeredFactories.pop( className )
  
  
  def createWidget( self, className, parent, name ):
    '''
    This method is called by C{qtui.QWidgetFactory.create} when a custom
    widget class is encountered. It find the appropriate widget factory
    according to C{className} and call it with two parameters: C{parent}
    and C{name}.
    '''
    className = str( className )
    widgetFactory = self.__registeredFactories.get( className )
    if widgetFactory is not None:
      w = widgetFactory( parent, name )
      self._preservedSipWidgets.add( w )
      w._qwidgetFactory = self
    else:
      # We cannot know, at this point, what to do with invalid custom widgets.
      # Therefore, invalid widgets are simple QWidgets with attribute 
      # _invalid_custom_widget set to the class name.
      w = qt.QWidget( parent, name )
      w._invalid_custom_widget = className
    return w


  def _widgetsPostprocessing( mainWidget, processChildWidget=None ):
    '''
    Anytime L{qtui.QWidgetFactory.create} is called on a designer file that may
    contain custom widgets, this function must be called to cleanup  a global
    list of all custom widgets. To avoid bothering about this, use 
    L{soma.qt3gui.api.createWidget} or 
    L{soma.qt3gui.api.WidgetFactory}.
    
    It is mandatory to keep a Python reference to any widget that need to
    preserve the link between C++ widget and Python widget. These references
    are kept in C{CustomizedQWidgetFactory()._preservedSipWidgets} 
    (L{CustomizedQWidgetFactory} is a L{Singleton}) and must be removed by a 
    call to _widgetsPostprocessing after the call to
    C{QWidgetFactory.create()}.
    '''
    for childWidget in mainWidget.queryList( 'QWidget', None ):
      qwidgetFactory = getattr( childWidget, '_qwidgetFactory', None )
      if qwidgetFactory is not None:
        del childWidget._qwidgetFactory
        qwidgetFactory._preservedSipWidgets.discard( childWidget )
      if processChildWidget is not None:
        processChildWidget( mainWidget, childWidget )
  _widgetsPostprocessing = staticmethod( _widgetsPostprocessing )


#------------------------------------------------------------------------------
def createWidget( uiFile, parent=None, name=None,
                  translationFile = None,
                  ignoreInvalidCustomWidgets=False ):
  '''
  You can use C{createWidget} if you need to create a widget from a C{*.ui} 
  file only once. It creates a L{WidgetFactory} and call it to create the 
  widget. C{widget = createWidgetFactory( uiFile, parent, name, ... )} is a 
  shortcut for::
    factory = WidgetFactory( uiFile, ... )
    widget = factory( parent, name )
  
  @see: L{WidgetFactory}
  '''
  return WidgetFactory( 
    uiFile,
    translationFile = translationFile,
    ignoreInvalidCustomWidgets = ignoreInvalidCustomWidgets 
  )( parent, name )

