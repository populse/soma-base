# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from soma.controller import Controller
import six

try:
    from traits.api import Undefined
except ImportError:
    class Undefined(object):
        pass

def to_json(value):
    '''
    Convert value to an object which will mark some types through JSON
    serialization. Typically, tuples will be replaced with lists which firsst
    element is '<tuple>', Undefined with ['<undefined'], sets with ['<set>,
    items], etc.

    "Decding" can be done using :func:`from_json`
    '''
    if isinstance(value, tuple):
        value = ['<tuple>'] + [to_json(x) for x in value]
    if isinstance(value, set):
        value = ['<set>'] + [to_json(x) for x in value]
    elif isinstance(value, list):
        value = [to_json(x) for x in value]
    elif isinstance(value, Controller):
        value = to_json(value.export_to_dict())
    elif getattr(value, 'items', None):
        # (hasattr may answer True for HasTraits)
        new_value = {}
        for key, item in six.iteritems(value):
            new_value[key] = to_json(item)
        value = new_value
    elif value is Undefined:
        value = ['<undefined>']
    return value


def from_json(value):
    '''
    Reverse of :func:`to_json`

    Convert value from an object which matches JSON serialization, containing
    "code" for some types. Typically, tuples, sets, Undefined, etc.
    '''
    if hasattr(value, 'items'):
        new_value = type(value)()
        for key, item in six.iteritems(value):
            new_value[key] = from_json(item)
        return new_value
    if not isinstance(value, list):
        return value
    if len(value) < 1:
        return value
    code = value[0]
    if code == '<tuple>':
        return tuple([from_json(x) for x in value[1:]])
    elif code == '<undefined>':
        return Undefined
    elif code == '<set>':
        return set([from_json(x) for x in value[1:]])
    return [from_json(x) for x in value]
