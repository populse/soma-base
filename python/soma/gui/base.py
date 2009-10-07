# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.

'''
Customizable framework for automatic creation of
U{Turbogears<http://docs.turbogears.org>} widgets to view or edit any
Python object. This framework is especially designed to work with 
L{soma.signature} module but it can be used in many other contexts.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys

from soma.translation import translate as _
from soma.singleton import Singleton
from soma.signature.api import DataType
from soma.notification import Notifier

#-------------------------------------------------------------------------------
class ApplicationBaseGUI( Singleton ):
  '''
  This class manage the creation of widgets for Python objects edition at
  global (I{i.e.} application) level.
  '''

  _definedGUI = {}

  def instanceGUI( instance, cls=None, _prefix='', _definedGUI=_definedGUI, _suffix='' ):
    '''
    Find the L{GUI} instance corresponding to an object. This function
    returns C{object._GUI} or C{None} if it is not defined. But first, it
    tries to associate all the parent classes of C{instance} with a 
    L{GUI} derived class by calling L{classGUI}.
    '''
    if cls is not None:
      if not isinstance( instance, cls ):
        raise TypeError( _( 'object of type %(type)s is not an instance of class %(cls)s' ) % {
                            'type': str(instance.__class__),
                            'cls': str( cls ) } )
      gui = ApplicationBaseGUI.classGUI( cls, _prefix=_prefix, _definedGUI=_definedGUI, _suffix=_suffix )
    else:
      cls = instance.__class__
      gui = ApplicationBaseGUI.classGUI( cls, _prefix=_prefix, _definedGUI=_definedGUI , _suffix=_suffix )
    if gui is None:
      raise RuntimeError( _( 'Cannot find GUI for %s' ) \
                          % ( str(instance), ) )
    if isinstance( instance, DataType ):
      return gui( instance )
    else:
      return gui( cls )
  instanceGUI = staticmethod( instanceGUI )


  def classGUI( cls, _prefix='', _definedGUI=_definedGUI, _suffix='' ):
    '''
    Ensure that the module defining the L{GUI} derived class associated with
    class C{cls} has been loaded. The name of a L{GUI} derived class
    associated to a class C{C} is always the name of {C} postfixed with 
    C{'_GUI'}. For instance, C{class MyClass( object ):} is associated to
    C{class MyClass_GUI( GUI ):}. This function look into several modules
    (eventually loading them) to find a L{GUI} derived class with the
    appropriate name:
      - In the module where class C{cls} has been defined. Let's call this 
        module the class module.
      - In a module named as the class module with C{'_gui'} postfix and
        defined in a C{gui} directory located in the same directory as the
        class module.
      - In a module named as the class module with C{'_gui'} postfix and
        defined in a C{gui} directory located in the parent directory of the
        class module.
    
    Example:
      If a class C{TestClass} has been defined in /home/me/python/tests/test_class.py, if a class C{TestClass_GUI} is defined.
    @todo: documentation not finished.
    '''
    suffixUpper = _suffix.upper()
    suffixLower = _suffix.lower()
    suffixTitle = _suffix.title()
    
    GUI = _definedGUI.get( cls )
    if GUI is None:
      stack = [ cls ]
      while stack:
        currentClass = stack.pop( 0 )
        stack += [ c for c in currentClass.__bases__ if
                   c not in _definedGUI ]
        GUIName = _prefix + currentClass.__name__ + '_' + suffixTitle + 'GUI'
        # Get the module where the data type is defined
        definitionModuleName = currentClass.__module__
        definitionModule = sys.modules.get( definitionModuleName )
        # Check if GUIName is defined in the definition module
        GUI = None
        if definitionModule is not None:
          GUI = getattr( definitionModule, GUIName, None )
        if GUI is None:
          # Try to import a module with '_gui' extension and to
          # find the ObjectGui in it
          try:
            GUIModuleName = definitionModuleName + '_' + suffixLower + 'gui'
            #print '!GUI! try to import:', GUIModuleName
            __import__( GUIModuleName )
            #print '!GUI! successful import:', GUIModuleName
            GUIModule = sys.modules[ GUIModuleName ]
            GUI = getattr( GUIModule, GUIName, None )
          except ImportError:
            GUIModuleName = definitionModuleName.split( '.' )
            for GUIModuleName in (
                '.'.join( GUIModuleName[:-1] + [ suffixLower + 'gui', GUIModuleName[-1] ] ) + '_' + suffixLower + 'gui',
                '.'.join( GUIModuleName[:-2] + [ suffixLower + 'gui', GUIModuleName[-1] ] ) + '_' + suffixLower + 'gui',
              ):
              try:
                #print '!GUI! try to import:', GUIModuleName
                __import__( GUIModuleName )
                #print '!GUI! successful import:', GUIModuleName
                GUIModule = sys.modules[ GUIModuleName ]
                GUI = getattr( GUIModule, GUIName, None )
                break
              except ImportError:
                pass
        #print '!GUI!', currentClass, '-->', GUI
        _definedGUI[ currentClass ] = GUI
    for c in cls.__mro__:
      GUI = _definedGUI.get( c )
      if GUI is not None: break
    return GUI
  classGUI = staticmethod( classGUI )
  
#-------------------------------------------------------------------------------
class GUI( object ):
  '''
  This class manage the creation of gui for Python objects edition at
  object level. 
  '''
  def editionWidget( self, object, parent=None, name=None, live=False ):
    '''
    Create a widget for editing an object.
    '''
  
  
  def closeEditionWidget( self, editionWidget ):
    '''
    Close a widget (and free associated ressources) created by
    C{self.L{editionWidget}}.
    '''
  
  
#  def multipleEditionWidget( self, objects, container=None, attributeName=None,
#                     parent=None, name=None, live=False ):
  
  
#  def closeMultipleEditionWidget( self, multipleEditionWidget ):
  
  
  def labelWidget( self, object, label, editionWidget=None,
                   parent=None, name=None, live=False ):
    '''
    Create a label widget for displaying a label associated with the edition
    widget. 
    '''
  
  
  def closeLabelWidget( self, labelWidget ):
    '''
    Close a widget (and free associated ressources) created by
    C{self.L{labelWidget}}.
    '''
    if labelWidget is not None:
      labelWidget.close()
  
  
  def setObject( self, editionWidget, object ):
    '''
    Modify C{object} to make it reflect the current state of C{editionWidget}.
    This method must be defined for mutable DataType.
    @see: L{getPythonValue}
    '''
  
  
  def getPythonValue( self, editionWidget ):
    '''
    Return a value that represent the current state of C{editionWidget}. This
    value must be a valid value for the L{DataType}.
    This method must be defined for immutable DataType.
    @see: L{setObject}
    '''

  def updateEditionWidget( self, editionWidget, object ):
    '''
    Update C{editionWidget} to reflect the current state of C{object}.
    This method must be defined for both mutable and immutable DataType.
    '''
  
  def __init__( self, dataType ):
    '''
    Constructors of L{GUI} (and its derived classes) must accept a single
    C{dataType} parameter representing the type of data that can be view or 
    edited by this GUI element.
    @param dataType: type data that this L{GUI} can handle. This can be any 
    value accepted by L{DataType.dataTypeInstance}.
    '''
    
    #: L{DataType} instance representing the type of data that is handled by 
    #: this GUI element.
    self.dataTypeInstance = DataType.dataTypeInstance( dataType )
    #: For immutable L{DataType}, this notifier must be called, with the
    #: edition widget as parameter, each time the user makes a modification on 
    #: the widget.
    self.onWidgetChange = Notifier( 1 )
  
  
