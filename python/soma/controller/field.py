# -*- coding: utf-8 -*-

import dataclasses
import re
import sys
import typing
from numpy import issubdtype

from pydantic import ValidationError

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
    if module and module not in {'builtins', 'typing', 'soma.controller.controller', 'soma.controller.field'}:
        name = f'{module}.{name}'
    args = getattr(type_, '__args__', ())
    if not ignore_args and args:
        result = f'{name.lower()}[{",".join(type_str(i) for i in args)}]'
    else:
        if controller:
            result = f'controller[{name}]'
        else:
            result = name  # .lower()
    return final_mapping.get(result, result)

def type_from_str(type_str):
    # TODO: avoid eval()
    return eval(type_str)

def literal_values(type):
    return type.__args__

def subtypes(type):
    return getattr(type, '__args__', ())

def is_list(type_):
    return (getattr(type_, '_name', None) == 'List'
            or getattr(type_, '__name__', None) == 'list'
            or (isinstance(type_, type) and issubclass(type_, list)))

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
    
    def __init__(self, dataclass_field):
        super().__setattr__('_dataclass_field', dataclass_field)

    @property
    def name(self):
        return self._dataclass_field.name
    
    @property
    def type(self):
        types = self._dataclass_field.type.__args__[:-1]
        if len(types) == 1:
            return types[0]
        else:
            return Union.__getitem__(types)

    @property
    def default(self):
        return self._dataclass_field.default
    
    @property
    def default_factory(self):
        return self._dataclass_field.default_factory
    
    def type_str(self):
        return type_str(self.type)

    def literal_values(self):
        return literal_values(self.type)

    def subtypes(self):
        return subtypes(self.type)

    def metadata(self, name=None, default=None):
        if name is None:
            return self._dataclass_field.metadata['_metadata']
        return self._dataclass_field.metadata['_metadata'].get(name, default)
    
    def __getattr__(self, name):
        value = self.metadata(name, undefined)
        if value is undefined:
            raise AttributeError(f'{self} has not attribute {name}')
        return value

    def __setattr__(self, name, value):
        self._dataclass_field.metadata['_metadata'][name] = value

    def __delattr__(self, name):
        del self._dataclass_field.metadata['_metadata'][name]

    def is_subclass(self, cls):
        type_ = self.type
        return isinstance(type_, type) and issubclass(type_, cls)

    def is_path(self):
        return self.is_subclass(Path)

    def is_file(self):
        return self.is_subclass(File)

    def is_directory(self):
        return self.is_subclass(Directory)

    def is_input(self):
        if self.output:
            return False
        if self.path_type:
            return self.read
        return True

    def is_output(self):
        if self.metadata('output', False) or self.metadata('write', False):
            return True
        return False

    def has_default(self):
        return (self._dataclass_field.default not in (undefined, dataclasses.MISSING)
                or self._dataclass_field.default_factory is not dataclasses.MISSING)

    def default_value(self):
        if self._dataclass_field.default is not dataclasses.MISSING:
            return self._dataclass_field.default
        if self._dataclass_field.default_factory is not dataclasses.MISSING:
            return self._dataclass_field.default_factory()
        return undefined

    def is_list(self):
        return is_list(self.type)
    
    @property
    def optional(self):
        optional = self._dataclass_field.metadata['_metadata'].get('optional')
        if optional is None:
            optional =  self.has_default()
        return optional

    @optional.setter
    def optional(self, optional):
        self._dataclass_field.metadata['_metadata']['optional'] = optional


    @optional.deleter
    def optional(self):
        del self._dataclass_field.metadata['_metadata']['optional']

    @property
    def doc(self):
        return self.__getattr__('doc')

    @doc.setter
    def doc(self, doc):
        self.__setattr__('doc', doc)
    
    @doc.deleter
    def doc(self):
        self.__delattr__('doc')

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
            default = type_._dataclass_field.default
        if default_factory is dataclasses.MISSING:
            default_factory = type_._dataclass_field.default_factory
        if init is None:
            init = type_._dataclass_field.init
        if repr is None:
            repr = type_._dataclass_field.repr
        if hash is None:
            init = type_._dataclass_field.hash
        if compare is None:
            init = type_._dataclass_field.compare
        if metadata is None:
            metadata = type_._dataclass_field.metadata.get(
                '_metadata', {}).copy()
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
    path_type = None
    if type_ is not None:
        result.type = Union[type_, type(undefined)]
        if isinstance(type_, type) and issubclass(type_, Path):
            path_type = type_.__name__.lower()
        elif is_list(type_):
            current_type = type_
            while is_list(current_type):
                s = subtypes(current_type)
                if s:
                    current_type = s[0]
                else:
                    break
            if isinstance(current_type, type) and issubclass(current_type, Path):
                path_type = current_type.__name__.lower()

    result = Field(result)
    result.path_type = path_type
    if path_type:
        result._dataclass_field.metadata['_metadata'].setdefault('read', True)
        result._dataclass_field.metadata['_metadata'].setdefault('write', False)
    return result



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


class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

class Path(str):
    pass

class File(Path):
    pass

class Directory(Path):
    pass


def _parse_type_metadata(type_):
    meta = {}
    todo = [type_]
    while todo:
        type_ = todo.pop(0)
        if hasattr(type_, '__args__') and isinstance(type_.__args__, tuple):
            todo += [t for t in type_.__args__ if isinstance(t, type)]
        if hasattr(type_, '__metadata__'):
            meta.update(type_.__metadata__)
    return meta
