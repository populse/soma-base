# -*- coding: utf-8 -*-

from collections import OrderedDict
import copy
import dataclasses
import inspect
from typing import Union

from pydantic.dataclasses import dataclass

from soma.undefined import undefined


class _ModelsConfig:
    validate_assignment = True
    arbitrary_types_allowed = True

        

class ValueEvent:
    def __init__(self):
        self.callbacks_mapping = {}
        self.callbacks = {}

    @staticmethod
    def normalize_callback_parameters(callback):
        signature = inspect.signature(callback)
        if len(signature.parameters) == 0:
            return lambda new_value, old_value, attribute_name, controller: callback()
        elif len(signature.parameters) == 1:
            return lambda new_value, old_value, attribute_name, controller: callback(new_value)
        elif len(signature.parameters) == 2:
            return lambda new_value, old_value, attribute_name, controller: callback(new_value, old_value)
        elif len(signature.parameters) == 3:
            return lambda new_value, old_value, attribute_name, controller: callback(new_value, old_value, attribute_name)
        elif len(signature.parameters) == 4:
            return callback
        raise ValueError('Invalid callback signature')


    def add(self, callback, attribute_name=None):
        real_callback = self.normalize_callback_parameters(callback)
        if real_callback is not callback:
            self.callbacks_mapping[callback] = real_callback
        self.callbacks.setdefault(attribute_name, []).append(real_callback)


    def remove(self, callback, attribute_name=None):
        real_callback = self.callbacks_mapping.pop(callback, callback)
        self.callbacks[attribute_name].remove(real_callback)


    def fire(self, attribute_name, new_value, old_value, controller):
        for callback in self.callbacks.get(attribute_name, []):
            callback(new_value, old_value, attribute_name, controller)
        for callback in self.callbacks.get(None, []):
            callback(new_value, old_value, attribute_name, controller)
    
    @property
    def has_callback(self):
        return bool(self.callbacks)


class ControllerBase:
    def __init__(self, **kwargs):
        object.__setattr__(self,'_dyn_fields', {})
        super().__init__()
        object.__setattr__(self,'_dyn_fields', {})
        for k, v in kwargs.items():
            setattr(self, k, v)
        super().__setattr__('on_attribute_change', ValueEvent())
        super().__setattr__('enable_notification', True)

    def add_field(self, name, type_, default=undefined, metadata=None):
        # Dynamically create a class equivalent to:
        # Without default if it is undefined
        #
        # @controller(class_field=False)
        # class {name}:
        #     value: type_ = default
        namespace = {
            '__annotations__': {
                name: type_,
            }
        }
        kwargs = {}
        if default is not undefined:
            kwargs['default'] = default
        if metadata is not None:
            kwargs['metadata'] = metadata
        if kwargs:
            namespace[name] = dataclasses.field(**kwargs)
        field_class = type(name, (), namespace)
        field_class = controller(field_class, class_field=False)
        super().__getattribute__('_dyn_fields')[name] = field_class()
        
    def remove_field(self, name):
        del self._dyn_fields[name]
    
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
            raise AttributeError('{} object has no attribute {}'.format(repr(self.__name__), repr(name)))
        return result

    def __setattr__(self, name, value):
        if name in self.__pydantic_model__.__fields__ or name in super().__getattribute__('_dyn_fields'):
            if getattr(self, 'enable_notification', False) and self.on_attribute_change.has_callback:
                old_value = getattr(self, name, undefined)
                self._unnotified_setattr(name, value)
                # Value can be converted, therefore get actual attribute new value
                new_value = getattr(self, name)
                if old_value != new_value:
                    self.on_attribute_change.fire(name, new_value, old_value, self)
            else:
                self._unnotified_setattr(name, value)
        else:
            super().__setattr__(name, value)

    def _unnotified_setattr(self, name, value):
        dyn_field = super().__getattribute__('_dyn_fields').get(name)
        if dyn_field:
            setattr(dyn_field, name, value)
        else:
            super().__setattr__(name, value)
    
    def fields(self):
        yield from dataclasses.fields(self)
        yield from (dataclasses.fields(i)[0] for i in super().__getattribute__('_dyn_fields').values())

    def field(self, name):
        field = self.__dataclass_fields__.get(name)
        if field is None:
            field = super().__getattribute__('_dyn_fields').get(name)
            if field is None:
                raise AttributeError(
                    'object {} has no attribute {}'.format(self ,name))
            else:
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

    def import_dict(self, state, clear=False):
        if clear:
            for field in self.fields():
                setattr(self, field.name, undefined)
        for name, value in state.items():
            field = self.field(name)
            # Field type is Union[real_type,UndefinedClass], get real type
            type = field.type.__args__[0]
            if issubclass(type, ControllerBase):
                controller = getattr(self, name, undefined)
                if controller is undefined:
                    setattr(self, name, value)
                else:
                    controller.import_dict(value, clear=clear)
            else:
                setattr(self, name, value)


