# -*- coding: utf-8 -*-
#
# Soma-base - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

"""Compatibility module for PyQt and PySide. Currently supports PyQt4,
PySide, and PyQt5.
This modules handles differences between PyQt and PySide APIs and behaviours,
and offers a few functions to make it easier to build neutral GUI code, which
can run using either backend.

The main function here is set_qt_backend() which must be called to initialize
the appropriate backend. Most functions of this module assume set_qt_backend()
has been called first to setup internal variables.

Note that such compatibility generally requires to use PyQt4 with SIP API
version 2, ie do not use QString, QVariant, QDate and similar classes, but
directly convert to/from python types, which is also PySide behaviour. The
qt_backend module switches to this API level 2, but this only works before the
PyQt modules are imported, thus it may fail if PyQt has already be imported
without such settings.

Qt submodules can be imported in two ways:

>>> from soma.qt_gui import qt_backend
>>> qt_backend.import_qt_submodule('QtWebKit')

or using the import statement:

>>> from soma.qt_gui.qt_backend import QtWebKit

in the latter case, set_qt_backend() will be called automatically to setup the
appropriate Qt backend, so that the use of the backend selection is more
transparent.
"""

import logging
import sys
import os
import importlib
import inspect
import types


getfullargspec = getattr(
    inspect, "getfullargspec", getattr(inspect, "getargspec", None)
)


# make qt_backend a fake module package, with Qt modules as sub-modules
__package__ = __name__
__spec__ = type(__spec__)(
    name=f"{__name__}.__init__",
    loader=__spec__.loader,
    origin=f"{__spec__.origin[:-3]}/__init__.py",
)
__path__ = [os.path.dirname(__file__)]

# internal variable to avoid warning several times
_sip_api_set = False

qt_backend = None
make_compatible_qt5 = False
headless = False
need_opengl = True


