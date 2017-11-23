#
# Soma-base - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#

'''Compatibility module for PyQt and PySide. Currently supports PyQt4,
PySide, and PyQt5.
This modules handles differences between PyQt and PySide APIs and behaviours,
and offers a few functions to make it easier to build neutral GUI code, which
can run using either backend.

The main funcion here is set_qt_backend() which must be called to initialize
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
'''

import logging
import sys
import os
import imp
from soma.utils.functiontools import partial


# make qt_backend a fake module package, with Qt modules as sub-modules
__package__ = __name__
__path__ = [os.path.dirname(__file__)]

# internal variable to avoid warning several times
_sip_api_set = False

qt_backend = None
make_compatible_qt5 = False


class QtImporter(object):

    def find_module(self, fullname, path=None):
        modsplit = fullname.split('.')
        modpath = '.'.join(modsplit[:-1])
        module_name = modsplit[-1]
        if modpath != __name__ or module_name == 'sip':
            return None
        set_qt_backend()
        qt_module = get_qt_module()
        if make_compatible_qt5 and get_qt_backend() in ('PyQt4', 'PySide'):
            if module_name == 'QtWidgets':
                module_name = 'QtGui'
            elif module_name == 'QtWebKitWidgets':
                module_name = 'QtWebKit'
        found = imp.find_module(module_name, qt_module.__path__)
        return self

    def load_module(self, name):
        qt_backend = get_qt_backend()
        module_name = name.split('.')[-1]
        imp_module_name = module_name
        if make_compatible_qt5:
            if module_name == 'QtWidgets':
                imp_module_name = 'QtGui'
            elif module_name == 'QtWebKitWidgets':
                imp_module_name = 'QtWebKit'
        __import__('.'.join([qt_backend, imp_module_name]))
        module = sys.modules['.'.join([qt_backend, imp_module_name])]
        sys.modules[name] = module
        if make_compatible_qt5:
            if imp_module_name == 'QtGui':
                from . import QtCore
                if qt_backend in ('PyQt4', 'PySide'):
                    sys.modules['.'.join([qt_backend, 'QtWidgets'])] = module
                    patch_qt4_modules(QtCore, module)
                elif qt_backend == 'PyQt5':
                    __import__('.'.join([qt_backend, 'QtWidgets']))
                    qtwidgets = sys.modules['.'.join([qt_backend,
                                                      'QtWidgets'])]
                    patch_qt5_modules(QtCore, module, qtwidgets)
                    if module_name == 'QtWidgets':
                        module = qtwidgets
            elif imp_module_name == 'QtWebKit':
                if qt_backend in ('PyQt4', 'PySide'):
                    sys.modules['.'.join([qt_backend, 'QtWebKitWidgets'])] \
                        = module
                elif qt_backend == 'PyQt5':
                    __import__('.'.join([qt_backend, 'QtWebKitWidgets']))
                    qtwebkitwidgets = sys.modules[
                        '.'.join([qt_backend,'QtWebKitWidgets'])]
                    patch_qt5_webkit_modules(module, qtwebkitwidgets)
                    if module_name == 'QtWebKitWidgets':
                        module = qtwebkitwidgets

        return module

# tune the import statement to get Qt submodules in this one
sys.meta_path.append(QtImporter())


def get_qt_backend():
    '''get currently setup or loaded Qt backend name: "PyQt4" or "PySide"'''
    global qt_backend
    if qt_backend is None:
        pyside = sys.modules.get('PySide')
        if pyside is not None:
            qt_backend = 'PySide'
        else:
            pyqt = sys.modules.get('PyQt5')
            if pyqt is not None:
                qt_backend = 'PyQt5'
            else:
                pyqt = sys.modules.get('PyQt4')
                if pyqt is not None:
                    qt_backend = 'PyQt4'
    return qt_backend


