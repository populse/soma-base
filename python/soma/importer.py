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
Utility classes and functions for Python import and sip namespace renaming.

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
import sys, imp, types

from soma.functiontools import partial
from soma.singleton import Singleton


class ExtendedImporter( Singleton ) :
  '''
    C{ExtendedImporter} is used to import external modules in a module managing rules that allow ro rename and delete or do anything else on the imported package. As imported packages could modify each others, all the registered rules are applied after each import using this C{ExtendedImporter}.
  '''
  extendedModules = dict()

  def importInModule( self, moduleName, globals, locals, importedModuleName, namespacesList = [], handlersList = None, *args, **kwargs ) :
    '''
    This method is used to import a module applying rules (rename rule, delete rule, ...) .

    @moduleName string: name of the module to import into.
    @globals dict: globals dictionary of the module to import into.
    @locals dict: locals dictionary of the module to import into.
    @importedModuleName string: name of the imported module.
    @namespacesList list: a list of rules concerned namespaces for the imported module.
    @handlersList list: a list of handlers to apply during the import of the module.
    '''
    if ( handlersList is None ) :
      # Add default handler
      handlersList = [GenericHandlers.moveChildren]

    # Import the module
    # Note : Pyro overloads __import__ method and usual keyword 'level' of
    # __builtin__.__import__ is not supported
    importedModule = __import__( importedModuleName, globals,  locals, [] )

    if not moduleName:
      moduleName = locals['__name__']
    else:
      moduleName = locals['__name__'] + '.' + moduleName
    # Add the extended module to the list if not already exists
    if moduleName not in self.extendedModules :
      extendedModule = ExtendedModule( moduleName, globals, locals )
      self.extendedModules[ moduleName ] = extendedModule
    else :
      extendedModule = self.extendedModules[ moduleName ]

    if len(namespacesList) == 0 :
      extendedModule.addHandlerRules( importedModule, handlersList, importedModuleName, *args, **kwargs  )
    else :
      for namespace in namespacesList :
        extendedModule.addHandlerRules( importedModule, handlersList, namespace, *args, **kwargs )

    self.applyRules( )

  def applyRules( self ) :
    '''
    This method apply rules for each extended module.
    '''
    for extendedModule in self.extendedModules.values() :
      extendedModule.applyRules()

class ExtendedModule :
  '''
  Register a series of rules to apply during the import process of the extended module.
  An extended module is able to refer to other modules and to apply rules to these other
  modules. The extended module manages the globals and locals variables declared for the module.
  Each rule contains the module to which it refers, and the handlers to call for the rule to apply. The calling order is the registering order.
  '''
  def __init__( self, moduleName, globals, locals ) :
    self.rules = dict()
    self.__name__ = moduleName
    self.globals = globals
    self.locals = locals

  def addHandlerRules( self, module, handlersList = [], *args, **kwargs ) :
    '''
    This method is used to add handler rules (renaming rule, deleting rule, ...) .

    @module module: module object to apply rules to.
    @handlersList list: a list of handlers to the module.
    '''
    for handler in handlersList :
      self.addPartialRules( module, [ partial( handler, *args, **kwargs ) ] )


  def addPartialRules( self, module, partialsList = [] ) :
    '''
    This method is used to add handler rules (renaming rule, deleting rule, ...) .

    @module module: module object to apply rules to.
    @partialsList list: a list of C{partial} object that will be called during the import of the module.
    '''
    key = module

    if key not in self.rules :
      self.rules[ key ] = list()

    for handler in partialsList :
      if handler not in self.rules[ key ] :
        self.rules[ key ].append( handler )

  def applyRules( self ) :
    '''
    Apply the C{partial} handler rules (renaming rule, deleting rule, ...) for the C{ExtendedModule}.
    '''
    for referedModule, partialsList in self.rules.items() :
      for handler in partialsList :
        # Call the handlers list for the found object
        handler.__call__( self, referedModule )

