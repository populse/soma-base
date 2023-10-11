# -*- coding: utf-8 -*-
import json
import http, http.server
import mimetypes
import os
import traceback

from soma.controller import Controller, to_json, from_json, OpenKeyController
from soma.controller.field import subtypes, type_str
from soma.undefined import undefined
from soma.qt_gui.qt_backend import QtWidgets
from soma.qt_gui.qt_backend.Qt import QObject, QVariant
from soma.qt_gui.qt_backend.QtCore import QUrl, pyqtSlot
from soma.qt_gui.qt_backend.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from soma.qt_gui.qt_backend.QtWebChannel import QWebChannel


'''
Infrastructure to make web-based GUI for applications displayed either as a
real web server or in a server-less QtWebEngineWidget.
'''


class JSONController:
    def __init__(self, controller):
        self.controller = controller
        self._schema = None
        
    def get_schema(self):
        if self._schema is None:
            schema = {
                "$id": "http://localhost:8080/schemas/id_of_a_controller",
                "$schema": "https://json-schema.org/draft/2020-12/schema",

                "$defs": {
                    "file": { "type": "string", "brainvisa": { "path_type": "file" }},
                    "directory": { "type": "string", "brainvisa": { "path_type": "directory" }},
                },

                "type": "object",
            }

            defs = schema['$defs']

            schema_type = self._build_json_schema(None, type(self.controller), self.controller, defs)
            if '$ref' in schema_type:
                schema['allOf'] = [schema_type]
            else:
                schema.update(schema_type)
            self._schema = schema
        return self._schema

    def get_value(self, path=None):
        container, path_item, _ = self._parse_path(path)
        if path_item:
            if isinstance(container, Controller):
                value = getattr(container, path_item)
            elif isinstance(container, list):
                value = container[int(path_item)]
            else:
                value = container[path_item]
        else:
            value = container
        return to_json(value)


    def set_value(self, path, value):
        container, path_item, container_type = self._parse_path(path)
        if isinstance(container, Controller):
            value = from_json(value, container.field(path_item).type)
            setattr(container, path_item, value)
        elif isinstance(container, list):
            value = from_json([value], container_type)[0]
            container[int(path_item)] = value
        else:
            container[int(path_item)] = value


    def new_list_item(self, path):
        container, path_item, container_type = self._parse_path(path)
        if isinstance(container, Controller):
            list_type = container.field(path_item).type
            list_value = getattr(container, path_item, None)
            if list_value is None:
                list_value = []
                setattr(container, path_item, list_value)
        elif isinstance(container, list):
            list_type = subtypes(container_type)[0]
            list_value = container[int(path_item)]
        else:
            raise NotImplementedError()
        item_type = getattr(list_type, '__args__', None)
        if not item_type:
            raise TypeError(f'Cannot create a new item for object of type {list_type}')
        item_type = item_type[0]
        if item_type.__name__ == 'Literal':
            new_value = item_type.__args__[0]
        else:
            new_value = item_type()
        list_value.append(new_value)
        return len(list_value) - 1


    def remove_item(self, path):
        container, path_item, container_type = self._parse_path(path)
        if isinstance(container, Controller):
            container.remove_field(path_item)
        elif isinstance(container, list):
            del container[int(path_item)]
        else:
            raise NotImplementedError()
        self._schema = None
        return True
    

    def new_named_item(self, path, key):
        container, path_item, container_type = self._parse_path(path)
        if isinstance(container, Controller):
            container_type = container.field(path_item).type
            container = getattr(container, path_item, None)
        elif isinstance(container, list):
            container_type = subtypes(container_type)[0]
            container = container[int(path_item)]
        else:
            raise NotImplementedError()
        if not isinstance(container, OpenKeyController):
            raise TypeError(f'Cannot create a new named item for object of type {container_type}')
        if container.field(key) is not None:
            raise ValueError(f'Cannot create a second field with name "{key}"')
        item_type = container._value_type
        new_value = item_type()
        setattr(container, key, new_value)
        self._schema = None
        return key

    
    def get_type(self, path=None):
        schema = self.get_schema()
        current_type = self._resolve_schema_type(schema, schema)
        if path:
            splitted_path = path.split('/')
            while current_type and splitted_path:
                path_item = splitted_path.pop(0)
                if current_type['type'] == 'object':
                    new_type = current_type.get('properties', {}).get(path_item)
                    if not new_type:
                        return None
                    current_type = self._resolve_schema_type(new_type, schema)
                elif current_type['type'] == 'array':
                    current_type = self._resolve_schema_type(current_type['items'], schema)
                else:
                    raise NotImplementedError()
        return current_type


    @staticmethod
    def _resolve_schema_type(type, schema):
        while '$ref' in type:
            ref_path = type['$ref'][2:].split('/')
            ref = schema
            for i in ref_path:
                ref = ref[i]
            type = ref
        if 'allOf' in type:
            result = {}
            parent_types = type['allOf']
            for parent_type in parent_types:
                for k, v in JSONController._resolve_schema_type(parent_type, schema).items():
                    if k == 'properties':
                        result.setdefault('properties', {}).update(v)
                    else:
                        result[k] = v
                for k, v in type.items():
                    if k == 'allOf' or k.startswith('$'):
                        continue
                    if k == 'properties':
                        result.setdefault('properties', {}).update(v)
                    else:
                        result[k] = v
            type = result
        return type
    
    def _parse_path(self, path):
        if path:
            splitted_path = path.split('/')
        else:
            splitted_path = []
        container = self.controller
        container_type = type(container)
        for path_item in splitted_path[:-1]:
            if isinstance(container, Controller):
                container_type = container.field(path_item).type
                container = getattr(container, path_item)
            elif isinstance(container, list):
                container = container[int(path_item)]
                container_type = subtypes(container_type)[0]
            else:
                container = container[path_item]
        if path:
            path_item = splitted_path[-1]
        else:
            path_item = None
        return (container, path_item, container_type)

    _json_simple_types = {
        str: {'type': 'string'},
        int: {'type': 'integer'},
        float: {'type': 'number'},
        bool: {'type': 'boolean'}
    }

    @classmethod
    def _build_json_schema(cls, field, value_type, value, defs):
        error = False
        result = cls._json_simple_types.get(value_type)
        if not result:
            if isinstance(value_type, type) and issubclass(value_type, Controller):
                if value_type.__name__ == 'OpenKeyController':
                    result = {
                        'type': 'object',
                        'brainvisa': {
                            'value_items': cls._build_json_schema(None, value_type._value_type, undefined, defs),
                        },
                        'properties': {}
                    }
                else:
                    result = {}
                    if value_type.__name__ not in defs:
                        class_schema = defs[value_type.__name__] = {
                            'type': 'object'
                        }
                        properties = class_schema['properties'] = {}
                        for f in value_type.this_class_fields():
                            properties[f.name] = cls._build_json_schema(f, f.type, undefined, defs)
                        base_schemas = []
                        for base_class in value_type.__mro__:
                            if issubclass(base_class, Controller) and base_class not in (Controller, value_type):
                                base_schemas.append(cls._build_json_schema(None, base_class, undefined, defs))
                        if base_schemas:
                            class_schema['allOf'] = base_schemas
                result['type'] = 'object'
                if value_type.__name__ != 'OpenKeyController':
                    result['allOf'] = [{'$ref': f'#/$defs/{value_type.__name__}'}]
                properties = result['properties'] = {}
                if value is not undefined:
                    for f in value.fields():
                        if not f.class_field or (
                                isinstance(f.type, type) and 
                                issubclass(f.type, Controller) and 
                                getattr(value, f.name).has_instance_fields()):
                            properties[f.name] = cls._build_json_schema(f, f.type, getattr(value, f.name), defs)
            elif value_type.__name__ == 'list':
                if hasattr(value_type, '__args__'):
                    result = {
                        'type': 'array',
                        'items': cls._build_json_schema(None, value_type.__args__[0], undefined, defs)
                    }
                    
                else:
                    error = True
            elif value_type.__name__ == 'Literal':
                result = {
                    "type": "string",
                    "enum": value_type.__args__
                }
            elif value_type.__name__ == 'File':
                result = { "type": "string", "brainvisa": { "path_type": "file" }}
            elif value_type.__name__ == 'Directory':
                result = { "type": "string", "brainvisa": { "path_type": "directory" }}
            else:
                error = True
        else:
            result = result.copy()
        
        if error:
            raise TypeError(f'Type not compatible with JSON schema: {type_str(value_type)}')
        else:
            if field:
                metadata = dict((k ,v) for k, v in field.metadata().items() if v is not None)
                if metadata:
                    result.setdefault('brainvisa', {}).update(metadata)
            return result