class QtImporter(object):
    debug_done = False

    def find_spec(self, fullname, path=None, target=None):
        modsplit = fullname.split(".")
        modpath = ".".join(modsplit[:-1])
        module_name = modsplit[-1]
        if modpath != __name__ or fullname == "sip":
            return None
        set_qt_backend()
        qt_backend = get_qt_backend()
        qt_module = get_qt_module()
        if make_compatible_qt5 and qt_backend in ("PyQt4", "PySide"):
            if module_name == "QtWidgets":
                module_name = "QtGui"
            elif module_name == "QtWebKitWidgets":
                module_name = "QtWebKit"
        if qt_backend in ("PySide", "PyQt6") and module_name == "Qt":
            module_name = "QtGui"
        try:
            found = importlib.util.find_spec(f".{module_name}", qt_module.__name__)
            if found:
                found.name = f"{qt_backend}.{modsplit[-1]}"
        except ImportError:
            found = None
        if found is None:
            if module_name == "sip":
                # importing qt_backend.sip and sip is not installed in
                # PyQt<x>: use the regular 'sip'
                try:
                    found = importlib.util.find_spec(module_name)
                    if found is not None:
                        found.loader = self
                        return found
                    else:
                        return None
                except ImportError:
                    return None
        if found is None:
            return None
        found.loader = self
        return found

    def exec_module(self, module):
        # this method can be used to execute the module in the module
        # namespace, which can include adding variables, functions, etc.
        pass

    def create_module(self, spec=None, name=None):
        if name is None:
            name = spec.name
        qt_backend = get_qt_backend()
        module_name = name.split(".")[-1]
        imp_module_name = module_name
        headless_res = None

        if headless and module_name not in ("sip", "QtCore", "QtGui"):
            # we use ..headless instead of .headless because we have
            # modified __package__
            from ..headless import setup_headless

            headless_res = setup_headless(need_opengl=need_opengl)

        if make_compatible_qt5:
            if module_name == "QtWidgets":
                imp_module_name = "QtGui"
            elif module_name == "QtWebKitWidgets":
                imp_module_name = "QtWebKit"

        if qt_backend in ("PyQt4", "PyQt5", "PyQt6") or module_name == "sip":
            # import the right sip module
            try:
                __import__("%s.sip" % qt_backend)
                sip = sys.modules.get("%s.sip" % qt_backend)
                if sip is not None:
                    sys.modules["sip"] = sip
                else:
                    sip = sys.modules.get("sip")
            except ImportError:
                import sip

        if module_name == "sip":
            sys.modules[name] = sip
            return sip

        if imp_module_name == "Qt" and (
            qt_backend in ("PySide", "PyQt6") or sip.SIP_VERSION >= 0x060000
        ):
            # PySide and PyQt6 don't define the aggregating Qt module
            psmods = []
            base = name.split(".")[:-1]
            qt_mod = sys.modules[qt_backend]
            mods = set(
                [
                    x.split(".")[0]
                    for x in os.listdir(os.path.dirname(qt_mod.__file__))
                    if not x.startswith("_")
                ]
            )
            if "Qt" in mods:
                # PyQt5 + sip6 brings a Qt module, but which is empty. We thus
                # need to re-populate it as in PyQt6, but here the module
                # already exists: don't reload it.
                mods.remove("Qt")
            for mod in mods:
                try:
                    psmods.append(self.create_module(name=".".join(base + [mod])))
                except ImportError:
                    pass
            patch_main_modules(psmods)
            mod = sys.modules[".".join([qt_backend, "Qt"])]
            sys.modules["soma.qt_gui.qt_backend.Qt"] = mod
            if headless_res is not None and headless_res.qapp is None:
                headless_res.qapp = mod.QApplication(
                    [sys.argv[0], "-platform", "offscreen"]
                )
                sip.transferto(headless_res.qapp, None)
                # to prevent deletion just after now

            return mod

        __import__(".".join([qt_backend, imp_module_name]))
        module = sys.modules[".".join([qt_backend, imp_module_name])]
        # fixes: #13432 - Ubuntu 14.04 LTS: Importing some modules
        #                                   of scikit learn from
        #                                   brainvisa process raises segfault
        # ref: https://bioproj.extra.cea.fr/redmine/issues/13432
        if module_name == "uic" and qt_backend == "PyQt4":

            def _safe_load_plugin(plugin, plugin_globals, plugin_locals):
                def _safe_getFilter():
                    import sys
                    import DLFCN

                    res = plugin_locals["getFilter_orig"]()
                    sys.setdlopenflags(DLFCN.RTLD_NOW)

                    return res

                import os

                __import__(".".join(["PyQt4", "uic", "objcreator"]))
                uic = sys.modules[".".join([qt_backend, module_name])]
                res = uic.objcreator.load_plugin_orig(
                    plugin, plugin_globals, plugin_locals
                )

                # It seems that this function is sometimes called with a first
                # argument of type File, sometimes of type str. Both cases
                # should be handled by this switch.
                if hasattr(plugin, "name"):
                    filename = plugin.name
                else:
                    filename = plugin
                if os.path.splitext(os.path.basename(filename))[0] == "kde4":
                    # Replaces kde4 getFilter function
                    if "getFilter_orig" not in plugin_locals:
                        plugin_locals["getFilter_orig"] = plugin_locals["getFilter"]
                        plugin_locals["getFilter"] = _safe_getFilter

                return res

            __import__(".".join([qt_backend, module_name, "objcreator"]))
            uic = sys.modules[".".join([qt_backend, module_name])]
            # Replaces the load_plugin function in objcreator
            # uic.port_v2.load_plugin.load_plugin_orig \
            # = uic.port_v2.load_plugin.load_plugin
            # uic.port_v2.load_plugin.load_plugin = _safe_load_plugin
            if not hasattr(uic.objcreator, "load_plugin_orig"):
                uic.objcreator.load_plugin_orig = uic.objcreator.load_plugin
                uic.objcreator.load_plugin = _safe_load_plugin

        sys.modules[name] = module
        if make_compatible_qt5:
            if imp_module_name == "QtGui":
                from . import QtCore

                if qt_backend in ("PyQt4", "PySide"):
                    sys.modules[".".join([qt_backend, "QtWidgets"])] = module
                    patch_qt4_modules(QtCore, module)
                elif qt_backend in ("PyQt5", "PyQt6"):
                    qtwname = ".".join([qt_backend, "QtWidgets"])
                    if qtwname in sys.modules:
                        del sys.modules[qtwname]
                    __import__(qtwname)
                    qtwidgets = sys.modules[".".join([qt_backend, "QtWidgets"])]
                    patch_qt5_modules(QtCore, module, qtwidgets)
                    if module_name == "QtWidgets":
                        module = qtwidgets
            elif imp_module_name == "QtWebKit":
                if qt_backend in ("PyQt4", "PySide"):
                    sys.modules[".".join([qt_backend, "QtWebKitWidgets"])] = module
                elif qt_backend in ("PyQt5", "PyQt6"):
                    __import__(".".join([qt_backend, "QtWebKitWidgets"]))
                    qtwebkitwidgets = sys.modules[
                        ".".join([qt_backend, "QtWebKitWidgets"])
                    ]
                    patch_qt5_webkit_modules(module, qtwebkitwidgets)
                    if module_name == "QtWebKitWidgets":
                        module = qtwebkitwidgets
            ensure_compatible_qt5()

        if headless_res is not None and headless_res.qapp is None:
            qtwname = ".".join([qt_backend, "QtWidgets"])
            __import__(qtwname)
            mod = sys.modules[".".join([qt_backend, "QtWidgets"])]
            if mod.QApplication.instance() is None:
                headless_res.qapp = mod.QApplication(
                    [sys.argv[0], "-platform", "offscreen"]
                )
                sip.transferto(headless_res.qapp, None)
                # to prevent deletion just after now
        return module


