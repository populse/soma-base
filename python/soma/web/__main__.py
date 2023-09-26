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
from soma.qt_gui.controller import ControllerWidget

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


def web_server_gui(controller):
    import http, http.server
    from soma.web import SomaHTTPHandler
    from soma.web.controller import ControllerRoutes, ControllerBackend

    class Handler(SomaHTTPHandler, base_url='http://localhost:8080',
            routes = ControllerRoutes(),
            backend = ControllerBackend(),
            title='Controller',
            controller=controller):
        pass
    httpd = http.server.HTTPServer(('', 8080), Handler)
    httpd.serve_forever()

    
def qt_web_gui(controller):
    import sys
    from soma.qt_gui.qt_backend import Qt
    from soma.web.controller import ControllerWindow
    
    app = Qt.QApplication(sys.argv)
    w = ControllerWindow(controller)
    w.show()
    w2 = ControllerWidget(controller, readonly=True)
    w2.show()
    app.exec_()


def echo(*args):
    print(args)

if __name__ == '__main__':
    controller = VisibleController()
    controller.on_attribute_change.add(echo)
    qt_web_gui(controller)
    # web_server_gui(controller)
