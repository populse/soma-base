# -*- coding: utf-8 -*-

from collections import OrderedDict
import copy
import dataclasses
import inspect
from typing import Union

from pydantic.dataclasses import dataclass

from soma.undefined import undefined

from .field import (field, field_type, has_default, field_type_str,
                    is_output, is_path, metadata, set_metadata)

class _ModelsConfig:
    validate_assignment = True
    arbitrary_types_allowed = True

        

class Event:
    def __init__(self):
        self.callbacks = []

    def add(self, callback, ):
        self.callbacks.append(callback)

    def remove(self, callback):
        try:
            self.callbacks.remove(callback)
            return True
        except ValueError:
            # The callback was not in the list
            return False

    def fire(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)
    
    @property
    def has_callback(self):
        return bool(self.callbacks)


class AttributeValueEvent(Event):
    def __init__(self):
        self.callbacks_mapping = {}
        self.callbacks = {}

    @staticmethod
    def normalize_callback_parameters(callback):
        signature = inspect.signature(callback)
        if len(signature.parameters) == 0:
            return lambda new_value, old_value, attribute_name, controller, index: callback()
        elif len(signature.parameters) == 1:
            return lambda new_value, old_value, attribute_name, controller, index: callback(new_value)
        elif len(signature.parameters) == 2:
            return lambda new_value, old_value, attribute_name, controller, index: callback(new_value, old_value)
        elif len(signature.parameters) == 3:
            return lambda new_value, old_value, attribute_name, controller, index: callback(new_value, old_value, attribute_name)
        elif len(signature.parameters) == 4:
            return lambda new_value, old_value, attribute_name, controller, index: callback(new_value, old_value, attribute_name, controller)
        elif len(signature.parameters) == 5:
            return callback
        raise ValueError('Invalid callback signature')


    def add(self, callback, attribute_name=None):
        real_callback = self.normalize_callback_parameters(callback)
        if real_callback is not callback:
            self.callbacks_mapping[callback] = real_callback
        self.callbacks.setdefault(attribute_name, []).append(real_callback)


    def remove(self, callback, attribute_name=None):
        real_callback = self.callbacks_mapping.pop(callback, callback)
        try:
            self.callbacks[attribute_name].remove(real_callback)
            return True
        except ValueError:
            # The callback was not in the list
            return False


    def fire(self, attribute_name, new_value, old_value, controller, index=None):
        for callback in self.callbacks.get(attribute_name, []):
            callback(new_value, old_value, attribute_name, controller, index)
        for callback in self.callbacks.get(None, []):
            callback(new_value, old_value, attribute_name, controller, index)
    
    @property
    def has_callback(self):
        return bool(self.callbacks)

class ControllerMeta(type):
    def __new__(cls, name, bases, namespace, class_field=True, ignore_metaclass=False):
        if ignore_metaclass:
            return super().__new__(cls, name, bases, namespace)
        base_controllers = [i for i in bases if issubclass(i, Controller)]
        if len(base_controllers) != 1:
            raise TypeError('There must be exactly one Controller in base classes')
        controller_class = base_controllers[0]
        annotations = namespace.pop('__annotations__', None)
        dataclass_namespace = {}
        if annotations:
            dataclass_namespace['__annotations__'] = annotations
            for i in list(annotations):
                type_ = annotations[i]
                value = namespace.get(i, undefined)
                dataclass_namespace[i] = value
                if isinstance(type_, dataclasses.Field):
                    field_type = type_
                    type_ = field_type.type
                    del annotations[i]
                else:
                    field_type = None
                    type_ = annotations[i] = Union[type_,type(undefined)]
                if isinstance(value, dataclasses.Field):
                    field_type = value
                    value = undefined
                if field_type:
                    mdata = metadata(field_type).copy()
                    mdata['class_field'] = class_field
                    annotations[i] = type_
                    if field_type.default is undefined:
                        default = value
                    elif value is not undefined and value is not field_type.default:
                        raise TypeError('Two default values given for '
                            f'field "{i}": {repr(value)} and '
                            f'{repr(field_type.default)}')
                    else:
                        default=field_type.default
                    default_factory=field_type.default_factory
                    kwargs = dict(
                        default=default,
                        default_factory=default_factory,
                        repr=field_type.repr,
                        hash=field_type.hash,
                        init=field_type.init,
                        compare=field_type.compare
                    )
                else:
                    kwargs = {
                        'default': value,
                    }
                    mdata = {
                        'class_field': class_field
                    }
                kwargs['metadata'] = mdata
                dataclass_namespace[i] = field(**kwargs)
        controller_dataclass = getattr(controller_class, '_controller_dataclass', None)
        if controller_dataclass:
            dataclass_bases = (controller_dataclass,)
        else:
            dataclass_bases = ()
        c = type(name + '_dataclass' , dataclass_bases, dataclass_namespace)
        c = dataclass(c, config=_ModelsConfig)
        namespace['_controller_dataclass'] = c
        namespace['__hash__'] = Controller.__hash__
        c = super().__new__(cls, name, bases + (c,) , namespace)
        return c