# tune the import statement to get Qt submodules in this one
sys.meta_path.append(QtImporter())


def get_qt_backend():
    '''get currently setup or loaded Qt backend name: "PyQt4" or "PySide"'''
    global qt_backend
    if qt_backend is None:
        pyside = sys.modules.get("PySide")
        if pyside is not None:
            qt_backend = "PySide"
        else:
            backends = ("PyQt6", "PyQt5", "PyQt4")
            for backend in backends:
                pyqt = sys.modules.get(backend)
                if pyqt is not None:
                    qt_backend = backend
                    break
    return qt_backend


def set_qt_backend(backend=None, pyqt_api=1, compatible_qt5=None):
    """set the Qt backend.

    If a different backend has already setup or loaded, a warning is issued.
    If no backend is specified, try to guess which one is already loaded.

    If no backend is loaded yet, try to behave like IPython does.
    See: https://ipython.org/ipython-doc/dev/interactive/reference.html#pyqt-and-pyside

    More precisely this means:
    * If QT_API environment variable is not set, use PyQt5
    * if QT_API is set to "pyqt" or "pyqt4", use PyQt4, with PyQt API v2
    * if QT_API is set to "pyside", use PySide
    * if QT_API is set to "pyqt5", use PyQt5
    * if QT_API is set to "pyqt6", use PyQt6

    Moreover if using PyQt4, QtCore is patched to duplicate QtCore.pyqtSignal
    and QtCore.pyqtSlot as QtCore.Signal and QtCore.Slot. This is meant to ease
    code portability between both worlds.

    if compatible_qt5 is set to True, modules QtGui and QtWidgets will be
    exposed and completed to contain the same content, with both Qt4 and Qt5.

    Parameters
    ----------
    backend: str (default: None)
        name of the backend to use
    pyqt_api: int (default: 1)
        PyQt API version: 1 or 2, only useful for PyQt4
    compatible_qt5: bool (default: None)
        expose QtGui and QtWidgets with the same content.
        If None (default), do not change the current setting.
        If True, in Qt5, when QtGui or QtWidgets is loaded, the other module
        (QtWidgets or QtGui) is also loaded, and the QtGui module is modified
        to contain also the contents of QtWidgets, so as to have more or less
        the same elements as in Qt4. It is a bit dirty and crappy but allows
        the same code to work with both versions of Qt.
        In Qt4, when QtGui is loaded, the module is also registered as
        QtWidgets, so QtGui and QtWidgets are the same module. Loading
        QtWidgets will also bring QtGui.

    Examples
    --------
        >>> from soma.qt_gui import qt_backend
        >>> qt_backend.set_qt_backend('PySide')
        >>> qt_backend.import_qt_submodule('QtCore')
        <module 'PySide.QtCore' from '/usr/lib/python2.7/dist-packages/PySide/QtCore.so'>
    """
    global qt_backend
    global make_compatible_qt5
    qt5_compat_changed = False
    if compatible_qt5 is not None:
        make_compatible_qt5 = compatible_qt5
        qt5_compat_changed = True
    get_qt_backend()
    if backend is None:
        if qt_backend is None:
            # try to get from the environment variable QT_API, complying to
            # ETS 4
            # see
            # https://ipython.org/ipython-doc/dev/interactive/reference.html#pyqt-and-pyside
            qt_api = os.getenv("QT_API")
            if qt_api == "pyqt6":
                backend = "PyQt6"
            elif qt_api == "pyqt5":
                backend = "PyQt5"
            elif qt_api in ("pyqt", "pyqt4"):
                backend = "PyQt4"
                pyqt_api = 2
            elif qt_api == "pyside":
                backend = "PySide"
            else:
                backend = "PyQt5"
        else:
            backend = qt_backend
    if qt_backend is not None and qt_backend != backend:
        logging.warn(
            "set_qt_backend: a different backend, %s, has already "
            "be set, and %s is now requested" % (qt_backend, backend)
        )
    if backend == "PyQt4":  # and sys.modules.get('PyQt4') is None:
        sip = load_sip_module(backend)
        if qt_backend is not None:
            backend = qt_backend
    if backend == "PyQt4":
        if pyqt_api == 2:
            sip_classes = [
                "QString",
                "QVariant",
                "QDate",
                "QDateTime",
                "QTextStream",
                "QTime",
                "QUrl",
            ]
            global _sip_api_set
            for sip_class in sip_classes:
                try:
                    sip.setapi(sip_class, pyqt_api)
                except ValueError as e:
                    if not _sip_api_set:
                        logging.warning(e.message)
            _sip_api_set = True
    if qt_backend is None:
        backends = ["PyQt5", "PyQt6", "PyQt4", "PySide2", "PySide"]
        backends.remove(backend)
        backends.insert(0, backend)
    else:
        backends = [backend]
    for test_backend in backends:
        try:
            qt_module = __import__(test_backend)
            __import__(test_backend + ".QtCore")
            # __import__(backend + '.QtGui')
            qt_backend = test_backend
            break
        except ImportError:
            pass
        if qt_backend is None:
            # all fail: re-raise the exception
            qt_module = __import__(backend)
            __import__(test_backend + ".QtCore")

    sip = load_sip_module(qt_backend)

    if make_compatible_qt5 and qt5_compat_changed:
        ensure_compatible_qt5()
    else:
        if backend in ("PyQt4", "PyQt5", "PyQt6"):
            qt_module.QtCore.Signal = qt_module.QtCore.pyqtSignal
            qt_module.QtCore.Slot = qt_module.QtCore.pyqtSlot