def set_qt_backend(backend=None, pyqt_api=1, compatible_qt5=None):
    '''set the Qt backend.

    If a different backend has already setup or loaded, a warning is issued.
    If no backend is specified, try to guess which one is already loaded.

    If no backend is loaded yet, try to behave like IPython does.
    See: https://ipython.org/ipython-doc/dev/interactive/reference.html#pyqt-and-pyside

    More precisely this means:
    * If QT_API environement variable is not set, use PyQt4, with PyQt API v1
    * if QT_API is set to "pyqt", use PyQt4, with PyQt API v2
    * if QT_API is set to "pyside", use PySide

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
    '''
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
            qt_api = os.getenv('QT_API')
            if qt_api == 'pyqt':
                backend = 'PyQt4'
                pyqt_api = 2
            elif qt_api == 'pyside':
                backend = 'PySide'
            else:
                backend = 'PyQt4'
                pyqt_api = 1
        else:
            backend = qt_backend
    if qt_backend is not None and qt_backend != backend:
        logging.warn('set_qt_backend: a different backend, %s, has already '
                     'be set, and %s is now requested' % (qt_backend, backend))
    if backend == 'PyQt4':  # and sys.modules.get('PyQt4') is None:
        import sip
        if pyqt_api == 2:
            sip_classes = ['QString', 'QVariant', 'QDate', 'QDateTime',
                           'QTextStream', 'QTime', 'QUrl']
            global _sip_api_set
            for sip_class in sip_classes:
                try:
                    sip.setapi(sip_class, pyqt_api)
                except ValueError as e:
                    if not _sip_api_set:
                        logging.warning(e.message)
            _sip_api_set = True
    qt_module = __import__(backend)
    __import__(backend + '.QtCore')
    #__import__(backend + '.QtGui')
    qt_backend = backend
    if make_compatible_qt5 and qt5_compat_changed:
        ensure_compatible_qt5()
    else:
        if backend in('PyQt4', 'PyQt5'):
            qt_module.QtCore.Signal = qt_module.QtCore.pyqtSignal
            qt_module.QtCore.Slot = qt_module.QtCore.pyqtSlot


def patch_qt5_modules(QtCore, QtGui, QtWidgets):
    # copy QtWidgets contents into QtGui
    for key in QtWidgets.__dict__:
        if not key.startswith('__') and key not in QtGui.__dict__:
            setattr(QtGui, key, getattr(QtWidgets, key))
    # more hacks
    QtGui.QSortFilterProxyModel = QtCore.QSortFilterProxyModel
    QtGui.QItemSelectionModel = QtCore.QItemSelectionModel


def patch_qt5_webkit_modules(QtWebKit, QtWebKitWidgets):
    # copy QtWebKitWidgets contents into QtWebKit
    for key in QtWebKitWidgets.__dict__:
        if not key.startswith('__') and key not in QtWebKit.__dict__:
            setattr(QtWebKit, key, getattr(QtWebKitWidgets, key))


def patch_qt4_modules(QtCore, QtGui):
    QtCore.QSortFilterProxyModel = QtGui.QSortFilterProxyModel
    QtCore.QItemSelectionModel = QtGui.QItemSelectionModel


def ensure_compatible_qt5():
    if not make_compatible_qt5:
        return
    qt_backend = get_qt_backend()
    if qt_backend == 'PyQt5':
        qtgui = None
        qtwidgets = None
        qtwebkit = None
        qtwebkitwidgets = None
        if 'PyQt5.QtGui' in sys.modules:
            qtgui = sys.modules['PyQt5.QtGui']
        if 'PyQt5.QtWidgets' in sys.modules:
            qtwidgets = sys.modules['PyQt5.QtWidgets']
        if 'PyQt5.QtWebKit' in sys.modules:
            qtwebkit = sys.modules['PyQt5.QtWebKit']
        if 'PyQt5.QtWebKitWidgets' in sys.modules:
            qtwebkitwidgets = sys.modules['PyQt5.QtWebKitWidgets']
        if qtgui and qtwidgets is None:
            from . import QtWidgets
            qtwidgets = sys.modules['PyQt5.QtWidgets']
        elif qtwidgets and qtgui is None:
            from . import QtGui
            qtgui = sys.modules['PyQt5.QtGui']
        elif qtgui and qtwidgets:
            from . import QtCore
            patch_qt5_modules(QtCore, qtgui, qtwidgets)
        if qtwebkit and qtwebkitwidgets is None:
            from . import QtWebKitWidgets
            qtwebkitwidgets = sys.modules['PyQt5.QtWebKitWidgets']
        elif qtwebkitwidgets and qtwebkit is None:
            from . import QtWebKit
        elif qtwebkit and qtwebkitwidgets:
            patch_qt5_webkit_modules(qtwebkit, qtwebkitwidgets)
    else:
        if '%s.QtGui' % qt_backend in sys.modules:
            from . import QtWidgets
        from . import QtCore, QtGui
        patch_qt4_modules(QtCore, QtGui)
    if qt_backend in('PyQt4', 'PyQt5'):
        from . import QtCore
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot


def get_qt_module():
    '''Get the main Qt module (PyQt4 or PySide)'''
    global qt_backend
    return sys.modules.get(qt_backend)


