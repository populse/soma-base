#from soma.controller import Controller
import sys
#~ try:
    #~ from etsconfig.api import ETSConfig
    #~ ETSConfig.toolkit = 'null'
#~ except ImportError:
    #~ from enthought.etsconfig.api import ETSConfig
    #~ ETSConfig.toolkit = 'null'

if __name__ == '__main__':
    from soma.qt_gui.qt_backend import set_qt_backend
    set_qt_backend('PyQt4')
from soma.qt_gui.qt_backend import QtGui, QtCore
from soma.gui.pipeline.study_window import StudyWindow
from soma.application import Application
from soma.global_naming import GlobalNaming


if __name__ == '__main__':
    soma_app = Application( 'soma.fom', '1.0' )
    # Register module to load and call functions before and/or after
    # initialization
    soma_app.plugin_modules.append( 'soma.fom' )
    # Application initialization (e.g. configuration file may be read here)
    soma_app.initialize()

    app = QtGui.QApplication( sys.argv )
    w = StudyWindow()
    w.show()
    app.exec_()