def set_headless(headless_mode=True, needs_opengl=None):
    """Configure to use the headless mode.

    see :mod:`headless`

    if needs_opengl is None (default), don't change the currently set value'
    """
    global headless, need_opengl
    headless = headless_mode
    if need_opengl is not None:
        need_opengl = needs_opengl


def load_sip_module(backend=None):
    sip = sys.modules.get("sip")
    if sip is not None:
        return sip

    global qt_backend
    if backend is None:
        backend = qt_backend
    if qt_backend is None:
        backends = [backend, "PyQt5", "PyQt6", "PyQt4"]
    else:
        backends = [backend]
    for test_backend in backends:
        # import the right sip module
        try:
            __import__("%s.sip" % test_backend)
            sip = sys.modules["%s.sip" % test_backend]
            sys.modules["sip"] = sip
            qt_backend = test_backend
        except ImportError:
            pass
    if sip is None:
        import sip
    return sip


def patch_qt5_modules(QtCore, QtGui, QtWidgets):
    # copy QtWidgets contents into QtGui
    for key in QtWidgets.__dict__:
        if not key.startswith("__") and key not in QtGui.__dict__:
            setattr(QtGui, key, getattr(QtWidgets, key))
    # more hacks
    QtGui.QSortFilterProxyModel = QtCore.QSortFilterProxyModel
    QtGui.QItemSelectionModel = QtCore.QItemSelectionModel


def patch_qt5_webkit_modules(QtWebKit, QtWebKitWidgets):
    # copy QtWebKitWidgets contents into QtWebKit
    for key in QtWebKitWidgets.__dict__:
        if not key.startswith("__") and key not in QtWebKit.__dict__:
            setattr(QtWebKit, key, getattr(QtWebKitWidgets, key))


def patch_qt4_modules(QtCore, QtGui):
    QtCore.QSortFilterProxyModel = QtGui.QSortFilterProxyModel
    QtCore.QItemSelectionModel = QtGui.QItemSelectionModel


def patch_main_modules(modules):
    if "%s.Qt" % qt_backend in sys.modules:
        Qt = sys.modules["%s.Qt" % qt_backend]
    else:
        # Qt = imp.new_module('%s.Qt' % qt_backend)
        Qt = types.ModuleType(f"{qt_backend}.Qt")
        sys.modules["%s.Qt" % qt_backend] = Qt
    for mod in modules:
        for key, item in mod.__dict__.items():
            if not key.startswith("__") and key not in Qt.__dict__:
                setattr(Qt, key, item)


