# -*- coding: utf-8 -*-
from soma.api import Controller
from .. import WebRoutes, WebBackend, SomaBrowserWindow


class ControllerRoutes(WebRoutes):
    _templates = {
        'qt_backend.js',
        'html_backend.js'
    }

    def view(self):
        return self._result('controller.html')



class ControllerBackend(WebBackend):
    def set_value(self, id: str, value: str):
        try:
            indices = id.split('.')[1:]
            container = self._handler['controller']
            for index in indices[:-1]:
                if isinstance(container, Controller):
                    container = getattr(container, index)
                elif isinstance(container, list):
                    container = container[int(index)]
                else:
                    container = container[index]
            index = indices[-1]
            if isinstance(container, Controller):
                setattr(container, index, value)
            elif isinstance(container, list):
                container[int(index)] = value
            else:
                container[index] = value
        except Exception:
            import traceback
            traceback.print_exc()

class ControllerWindow(SomaBrowserWindow):
    def __init__(self, controller, title='Controller'):
        super().__init__(
            routes = ControllerRoutes(),
            backend = ControllerBackend(),
            starting_url='soma://view',
            title=title,
            window_title=title,
            controller=controller,
        )
        self.controller = controller
