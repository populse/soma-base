"""
Module content
==============

The content of soma module is composed of many submodules. However,
all important items can be imported from soma.api. For example, if
one wants to use the Application class defined in the module
soma.application, he just have to use the following import
statement::

  from soma.api import Application

Main classes
------------
- :class:`Application <soma.application.Application>`: an Application instance
  contains all information that is shared across all modules of an application.
- :class:`Controller <soma.controller.controller.Controller>`

Advanced classes
----------------
- :class:`Singleton <soma.singleton.Singleton>`: A class deriving from
  Singleton can have only one instance.
"""


from .singleton import Singleton
from .application import Application
from .controller import Controller
from .undefined import undefined
from .proxy import DictWithProxy, ListWithProxy
