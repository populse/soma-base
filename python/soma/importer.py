# -*- coding: utf-8 -*-

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

* author: Yann Cointepas
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import
__docformat__ = "restructuredtext en"

import sys
import imp
import types
import six
import importlib

from soma.functiontools import partial
from soma.singleton import Singleton


# list of namespace objects that should not be patched to avoid a side effect
# in sip imported namespaces: we must not access their attributes during
# imports.
__namespaces__ = ['soma', 'aims', 'carto', 'anatomist']


class ExtendedImporter(Singleton):

    '''
      ExtendedImporter is used to import external modules in a module managing rules that allow ro rename and delete or do anything else on the imported package. As imported packages could modify each others, all the registered rules are applied after each import using this ExtendedImporter.
    '''
    extendedModules = dict()

    def importInModule(self, moduleName, globals, locals, importedModuleName,
                       namespacesList=[], handlersList=None, *args, **kwargs):
        '''
        This method is used to import a module applying rules (rename rule, delete rule, ...) .

        Parameters
        ----------
        moduleName: string
            name of the module to import into (destination, not where to find
            it).
        globals: dict
            globals dictionary of the module to import into.
        locals: dict
            locals dictionary of the module to import into.
        importedModuleName: string
            name of the imported module. Normally relative to the current
            calling module package.
        namespacesList: list
            a list of rules concerned namespaces for the imported module.
        handlersList: list
            a list of handlers to apply during the import of the module.
        '''

        if (handlersList is None):
            # Add default handler
            handlersList = [GenericHandlers.moveChildren]

        if not moduleName:
            moduleName = locals['__name__']
        elif moduleName.startswith('.'):
            moduleName = locals['__name__'] + moduleName

        package = locals['__package__'] or locals['__name__']

        # Import the module
        # Note : Pyro overloads __import__ method and usual keyword 'level' of
        # __builtin__.__import__ is not supported
        importedModule = importlib.import_module('.' + importedModuleName,
                                                 package)
        sys.modules[importedModuleName.split('.')[-1]] = importedModule

        # Add the extended module to the list if not already exists
        if moduleName not in self.extendedModules:
            extendedModule = ExtendedModule(moduleName, globals, locals)
            self.extendedModules[moduleName] = extendedModule
        else:
            extendedModule = self.extendedModules[moduleName]

        if len(namespacesList) == 0:
            extendedModule.addHandlerRules(
                importedModule, handlersList, importedModuleName, *args,
                **kwargs)
        else:
            for namespace in namespacesList:
                extendedModule.addHandlerRules(
                    importedModule, handlersList, namespace, *args, **kwargs)

        self.applyRules()

    def applyRules(self):
        '''
        This method apply rules for each extended module.
        '''
        for extendedModule in self.extendedModules.values():
            extendedModule.applyRules()


class ExtendedModule(object):

    '''
    Register a series of rules to apply during the import process of the
    extended module. An extended module is able to refer to other modules and
    to apply rules to these other modules. The extended module manages the
    globals and locals variables declared for the module.

    Each rule contains the module to which it refers, and the handlers to call
    for the rule to apply. The calling order is the registering order.
    '''

    def __init__(self, moduleName, globals, locals):
        self.rules = dict()
        self.__name__ = moduleName
        self.globals = globals
        self.locals = locals

    def addHandlerRules(self, module, handlersList=[], *args, **kwargs):
        '''
        This method is used to add handler rules (renaming rule, deleting rule, ...) .

        Parameters
        ----------
        module: module
            module object to apply rules to.
        handlersList: list
            a list of handlers to the module.
        '''
        for handler in handlersList:
            self.addPartialRules(
                module, [partial(handler, *args, **kwargs)])

    def addPartialRules(self, module, partialsList=[]):
        '''
        This method is used to add handler rules (renaming rule, deleting rule, ...) .

        Parameters
        ----------
        module: module
            module object to apply rules to.
        partialsList: list
            a list of :func:`functools.partial` objects that will be called
            during the import of the module.
        '''
        key = module

        if key not in self.rules:
            self.rules[key] = list()

        for handler in partialsList:
            if handler not in self.rules[key]:
                self.rules[key].append(handler)

    def applyRules(self):
        '''
        Apply the :func:`functools.partial` handler rules (renaming rule, deleting rule, ...) for the :class:`ExtendedModule`.
        '''
        for referedModule, partialsList in self.rules.items():
            for handler in partialsList:
                # Call the handlers list for the found object
                handler.__call__(self, referedModule)


