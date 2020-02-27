# -*- coding: utf-8 -*-

from __future__ import print_function

from __future__ import absolute_import
import unittest
import os
import sys
try:
    #from soma import qimage2ndarray
    from soma import qt_gui
    from soma.qt_gui import controller_widget
    from soma.qt_gui import controls
    from soma.qt_gui import generic_table_editor
    from soma.qt_gui import io
    from soma.qt_gui import qtThread
    from soma.qt_gui import tangeSlider
    from soma.qt_gui import timered_widgets

    class TestQtGui(unittest.TestCase):

        def test_qtgui(self):
            from soma.qt_gui import qt_backend
            qt_backend.set_qt_backend(compatible_qt5=True)
            self.assertTrue(qt_backend.get_qt_backend()
                            in ('PyQt4', 'PyQt5', 'PySide'))


    def test():
        suite = unittest.TestLoader().loadTestsFromTestCase(TestQtGui)
        runtime = unittest.TextTestRunner(verbosity=2).run(suite)
        return runtime.wasSuccessful()


    if __name__ == "__main__":
        test()

except ImportError:
    # PyQt not installed
    have_gui = False