def controller(cls, class_field=True, **kwargs):
    annotations = getattr(cls, '__annotations__', None)
    if annotations:
        for i in list(annotations):
            annotations[i] = Union[annotations[i],type(undefined)]
            if getattr(cls, i, undefined) is undefined:
                setattr(cls, i, undefined)
            v = getattr(cls, i, None)
            if v is not None:
                if isinstance(v, dataclasses.Field):
                    metadata = v.metadata.copy()
                    metadata['class_field'] = class_field
                    setattr(cls, i, dataclasses.field(default=v.default,
                                          default_factory=v.default_factory,
                                          repr=v.repr,
                                          hash=v.hash,
                                          init=v.init,
                                          compare=v.compare,
                                          metadata=metadata))
                else:
                    setattr(cls, i, dataclasses.field(default=v, metadata={'class_field': class_field}))
    return type(cls.__name__, 
                (ControllerBase, dataclass(cls, config=_ModelsConfig, **kwargs)),
                {})


def asdict(obj, dict_factory=dict, exclude_empty=False):
    if isinstance(obj, ControllerBase):
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

# Shortcuts from controller decorator
controller.asdict = asdict

@controller
class Controller:
    pass


# from collections import OrderedDict
# import inspect
# from typing import Union, List

# from pydantic import create_model, Field, BaseModel
# from pydantic.fields import ModelField
# from pydantic.schema import field_schema, schema

# from soma.undefined import undefined

# class BaseSchema(BaseModel):
#     class Config:
#         validate_assignment = True
#         arbitrary_types_allowed = True

# class ControllerMeta(type):
#     def __new__(cls, name, bases, namespace):
#         result = super().__new__(cls, name, bases, namespace)
#         schema_dict = OrderedDict()
#         for attribute, annotation in namespace.get('__annotations__', {}).items():
#             default = namespace.get(attribute, ...)
#             if annotation.__name__ == 'Annotated':
#                 type_, field = annotation.__args__
#                 field = field[0]
#                 field.extra['class_field'] = True
#                 field.default = default
#             else:
#                 type_ = annotation
#                 field = Field(default, class_field=True)
#             schema_dict[attribute] = (type_, field)
#         if bases and bases[0] is Controller:
#             base = BaseSchema
#         elif bases and issubclass(bases[0], Controller):
#             base = bases[0]._schema
#         else:
#             base = BaseSchema
#         result._schema = create_model(name, 
#                                       __base__=base,
#                                       **schema_dict)
#         result._schema_dict = schema_dict
#         return result


# BaseSchema.Config.json_encoders = {
#     ControllerMeta: lambda v: '{}.{}'.format(v.__module__, v.__name__),
# }


# class Controller(metaclass=ControllerMeta):

#     """ A Controller contains some traits: attributes typing and observer
#     (callback) pattern.

#     The class provides some methods to add/remove/inspect user defined traits.

#     Attributes
#     ----------
#     `on_attribute_change` : Controller.ValueEvent
#         Callbacks added to this object are called when an attribute value that
#          is in the traits is modified.

#     `on_trait_change` : Controller.TypeEvent
#         single event that can be sent when several traits changes. This event
#         has to be triggered explicitely to take into account changes due to
#         call(s) to add_trait or remove_trait.

#     Methods
#     -------
#     user_traits
#     add_trait
#     remove_trait
#     """
    

#     def __init__(self, *args, **kwargs):
#         super().__init__()
#         values = dict(zip(self._schema.__fields__, args))
#         values.update(kwargs)
#         super().__setattr__('_model', self._schema.construct(**values))
#         # for n, v in values.items():
#         #     setattr(self._model, n, v)
#         super().__setattr__('on_attribute_change', self.ValueEvent())
#         self.enable_notification = True
    
    
#     def __getattribute__(self, name):
#         if name in super().__getattribute__('_schema').__fields__:
#             return getattr(self._model, name)
#         else:
#             return super().__getattribute__(name)