def ensure_compatible_qt5():
    if not make_compatible_qt5:
        return
    qt_backend = get_qt_backend()
    if qt_backend in ("PyQt5", "PyQt6"):
        qtgui = None
        qtwidgets = None
        qtwebkit = None
        qtwebkitwidgets = None
        if "%s.QtGui" % qt_backend in sys.modules:
            qtgui = sys.modules["%s.QtGui" % qt_backend]
        if "%s.QtWidgets" % qt_backend in sys.modules:
            qtwidgets = sys.modules["%s.QtWidgets" % qt_backend]
        if "%s.QtWebKit" % qt_backend in sys.modules:
            qtwebkit = sys.modules["%s.QtWebKit" % qt_backend]
        if "%s.QtWebKitWidgets" % qt_backend in sys.modules:
            qtwebkitwidgets = sys.modules["%s.QtWebKitWidgets" % qt_backend]
        if qtgui and qtwidgets is None:
            importlib.import_module(f"{qt_backend}.QtWidgets")
            QtWidgets = sys.modules[f"{qt_backend}.QtWidgets"]
            qtwidgets = sys.modules["%s.QtWidgets" % qt_backend]
        elif qtwidgets and qtgui is None:
            importlib.import_module(f"{qt_backend}.QtGui")
            QtGui = sys.modules[f"{qt_backend}.QtGui"]
            qtgui = sys.modules["%s.QtGui" % qt_backend]
        elif qtgui and qtwidgets:
            importlib.import_module(f"{qt_backend}.QtCore")
            QtCore = sys.modules[f"{qt_backend}.QtCore"]
            patch_qt5_modules(QtCore, qtgui, qtwidgets)
        if qtwebkit and qtwebkitwidgets is None:
            importlib.import_module(f"{qt_backend}.QtWebKitWidgets")
            qtwebkitwidgets = sys.modules[f"{qt_backend}.QtWebKitWidgets"]
            qtwebkitwidgets = sys.modules["%s.QtWebKitWidgets" % qt_backend]
        elif qtwebkitwidgets and qtwebkit is None:
            importlib.import_module(f"{qt_backend}.QtWebKit")
            qtwebkit = sys.modules[f"{qt_backend}.QtWebKit"]
        elif qtwebkit and qtwebkitwidgets:
            patch_qt5_webkit_modules(qtwebkit, qtwebkitwidgets)
    else:
        if "%s.QtGui" % qt_backend in sys.modules:
            importlib.import_module(f"{qt_backend}.QtWidgets")
            QtWidgets = sys.modules[f"{qt_backend}.QtWidgets"]
        importlib.import_module(f"{qt_backend}.QtCore")
        QtCore = sys.modules[f"{qt_backend}.QtCore"]
        importlib.import_module(f"{qt_backend}.QtGui")
        QtGui = sys.modules[f"{qt_backend}.QtGui"]
        patch_qt4_modules(QtCore, QtGui)
    if qt_backend in ("PyQt4", "PyQt5", "PyQt6"):
        importlib.import_module(f"{qt_backend}.QtCore")
        QtCore = sys.modules[f"{qt_backend}.QtCore"]
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot

    # export enums
    from soma.utils.sip_compat import sip_export_enums

    pyqt = sys.modules[qt_backend]
    sip_export_enums(pyqt)


def get_qt_module():
    """Get the main Qt module (PyQt4 or PySide)"""
    global qt_backend
    return sys.modules.get(qt_backend)


def import_qt_submodule(submodule):
    """Import a specified Qt submodule.
    An alternative to the standard statement:

    >>> from soma.qt_gui.qt_backend import <submodule>

    The main differences is that it forces loading the module from the
    appropriate backend, whereas the import statement will reuse the already
    loaded one. Moreover it returns the module.

    For instance,

    >>> from soma.qt_gui import qt_backend
    >>> qt_backend.set_qt_backend('PyQt4')
    >>> from soma.qt_gui.qt_backend import QtWebKit
    >>> QtWebKit
    <module 'PyQt4.QtWebKit' from '/usr/lib/python2.7/dist-packages/PyQt4/QtWebKit.so'>
    >>> qt_backend.set_qt_backend('PySide') # changing backend
    WARNING:root:set_qt_backend: a different backend, PyQt4, has already be set, and PySide is now requested
    >>> from soma.qt_gui.qt_backend import QtWebKit
    >>> QtWebKit
    <module 'PyQt4.QtWebKit' from '/usr/lib/python2.7/dist-packages/PyQt4/QtWebKit.so'>

    In the above example, we are still using the QtWebKit from PyQt4.
    Now:

    >>> QtWebKit = qt_backend.import_qt_submodule('QtWebKit')
    >>> QtWebKit
    <module 'PySide.QtWebKit' from '/usr/lib/python2.7/dist-packages/PySide/QtWebKit.so'>

    We are now actually using PySide.
    Note that it is generally a bad idea to mix both...

    Parameters
    ----------
        submodule: str (mandatory)
            submodule name, ex: QtWebKit

    Returns
    -------
        the loaded submodule
    """
    __import__(qt_backend + "." + submodule)
    mod = sys.modules[qt_backend + "." + submodule]
    return mod


