import dataclasses

from soma.controller import field
from soma.undefined import undefined

def path(type,
         dataset=undefined,
         read=undefined,
         write=False,
         default=undefined,
         default_factory=undefined,
         doc=undefined,
         **metadata):
    if read is undefined:
        read = not write
    if dataset is undefined:
        dataset = ('output' if write else 'input')
    field_metadata = {
        'format': f'path/{type}',
        'dataset': dataset,
        'read': read,
        'write': write,
    }
    if doc is not undefined:
        field_metadata['doc'] = doc
    field_metadata.update(metadata)
    if default_factory is undefined:
        default_factory = dataclasses.MISSING
    return field(type_=str,
                 metadata=field_metadata,
                 default=default,
                 default_factory=default_factory)


def file(**kwargs):
    return path(type='file', **kwargs)


def directory(**kwargs):
    return path(type='directory', **kwargs)


def is_path(field):
    return field.type_ is str and field.metadata.get('format', '').startswith('path/')


def is_file(field):
    return field.type_ is str and field.metadata.get('format', '') == 'path/file'


def is_directory(field):
    return field.type_ is str and field.metadata.get('format', '') == 'path/directory'