class GenericHandlers(object):

    '''
    Static generic handlers used as import rules.
    '''
    @staticmethod
    def moveChildren(namespace, extendedModule, referedModule):
        '''
        This static method is used to move child objects of a refered module to the extended module.

        Parameters
        ----------
        namespace: string
            namespace of the referedModule to get objects to move from.
        extendedModule: ExtendedModule
            :class:`ExtendedModule` object into which move objects.
        referedModule: module
            refered module object to get objects to move from.
        '''

        # during this whole function we should avoid tu use
        # getattr(mobject, something) (directly or indirectly) because it
        # breaks things in sip imports later.

        # Get module names
        newName = extendedModule.__name__

        # Get extended module locals declaration
        locals = extendedModule.locals

        # Get the old object in module
        mobject = ExtendedImporterHelper.getModuleObject(
            referedModule, namespace)

        if mobject is not None:

            # Changes child objects locals declaration
            for childName \
                    in list(object.__getattribute__(mobject, '__dict__').keys()):
                # in sip >= 4.8, obj.__dict__[key] and getattr(obj, key)
                # do *not* return the same thing for functions !
                # object.__getattribute__(mobject, childName) returns a
                # "methoddescriptor", whereas
                # getattr(mobject, childName) returns a
                # "builtin_function_or_method", which is what we want

                # childObject = object.__getattribute__(mobject, childName)
                childObject = getattr(mobject, childName)
                if not childName.startswith("__"):

                    locals[childName] = childObject

            # Changes child objects module, recursively and avoiding loops
            stack = []
            done = []
            for (childName, childObject) in six.iteritems(locals):
                if not childName.startswith("__"):
                    try:
                        mod = object.__getattribute__(childObject,
                                                      '__module__')
                        if mod == referedModule.__name__:
                            stack.append(childObject)
                    except AttributeError:
                        pass

            # set new module on objects

            while stack:
                childObject = stack.pop(0)
                done.append(childObject)
                try:
                    name = object.__getattribute__(childObject, '__name__')
                    mod = object.__getattribute__(childObject, '__module__')
                except AttributeError:
                    continue
                try:
                    # skip namespace objects
                    if name not in __namespaces__:
                        childObject.__module__ = newName
                except Exception as e:
                    pass
                try:
                    d = object.__getattribute__(childObject, '__dict__')
                except AttributeError:
                    continue
                for x in list(d.keys()):
                    try:
                        # y = object.__getattribute__(childObject, x)
                        y = getattr(childObject, x)
                        if not x.startswith( '__' ) \
                                and y not in stack and y not in done:
                            stack.append(y)
                    except AttributeError:
                        pass

    # Declare a function to delete non generics Reader/Writer objects
    @staticmethod
    def removeChildren(namespace, prefixes, extendedModule, referedModule):
        '''
        This static method is used to remove children from the extended module.

        Parameters
        ----------
        namespace: string
            namespace of the referedModule.
        prefixes: list
            list of prefixes of objects to remove.
        extendedModule: ExtendedModule
            :class:`ExtendedModule` object to remove objects from.
        referedModule: module
            refered module object.
        '''
        locals = extendedModule.locals

        # Remove Reader and Writer classes because a generic class
        # to manage it exists
        to_remove = []
        for key in locals.keys():
            if not key.startswith('__'):
                for prefix in prefixes:
                    if key.startswith(prefix):
                        to_remove.append(key)
        for key in to_remove:
            del locals[key]


class ExtendedImporterHelper(object):

    '''
    Static methods declared to help extended import process.
    '''

    @staticmethod
    def getModuleObject(module, name):
        '''
        This static method is used to get an object contained in the namespace of a module.

        Parameters
        ----------
        name: string
            complete name including namespace of the object to get.
        module: module
            module object to get objects from.

        Returns
        -------
        object:
            Object found in the module or None if no object was found.
        '''

        # Split the name of the object
        # but keep the 1st element unsplit like the module name
        # if needed.
        if name == '':
            return module

        names = name.split('.')
        if not hasattr(module, names[0]) and module.__name__.split('.')[-1] == names[0]:
            names = names[1:]
        obj = module
        while names:
            mname = names.pop(0)
            if not hasattr(obj, mname):
                return None
            obj = getattr(obj, mname)
        return obj


def execfile(filename, globals=None, locals=None):
    ''' Replacement for python2 execfile()
    six.exec_() needs an open file, hence this wrapper for convenience.
    Files are open with UTF-8 encoding on python3.
    '''
    fopts = {} if six.PY2 else {'encoding': 'utf-8'}
    with open(filename, **fopts) as f:
        six.exec_(f, globals, locals)
