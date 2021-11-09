# -*- coding: utf-8 -*-

import typing
import dataclasses

from soma.undefined import undefined

# Import allsupported types from typing
from typing import (
    Any,
    Literal,
    Tuple,
    Union,
    Dict,
    Set,
)

def field(name=None, type_=None, 
         default=dataclasses.MISSING, 
         default_factory=dataclasses.MISSING, 
         init=None, 
         repr=None,
         hash=None, 
         compare=None, 
         metadata=None,
         **kwargs):
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
            metadata = type_.metadata
    elif metadata is None:
        metadata = kwargs
    elif kwargs:
        metadata = metadata.copy()
        metadata.update(kwargs)
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
        metadata=metadata)
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
    if is_path(field):
        path_type = field.metadata['format'].split('/')[1]
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
            ignore_args = args == Dict.__args__
        elif name == 'Set':
            name = 'set'
            args = getattr(type_, '__args__', None)
            ignore_args = args == Set.__args__
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


def literal_values(type):
    return type.__args__


def field_literal_values(field):
    return literal_values(field_type(field))


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


class ListMeta(type):
    def __getitem__(cls, type):
        if isinstance(type, dataclasses.Field):
            result = field(
                type_=List[field_type(type)], 
                metadata=type.metadata)
        else:
            result = typing.List[type]
        return result

class List(metaclass=ListMeta):
    pass

def path(format,
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
        'format': f'path/{format}',
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


def is_path(field):
    return field.metadata.get('format', '').startswith('path/')


def is_file(field):
    return field.metadata.get('format', '') == 'path/file'


def is_directory(field):
    return field.metadata.get('format', '') == 'path/directory'

def is_input(field):
    return (not field.metadata.get('output', False)
            and field.metadata.get('read', True))

def is_output(field):
    return (field.metadata.get('output', False)
            or field.metadata.get('write', False))

def has_default(field):
    return (field.default not in (undefined, dataclasses.MISSING)
            or field.default_factory is not dataclasses.MISSING)

def is_list(field):
    t = field_type(field)
    return (getattr(t, '_name', None) == 'List'
            or (isinstance(t, type) and issubclass(t, list)))


