# -*- coding: utf-8 -*-
import sys

# Soma import
from soma.qt_gui.qt_backend import QtGui
from soma.qt_gui.controller_widget import (
    ControllerWidget, ScrollControllerWidget)

# Soma import
from soma.controller import (Controller,
                             Literal,
                             List,
                             file,
                             directory)


class Point(Controller):
    x : float
    y : float


class TestControls(Controller):

    """ A dummy class to test all available controls.
    """

    # Global parameters
    # Traits we want to parametrized thanks to control widgets
    enum : Literal['1', '2', '3']
    i: int
    s: str
    f: float
    b: bool
    fp: file()
    dp: directory()
    l: List[float]
    # ll: List[List[float]]
    # lll = List[List[List[str]]]

    def __init__(self):
        """" Initialize the TestControls class.
        """
        # Inheritance
        super().__init__()

        # Set some default values
        self.l = [3.2, 0.5]
        self.ll = [[3.2, 0.5],  [1.1, 0.9]]
        self.lll = [[["a", "b", ""]], [["aa", "", "ff"]], [["s"]]]


if __name__ == "__main__":
    # Create a qt applicaction
    app = QtGui.QApplication(sys.argv)

    # Create the controller we want to parametrized
    controller = TestControls()

    # Set some values to the controller parameters
    controller.s = ""
    controller.f = 10.2

    # Create to controller widget that are synchronized on the fly
    widget1 = ScrollControllerWidget(controller, live=True)
    widget2 = ControllerWidget(controller, live=True)
    widget1.show()
    widget2.show()

    # Check if the controller widget is valid before edition
    print("Controller widget valid before edition: ", end=' ')
    print(widget1.controller_widget.is_valid())

    # Start the qt loop
    app.exec_()

    # Check if the controller widget is valid after edition
    print("Controller widget valid after edition: ", end=' ')
    print(widget1.controller_widget.is_valid())