class WebHandler(QObject):
    '''
    This class is used internally in web implementations. It puts together the
    various objects and parameters necessary to answer to all browser queries. 
    '''

    static_path = os.path.join(os.path.dirname(__file__), 'static')

    def __init__(self, **controllers):
        super().__init__()
        self.json_controller = {}
        for name, controller in controllers.items():
            self.json_controller[name] = JSONController(controller)
        self._file_dialog = None
    
    @pyqtSlot(str, QVariant, result=QVariant)
    def resolve(self, path, args):
        '''
        Main method used to forge a reply to a browser request.

        Parameters
        ----------
        path: str
            path extracted from the request URL. If the URL path contains
            several / separated elements, this parameter only contains the 
            first one. The others are passed in `args`.
        args: list[str]
            List of parameters extracted from URL path. These parameters are
            passed to the method correponding to `path`.
        
        '''
        try:
            if path:
                if path[0] == '/':
                    path = path[1:]
                paths = path.split('/')
                if paths:
                    if paths[0] == 'static':
                        return (os.path.join(self.static_path, *paths[1:]), )
                    elif paths[0] == 'backend' and len(paths) >= 3:
                        _, method_name, controller_name = paths[:3]
                        method_path = '/'.join(paths[3:])
                        method = getattr(self.json_controller.get(controller_name), method_name, None)
                        if method:
                            if method_path:
                                args = [method_path] + args
                            return { 'result': method(*args) }                            
            raise ValueError(f'Invalid path: {path}')
        except Exception as e:
            return {
                'error_type': e.__class__.__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
            }

    @pyqtSlot(result=QVariant)
    def file_selector(self):
        try:
            if self._file_dialog is None:
                self._file_dialog = QtWidgets.QFileDialog()
            self._file_dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
            if self._file_dialog.exec_():
                selected = self._file_dialog.selectedFiles()
                if selected:
                    return {'result': selected[0]}
            return ''
        except Exception as e:
            return {
                'error_type': e.__class__.__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
            }


    @pyqtSlot(result=QVariant)
    def directory_selector(self):
        try:
            if self._file_dialog is None:
                self._file_dialog = QtWidgets.QFileDialog()
            self._file_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
            if self._file_dialog.exec_():
                selected = self._file_dialog.selectedFiles()
                if selected:
                    return {'result': selected[0]}
            return ''
        except Exception as e:
            return {
                'error_type': e.__class__.__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc(),
            }

 