def import_qt_submodule(submodule):
    '''Import a specified Qt submodule.
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
    '''
    __import__(qt_backend + '.' + submodule)
    mod = sys.modules[qt_backend + '.' + submodule]
    return mod


def _iconset(self, prop):
    return QtGui.QIcon(os.path.join(self._basedirectory,
                                    prop.text).replace("\\", "\\\\"))


def _pixmap(self, prop):
    return QtGui.QPixmap(os.path.join(self._basedirectory,
                                      prop.text).replace("\\", "\\\\"))


def loadUi(ui_file, *args, **kwargs):
    '''Load a .ui file and returns the widget instance.

    This function is a replacement of PyQt4.uic.loadUi. The only difference is
    that relative icon or pixmap file names that are stored in the *.ui file
    are considered to be relative to the directory containing the ui file. With
    PyQt4.uic.loadUi, relative file names are considered relative to the
    current working directory therefore if this directory is not the one
    containing the ui file, icons cannot be loaded.
    '''
    if get_qt_backend() in ('PyQt4', 'PyQt5'):
        # the problem is corrected in version > 4.7.2,
        from . import QtCore
        if QtCore.PYQT_VERSION > 0x040702:
            from . import uic
            return uic.loadUi(ui_file, *args, **kwargs)
        else:
            # needed import and def
            from .uic.Loader import loader
            if not hasattr(globals(), 'partial'):
                from soma.functiontools import partial

            def _iconset(self, prop):
                return QtGui.QIcon(os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\"))

            def _pixmap(self, prop):
                return QtGui.QPixmap(os.path.join(self._basedirectory, prop.text).replace("\\", "\\\\"))
            uiLoader = loader.DynamicUILoader()
            uiLoader.wprops._basedirectory = os.path.dirname(
                os.path.abspath(ui_file))
            uiLoader.wprops._iconset = partial(_iconset, uiLoader.wprops)
            uiLoader.wprops._pixmap = partial(_pixmap, uiLoader.wprops)
            return uiLoader.loadUi(ui_file, *args, **kwargs)
    else:
        from PySide.QtUiTools import QUiLoader
        return QUiLoader().load(ui_file)  # , *args, **kwargs )


def loadUiType(uifile, from_imports=False):
    '''PyQt4 / PySide abstraction to uic.loadUiType.
    Not implemented for PySide, actually, because PySide does not have this
    feature.
    '''
    if get_qt_backend() == 'PyQt5':
        from PyQt5 import uic
        return uic.loadUiType(uifile, from_imports=from_imports)
    if get_qt_backend() == 'PyQt4':
        # the parameter from_imports doesn't exist in our version of PyQt
        from PyQt4 import uic
        return uic.loadUiType(uifile)
    else:
        raise NotImplementedError('loadUiType does not work with PySide')
        # ui = loadUi(uifile)
        # return ui.__class__, QtGui.QWidget # FIXME


def getOpenFileName(parent=None, caption='', directory='', filter='',
                    selectedFilter=None, options=0):
    '''PyQt4 / PySide compatible call to QFileDialog.getOpenFileName'''
    if get_qt_backend() in('PyQt4', 'PyQt5'):
        kwargs = {}
        # kwargs are used because passing None or '' as selectedFilter
        # does not work, at least in PyQt 4.10
        # On the other side I don't know if this kwargs works with older
        # sip/PyQt versions.
        if selectedFilter:
            kwargs['selectedFilter'] = selectedFilter
        if options:
            kwargs['options'] = QtGui.QFileDialog.Options(options)
        filename = get_qt_module().QtGui.QFileDialog.getOpenFileName(
            parent, caption, directory, filter, **kwargs)
        if get_qt_backend() == 'PyQt4':
            return filename
        else:
            return filename[0] # PyQt5 returns (filaname, filter)
    else:
        return get_qt_module().QtGui.QFileDialog.getOpenFileName(
            parent, caption, directory, filter, selectedFilter,
            QtGui.QFileDialog.Options(options))[0]


def getSaveFileName(parent=None, caption='', directory='', filter='',
                    selectedFilter=None, options=0):
    '''PyQt4 / PySide compatible call to QFileDialog.getSaveFileName'''
    if get_qt_backend() in ('PyQt4', 'PyQt5'):
        kwargs = {}
        # kwargs are used because passing None or '' as selectedFilter
        # does not work, at least in PyQt 4.10
        # On the other side I don't know if this kwargs works with older
        # sip/PyQt versions.
        if selectedFilter:
            kwargs['selectedFilter'] = selectedFilter
        if options:
            kwargs['options'] = QtGui.QFileDialog.Options(options)
        filename = get_qt_module().QtGui.QFileDialog.getSaveFileName(
            parent, caption, directory, filter, **kwargs)
        if get_qt_backend() == 'PyQt4':
            return filename
        else:
            return filename[0] # PyQt5 returns (filaname, filter)
    else:
        return get_qt_module().QtGui.QFileDialog.getSaveFileName(
            parent, caption, directory, filter, selectedFilter, options)[0]


def getExistingDirectory(parent=None, caption='', directory='', options=None):
    '''PyQt4 / PySide compatible call to QFileDialog.getExistingDirectory'''
    if get_qt_backend() in ('PyQt4', 'PyQt5'):
        kwargs = {}
        if options is not None:
            kwargs['options'] = QtGui.QFileDialog.Options(options)
        return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
            parent, caption, directory, **kwargs)
    else:
        if options is not None:
            return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
                parent, caption, directory,
                QtGui.QFileDialog.Options(options))[0]
        else:
            return get_qt_module().QtGui.QFileDialog.getExistingDirectory(
                parent, caption, directory)[0]


