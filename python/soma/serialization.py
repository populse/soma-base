# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import six


'''
Framework to serialize/deserialize Python objects in JSON. The main
feature of this framework is that deserialization of a JSON value requires
no other information than the JSON itself. It is not necessary to know the
class of the object to deserialize. This imposes that the serialization
contains a reference to a factory that is responsible to build the Python
object given its JSON.
'''

class JSONSerializable(object):
    '''
    Instances of classes deriving from `JSONSerializable` can be serialized
    in a JSON compatible object with :meth:`to_json` method. This JSON object
    contains a reference to a factory as well as the full state of the 
    instance. Calling the factory with the state of the instance makes it
    possible to recreate the instance (this is what function :func:`from_json`
    is doing). A typical usage of this serialization system is to store the
    JSON serialization of an instance in a configuration file (or database)
    and latter (possibly in another Python instance) recreate the same
    instance. This is an alternative to pickle allowing to use a standard
    representation format (JSON) and to have full control on instances
    creation.
    '''
    def to_json(self):
        '''
        Return a JSON serialization of self. The returned object can be given
        to :func:`from_json` to create another instance that is eqivalent to
        self.
        Here, equivalent means that all attributes values are the same and the
        methods called with the same parameters give the same results.

        See :func:`from_json` to have insight of what is a JSON serialization
        object.
        '''
        raise NotImplementedError()

def to_json(object):
    '''
    Return a JSON serialization of an object.
    Standard types (None, bool, int, float, str, etc.) are using
    json.dumps whereas other type of object must define a to_json
    method returning the serialization.
    '''
    serializer = getattr(object, 'to_json', None)
    if serializer is None:
        if object is None:
            return None
        raise ValueError('Cannot serialize in JSON object of type {0}'.format(type(object)))
    else:
        return serializer()

def from_json(json_serialization):
    '''
    Takes a JSON serialization object (typically created by a
    :meth:`JSONSerializable.to_json` method) and create and return the
    corresponding instance.
    
    A JSON serialization object can have one of the following structures:
    - A simple string containing a factory reference
    - A list with one, two or three of the following items:

        - factory: a mandatory item containing a reference to a factory
          (see :func:`find_factory`)
        - args: an optional item containing a list of parameters values
          for the factory
        - kwargs: an optional item containing a dictionary of parameters
          for the factory
    
    A reference to a factory identifies a :class:`callable` (e.g a function or
    a class) in a Python module. It is a string containing the module name
    and the callable name separated by a dot. For instance 
    ``'catidb.data_models.catidb_3_4'`` would identify the *catidb_3_4*
    callable in the *catidb.data_models* module.
    '''
    if json_serialization is None:
        return None
    elif isinstance(json_serialization, six.string_types):
        callable = find_factory(json_serialization)
        return callable()
    elif isinstance(json_serialization, list):
        if len(json_serialization) == 3:
            callable, args, kwargs = json_serialization
            callable = find_factory(callable)
            return callable(*args, **kwargs)
        elif len(json_serialization) == 2:
            callable, args_or_kwargs = json_serialization
            if isinstance(args_or_kwargs, list):
                callable = find_factory(callable)
                return callable(*args_or_kwargs)
            elif isinstance(args_or_kwargs, dict):
                callable = find_factory(callable)
                return callable(**args_or_kwargs)
        elif len(json_serialization) == 1:
            callable = find_factory(json_serialization[0])
            return callable()
    raise ValueError('Object is not a valid JSON serialization: %s' % repr(json_serialization))


def find_factory(reference):
    '''
    Finds a factory callable given its reference. The reference is simply
    a string containing a module name and the name of fatory in that module
    separated by a dot. For instance ``'my_packages.my_module.my_factory'``
    would refer to the item *my_factory* in the module
    ``my_packages.my_module``.
    This funcion simply loads the module and returns the module attribute with
    the factory name.
    
    :class:`exceptions.ValueError` is raised if the factory cannot be found.
    '''
    split = reference.rsplit('.', 1)
    if len(split) != 2:
        raise ValueError('%s is not a valid reference to a factory' % reference)
    module_name, item_name = split
    try:
        __import__(module_name)
    except ImportError as e:
        raise ValueError('{0} is not a valid reference to a factory: {1}'.format(reference, e))
    module = sys.modules[module_name]
    factory = getattr(module, item_name, None)
    if factory is None:
        raise ValueError('{0} is not a valid reference to a factory: module {1} has no attribute {2}'.format(reference, module_name, item_name))
    return factory