def _iconset(self, prop):
    from . import QtGui

    return QtGui.QIcon(
        os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\")
    )


def _pixmap(self, prop):
    from . import QtGui

    return QtGui.QPixmap(
        os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\")
    )


def loadUi(ui_file, *args, **kwargs):
    """Load a ``.ui`` file and returns the widget instance.

    This function is a replacement of PyQt4.uic.loadUi. The only difference is
    that relative icon or pixmap file names that are stored in the ``*.ui``
    file are considered to be relative to the directory containing the ui file.
    With PyQt4.uic.loadUi, relative file names are considered relative to the
    current working directory therefore if this directory is not the one
    containing the ui file, icons cannot be loaded.
    """
    from . import QtGui

    if get_qt_backend() in ("PyQt4", "PyQt5", "PyQt6"):
        # the problem is corrected in version > 4.7.2,
        from . import QtCore

        if QtCore.PYQT_VERSION > 0x040702:
            from . import uic

            return uic.loadUi(ui_file, *args, **kwargs)
        else:
            # needed import and def
            from .uic.Loader import loader

            if not hasattr(globals(), "partial"):
                from soma.functiontools import partial

            def _iconset(self, prop):
                return QtGui.QIcon(
                    os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\")
                )

            def _pixmap(self, prop):
                return QtGui.QPixmap(
                    os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\")
                )

            uiLoader = loader.DynamicUILoader()
            uiLoader.wprops._basedirectory = os.path.dirname(os.path.abspath(ui_file))
            uiLoader.wprops._iconset = partial(_iconset, uiLoader.wprops)
            uiLoader.wprops._pixmap = partial(_pixmap, uiLoader.wprops)
            return uiLoader.loadUi(ui_file, *args, **kwargs)
    else:
        from PySide.QtUiTools import QUiLoader

        return QUiLoader().load(ui_file)  # , *args, **kwargs )


def loadUiType(uifile, from_imports=False):
    """PyQt4 / PySide abstraction to uic.loadUiType.
    Not implemented for PySide, actually, because PySide does not have this
    feature.
    """
    if get_qt_backend() == "PyQt6":
        from PyQt6 import uic

        return uic.loadUiType(uifile, from_imports=from_imports)
    if get_qt_backend() == "PyQt5":
        from PyQt5 import uic

        return uic.loadUiType(uifile, from_imports=from_imports)
    if get_qt_backend() == "PyQt4":
        # the parameter from_imports doesn't exist in our version of PyQt
        from PyQt4 import uic

        return uic.loadUiType(uifile)
    else:
        raise NotImplementedError("loadUiType does not work with PySide")
        # ui = loadUi(uifile)
        # return ui.__class__, QtGui.QWidget # FIXME


def getOpenFileName(
    parent=None, caption="", directory="", filter="", selectedFilter=None, options=0
):
    """PyQt4 / PySide compatible call to QFileDialog.getOpenFileName"""
    set_qt_backend(compatible_qt5=True)
    from . import QtGui

    if get_qt_backend() in ("PyQt4", "PyQt5", "PyQt6"):
        kwargs = {}
        # kwargs are used because passing None or '' as selectedFilter
        # does not work, at least in PyQt 4.10
        # On the other side I don't know if this kwargs works with older
        # sip/PyQt versions.
        if selectedFilter:
            kwargs["selectedFilter"] = selectedFilter
        if options:
            kwargs["options"] = QtGui.QFileDialog.Option(options)
        filename = get_qt_module().QtGui.QFileDialog.getOpenFileName(
            parent, caption, directory, filter, **kwargs
        )
        if get_qt_backend() == "PyQt4":
            return filename
        else:
            return filename[0]  # PyQt5 returns (filename, filter)
    else:
        return get_qt_module().QtGui.QFileDialog.getOpenFileName(
            parent,
            caption,
            directory,
            filter,
            selectedFilter,
            QtGui.QFileDialog.Option(options),
        )[0]


