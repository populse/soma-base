import sys

from soma.controller import (
    Controller,
    Dict,
    List,
    Literal,
    Set,
    Union,
    directory,
    field,
    file,
)
from soma.qt_gui.controller import ControllerWidget
from soma.qt_gui.qt_backend import Qt


class CustomController(Controller):
    s: str
    i: int
    ls: List[str]


class TestControls(Controller):
    s: field(type_=str, group="string", label="the label")
    os: field(type_=str, optional=True, group="string")
    ls: field(type_=List[str], group="string")
    ols: field(type_=List[str], output=True, group="string")
    lls: field(type_=List[List[str]], label="list^2[str]", group="string")
    llls: field(type_=List[List[List[str]]], label="list^3[str]", group="string")

    i: field(type_=int, group="integer")
    oi: field(type_=int, optional=True, group="integer")
    li: field(type_=List[int], group="integer")
    oli: field(type_=List[int], output=True, group="integer")
    lli: field(type_=List[List[int]], label="list^2[int]", group="integer")
    llli: field(type_=List[List[List[int]]], label="list^3[int]", group="integer")

    n: field(type_=float, group="float")
    on: field(type_=float, optional=True, group="float")
    ln: field(type_=List[float], group="float")
    oln: field(type_=List[float], output=True, group="float")
    lln: field(type_=List[List[float]], label="list^2[float]", group="float")
    llln: field(type_=List[List[List[float]]], label="list^3[float]", group="float")

    b: field(type_=bool, group="bool")
    ob: field(type_=bool, output=True, group="bool")
    lb: field(type_=List[bool], group="bool")
    olb: field(type_=List[bool], output=True, group="bool")

    e: field(type_=Literal["one", "two", "three"], group="enum")
    oe: field(type_=Literal["one", "two", "three"], output=True, group="enum")
    le: field(type_=List[Literal["one", "two", "three"]], group="enum")
    ole: field(type_=List[Literal["one", "two", "three"]], output=True, group="enum")

    f: file(group="file")
    of: file(write=True, group="file")
    lf: field(type_=List[file()], group="file")
    olf: field(type_=List[file(write=True)], group="file")

    d: directory(group="directory")
    od: directory(write=True, group="directory")
    ld: field(type_=List[directory()], group="directory")
    old: field(type_=List[directory(write=True)], group="directory")

    u: field(type_=Union[str, List[str]], group="union")
    ou: field(type_=Union[str, List[str]], output=True, group="union")
    lu: field(type_=List[Union[str, List[str]]], group="union")
    olu: field(type_=List[Union[str, List[str]]], output=True, group="union")

    m: field(type_=Dict, group="dict")
    om: field(type_=dict, output=True, group="dict")
    lm: field(type_=List[dict], group="dict")
    olm: field(type_=List[dict], output=True, group="dict")
    mt: field(type_=Dict[str, List[int]], group="dict")

    controller: field(type_=Controller, group="controller")
    list_controller: field(type_=List[Controller], group="controller")
    custom: field(type_=CustomController, group="controller")
    list_custom: field(type_=List[CustomController], group="controller")
    list2_custom: field(type_=List[List[CustomController]], group="controller")

    Set_str: Set[str]


if __name__ == "__main__":
    # Create a qt applicaction
    app = Qt.QApplication(sys.argv)

    # Create the controller we want to parametrized
    controller = TestControls()

    # Set some values to the controller parameters
    controller.s = "a text value"
    controller.n = 10.2

    controller.lls = [[], ["a", "b", "c"], []]
    # Create to controller widget that are synchronized on the fly
    widget1 = ControllerWidget(controller)
    widget2 = ControllerWidget(controller)
    widget1.show()
    widget2.show()

    # Start the qt loop
    app.exec_()