class GenericHandlers :
  '''
  Static generic handlers used as import rules.
  '''
  @staticmethod
  def moveChildren( namespace, extendedModule, referedModule ) :
    '''
    This static method is used to move child objects of a refered module to the extended module.

    @namespace string: namespace of the referedModule to get objects to move from.
    @extendedModule ExtendedModule: C{ExtendeModule} object into which move objects.
    @referedModule module: refered module object to get objects to move from.
    '''

    # Get module names
    newName = extendedModule.__name__

    # Get extended module locals declaration
    locals = extendedModule.locals

    # Get the old object in module
    object = ExtendedImporterHelper.getModuleObject( referedModule, namespace )

    if object is not None :

      # Changes child objects locals declaration
      for childName in object.__dict__.keys() :
        # in sip >= 4.8, obj.__dict__[key] and getattr(obj, key)
        # do *not* return the same thing for functions !
        childObject = getattr( object, childName )
        if not childName.startswith("__"):

          locals[ childName ] = childObject

      # Changes child objects module, recursively and avoiding loops
      stack = []
      done = []
      for ( childName, childObject ) in locals.iteritems() :
        if not childName.startswith("__") \
          and hasattr( childObject, '__module__' ) \
          and childObject.__module__ == referedModule.__name__ :
            stack.append( childObject )
      while stack:
        childObject = stack.pop(0)
        done.append( childObject )
        if hasattr( childObject, '__name__' ) \
          and hasattr( childObject, '__module__' ) \
            and childObject.__module__ == referedModule.__name__ :
          try:
            childObject.__module__ = newName
            if hasattr( childObject, '__dict__' ):
              for x in childObject.__dict__.keys():
                y = getattr( childObject, x )
                if not x.startswith( '__' ) \
                  and y not in stack and y not in done:
                  stack.append( y )
          except Exception, e:
            del e


  # Declare a function to delete non generics Reader/Writer objects
  @staticmethod
  def removeChildren( namespace, prefixes, extendedModule, referedModule ) :
    '''
    This static method is used to remove children from the extended module.

    @namespace string: namespace of the referedModule.
    @prefixes list: list of prefixes of objects to remove.
    @extendedModule ExtendedModule: C{ExtendeModule} object to remove objects from.
    @referedModule module: refered module object.
    '''
    locals = extendedModule.locals

    # Remove Reader and Writer classes because a generic class
    # to manage it exists
    for key in locals.keys():
      if not key.startswith('__') :
        for prefix in prefixes :
          if key.startswith( prefix ) :
            del locals[key]

class ExtendedImporterHelper :
  '''
  Static methods declared to help extended import process.
  '''

  @staticmethod
  def getModuleObject( module, name ) :
    '''
    This static method is used to get an object contained in the namespace of a module.

    @name string: complete name including namespace of the object to get.
    @module module: module object to get objects from.

    @return:  Object found in the module or None if no object was found.
    '''

    # Split the name of the object
    # but keep the 1st element unsplit like the module name
    # if needed.
    mname = None
    if name.startswith( module.__name__ ):
      mname = module.__name__
    else:
      mname = module.__name__.split( '.' )[-1]
      if not name.startswith( mname ):
        mname = None
    if mname is not None:
      listName = [ module.__name__ ]
      if len( name ) > len( mname ):
        listName = tuple( listName \
          + name[ len(mname) + 1: ].split( '.' ) )
      else:
        listName = tuple( listName )
    else:
      listName = tuple( name.split('.') )

    # Get the object that is matching the rule in the tree
    return ExtendedImporterHelper.getMatchingObject( module, listName )

  @staticmethod
  def getMatchingObject( object, listName, level = 0 ) :
    '''
    This static method is used to get an object contained in another object.

    @module object: object to get objects from.
    @listName list: complete name including name hierarchy split in list.

    @return:  Object found in the hierarchy or None if no object was found.
    '''
    result = None

    name = getattr( object, '__name__', None )

    if level < ( len( listName ) - 1 ) :
      if ( listName[ level ] == name ) :
        if( hasattr( object, '__dict__' ) ) :
          for child in object.__dict__.values() :
            # Recursive call to go through the hierarchy
            result = ExtendedImporterHelper.getMatchingObject( child, listName, level + 1 )

            if ( result is not None ) :
              break
    elif level == ( len( listName ) - 1 ) :
      if ( listName[ level ] == name ) :
        result = object

    return result