def init_matplotlib_backend():
    '''Initialize Matplotlib to use Qt, and the appropriate Qt/Python binding
    (PySide or PyQt) according to the configured/loaded toolkit.
    Moreover, the appropriate FigureCanvas type is set in the current module,
    and returned by this function.
    '''
    try:
        import matplotlib
    except ImportError:
        # if matplotlib cannot be found, don't do anything.
        return

    mpl_ver = [int(x) for x in matplotlib.__version__.split('.')[:2]]
    qt_backend = get_qt_backend()
    if qt_backend == 'PyQt5':
        guiBackend = 'Qt5Agg'
        mpl_backend_mod = 'matplotlib.backends.backend_qt5agg'
    else:
        guiBackend = 'Qt4Agg'
        mpl_backend_mod = 'matplotlib.backends.backend_qt4agg'
    if 'matplotlib.backends' not in sys.modules:
        matplotlib.use(guiBackend)
    elif matplotlib.get_backend() != guiBackend:
        raise RuntimeError(
            'Mismatch between Qt version and matplotlib backend: '
            'matplotlib uses ' + matplotlib.get_backend() + ' but '
            + guiBackend + ' is required.')
    if qt_backend == 'PySide':
        if 'backend.qt4' in matplotlib.rcParams.keys():
            matplotlib.rcParams['backend.qt4'] = 'PySide'
        else:
            raise RuntimeError("Could not use Matplotlib, the backend using "
                               "PySide is missing.")
    else:
        if qt_backend == 'PyQt5':
            rc_key = 'backend.qt5'
        else:
            rc_key = 'backend.qt4'
        if rc_key in matplotlib.rcParams.keys():
            matplotlib.rcParams[rc_key] = qt_backend
        else:
            # older versions of matplotlib used only PyQt4.
            if mpl_ver >= [1, 1]:
                raise RuntimeError("Could not use Matplotlib, the backend "
                                   "using PyQt4 is missing.")
    __import__(mpl_backend_mod)
    backend_mod = sys.modules[mpl_backend_mod]
    FigureCanvas = backend_mod.FigureCanvasQTAgg
    sys.modules[__name__].FigureCanvas = FigureCanvas
    return mpl_backend_mod


def init_traitsui_handler():
    ''' Setup handler for traits notification in Qt GUI.
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
    '''
    try:
        from traitsui.qt4 import toolkit
    except:
        # copy of the code from traitsui.qt4.toolkit

        from traits.trait_notifiers import set_ui_handler

        #-------------------------------------------------------------------------------
        #  Handles UI notification handler requests that occur on a thread other than
        #  the UI thread:
        #-------------------------------------------------------------------------------
        _QT_TRAITS_EVENT = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

        class _CallAfter(QtCore.QObject):
            """ This class dispatches a handler so that it executes in the main GUI
                thread (similar to the wx function).
            """

            # The list of pending calls.
            _calls = []

            # The mutex around the list of pending calls.
            _calls_mutex = QtCore.QMutex()

            def __init__(self, handler, *args, **kwds):
                """ Initialise the call.
                """
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
                """ QObject event handler.
                """
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
                """ Remove the call from the list, so it can be garbage collected.
                """
                self._calls_mutex.lock()
                del self._calls[self._calls.index(self)]
                self._calls_mutex.unlock()

        def ui_handler ( handler, *args, **kwds ):
            """ Handles UI notification handler requests that occur on a thread other
                than the UI thread.
            """
            _CallAfter(handler, *args, **kwds)

        # Tell the traits notification handlers to use this UI handler
        set_ui_handler( ui_handler )