#     def __setattr__(self, name, value):
#         if name in self._schema.__fields__:
#             if getattr(self, 'enable_notification', False):
#                 old_value = getattr(self, name, undefined)
#                 self._unnotified_setattr(name, value)
#                 if old_value != value:
#                     self.on_attribute_change.fire(name, value, old_value, self)
#             else:
#                 self._unnotified_setattr(name, value)
#         else:
#             super().__setattr__(name, value)
    

#     def _unnotified_setattr(self, name, value):
#         field = self.user_traits().get(name)
#         if field and issubclass(field.outer_type_, Controller) and isinstance(value, dict):
#             controller = getattr(self, name, None)
#             if not controller:
#                 controller = field.outer_type_()
#                 clear = False
#             else:
#                 clear = True
#             controller.import_from_dict(value, clear=clear)
#             setattr(self._model, name, controller)
#             return
#         setattr(self._model, name, value)


#     def user_traits(self):
#         """ Method to access the user parameters.

#         Returns
#         -------
#         out: dict
#             a dictionnary containing class traits and instance traits
#             defined by user (i.e.  the traits that are not automatically
#             defined by HasTraits or Controller). Returned values are
#             sorted according to the 'order' trait meta-attribute.
#         """
#         return self._model.__fields__


#     def add_trait(self, type_, name=None, default=undefined, **kwargs):
#         field_default = (... if default is undefined else default)
#         if type_.__name__ == 'Annotated':
#             type_, field = type_.__args__
#             field = field[0]
#             field.extra['class_field'] = False
#             field.extra.update(kwargs)
#             field.default = field_default
#         else:
#             field = Field(field_default, class_field=False, **kwargs)
#         self._schema_dict[name] = (type_, field)
#         self._rebuild_model()
    

#     def _rebuild_schema(self):
#         # bases = self.__class__.__bases__
#         # if bases and bases[0] is Controller:
#         #     base = BaseSchema
#         # elif bases and issubclass(bases[0], Controller):
#         #     base = bases[0]._schema
#         # else:
#         #     base = BaseSchema
#         self._schema = create_model(self.__class__.__name__, 
#                                     __base__=self.__class__._schema,
#                                     **self._schema_dict)
    

#     def _rebuild_model(self):
#         values = self._model.__dict__
#         self._rebuild_schema()
#         self._model =  self._schema.construct(**values)


#     def remove_trait(self, name):
#         """ Remove a trait from its name.

#         Parameters
#         ----------
#         name: str (mandatory)
#             the trait name to remove.
#         """
#         field = self._model.__fields__[name]
#         if field.field_info.extra.get('class_trait', False):
#             raise ValueError('Cannot remove a class trait')
#         del self._schema_dict[name]
#         values = self._model.__dict__
#         value = values.pop(name, None)
#         self._rebuild_schema()
#         super().__setattr__('_model', self._schema.construct(**values))


#     def export_to_dict(self, exclude_transient=False,
#                        exclude_none=False,
#                        exclude_empty=False,
#                        dict_class=dict):
#         """ return the controller state to a dictionary, replacing controller
#         values in sub-trees to dicts also.

#         Parameters
#         ----------
#         exclude_transient: bool (optional)
#             if set, do not export values whose trait is marked "transcient"
#         exclude_none: bool (optional)
#             if set, do not export None values
#         exclude_empty: bool (optional)
#             if set, do not export empty lists/dicts values
#         dict_class: class type (optional, default: soma.sorted_dictionary.OrderedDict)
#             use this type of mapping type to represent controllers. It should
#             follow the mapping protocol API.
#         """
#         return controller_to_dict(self,
#                                   exclude_transient=exclude_transient,
#                                   exclude_none=exclude_none,
#                                   exclude_empty=exclude_empty,
#                                   dict_class=dict_class)

#     def import_from_dict(self, state_dict, clear=False):
#         """ Set Controller variables from a dictionary. When setting values on
#         Controller instances (in the Controller sub-tree), replace dictionaries
#         by Controller instances appropriately.

