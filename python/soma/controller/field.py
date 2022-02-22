# -*- coding: utf-8 -*-

import dataclasses
import re
import sys
import typing

from soma.undefined import undefined

# Import allsupported types from typing
from typing import (
    Any,
    Literal,
    Union,
)

if sys.version_info < (3,9):
    from typing import (
        Tuple,
        Dict,
        Set,
    )
else:
    Tuple = tuple
    Dict = dict
    Set = set

def type_str(type_):
    from soma.controller import Controller

    final_mapping = {
        'list[any]': 'list',
        'typing.any': 'Any',
        'tuple[any]': 'tuple',
        'dict[any,any]': 'dict',
        'controller[Controller]': 'controller',
    }
    name = getattr(type_, '__name__', None)
    ignore_args = False
    if not name:
        name = getattr(type_, '_name', None)
        if name == 'List':
            name = 'list'
        elif name == 'Dict':
            name = 'dict'
            args = getattr(type_, '__args__', None)
            ignore_args = args == getattr(Dict, '__args__', None)
        elif name == 'Set':
            name = 'set'
            args = getattr(type_, '__args__', None)
            ignore_args = args == getattr(Set, '__args__', None)
    if name:
        name = name
    if not name and getattr(type_, '__origin__', None) is Union:
        name = 'union'
    if not name:
        name = str(type_).replace(' ', '')
        if name.startswith('typing.'):
            name = name[7:]
            ignore_args = True
    module = getattr(type_, '__module__', None)
    controller = isinstance(type_, type) and issubclass(type_, Controller)
    if module and module not in {'builtins', 'typing', 'soma.controller.controller'}:
        name = f'{module}.{name}'
    args = getattr(type_, '__args__', ())
    if not ignore_args and args:
        result = f'{name.lower()}[{",".join(type_str(i) for i in args)}]'
    else:
        if controller:
            result = f'controller[{name}]'
        else:
            result = name.lower()
    return final_mapping.get(result, result)

def type_from_str(type_str):
    # TODO: avoid eval()
    return eval(type_str)

def literal_values(type):
    return type.__args__

def subtypes(type):
    return type.__args__

def parse_type_str(type_str):
    '''
    Returns a tuple with two elements:
    - The main type name
    - A (possibly empty) list of parameter types

    Examples:
    'str' -> ('str', [])
    'List[str]' -> ('List', ['str'])
    'union[list[str],Dict[str,controller[Test]]]' -> ('union', ['list[str]', 'Dict[str,controller[Test]]'])
    '''
    p = re.compile('(^[^\[\],]*)(?:\[(.*)\])?$')
    type, inner = p.match(type_str).groups()
    if inner:
        p = re.compile(r'\[[^\[\]]*\]')
        substitution = {}
        i = 0
        while True:
            c = 0
            new_inner = []
            for m in p.finditer(inner):
                skey = f's{i}'
                i += 1
                substitution[skey] = m.group(0).format(**substitution)
                new_inner += [inner[c:m.start()], f'{{{skey}}}']
                c = m.end()
            if new_inner:
                new_inner.append(inner[c:])
                inner = ''.join(new_inner)
            else:
                return (type, [i.format(**substitution) for i in inner.split(',')])
    else:
        return (type, [])


type_default_value_functions = {
    'str': lambda t: '',
    'int': lambda t: 0,
    'float': lambda t: 0.0,
    'bool': lambda t: False,
    'list': lambda t: [],
    'controller': lambda t: t(),
    'literal': lambda t: literal_values(t)[0],
}


def type_default_value(type):
    global type_default_value

    full_type = type_str(type)
    main_type = full_type.split('[', 1)[0]
    f = type_default_value_functions.get(main_type)
    if f:
        return f(type)
    raise TypeError(f'Cannot get default value for type {type_str}')


