# -*- coding: utf-8 -*-
from functools import wraps
import traceback

from soma.api import Controller
from soma.controller.field import subtypes
from soma.web import JSONController
from .. import WebRoutes, WebBackend, SomaBrowserWindow


class ControllerRoutes(WebRoutes):
    def view(self):
        return self._result('controller.html', read_only=True)


    def edit(self):
        return self._result('controller.html', read_only=False)



class ControllerBackend(WebBackend):
    _json_controller = None

    @property
    def json_controller(self):
        if self._json_controller is None:
            self._json_controller = JSONController(self._handler['controller'])
        return self._json_controller
    
    def json_exception(callable):
        @wraps(callable)
        def wrapper(*args):
            try:
                return { 'result': callable(*args) }
            except Exception as e:
                return {
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc(),
                }
        return wrapper
    
    @json_exception
    def get_type(self, path: str = None) -> dict:
        return self.json_controller.get_type(path)

    @json_exception        
    def get_value(self, path: str = None) -> dict:
        return self.json_controller.get_value(path)
   
    @json_exception        
    def set_value(self, path: str, value: 'QVariant') -> dict:
        self.json_controller.set_value(path, value)

    @json_exception        
    def new_list_item(self, path: str) -> int:
        return self.json_controller.new_list_item(path)


class ControllerWindow(SomaBrowserWindow):
    def __init__(self, controller, title='Controller', read_only=False):
        super().__init__(
            routes = ControllerRoutes(),
            backend = ControllerBackend(),
            starting_url=f'soma://{("view" if read_only else "edit")}',
            title=title,
            window_title=title,
            controller=controller,
        )
        self.controller = controller
