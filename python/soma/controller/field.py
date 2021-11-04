# -*- coding: utf-8 -*-

import typing
import dataclasses

from soma.undefined import undefined

from typing import (
    Any,
    Tuple,
    Literal,
    Union,
    Dict,
)

def field(name=None, type_=None, 
         default=dataclasses.MISSING, 
         default_factory=dataclasses.MISSING, 
         init=True, 
         repr=True,
         hash=None, 
         compare=True, 
         metadata=None,
         **kwargs):
    if metadata is None:
        metadata = kwargs
    elif kwargs:
        metadata = metadata.copy()
        metadata.update(kwargs)
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


def field_doc(field):
    result = ['{} [{}]'.format(field.name, field_type_str(field))]
    optional = field.metadata.get('optional')
    if optional is None:
        optional = (field.default not in (undefined, dataclasses.MISSING) or
                    field.default_factory is not dataclasses.MISSING)
    if not optional:
        result.append(' mandatory')
    default = field.default
    if default not in (undefined, dataclasses.MISSING):
        result.append(' ({})'.format(repr(default)))
    desc = field.metadata.get('desc')
    if desc:
        result.append(': ' + desc)
    return ''.join(result)


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
            return f'List[{path_type}]'
        else:
            return path_type
    return type_str(field_type(field))


def type_str(type_):
    final_mapping = {
        'List[Any]': 'list',
        'Tuple': 'tuple',
        'typing.Any': 'Any',
        'Tuple[Any]': 'tuple',
        'Dict': 'dict',
        'Dict[Any,Any]': 'dict',
    }
    name = getattr(type_, '__name__', None)
    ignore_args = False
    if not name:
        name = getattr(type_, '_name', None)
        if name == 'List':
            name = 'list'
        if name == 'Dict':
            name = 'dict'
            args = getattr(type_, '__args__', None)
            ignore_args = args == Dict.__args__
    if name:
        name = name
    if not name and getattr(type_, '__origin__', None) is Union:
        name = 'Union'
    if not name:
        name = str(type_).replace(' ', '')
        if name.startswith('typing.'):
            name = name[7:]
            ignore_args = True
    module = getattr(type_, '__module__', None)
    if module and module not in {'builtins', 'typing'}:
        name = '{}.{}'.format(module, name)
    args = getattr(type_, '__args__', ())
    if not ignore_args and args:
        result = '{}[{}]'.format(
            name,
            ','.join(type_str(i) for i in args)
        )
    else:
        result = name
    return final_mapping.get(result, result)

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

def is_output(field):
    return (field.metadata.get('output', False)
            or field.metadata.get('write', False))

def is_list(field):
    t = field_type(field)
    return (getattr(t, '_name', None) == 'List'
            or (isinstance(t, type) and issubclass(t, list)))


