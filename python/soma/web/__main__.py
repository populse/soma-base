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
    s: str = 'a string'
    i: int = 42
    n: float = 42.42
    bt: bool = True
    bf: bool = False
    e: Literal['one', 'two', 'three'] = 'two'
    f: File = '/somewhere/a_file'
    d: Directory = '/elsewhere/a_directory'
    ls: field(type_=list[str], default_factory=lambda: ['a string', 'another string'])
    li: field(type_=list[int], default_factory=lambda: [42, 24])
    ln: field(type_=list[float], default_factory=lambda: [42.24, 24.42])
    lb: field(type_=list[bool], default_factory=lambda: [True, False])
    le: field(type_=list[Literal['one', 'two', 'three']], default_factory=lambda: ['one', 'two'])
    lf: field(type_=list[File], default_factory=lambda: ['/somewhere/a_file', '/elsewhere/another_file'])
    ld: field(type_=list[Directory], default_factory=lambda: ['/somewhere/a_directory', '/elsewhere/another_directory'])
    ok: field(type_=OpenKeyController[str], default_factory=lambda: OpenKeyController[str]())

class VisibleController(SubController):
    o: field(type_=SubController, default_factory=lambda: SubController())
    lo: field(type_=list[SubController], default_factory=lambda: [SubController(), SubController()])


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
    rw = ControllerWindow(controller)
    ro = ControllerWindow(controller, read_only=True)
    qt = ControllerWidget(controller)
    rw.show()
    ro.show()
    qt.show()
    app.exec_()


def echo(*args):
    print(args)

if __name__ == '__main__':
    controller = VisibleController()
    controller.on_attribute_change.add(echo)
    # qt_web_gui(controller)
    web_server_gui(controller)