class Field:
    _max_field_creation_order = 1000000
    
    def __init__(self, field):
        self.field = field

    @property
    def name(self):
        return self.field.name
    
    @property
    def type(self):
        types = self.field.type.__args__[:-1]
        if len(types) == 1:
            return types[0]
        else:
            return Union.__getitem__(types)

    @property
    def default(self):
        return self.field.default
    
    @property
    def default_factory(self):
        return self.field.default_factory
    
    def type_str(self):
        if self.has_path():
            path_type = self.metadata('format').split('/')[1]
            if self.is_list():
                return f'list[{path_type}]'
            else:
                return path_type
        return type_str(self.type)

    def literal_values(self):
        return literal_values(self.type)

    def subtypes(self):
        return subtypes(self.type)

    def metadata(self, key=None, default=None):
        editable_metadata = self.field.metadata['_metadata']
        if key is None:
            return editable_metadata
        else:
            return editable_metadata.get(key, default)

    def set_metadata(self, key, value):
        editable_metadata = self.field.metadata['_metadata']
        if value is undefined:
            editable_metadata.pop(key, None)
        else:
            editable_metadata[key] = value

    def has_path(self):
        return self.metadata('format', '').startswith('path/')

    def has_file(self):
        return self.metadata('format', '') == 'path/file'

    def has_directory(self):
        return self.metadata('format', '') == 'path/directory'

    def is_path(self):
        return self.type is str and self.has_path()

    def is_file(self):
        return self.type is str and self.has_file()

    def is_directory(self):
        return self.type is str and self.has_directory()

    def is_input(self):
        return (not self.metadata('output', False)
                and self.metadata('read', True))

    def is_output(self):
        return (self.metadata('output', False)
                or self.metadata('write', False))

    def has_default(self):
        return (self.field.default not in (undefined, dataclasses.MISSING)
                or self.field.default_factory is not dataclasses.MISSING)

    def default_value(self):
        if self.field.default is not dataclasses.MISSING:
            return self.field.default
        if self.field.default_factory is not dataclasses.MISSING:
            return self.field.default_factory()
        return undefined

    def is_list(self):
        t = self.type
        return (getattr(t, '_name', None) == 'List'
                or getattr(t, '__name__', None) == 'list'
                or (isinstance(t, type) and issubclass(t, list)))

    def is_optional(self):
        optional = self.metadata('optional', None)
        if optional is None:
            optional =  self.has_default()
        return optional

    def set_optional(self, optional):
        if optional is None:
            self.set_metadata('optional', undefined)
        else:
            self.set_metadata('optional', bool(optional))

def field(
         name=None, 
         type_=None, 
         default=dataclasses.MISSING, 
         default_factory=dataclasses.MISSING, 
         init=None, 
         repr=None,
         hash=None, 
         compare=None, 
         metadata=None,
         **kwargs):
    if isinstance(type_, Field):
        if default is dataclasses.MISSING or default is undefined:
            default = type_.field.default
        if default_factory is dataclasses.MISSING:
            default_factory = type_.field.default_factory
        if init is None:
            init = type_.field.init
        if repr is None:
            repr = type_.field.repr
        if hash is None:
            init = type_.field.hash
        if compare is None:
            init = type_.field.compare
        if metadata is None:
            metadata = type_.metadata().copy()
        else:
            metadata = metadata.copy()
        type_ = type_.type
    elif metadata is None:
        metadata = {}
    else:
        metadata = metadata.copy()
    metadata.update(kwargs)
    order = metadata.get('order')
    if order is None:
        Field._max_field_creation_order += 1
        order = Field._max_field_creation_order
    else:
        Field._max_field_creation_order = max(Field._max_field_creation_order, order)
    metadata['order'] = order
    if init is None:
        init=True
    if repr is None:
        repr = True
    if compare is None:
        compare = True
    if default is dataclasses.MISSING and default_factory is dataclasses.MISSING:
        default = undefined
    result = dataclasses.field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata={'_metadata': metadata})
    if name is not None:
        result.name = name
    if type_ is not None:
        result.type = Union[type_, type(undefined)]
    return Field(result)


class ListMeta(type):
    def __getitem__(cls, type):
        if isinstance(type, Field):
            result = field(
                type_=List[type.type], 
                metadata=type.metadata())
        else:
            result = typing.List[type]
        return result

class List(metaclass=ListMeta):
    pass

def path(format=None,
         dataset=undefined,
         read=undefined,
         write=False,
         default=undefined,
         default_factory=undefined,
         doc=undefined,
         _type=str,
         **metadata):
    if read is undefined:
        read = not write
    if dataset is undefined:
        dataset = ('output' if write else 'input')
    field_metadata = {
        'format': (f'path/{format}' if format else 'path'),
        'dataset': dataset,
        'read': read,
        'write': write,
    }
    if doc is not undefined:
        field_metadata['doc'] = doc
    field_metadata.update(metadata)
    if default_factory is undefined:
        default_factory = dataclasses.MISSING
    return field(type_=_type,
                 metadata=field_metadata,
                 default=default,
                 default_factory=default_factory)


def file(**kwargs):
    return path(format='file', **kwargs)


def directory(**kwargs):
    return path(format='directory', **kwargs)