def getSaveFileName(
    parent=None, caption="", directory="", filter="", selectedFilter=None, options=0
):
    """PyQt4 / PySide compatible call to QFileDialog.getSaveFileName"""
    set_qt_backend(compatible_qt5=True)
    from . import QtGui

    if get_qt_backend() in ("PyQt4", "PyQt5", "PyQt6"):
        kwargs = {}
        # kwargs are used because passing None or '' as selectedFilter
        # does not work, at least in PyQt 4.10
        # On the other side I don't know if this kwargs works with older
        # sip/PyQt versions.
        if selectedFilter:
            kwargs["selectedFilter"] = selectedFilter
        if options:
            kwargs["options"] = QtGui.QFileDialog.Option(options)
        filename = get_qt_module().QtGui.QFileDialog.getSaveFileName(
            parent, caption, directory, filter, **kwargs
        )
        if get_qt_backend() == "PyQt4":
            return filename
        else:
            return filename[0]  # PyQt5 returns (filename, filter)
    else:
        return get_qt_module().QtGui.QFileDialog.getSaveFileName(
            parent, caption, directory, filter, selectedFilter, options
        )[0]


def getExistingDirectory(parent=None, caption="", directory="", options=None):
    """PyQt4 / PySide compatible call to QFileDialog.getExistingDirectory"""
    set_qt_backend(compatible_qt5=True)
    from . import QtGui

    if get_qt_backend() in ("PyQt4", "PyQt5", "PyQt6"):
        kwargs = {}
        if options is not None:
            kwargs["options"] = QtGui.QFileDialog.Option(options)
        return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
            parent, caption, directory, **kwargs
        )
    else:
        if options is not None:
            return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
                parent, caption, directory, QtGui.QFileDialog.Option(options)
            )[0]
        else:
            return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
                parent, caption, directory
            )[0]


def init_matplotlib_backend(force=True):
    """Initialize Matplotlib to use Qt, and the appropriate Qt/Python binding
    (PySide or PyQt) according to the configured/loaded toolkit.
    Moreover, the appropriate FigureCanvas type is set in the current module,
    and returned by this function.

    Parameters
    ----------
    force: bool
        if False, if the backend is already initialized with a different value,
        then raise an exception. If True (the default), force the new
        backend in matplotlib. If matplotlib does not support the force
        parameter, then the backend will not be forced.
    """
    try:
        import matplotlib
    except ImportError:
        # if matplotlib cannot be found, don't do anything.
        return

    mpl_ver = [int(x) for x in matplotlib.__version__.split(".")[:2]]
    qt_backend = get_qt_backend()
    if qt_backend == "PyQt6":
        guiBackend = "Qt5Agg"  # apparently not Qt6Agg
        mpl_backend_mod = "matplotlib.backends.backend_qt5agg"
    elif qt_backend == "PyQt5":
        guiBackend = "Qt5Agg"
        mpl_backend_mod = "matplotlib.backends.backend_qt5agg"
    else:
        guiBackend = "Qt4Agg"
        mpl_backend_mod = "matplotlib.backends.backend_qt4agg"
    if "matplotlib.backends" not in sys.modules or force:
        argspec = inspect.getfullargspec(matplotlib.use)
        if "force" in argspec.args or "force" in argspec.kwonlyargs:
            matplotlib.use(guiBackend, force=force)
        else:
            matplotlib.use(guiBackend)
    elif matplotlib.get_backend() != guiBackend:
        raise RuntimeError(
            "Mismatch between Qt version and matplotlib backend: "
            "matplotlib uses "
            + matplotlib.get_backend()
            + " but "
            + guiBackend
            + " is required."
        )
    if qt_backend == "PySide":
        if "backend.qt4" in list(matplotlib.rcParams.keys()):
            # some versions (>=1.1, <3) of matplotlib have this rcParams setting
            matplotlib.rcParams["backend.qt4"] = "PySide"
    else:
        if qt_backend == "PyQt6":
            rc_key = "backend.qt6"
        elif qt_backend == "PyQt5":
            rc_key = "backend.qt5"
        else:
            rc_key = "backend.qt4"
        if rc_key in list(matplotlib.rcParams.keys()):
            # some versions (>=1.1, <3) of matplotlib have this rcParams setting
            matplotlib.rcParams[rc_key] = qt_backend
    __import__(mpl_backend_mod)
    backend_mod = sys.modules[mpl_backend_mod]
    FigureCanvas = backend_mod.FigureCanvasQTAgg
    sys.modules[__name__].FigureCanvas = FigureCanvas
    return mpl_backend_mod


traits_ui_handler_initialized = False


