# -*- coding: utf-8 -*-
from .. import WebRoutes, WebBackend, SomaBrowserWindow


class ControllerRoutes(WebRoutes):
    def view(self):
        return self._result('controller.html')



class ControllerBackend(WebBackend):
    ...

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
