"""
This module contains tools to replace a Qt application which will propose to
open a Qtconsole jupyter shell from within the application (like the anatomist
or brainvisa commands). Recent versions of jupyter/ipython/qtconsole cannot be
tweaked to start their ipython kernel from a running Qt event loop, and always
hang.

An IPython kernel is started, so that connections from a qtconsole will
always be possible. In the C++ anatomist command, the python engine is
started from a module, and the ipython kernel is run on demand when we open a
python qtconsole shell.

Unfortunately in recent ipython/jupyter/tornado or other modules, this does
not work any longer, the IP kernel loop does not return to the running
python, so the IP kernel is blocked.
To overcome that, we run the IP kernel, and the Qt event loop inside it (like
in a regular ipython).

Drawbacks:

- it always run an IP kernel, with its server engine
- it does it from the start, thus slows down the startup of Anatomist
- the IP engine *never* returns. Even when the QApplication should exit the
  loop (last window closed, quit called etc). Not my fault. So we need to setup
  an abrupt exit mechanism.

But it works, and will continue to in the future since it is the way it is
designed for (our way was a hack).

How to use it:
In the main script of your GUI application, do::

    from soma.qt_gui import ipkernel_tools

    # if needed here, do things to select Qt version etc through
    # soma.qt_gui.qt_backend
    # then:

    ipkernel_tools.before_start_ipkernel()

    # Here, instantiate your GUI, widgets, etc, and a QApplication
    # But DON'T RUN THE EVENT LOOP
    # Then:

    # instantiate an exit mechanism, like a callback in the Qt GUI which will
    # be called before the Qt event loop is exited, and which will call
    # sys.exit().

    # Then:

    ipkernel_tools.start_ipkernel_qt_engine()

As said before, the last function, :func:`start_ipkernel_qt_engine`, will never
return. So you have to setup an exit mechanism by your own.
"""

import os
import sys

try:
    from ipykernel import eventloops

    if hasattr(eventloops, "loop_qt4"):
        # ipykernel v7 needs a patch for qt6
        # v8 is OK

        def _loop_qt(app):
            if not getattr(app, "_in_event_loop", False):
                app._in_event_loop = True
                app.exec()
                app._in_event_loop = False

        @eventloops.register_integration("qt", "qt5")
        def loop_qt5(kernel):
            return eventloops.loop_qt4(kernel)

        eventloops._loop_qt = _loop_qt
        eventloops.loop_qt5 = loop_qt5

    from ipykernel import kernelapp as app

except ImportError:
    # ipykernel is not installed
    app = None


def restore_stdout():
    # restore stdout / stderr from their initial values
    sys.__ip_stdout = sys.stdout
    sys.__ip_stderr = sys.stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def before_start_ipkernel():
    """To be called before instantiating a QApplication"""

    from soma.qt_gui.qt_backend import QtCore, QtWidgets

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    qapp = QtWidgets.QApplication([])
    if app is not None:
        # ipkernel loop does not exit after QApplication.quit().
        # We must force exit
        # NOTE in recent ipykernels, Qt doesn't call callbacks after
        # QApplication.quit() so this doesn't work any longer.
        QtWidgets.QApplication.instance().aboutToQuit.connect(
            sys.exit, QtCore.Qt.QueuedConnection
        )


def start_ipkernel_qt_engine():
    """Starts the IPython engine and Qt event loop. Never returns."""

    from soma.qt_gui import qt_backend
    from soma.qt_gui.qt_backend import QtCore, QtWidgets

    if app is not None:
        # init Qt GUI in ipython
        os.environ["QT_API"] = qt_backend.get_qt_backend().lower()
        sys.argv.insert(1, "--gui=qt")
        # purge argv for args meant for anatomist
        while len(sys.argv) > 2:
            del sys.argv[-1]

        # trigger a timer just after the event loop is started
        # it will restore stdout / stderr because if we don't, they are
        # captured
        # for redirection to the qtconsole, but the console client is not here
        # yet.
        QtCore.QTimer.singleShot(10, restore_stdout)

        # will never return, exit is done via the callback above
        app.launch_new_instance()
        print("EXIT")
    else:
        # without ipython, just run the Qt loop
        result = QtWidgets.QApplication.instance().exec()
        sys.exit(result)
