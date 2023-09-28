# -*- coding: utf-8 -*-
from soma.api import Controller
from .. import WebRoutes, WebBackend, SomaBrowserWindow


class ControllerRoutes(WebRoutes):
    def view(self):
        return self._result('controller.html', read_only=True)


    def edit(self):
        return self._result('controller.html', read_only=False)



class ControllerBackend(WebBackend):
    def set_value(self, id: str, value: 'QVariant') -> dict:
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
                print('!1!', index, value)
                setattr(container, index, value)
                print('!2!', index, value)
                value = getattr(container, index)
                print('!3!', index, value)
            elif isinstance(container, list):
                container[int(index)] = value
            else:
                container[index] = value
        except Exception as e:
            return {
                'value': None,
                'error': str(e)
            }
        return {
            'value': value
        }

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
