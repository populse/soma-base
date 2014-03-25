#from soma.controller import Controller
import sys
#~ try:
    #~ from etsconfig.api import ETSConfig
    #~ ETSConfig.toolkit = 'null'
#~ except ImportError:
    #~ from enthought.etsconfig.api import ETSConfig
    #~ ETSConfig.toolkit = 'null'

# Force QString API version in order to be compatible with recent version
# of enthought.traits.ui (3.6 for instance)
import sip
PYQT_API_VERSION = 2
qt_api = [ "QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
"QVariant" ]
for qt_class in qt_api:
    sip.setapi( qt_class, PYQT_API_VERSION )
del qt_api, qt_class
from PyQt4 import QtGui, QtCore
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