class Controller(metaclass=ControllerMeta, ignore_metaclass=True):
    def __new__(cls, *args, **kwargs):
        if cls is Controller:
            return EmptyController()
        return super().__new__(cls)
    
    def __init__(self, **kwargs):
        object.__setattr__(self,'_dyn_fields', {})
        super().__init__()
        object.__setattr__(self,'_dyn_fields', {})
        for k, v in kwargs.items():
            setattr(self, k, v)


        super().__setattr__('on_attribute_change', AttributeValueEvent())
        super().__setattr__('on_inner_value_change',  Event())
        super().__setattr__('on_fields_change',  Event())
        super().__setattr__('enable_notification', True)
        super().__setattr__('_metadata', {})

    def add_field(self, name, type_, default=undefined, metadata=None,
                  **kwargs):
        # Dynamically create a class equivalent to:
        # (without default if it is undefined)
        #
        # class {name}(Controller):
        #     value: type_ = default
        namespace = {
            '__annotations__': {
                name: type_,
            }
        }

        field_kwargs = {}
        if default is not undefined:
            field_kwargs['default'] = default
        if metadata is not None:
            field_kwargs['metadata'] = metadata
        field_kwargs['type_'] = type_
        namespace[name] = field(**field_kwargs, **kwargs)
        field_class = type(name, (Controller,), namespace, class_field=False)
        field_instance = field_class()
        super().__getattribute__('_dyn_fields')[name] = field_instance
        if getattr(self, 'enable_notification', False) \
                and self.on_fields_change.has_callback:
            self.on_fields_change.fire()
        
    def remove_field(self, name):
        del self._dyn_fields[name]
        if getattr(self, 'enable_notification', False) and self.on_fields_change.has_callback:
            self.on_fields_change.fire()
    
    def __getattribute__(self, name):
        try:
            dyn_fields = super().__getattribute__('_dyn_fields')
        except AttributeError:
            dyn_fields = {}
        dyn_field = dyn_fields.get(name)
        if dyn_field:
            result = getattr(dyn_field, name)
        else:
            result = super().__getattribute__(name)
        if result is undefined:
            raise AttributeError('{} object has no attribute {}'.format(repr(self.__class__), repr(name)))
        return result

    def __setattr__(self, name, value):
        if name in self.__pydantic_model__.__fields__ \
                or (hasattr(self, '_dyn_fields')
                    and name in super().__getattribute__('_dyn_fields')):
            if getattr(self, 'enable_notification', False) and self.on_attribute_change.has_callback:
                old_value = getattr(self, name, undefined)
                self._unnotified_setattr(name, value)
                # Value can be converted, therefore get actual attribute new value
                new_value = getattr(self, name, undefined)
                if old_value != new_value:
                    self.on_attribute_change.fire(name, new_value, old_value, self)
            else:
                self._unnotified_setattr(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        dyn_field = super().__getattribute__('_dyn_fields').get(name)
        if dyn_field:
            delattr(dyn_field, name)
        else:
            super().__delattr__(name)

    def __repr__(self):
        fields = []
        for f in self.fields():
            value = getattr(self, f.name, undefined)
            if value is undefined:
                svalue = 'undefined'
            else:
                try:
                    svalue = repr(value)
                except Exception:
                    svalue = '<non_printable>'
            fields.append((f.name, svalue))
        drepr = ', '.join(['%s=%s' % f for f in fields])
        return '%s(%s)' % (self.__class__.__name__, drepr)

    def _unnotified_setattr(self, name, value):
        dyn_field = super().__getattribute__('_dyn_fields').get(name)
        if dyn_field:
            setattr(dyn_field, name, value)
        else:
            field = self.__dataclass_fields__[name]
            type = field_type(field)
            if isinstance(value, dict) and issubclass(type, Controller):
                controller = getattr(self, name, undefined)
                if controller is undefined:
                    controller = type()
                    controller.import_dict(value)
                    value = controller
                else:
                    controller.import_dict(value, clear=True)
                    return
            super().__setattr__(name, value)
    
    def fields(self):
        yield from dataclasses.fields(self)
        yield from (dataclasses.fields(i)[0] for i in super().__getattribute__('_dyn_fields').values())

    def field(self, name):
        field = self.__dataclass_fields__.get(name)
        if field is None:
            field = super().__getattribute__('_dyn_fields').get(name)
            if field is not None:
                field = dataclasses.fields(field)[0]
        return field

    def reorder_fields(self, fields=()):
        """Reorder dynamic fields according to a new ordered list.

        If the new list does not contain all user traits, the remaining ones
        will be appended at the end (sorted by their order attribute or hash 
        value).

        Parameters
        ----------
        fields: list[str]
            List of field names. This list order will be kept.
        """
        dyn_fields = super().__getattribute__('_dyn_fields')
        new_fields = OrderedDict((i, dyn_fields.pop(i)) for i in fields)
        for k, v in sorted(dyn_fields.items(), 
                           key=lambda x: x[1].extra.get('order', hash(x[1]))):
            new_fields[k] = v
        object.__setattr__(self,'_dyn_fields', new_fields)


    def asdict(self, **kwargs):
        return asdict(self, **kwargs)
    

    def import_dict(self, state, clear=False):
        if clear:
            for field in self.fields():
                delattr(self, field.name)
        for name, value in state.items():
            field = self.field(name)
            if field:
                # Field type is Union[real_type,UndefinedClass], get real type
                type = field_type(field)
                if issubclass(type, Controller):
                    controller = getattr(self, name, undefined)
                    if controller is not undefined:
                        controller.import_dict(value, clear=clear)
                        continue
            setattr(self, name, value)

    def copy(self, with_values=True):
        result = self.__class__()
        for name, field in super().__getattribute__('_dyn_fields').items():
            result.add_field(name, field)
        if with_values:
            result.import_dict(self.asdict())
        return result
    
    def field_doc(self, field_or_name):
        if isinstance(field_or_name, str):
            field = self.field(field_or_name)
        else:
            field = field_or_name
        if not field:
            raise ValueError(f'No such field: {field_or_name}')
        result = ['{} [{}]'.format(field.name, field_type_str(field))]
        optional = self.metadata(field, 'optional')
        if optional is None:
            optional = (field.default not in (undefined, dataclasses.MISSING) or
                        field.default_factory is not dataclasses.MISSING)
        if not optional:
            result.append(' mandatory')
        default = field.default
        if default not in (undefined, dataclasses.MISSING):
            result.append(' ({})'.format(repr(default)))
        desc = self.metadata(field, 'desc')
        if desc:
            result.append(': ' + desc)
        return ''.join(result)
    
    def ensure_field(self, field_or_name):
        if isinstance(field_or_name, str):
            return self.field(field_or_name)
        else:
            return field_or_name

    def metadata(self, field_or_name, key=None, default=None):
        return metadata(self.ensure_field(field_or_name), key, default)
    
    def set_metadata(self, field_or_name, key, value):
        return set_metadata(self.ensure_field(field_or_name), key, value)

    def is_output(self, field_or_name):
        field = self.ensure_field(field_or_name)
        return is_output(field)

    def is_path(self, field_or_name):
        field = self.ensure_field(field_or_name)
        return is_path(field)

    def is_optional(self, field_or_name):
        field = self.ensure_field(field_or_name)
        optional = metadata(field, 'optional', None)
        if optional is None:
            optional =  has_default(field)
        return optional

    def set_optional(self, field_or_name, optional):
        field = self.ensure_field(field_or_name)
        if optional is None:
            self.set_metadata(field, 'optional', undefined)
        else:
            self.set_metadata(field, 'optional', bool(optional))


    def json(self):
        result = {}
        for field in self.fields():
            value = getattr(self, field.name, undefined)
            if value is not undefined:
                result[field.name] = self.json_value(value)
        return result
    
    
    def import_json(self, json):
        for field_name, json_value in json.items():
            setattr(self, field_name, json_value)
    

    def json_value(self, value):
        if isinstance(value, Controller):
            return value.json()
        elif isinstance(value, (tuple, set, list)):
            return [self.json_value(i) for i in value]
        elif isinstance(value, dict):
            return dict((i,self.json_value(j)) for i,j in value.items())
        return value

def asdict(obj, dict_factory=dict, exclude_empty=False):
    if isinstance(obj, Controller):
        result = []
        for f in obj.fields():
            value = getattr(obj, f.name, undefined)
            if value is undefined:
                continue
            value = asdict(value, dict_factory, exclude_empty)
            if not exclude_empty or value not in ([], {}, ()):
                result.append((f.name, value))
        return dict_factory(result)
    elif isinstance(obj, (list, tuple)):
        return type(obj)(asdict(v, dict_factory, exclude_empty) for v in obj)
    elif isinstance(obj, dict):
        result = []
        for k, v in obj.items():
            dk = asdict(k, dict_factory, exclude_empty)
            dv = asdict(v, dict_factory, exclude_empty)
            if not exclude_empty or dv not in ([], {}, ()):
                result.append((dk, dv))
        
    else:
        return copy.deepcopy(obj)


class EmptyController(Controller):
    pass


class OpenKeyControllerMeta(ControllerMeta):
    _cache = {}

    def __getitem__(cls, value_type):
        cls_value_type = getattr(cls, '_value_type', None)
        if value_type is cls_value_type:
            return cls
        result = cls._cache.get(value_type)
        if result is None:
            result = type('OpenKeyController_{}'.format(value_type.__name__), 
                          (OpenKeyController,), {'_value_type': value_type}, ignore_metaclass=True)
            cls._cache[value_type] = result
            return result
        

class OpenKeyController(Controller, metaclass=OpenKeyControllerMeta, ignore_metaclass=True):

    """ A dictionary-like controller, with "open keys": items may be added
    on the fly, traits are created upon assignation.

    A value trait type should be specified to build the items.

    Usage:

    >>> dict_controller = OpenKeyController(value_trait=traits.Str())
    >>> print(dict_controller.user_traits().keys())
    []
    >>> dict_controller.my_item = 'bubulle'
    >>> print(dict_controller.user_traits().keys())
    ['my_item']
    >>> print(dict_controller.export_to_dict())
    {'my_item': 'bubulle'}
    >>> del dict_controller.my_item
    >>> print(dict_controller.export_to_dict())
    {}
    """
    _reserved_names = {'enable_notification'}

    def __new__(cls, **kwargs):
        if cls is OpenKeyController:
            return EmptyOpenKeyController()
        return super().__new__(cls)

    def __setattr__(self, name, value):
        if not name.startswith('_') and name not in self.__dict__ \
                and self.field(name) is None \
                and not name in self._reserved_names:
            self.add_field(name, self._value_type)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.field(name) is not None:
            self.remove_field(name)
        else:
            super().__delattr__(name)


class EmptyOpenKeyController(OpenKeyController[str]):
    pass