def init_traitsui_handler():
    """Setup handler for traits notification in Qt GUI.
    This function needs to be called before using traits notification which
    trigger GUI modification from non-principal threads.

    **WARNING**: depending on the Qt bindings (PyQt or PySide), this function
    may instantiate a QApplication. It seems that when using PyQt4,
    QApplication is not instantiated, whereas when using PySide, it is.
    This means that after this function has been called, one must check if
    the application has been created before recreating it:

    ::

        app = QtGui.QApplication.instance()
        if not app:
            app = QtGui.QApplication(sys.argv)

    This behaviour is triggered somewhere in the traitsui.qt4.toolkit module,
    we cannot change it easily.
    """
    global traits_ui_handler_initialized
    from . import QtCore, QtGui

    if traits_ui_handler_initialized:
        return  # already done

    try:
        if get_qt_backend() in ("PyQt4", "PySide"):
            from traitsui.qt4 import toolkit
        else:
            # if using Qt5 we must not import traitsui.qt4, which would cause
            # a crash. Then use the code taken from traitsui.qt4.toolkit
            # in a qt-independent manner
            raise ImportError("traitsui doesn't provide a PyQt5 backend")
    except Exception:
        # copy of the code from traitsui.qt4.toolkit

        from traits.trait_notifiers import set_ui_handler

        # -------------------------------------------------------------------------------
        #  Handles UI notification handler requests that occur on a thread other than
        #  the UI thread:
        # -------------------------------------------------------------------------------
        _QT_TRAITS_EVENT = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

        class _CallAfter(QtCore.QObject):
            """This class dispatches a handler so that it executes in the main GUI
            thread (similar to the wx function).
            """

            # The list of pending calls.
            _calls = []

            # The mutex around the list of pending calls.
            _calls_mutex = QtCore.QMutex()

            def __init__(self, handler, *args, **kwds):
                """Initialise the call."""
                QtCore.QObject.__init__(self)

                # Save the details of the call.
                self._handler = handler
                self._args = args
                self._kwds = kwds

                # Add this to the list.
                self._calls_mutex.lock()
                self._calls.append(self)
                self._calls_mutex.unlock()

                # Move to the main GUI thread.
                self.moveToThread(QtGui.QApplication.instance().thread())

                # Post an event to be dispatched on the main GUI thread. Note that
                # we do not call QTimer.singleShot, which would be simpler, because
                # that only works on QThreads. We want regular Python threads to work.
                event = QtCore.QEvent(_QT_TRAITS_EVENT)
                QtGui.QApplication.instance().postEvent(self, event)

            def event(self, event):
                """QObject event handler."""
                if event.type() == _QT_TRAITS_EVENT:
                    # Invoke the handler
                    self._handler(*self._args, **self._kwds)

                    # We cannot remove from self._calls here. QObjects don't like being
                    # garbage collected during event handlers (there are tracebacks,
                    # plus maybe a memory leak, I think).
                    QtCore.QTimer.singleShot(0, self._finished)

                    return True
                else:
                    return QtCore.QObject.event(self, event)

            def _finished(self):
                """Remove the call from the list, so it can be garbage collected."""
                self._calls_mutex.lock()
                del self._calls[self._calls.index(self)]
                self._calls_mutex.unlock()

        def ui_handler(handler, *args, **kwds):
            """Handles UI notification handler requests that occur on a thread other
            than the UI thread.
            """
            _CallAfter(handler, *args, **kwds)

        # Tell the traits notification handlers to use this UI handler
        set_ui_handler(ui_handler)


def qimage_to_np(qimage):
    """
    Utility function to transform a Qt QImage into a numpy array suitable
    for matplotlib imshow() for instance.
    """
    import numpy as np
    from . import Qt

    w, h = qimage.width(), qimage.height()
    if isinstance(qimage, Qt.QPixmap):
        qimage = qimage.toImage()
    # sip.voidptr (qimage.bits()) asarray method is only available
    # in sip >= 4.15
    # aim = aim = np.array(qimage.bits().asarray(w * h * 4)).reshape((h, w, 4))
    b = qimage.bits()
    b.setsize(w * h * 4)
    aim = np.array(b).reshape((h, w, 4))
    # TODO: handle different pixel formats
    aim[:, :, 0:3] = np.flip(aim[:, :, 0:3], axis=2)
    return aim


def imshow_widget(widget, figure=None, show=False):
    """
    Display a snapshot of a QWidget into a Matplotlib figure using
    pylab.imshow(). This is useful to use the sphinx_gallery module for
    documentation.
    """
    from . import Qt
    from matplotlib import pyplot

    Qt.QApplication.instance().processEvents()
    if Qt.QT_VERSION >= 0x050000:
        im = widget.grab()  # Qt5 only
    else:
        im = Qt.QPixmap.grabWidget(widget)  # Qt4 only
    aim = qimage_to_np(im)
    plot = pyplot.imshow(aim, figure=figure)
    if figure is not None:
        axes = figure.axes()
    else:
        axes = pyplot.axes()
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    if show:
        if figure is not None:
            figure.show()
        else:
            pyplot.show(block=False)
    return plot
