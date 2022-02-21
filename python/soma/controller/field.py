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

max_field_creation_order = 1000000
def field(name=None, type_=None, 
         default=dataclasses.MISSING, 
         default_factory=dataclasses.MISSING, 
         init=None, 
         repr=None,
         hash=None, 
         compare=None, 
         metadata=None,
         **kwargs):
    global max_field_creation_order
    if isinstance(type_, dataclasses.Field):
        if default is dataclasses.MISSING:
            default = type_.default
        if default_factory is dataclasses.MISSING:
            default_factory = type_.default_factory
        if init is None:
            init = type_.init
        if repr is None:
            repr = type_.repr
        if hash is None:
            init = type_.hash
        if compare is None:
            init = type_.compare
        if metadata is None:
            metadata = type_.metadata.get('_metadata', {}).copy()
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
        max_field_creation_order += 1
        order = max_field_creation_order
    else:
        max_field_creation_order = max(max_field_creation_order, order)
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
    return result


def field_type(field):
    types = field.type.__args__[:-1]
    if len(types) == 1:
        return types[0]
    else:
        return Union.__getitem__(types)

def field_type_str(field):
    if has_path(field):
        path_type = metadata(field, 'format').split('/')[1]
        if is_list(field):
            return f'list[{path_type}]'
        else:
            return path_type
    return type_str(field_type(field))

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


def field_literal_values(field):
    return literal_values(field_type(field))


def subtypes(type):
    return type.__args__


def field_subtypes(field):
    return subtypes(field_type(field))


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

def metadata(field, key=None, default=None):
    editable_metadata = field.metadata['_metadata']
    if key is None:
        return editable_metadata
    else:
        return editable_metadata.get(key, default)

def set_metadata(field, key, value):
    editable_metadata = field.metadata['_metadata']
    if value is undefined:
        editable_metadata.pop(key, None)
    else:
        editable_metadata[key] = value


class ListMeta(type):
    def __getitem__(cls, type):
        if isinstance(type, dataclasses.Field):
            result = field(
                type_=List[field_type(type)], 
                metadata=type.metadata.get('_metadata', {}))
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


def has_path(field):
    return metadata(field, 'format', '').startswith('path/')

def has_file(field):
    return metadata(field, 'format', '') == 'path/file'

def has_directory(field):
    return metadata(field, 'format', '') == 'path/directory'

def is_path(field):
    return field_type(field) is str and has_path(field)

def is_file(field):
    return field_type(field) is str and has_file(field)

def is_directory(field):
    return field_type(field) is str and has_directory(field)

def is_input(field):
    return (not metadata(field, 'output', False)
            and metadata(field, 'read', True))

def is_output(field):
    return (metadata(field, 'output', False)
            or metadata(field, 'write', False))

def has_default(field):
    return (field.default not in (undefined, dataclasses.MISSING)
            or field.default_factory is not dataclasses.MISSING)

def default_value(field):
    if field.default is not dataclasses.MISSING:
        return field.default
    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()
    return undefined

def is_list(field):
    t = field_type(field)
    return (getattr(t, '_name', None) == 'List'
            or getattr(t, '__name__', None) == 'list'
            or (isinstance(t, type) and issubclass(t, list)))
