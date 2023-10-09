# -*- coding: utf-8 -*-
import importlib
import json
import http, http.server
import mimetypes
import os
import traceback
import weakref

import jinja2

from soma.controller import Controller, to_json, from_json, OpenKeyController
from soma.controller.field import is_list, subtypes, parse_type_str, type_str
from soma.undefined import undefined
from soma.qt_gui.qt_backend import Qt, QtWidgets
from soma.qt_gui.qt_backend.QtCore import pyqtSlot, QUrl, QBuffer, QIODevice
from soma.qt_gui.qt_backend.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from soma.qt_gui.qt_backend.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlScheme, QWebEngineUrlRequestJob
from soma.qt_gui.qt_backend.QtWebChannel import QWebChannel


'''
Infrastructure to make web-based GUI for applications displayed either as a
real web server or in a server-less QtWebEngineWidget.

An application who wants to create an interactive Web GUI must define two
things:

    - A series of valid URLs connected to an HTML content usualy
      contained in a file. These URLs are defined by deriving a
      `WebRoutes` class.
    - A series of valid URLs connected to a Python function returning
      a JSON object. These API URLs are defined by deriving a
      `WebBackend` class.
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

    def get_value(self, path):
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
        new_value = item_type()
        list_value.append(new_value)
        return len(list_value) - 1

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

@jinja2.pass_context
def render_controller_value(context, field, label, item_type, editor_type, id, value):
    type_string, type_string_params = parse_type_str(type_str(item_type))
    macro = context.vars.get(f'{editor_type}_{type_string}')
    if not macro:
        if issubclass(item_type, Controller):
            for parent_type in item_type.__mro__:
                parent_type_string = parent_type.__name__
                macro = context.vars.get(f'{editor_type}_{parent_type_string}')
                if macro:
                    break
        elif is_list(item_type):
            macro = context.vars.get(f'{editor_type}_list_{type_string_params[0]}')
            if macro is None:
                item_subtype = subtypes(item_type)[0]
                subtype_string, subtype_string_params = parse_type_str(type_string_params[0])
                macro = context.vars.get(f'{editor_type}_{subtype_string}')
                if macro:
                    result = []
                    i = 0
                    for item_value in value:
                        result.append(render_controller_value(
                            context,
                            field,
                            f'[{i}]',
                            item_subtype,
                            editor_type,
                            f'{id}.{i}',
                            item_value))
                        i += 1
                    list_macro = context.vars.get(f'{editor_type}_generic_list')
                    return list_macro(id, label, field, result, type_string_params)
    if macro:
        return macro(id, label, field, value, type_string_params)
    return None


class WebRoutes:
    '''
    Class derived from `WebRoutes` are used to define the routes that will be
    available to the GUI browser (that is either a Qt widget or a real web
    browser). Each method define in the derived class will add a route (an URL
    that will be recognized by the browser). Each method must return an HTML
    document templated with Jinja2 using `return self._result(filename)` where
    `filename` is a path relative to the `templates` folder of the `soma.web`
    module.

    Derived class can also define a `_template` set containing paths (relative
    to `templates` directory of `soma.web` module). Each path will be added
    as a valid web route displaying this file filtered by Jinja2 (the
    `Content-Type` of the file is guessed from the filename extension).

    The following Jinja2 template parameters are always set:
    - `base_url`: prefix to build any URL in template. For instance to create
      a link to a route corresponding to a method in this class, one should
      use: `<a href="{{base_url}}/method_name">the link</a>`.
    - `server_type`: a string containing either `qt` if the browser is a
       serverless Qt widget or `html` for a real browser with an HTTP server.
    For instance, let's consider that the base URL of the GUI is `soma://`, 
    the following definition declares four routes: 
    
    - `soma:///qt_backend.js`: using the result of 
      `{soma.web directory}/templates/qt_backend.js` send to Jinja2.
    - `soma:///html_backend.js`: using the result of 
      `{soma.web directory}/templates/html_backend.js` send to Jinja2.
    - `soma:///dashboard`: calling `dahsboard()` method.
    - `soma:///engine/{engine_id}`. calling `engine(engine_id) method.

    ```
    from soma.web import WebRoutes

    class CapsulRoutes(WebRoutes):
        _templates = {
            'qt_backend.js',
            'html_backend.js'
        }

        def dashboard(self):
            return self._result('dashboard.html')

        def engine(self, engine_id):
            engine = self.handler.capsul.engine(engine_id)
            if engine:
                return self._result('engine.html', engine=engine)
    ```

    '''
    _templates = {
        'qt_backend.js',
        'html_backend.js'
    }

    def _result(self, template, **kwargs):
        '''
        Return a valid result value that is passed to the `WebHandler` and
        will be interpreted as: an HTML page whose the result of a Jinja2
        template usControllerRoutesing builtin variables and those given in parameters.
        '''
        return (template, kwargs)


class WebBackendMeta(type(Qt.QObject)):
    '''
    `WebBackend` metaclass. Analyses all methods declared by `WebBackend`
    subclasses. Those using annotations are considered as valid API routes.
    Valid API routes are transformed in PyQt slots to be recognized by
    `QWebChannel` and some attributes are added to quickly list their
    parameters and return value type.
    '''
    def __new__(cls, name, bases, dict):
        for k, v in dict.items():
            if callable(v) and v.__annotations__:
                args = [type for name, type in v.__annotations__.items() if name != 'return']
                return_type = v.__annotations__.get('return')
                if return_type:
                    result = pyqtSlot(*args, result=Qt.QVariant)(v)
                else:
                    result = pyqtSlot(*args)(v)
                result._params = [name for name in v.__annotations__ if name != 'return']
                result._return = return_type
                dict[k] = result
        return super().__new__(cls, name, bases, dict)


class WebBackend(Qt.QObject, metaclass=WebBackendMeta):
    '''
    Base class to declare routes correponding to JSON backend API. Each method
    in derived class that has annotations can be called from the client browser
    using JavaScript. In all web pages, a `backend` global variable is
    declared. This Javascript object contains one method for each `WebBackend`
    method. The calling of these methods is Javascript is done as if using a Qt
    QWebChannel. But, in case of a real browser with a HTML server, an Ajax
    call to the server (using Javascript `fetch()` function) will be performed. 

    A method without return value can be called directly:
    ```
    backend.a_method_without_return(parameter1, parameter2);
    ```

    When there is a return value, a callback function must be given as last
    parameter. This function will be called with the method's result as last
    parameter:
    ```
    backend.a_method_with_return(parameter1, parameter2, (result) => { ... });
    ```

    Methods can return anything that can be serialized using `json.dumps()`.
    '''
    _file_dialog = None

    @pyqtSlot(result=str)
    def file_selector(self):
        if self._file_dialog is None:
            self._file_dialog = QtWidgets.QFileDialog()
        self._file_dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        if self._file_dialog.exec_():
            selected = self._file_dialog.selectedFiles()
            if selected:
                return selected[0]
        return ''
    file_selector._params = []
    file_selector._return = str


    @pyqtSlot(result=str)
    def directory_selector(self):
        if self._file_dialog is None:
            self._file_dialog = QtWidgets.QFileDialog()
        self._file_dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if self._file_dialog.exec_():
            selected = self._file_dialog.selectedFiles()
            if selected:
                return selected[0]
        return ''
    directory_selector._params = []
    directory_selector._return = str

class WebHandler:
    '''
    This class is used internally in web implementations. It puts together the
    various objects and parameters necessary to answer to all browser queries. 
    '''

    def __init__(self, base_url, server_type, routes, backend, templates,
                 static=None, **kwargs):
        '''
        Creates a handler for handling any browser requests. This class is
        build and used internally by Qt or HTML server implementations.

        Parameters
        ----------
        base_url: str
            URL prefix passed to Jinja2 templates and used to create links.
        server_type: str
            Either `'qt'` for browser using serverless QWebEngine or `'html'`
            for real web browser using an http server.
        routes: :class:`WebRoutes`
            Defines routes that will be available to browser to display HTML
            content to the user. These routes are exposed as 
            `{{base_url}}/method_name`.
        backend: :class:`WebBackend`
            Defines routes that are avalaible as a JSON API backend. These
            routes are exposed as `{{base_url}}/backend/method_name`.
        templates: list[str] or str
            Template directories where template files are looked for. A str
            value is considered as a list with a single value. Each value can
            be either an existing path or a valid Python module name. If it is
            a module, the considered path is the `templates` directory located
            if this module directory.
        static: list[str] or str
            Static directories whose content will be exposed through
            `{{base_url}}/static/file_name`. A str
            value is considered as a list with a single value. Each value can
            be either an existing path or a valid Python module name. If it is
            a module, the considered path is the `templates` directory located
            if this module directory.
        kwargs: dict
            All supplementary keyword parameter will be passed to every Jinja2
            templates.
        '''
        self.routes = routes
        self.routes._handler = weakref.proxy(self)
        routes.handler = self
        self.backend = backend
        self.backend._handler = weakref.proxy(self)
        self.static_path = []
        self.jinja_kwargs = kwargs
        self.base_url = self.jinja_kwargs['base_url'] = base_url 
        self.server_type = self.jinja_kwargs['server_type'] = server_type

        loader = jinja2.ChoiceLoader([jinja2.PackageLoader('soma.web')])
        if templates is None:
            templates = []
        elif isinstance(templates, str):
            templates = [templates]
        for t in templates:
            if os.path.isdir(t):
                loader.loaders.append(jinja2.FileSystemLoader(t))
            else:
                loader.loaders.append(jinja2.PackageLoader(t))
        self.jinja = jinja2.Environment(
            loader=loader,
            autoescape=jinja2.select_autoescape()
        )
        self.jinja.filters['render_controller_value'] = render_controller_value
        self.jinja.globals['undefined'] = undefined
        self.jinja.globals['map'] = map
        self.jinja.globals['str'] = str

        if static is None:
            static = []
        elif isinstance(static, str):
            static = [static]
        for s in ['soma.web'] + static:
            if os.path.isdir(s):
                self.static_path.append(s)
            else:
                m = importlib.import_module(s)
                self.static_path.append(os.path.join(os.path.dirname(m.__file__), 'static'))
    
    def resolve(self, path, *args):
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
        if path:
            if path[0] == '/':
                path = path[1:]
            paths = path.split('/')
            name = paths[0]
            path_args = paths[1:]

            if name in self.routes._templates and not path_args:
                return (name, self.jinja_kwargs)
            method = getattr(self.routes, name, None)
            if method:
                template, kwargs = method(*(tuple(path_args) + args))
                kwargs.update(self.jinja_kwargs)
                return (template, kwargs)
            if path.startswith('backend/') and self.backend:
                name, path = (path[8:].split('/', 1) + [''])[:2]
                if path:
                    args = (path,) + args
                method = getattr(self.backend, name, None)
                if method:
                    return method(*args)
            elif path.startswith('static/'):
                path = path[7:]
                for p in self.static_path:
                    fp = os.path.join(p, path)
                    if os.path.exists(fp):
                        return (fp, None)
        raise ValueError('Invalid path')


    def __getitem__(self, key):
        return self.jinja_kwargs[key]
    

class SomaHTTPHandlerMeta(type(http.server.BaseHTTPRequestHandler)):
    '''
    Python standard HTTP server needs a handler class. This metaclass
    allows to instanciate this class with parameters required to
    build a :class:`WebHandler`.
    '''
    def __new__(cls, name, bases, dict, base_url=None,
                routes=None, backend=None, templates=None,
                static=None, **kwargs):
        if name != 'SomaHTTPHandler':
            l = locals()
            missing = [i for i in ('base_url', 'routes', 'backend') if l.get(i) is None]
            if missing:
                raise TypeError(f'SomaHTTPHandlerMeta.__new__() missing {len(missing)} required positional arguments: {", ".join(missing)}')
            backend_methods = {
                'file_selector': backend.file_selector,
                'directory_selector': backend.directory_selector,
            }
            for attr in backend.__class__.__dict__:
                if attr.startswith('_'):
                    continue
                backend_methods[attr] = getattr(backend.__class__, attr)
            dict['_handler'] = WebHandler(
                server_type='http',
                base_url=base_url,
                routes=routes, 
                backend=backend,
                templates=templates,
                static=static,
                backend_methods=backend_methods,
                **kwargs)
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
        path = self.path.split('?',1)[0]
        path = path.split('#',1)[0]
        try:
            template_data = self._handler.resolve(path, *args)
        except ValueError as e:
            self.send_error(400, str(e))
            return None
        except Exception as e:
            self.send_error(500, str(e))
            raise
            return None
        header = {}
        if template_data is None:
            body = None
        elif isinstance(template_data, tuple):
            template, data = template_data
            if data is None:
                try:
                    s = os.stat(template)
                except FileNotFoundError:
                    self.send_error(http.HTTPStatus.NOT_FOUND, "File not found")
                    return None
                _, extension = os.path.splitext(template)
                mime_type = mimetypes.types_map.get(extension, 'text/plain')
                header['Content-Type'] = mime_type
                header['Last-Modified'] = self.date_time_string(os.stat(template).st_mtime)
                body = open(template).read()
            else:
                _, extension = os.path.splitext(template)
                mime_type = mimetypes.types_map.get(extension, 'text/html')
                try:
                    template = self._handler.jinja.get_template(template)
                except jinja2.TemplateNotFound:
                    self.send_error(http.HTTPStatus.NOT_FOUND, "Template not found")
                    return None
                header['Content-Type'] = mime_type
                header['Last-Modified'] = self.date_time_string(os.stat(template.filename).st_mtime)
                body = template.render(**data)
        else:
            header['Content-Type'] = 'application/json'
            body = json.dumps(template_data)
        
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


class SomaSchemeHandler(QWebEngineUrlSchemeHandler):
    '''
    In Qt implementation of Soma GUI, all internal links uses the scheme
    'soma'. For instance, the dashboard page URL is soma:///dashboard.
    A :class:`SomaSchemeHandler` is installed to process these URL and
    return appropriate content using a :class:̀ WebHandler`.
    '''
    def __init__(self, parent, routes, backend, **kwargs):
        super().__init__(parent)
        self._handler = WebHandler(
            base_url='soma://',
            server_type='qt',
            routes=routes,
            backend=backend,
            **kwargs)

    def requestStarted(self, request):
        url = request.requestUrl()
        path = url.toString().split('://', 1)[-1]

        try:
            try:
                template_data = self._handler.resolve(path)
            except ValueError as e:
                request.fail(QWebEngineUrlRequestJob.UrlNotFound)
                return None
            body = None
            if template_data:
                template, data = template_data
                if data is None:
                    body = open(template).read()
                else:
                    try:
                        template = self._handler.jinja.get_template(template)
                    except jinja2.TemplateNotFound:
                        request.fail(QWebEngineUrlRequestJob.UrlNotFound)
                        return None
                    body = template.render(**data)
        except Exception as e:
            template = self._handler.jinja.get_template('exception.html')
            body = template.render(exception=e, traceback=traceback.format_exc())
        if isinstance(body, str):
            body = body.encode('utf8')
        buf = QBuffer(parent=self)
        request.destroyed.connect(buf.deleteLater)
        buf.open(QIODevice.WriteOnly)
        buf.write(body)
        buf.seek(0)
        buf.close()
        mime_type = mimetypes.guess_type(path)[0]
        if mime_type is None:
            mime_type = 'text/html'
        request.reply(mime_type.encode(), buf)

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
                    routes = parent.routes,
                    backend = parent.backend,
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
    def __init__(self, starting_url, routes, backend,
                 templates=None, static=None, window_title=None,
                 **kwargs):
        super(QtWidgets.QMainWindow, self).__init__()
        self.setWindowTitle(window_title or 'Soma Browser')
        self.starting_url = starting_url
        self.routes = routes
        self.backend = backend
        if not QWebEngineUrlScheme.schemeByName(b'soma').name():
            scheme = QWebEngineUrlScheme(b'soma')
            scheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
            QWebEngineUrlScheme.registerScheme(scheme)

            profile = QWebEngineProfile.defaultProfile()
            backend_methods = {
                'file_selector': backend.file_selector,
                'directory_selector': backend.directory_selector,
            }
            for attr in backend.__class__.__dict__:
                if attr.startswith('_'):
                    continue
                backend_methods[attr] = getattr(backend.__class__, attr)
            SomaBrowserWindow.url_scheme_handler = SomaSchemeHandler(
                self, 
                routes=routes, 
                backend=backend,
                templates=templates,
                static=static,
                backend_methods=backend_methods,
                **kwargs)
            profile.installUrlSchemeHandler(b'soma', SomaBrowserWindow.url_scheme_handler)


        self.browser = SomaWebEngineView()

        self.channel = QWebChannel()
        self.channel.registerObject('backend', SomaBrowserWindow.url_scheme_handler._handler.backend)
        self.browser.page().setWebChannel(self.channel)
        self.setCentralWidget(self.browser)
        self.browser.iconChanged.connect(self.set_icon)
        if starting_url:
            self.browser.setUrl(QUrl(starting_url))

    def set_icon(self):
        self.setWindowIcon(self.browser.icon())