#         Parameters
#         ----------
#         state_dict: dict, sorted_dictionary or OrderedDict
#             dict containing the variables to set
#         clear: bool (optional, default: False)
#             if True, older values (in keys not listed in state_dict) will be
#             cleared, otherwise they are left in place.
#         """
#         if clear:
#             self._model =  self._schema.construct()
#         for trait_name, value in state_dict.items():
#             if value is undefined:
#                 if getattr(self, trait_name, undefined) is not undefined:
#                     delattr(self._model, trait_name)
#                 continue
#             trait = self.user_traits().get(trait_name)
#             if trait_name == 'protected_parameters' and trait is None:
#                 self.add_trait(List[str], name='protected_parameters', default=[], hidden=True)
#                 trait = self.traits['protected_parameters']
#             if trait is None and not isinstance(self, BaseOpenKeyController):
#                 raise KeyError(
#                     "item %s is not a trait in the Controller" % trait_name)
#             if trait and isinstance(trait.outer_type_, type) \
#                     and issubclass(trait.outer_type_, Controller):
#                 controller = getattr(self, trait_name, undefined)
#                 if controller is undefined:
#                     setattr(self, trait_name, value)
#                 else:
#                     controller.import_from_dict(value, clear=clear)
#             else:
#                 if value is None:
#                     # None / Undefined may be an acceptable value for many
#                     # traits types
#                     setattr(self, trait_name, value)
#                 else:
#                     # check trait type for conversions
#                     if trait and isinstance(trait.type_, set):
#                         setattr(self, trait_name, set(value))
#                     elif trait and isinstance(trait.type_, tuple):
#                         setattr(self, trait_name, tuple(value))
#                     else:
#                         setattr(self, trait_name, value)

#     def copy(self, with_values=True):
#         """ Copy traits definitions to a new Controller object

#         Parameters
#         ----------
#         with_values: bool (optional, default: False)
#             if True, traits values will be copied, otherwise the defaut trait
#             value will be left in the copy.

#         Returns
#         -------
#         copied: Controller instance
#             the returned copy will have the same class as the copied object
#             (which may be a derived class from Controller). Traits definitions
#             will be copied. Traits values will only be copied if with_values is
#             True.
#         """
#         import copy

#         initargs = ()
#         if hasattr(self, '__getinitargs__'):
#             # if the Controller class is subclassed and needs init parameters
#             initargs = self.__getinitargs__()
#         copied = self.__class__(*initargs)
#         for attribute, field in self._model.__fields__.items():
#             if not field.field_info.extra['class_field']:
#                 copied.add_trait(field.outer_type_, 
#                                  name=attribute,
#                                  default=field.field_info.default
#                 )

#         copied._schema_dict = self._schema_dict.copy()
#         copied._rebuild_model()
#         if with_values:
#             copied.import_from_dict(self.export_to_dict())
#         return copied


#     def reorder_traits(self, traits_list):
#         """ Reorder traits in the controller according to a new ordered list.

#         If the new list does not contain all user traits, the remaining ones
#         will be appended at the end (sorted by their order attribute or hash 
#         value).

#         Parameters
#         ----------
#         traits_list: list
#             New list of trait names. This list order will be kept.
#         """
#         new_schema = OrderedDict((i, self._schema_dict.pop(i)) for i in traits_list)
#         for k, v in sorted(self._schema_dict.items(), 
#                            key=lambda x: x[1].extra.get('order', hash(x[1]))):
#             new_schema[k] = v
#         self._schema_dict = new_schema
#         self._rebuild_model()


#     def protect_parameter(self, param, state=True):
#         """ Protect the named parameter.

#         Protecting is not a real lock, it just marks the parameter a list of
#         "protected" parameters. This is typically used to mark values that have
#         been set manually by the user (using the ControllerWidget for instance)
#         and that should not be later modified by automatic parameters tweaking
#         (such as completion systems).

#         Protected parameters are listed in an additional trait,
#         "protected_parameters".

#         If the "state" parameter is False, then we will unprotect it
#         (calling unprotect_parameter())
#         """
#         if not state:
#             return self.unprotect_parameter(param)
#         if not self.trait('protected_parameters'):
#             # add a 'protected_parameters' trait bypassing the
#             # Controller.add_trait mechanism (it will not be a "user_trait")
#             self.add_trait(List[str],
#                            name='protected_parameters',
#                            default=[],
#                            hidden=True)
#         protected = set(self.protected_parameters)
#         protected.update([param])
#         self.protected_parameters = sorted(protected)

#     def unprotect_parameter(self, param):
#         """ Unprotect the named parameter
#         """
#         if self.trait('protected_parameters'):
#             try:
#                 self.protected_parameters.remove(param)
#             except ValueError:
#                 pass  # it was not protected.

#     def is_parameter_protected(self, param):
#         """ Tells whether the given parameter is protected or not
#         """
#         if not self.trait('protected_parameters'):
#             return False
#         return param in self.protected_parameters

#     @staticmethod
#     def field_json_schema(field):
#         type_ = field.outer_type_
#         if issubclass(type_, Controller):
#             result = schema(type_._schema)
#         elif issubclass(type_, BaseModel):
#             result = schema([field])
#         else:
#             result = field_schema(field, model_name_map={})
#         return result


