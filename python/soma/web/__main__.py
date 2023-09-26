# -*- coding: utf-8 -*-
from soma.controller import (Controller,
                             field,
                             OpenKeyController,
                             List,
                             Literal,
                             Union,
                             Dict,
                             Set,
                             File,
                             Directory)

class SubController(Controller):
    dummy: str


class VisibleController(Controller):
    s: str = 'a string'
    i: int = 42
    n: float = 42.42
    bt: bool = True
    bf: bool = False
    e: Literal['one', 'two', 'three'] = 'two'
    f: File = '/somewhere/a_file'
    d: Directory = '/elsewhere/a_directory'
    u: Union[str, List[str]]
    m: dict
    lm: list[dict]
    mt: Dict[str, List[int]]
    l: list
    ll: List[List[str]]
    c: Controller
    lc: List[Controller]
    o: SubController
    lo: List[SubController]
    set_str: Set[str]
    set: set
    open_key: OpenKeyController[str]


def qt_web_gui():
    import sys
    from soma.qt_gui.qt_backend import Qt
    from soma.web.controller import ControllerWindow
    
    controller = VisibleController()
    # for field in controller.fields():
    #     print(field.name, ':', field.parse_type_str())
    app = Qt.QApplication(sys.argv)
    w = ControllerWindow(controller)
    w.showMaximized()
    app.exec_()


qt_web_gui()