class SomaHTTPHandlerMeta(type(http.server.BaseHTTPRequestHandler)):
    '''
    Python standard HTTP server needs a handler class. This metaclass
    allows to instanciate this class with parameters required to
    build a :class:`WebHandler`.
    '''
    def __new__(cls, name, bases, dict, **kwargs):
        if name != 'SomaHTTPHandler':
            dict['_handler'] = WebHandler(**kwargs)
        return super().__new__(cls, name, bases, dict)



class SomaHTTPHandler(http.server.BaseHTTPRequestHandler, metaclass=SomaHTTPHandlerMeta):
    '''
    Base class to create a handler in order to implement a proof-of-concept
    http server for Soma GUI. This class must be used only for demo, debug
    or tests. It must not be used in production. Here is an example of server
    implementation:

    ::
        #
        # This example is obsolete, it must be rewritten
        #
        # import http, http.server

        # from capsul.api import Capsul
        # from capsul.ui import CapsulRoutes, CapsulBackend
        # from capsul.web import CapsulHTTPHandler

        # routes = CapsulRoutes()
        # backend = CapsulBackend()
        # capsul=Capsul()

        # class Handler(CapsulHTTPHandler, base_url='http://localhost:8080',
        #             capsul=capsul, routes=routes, backend=backend):
        #     pass

        # httpd = http.server.HTTPServer(('', 8080), Handler)
        # httpd.serve_forever()
    '''
    
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)


    def do_GET(self):
        if self.headers.get('Content-Type') == 'application/json':
            length = int(self.headers.get('Content-Length'))
            if length:
                args = json.loads(self.rfile.read(length))
        else:
            args = []
        try:
            path = self.path.split('?',1)[0]
            path = path.split('#',1)[0]            
            filename_or_json = self._handler.resolve(path, args)
        except ValueError as e:
            self.send_error(400, str(e))
            return None
        except Exception as e:
            self.send_error(500, str(e))
            raise
            return None
        header = {}
        if filename_or_json is None:
            body = None
        elif isinstance(filename_or_json, tuple):
            filename = filename_or_json[0]
            try:
                s = os.stat(filename)
            except FileNotFoundError:
                self.send_error(http.HTTPStatus.NOT_FOUND, "File not found")
                return None
            _, extension = os.path.splitext(filename)
            mime_type = mimetypes.types_map.get(extension, 'text/plain')
            header['Content-Type'] = mime_type
            header['Last-Modified'] = self.date_time_string(s.st_mtime)
            body = open(filename).read()
        else:
            header['Content-Type'] = 'application/json'
            body = json.dumps(filename_or_json)
        
        self.send_response(http.HTTPStatus.OK)
        # The following line introduces a security issue by allowing any 
        # site to use the backend. But this is a demo only server.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST')
        self.send_header('Access-Control-Allow-HEADERS', 'Content-Type')
        for k, v in header.items():
            self.send_header(k, v)

        if body is not None:
            body = body.encode('utf8')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_OPTIONS(self):
        # The following line introduces a security issue by allowing any 
        # site to use the backend. But this is a demo only server.
        self.send_response(http.HTTPStatus.OK)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST')
        self.send_header('Access-Control-Allow-HEADERS', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        return self.do_GET()



class SomaWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print (msg)


class SomaWebEngineView(QWebEngineView):
    '''
    Reimplements :meth:`SomaWebEngineView.createWindow` to allow the browser
    to open new windows.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page = SomaWebPage()
        self.setPage(self._page)
    
    def createWindow(self, wintype):
        w = super().createWindow(wintype)
        if not w:
            try:
                parent = self.parent()
                self.source_window = SomaBrowserWindow(
                    starting_url = parent.starting_url,
                )
                self.source_window.show()
                w = self.source_window.browser
            except Exception as e:
                print('ERROR: Cannot create browser window:', e)
                w = None
        return w


class SomaBrowserWindow(QtWidgets.QMainWindow):
    '''
    Top level widget to display Soma GUI in Qt.

    ::

        #
        # This exapmle is obsolete and must be rewritten
        #
        # import sys
        # from soma.qt_gui.qt_backend import Qt
        # from soma.web import SomaBrowserWindow

        # app = Qt.QApplication(sys.argv)
        # w = SomaBrowserWindow()
        # w.show()
        # app.exec_()

    '''
    def __init__(self, starting_url=None, window_title=None,
                 **kwargs):
        super(QtWidgets.QMainWindow, self).__init__()
        self.setWindowTitle(window_title or 'Soma Browser')
        if starting_url:
            self.starting_url = starting_url
        else:
            s = os.path.split(os.path.dirname(__file__)) + ('static', 'controller.html')
            self.starting_url = f'file://{"/".join(s)}'
        self._handler = WebHandler(**kwargs)
        self.browser = SomaWebEngineView()
        self.channel = QWebChannel()
        self.channel.registerObject('backend', self._handler)
        self.browser.page().setWebChannel(self.channel)
        self.setCentralWidget(self.browser)
        self.browser.iconChanged.connect(self.set_icon)
        self.browser.setUrl(QUrl(self.starting_url))

    def set_icon(self):
        self.setWindowIcon(self.browser.icon())