# class OpenKeyController:
#     def __new__(cls, value_type=str):
#         return type('OpenKeyController({})'.format(value_type.__name__), (BaseOpenKeyController,), {'_value_trait': value_type})


# class BaseOpenKeyController(Controller):

#     """ A dictionary-like controller, with "open keys": items may be added
#     on the fly, traits are created upon assignation.

#     A value trait type should be specified to build the items.

#     Usage:

#     >>> dict_controller = OpenKeyController(value_trait=traits.Str())
#     >>> print(dict_controller.user_traits().keys())
#     []
#     >>> dict_controller.my_item = 'bubulle'
#     >>> print(dict_controller.user_traits().keys())
#     ['my_item']
#     >>> print(dict_controller.export_to_dict())
#     {'my_item': 'bubulle'}
#     >>> del dict_controller.my_item
#     >>> print(dict_controller.export_to_dict())
#     {}
#     """
#     _reserved_names = {'enable_notification'}

#     def __init__(self, *args, **kwargs):
#         """ Build an OpenKeyController controller.

#         Parameters
#         ----------
#         value_trait: Trait instance (optional, default: Any())
#             trait type to be used when creating traits on the fly
#         """
#         super().__init__(*args, **kwargs)

#     def __setattr__(self, name, value):
#         if not name.startswith('_') and name not in self.__dict__ \
#                 and name not in self.user_traits() \
#                 and not name in self._reserved_names:
#             self.add_trait(self._value_trait, name=name)
#         super().__setattr__(name, value)

#     def __delattr__(self, name):
#         if name in self.user_traits():
#             self.remove_trait(name)
#         else:
#             super().__delattr__(name)

# def controller_to_dict(item,
#                        exclude_transient=False,
#                        exclude_none=False,
#                        exclude_empty=False,
#                        dict_class=OrderedDict):
#     """
#     Convert an item to a Python value where controllers had been converted
#     to dictionary. It can recursively convert the values contained in a
#     Controller instances or a  dict instances. All other items are returned
#     untouched.

#     Parameters
#     ----------
#     exclude_transient: bool (optional)
#         if set, do not export values whose trait is marked "transcient"
#     exclude_none: bool (optional)
#         if set, do not export None values
#     exclude_empty: bool (optional)
#         if set, do not export empty lists/dicts values
#     dict_class: class type (optional, default: collections.OrderedDict)
#         use this type of mapping type to represent controllers. It should
#         follow the mapping protocol API.
#     """
#     if isinstance(item, Controller):
#         result = dict_class()
#         for name, field in item.user_traits().items():
#             if exclude_transient and field.field_info.extra.get('transient', False):
#                 continue
#             value = getattr(item, name, undefined)
#             if value is undefined \
#                 or (exclude_none and value is None) \
#                 or (exclude_empty and value in ([], {})):
#                 continue
#             value = controller_to_dict(value,
#                                        exclude_transient=exclude_transient,
#                                        exclude_none=exclude_none,
#                                        exclude_empty=exclude_empty,
#                                        dict_class=dict_class)
#             result[name] = value
#         if 'protected_parameters' in item.user_traits():
#             result['protected_parameters'] = item.protected_parameters
#     elif isinstance(item, dict):
#         result = dict_class()
#         for name, value in item.items():
#             if exclude_none and value is None:
#                 continue
#             if exclude_empty and value in ([], {}):
#                 continue
#             value = controller_to_dict(value,
#                                        exclude_transient=exclude_transient,
#                                        exclude_none=exclude_none,
#                                        exclude_empty=exclude_empty,
#                                        dict_class=dict_class)
#             result[name] = value
#     else:
#         result = item

#     return result

def type_id(type_):
    final_mapping = {
        'List[Any]': 'list',
        'Tuple': 'tuple',
        'typing.Any': 'Any',
        'Tuple[Any]': 'tuple',
        'Dict': 'dict',
        'Dict[Any,Any]': 'dict',
    }
    name = getattr(type_, '__name__', None)
    if not name:
        name = str(type_)
    module = getattr(type_, '__module__', None)
    if module and module not in {'builtins', 'typing'}:
        name = '{}.{}'.format(module, name)
    args = getattr(type_, '__args__', ())
    if args:
        result = '{}[{}]'.format(
            name,
            ','.join(type_id(i) for i in args)
        )
    else:
        result = name
    return final_mapping.get(result, result)
