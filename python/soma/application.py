# -*- coding: utf-8 -*-
__docformat__ = "restructuredtext en"


import os
import platform
import sys
import traceback
from os.path import dirname

from soma.controller import Controller, Directory, field
from soma.singleton import Singleton

# -------------------------------------------------------------------------


class Application(Singleton, Controller):
    """Any program using soma should create an Application instance to manage
    its configuration and to store any kind of value that have to be global to
    the program."""

    # TODO: reimplement read only attributes in controller
    # name = ReadOnly(desc='Name of the application')
    # version = ReadOnly()

    # TODO: make it possible to add metaattributes such as "desc"
    plugin_modules: field(type_=list[str], default_factory=lambda: [])
    "List of Python module to load after application configuration"

    def __singleton_init__(self, name=None, version=None, *args, **kwargs):
        """Replaces __init__ in Singleton."""
        super().__singleton_init__(*args, **kwargs)
        # Warning : Traits bug
        # Using the trait Directory() might instantiate a QApplication (seems to depend on the
        # traits release). If it is declared in the class, the QApplication is instantiated at
        # module importation which prevent to customize QApplication.
        self.add_field(
            "install_directory",
            Directory,
            doc="Base directory where the application is installed",
        )
        self.add_field(
            "user_directory",
            Directory,
            doc="Base directory where user specific information can be find",
        )
        self.add_field(
            "application_directory",
            Directory,
            doc="Base directory where application specific information can be find",
        )
        self.add_field(
            "site_directory",
            Directory,
            doc="Base directory where site specific information can be find",
        )
        self._controller_factories = None

        if name is None:
            name = os.path.basename(sys.argv[0])
        self.name = name
        self.version = version
        self.loaded_plugin_modules = {}

    def initialize(self):
        """This method must be called once to setup the application."""
        self.install_directory = dirname(dirname(dirname(__file__)))
        homedir = os.getenv("HOME")
        if not homedir:
            homedir = ""
            if platform.system() == "Windows":
                homedir = os.getenv("USERPROFILE")
                if not homedir:
                    homedir = os.getenv("HOMEPATH")
                    if not homedir:
                        homedir = "\\"
                    drive = os.getenv("HOMEDRIVE")
                    if not drive:
                        drive = os.getenv("SystemDrive")
                        if not drive:
                            drive = os.getenv("SystemRoot")
                            if not drive:
                                drive = os.getenv("windir")
                            if drive and len(drive) >= 2:
                                drive = drive[:2]
                            else:
                                drive = ""
                    homedir = drive + homedir
        if homedir and os.path.exists(homedir):
            self.user_directory = homedir

        # Load early plugin modules
        for plugin_module in self.plugin_modules:
            module = self.load_plugin_module(plugin_module)
            if module is not None:
                self.loaded_plugin_modules[plugin_module] = module
                init = getattr(module, "call_before_application_initialization", None)
                if init is not None:
                    init(self)

        appdir = os.path.normpath(os.path.dirname(os.path.dirname(sys.argv[0])))
        if os.path.exists(appdir):
            self.application_directory = appdir

        sitedir = os.path.join("/etc", self.name)
        if os.path.exists(sitedir):
            self.site_directory = sitedir

        # Load plugin modules
        for plugin_module in self.plugin_modules:
            module = self.loaded_plugin_modules.get(plugin_module)
            if module is None:
                module = self.load_plugin_module(plugin_module)
            if module is not None:
                self.loaded_plugin_modules[plugin_module] = module
                init = getattr(module, "call_after_application_initialization", None)
                if init is not None:
                    init(self)

    @staticmethod
    def load_plugin_module(plugin_module):
        """This method loads a plugin module. It imports the module without raising
        an exception if it fails."""
        try:
            __import__(plugin_module, level=0)
            return sys.modules[plugin_module]
        except Exception:
            # Python 2.6 hack : print_last may fail here (maybe due to threads management)
            # traceback.print_last()
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
        return None
