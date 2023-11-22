import unittest

try:
    # from soma import qimage2ndarray
    from soma import qt_gui
    from soma.qt_gui import (
        controller,
        generic_table_editor,
        io,
        qtThread,
        tangeSlider,
        timered_widgets,
    )

    class TestQtGui(unittest.TestCase):
        def test_qtgui(self):
            from soma.qt_gui import qt_backend

            qt_backend.set_qt_backend(compatible_qt5=True)
            self.assertTrue(qt_backend.get_qt_backend() in ("PyQt4", "PyQt5", "PySide"))

    def test():
        suite = unittest.TestLoader().loadTestsFromTestCase(TestQtGui)
        runtime = unittest.TextTestRunner(verbosity=2).run(suite)
        return runtime.wasSuccessful()

    if __name__ == "__main__":
        test()

except ImportError:
    # PyQt not installed
    have_gui = False
