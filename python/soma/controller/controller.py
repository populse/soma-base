# -*- coding: utf-8 -*-

from collections import OrderedDict
import inspect
from typing import Union, List

from pydantic import BaseModel
from pydantic.fields import ModelField

from soma.undefined import undefined


class Trait:
    def __init__(self, type_, default=undefined, name=None, required=undefined, alias=None, **kwargs):
        if required is undefined:
            required = default is undefined
        self.name = name
        self.type_ = type_
        self.default = default
        self.required = required
        self.alias = alias
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_model_field(cls, model_field):
        type_ = getattr(model_field.outer_type_, '__args__', None)
        if isinstance(type_, tuple) and type_ and type_[0] is undefined.__class__:
            type_ = type_[1]
        return cls(
            name=model_field.name,
            type_=type_,
            default=model_field.default,
            required=model_field.required,
            alias=model_field.alias,
        )


    def model_field(self, model_config, class_validators):
        return ModelField(name=self.name, 
                          type_=self.type_,
                          model_config=model_config,
                          class_validators=class_validators,
                          required=self.required,
                          default=self.default,
                          alias=self.alias)

    def clone(self, **kwargs):
        for k, v in self.__dict__.items():
            if k not in kwargs:
                kwargs[k] = v
        type_ = kwargs['type_']
        if isinstance(type_, Controller):
            type_ = type_.__class__()
        kwargs['type_'] = type_
        return self.__class__(**kwargs)


class ControllerMeta(BaseModel.__class__):
    def __new__(cls, name, bases, dict):
        annotations = dict.get('__annotations__', {})
        traits = OrderedDict()
        for n in annotations:
            if n not in dict:
                dict[n] = undefined
            t = annotations[n]
            if isinstance(t, Trait):
                t.name = n
                traits[n] = t
                annotations[n] = t.type_
            annotations[n] = Union[undefined.__class__, annotations[n]]

        result = super(ControllerMeta, cls).__new__(cls, name, bases, dict)
        for name, field_model in result.__fields__.items():
            if name not in traits:
                trait = Trait.from_model_field(field_model)
                trait.class_trait = True
                traits[name] = trait
        result.traits = traits
        return result


class Controller(BaseModel, metaclass=ControllerMeta):

    """ A Controller contains some traits: attributes typing and observer
    (callback) pattern.

    The class provides some methods to add/remove/inspect user defined traits.

    Attributes
    ----------
    `on_attribute_change` : Controller.ValueEvent
        Callbacks added to this object are called when an attribute value that
         is in the traits is modified.

    `on_trait_change` : Controller.TypeEvent
        single event that can be sent when several traits changes. This event
        has to be triggered explicitely to take into account changes due to
        call(s) to add_trait or remove_trait.

    Methods
    -------
    user_traits
    add_trait
    remove_trait
    """
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        extra = 'allow'


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
            self.callbacks.remove(real_callback)


        def fire(self, attribute_name, new_value, old_value, controller):
            for callback in self.callbacks.get(attribute_name, []):
                callback(new_value, old_value, attribute_name, controller)
            for callback in self.callbacks.get(None, []):
                callback(new_value, old_value, attribute_name, controller)
    

    def __init__(self, *args, **kwargs):
        class_traits = self.traits
        super().__init__(*args, 
                         on_attribute_change = self.ValueEvent(),
                         traits=OrderedDict(),
                         **kwargs)
        self.__fields__ = self.__fields__.copy()
        self.__fields_set__ = self.__fields_set__.copy()

        for name, trait in class_traits.items():
            self.traits[name] = trait
        self.enable_notification = True
    
    
    def __setattr__(self, name, value):
        print('!Controller.setattr!', name, '=', repr(value))
        if getattr(self, 'enable_notification', False) and name in self.__fields__:
            old_value = getattr(self, name, undefined)
            self._unnotified_setattr(name, value)
            if old_value != value:
                self.on_attribute_change.fire(name, value, old_value, self)
        else:
            self._unnotified_setattr(name, value)

    def _unnotified_setattr(self, name, value):
        trait = self.traits.get(name)
        if trait and issubclass(trait.type_, Controller):
            if isinstance(value, dict):
                new_value = trait.type_()
                for k, v in value.items():
                    setattr(new_value, k, v)
                print('!here!', repr(name), type(new_value))
                super().__setattr__(name, new_value)
                print('!done!')
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)


    def user_traits(self):
        """ Method to access the user parameters.

        Returns
        -------
        out: dict
            a dictionnary containing class traits and instance traits
            defined by user (i.e.  the traits that are not automatically
            defined by HasTraits or Controller). Returned values are
            sorted according to the 'order' trait meta-attribute.
        """
        return self.traits


    def add_trait(self, type_, name=None, default=undefined, **kwargs):
        if isinstance(type_, Trait):
            trait = type_
        else:
            trait = Trait(type_, name=name, default=default, **kwargs)
        trait.class_trait = False
        self.traits[name] = trait
        mf = trait.model_field(model_config=self.__config__,
                               class_validators=self.__validators__)
        
        self.__fields__[name] = mf
        self.__fields_set__.add(name)
        if default is not undefined:
            setattr(self, name, default)


    def remove_trait(self, name):
        """ Remove a trait from its name.

        Parameters
        ----------
        name: str (mandatory)
            the trait name to remove.
        """
        trait = self.traits[name]
        if trait.class_trait:
            raise TypeError('Cannot remove a class trait')
        self.traits.pop(name)
        self.__fields__.pop(name)
        self.__fields_set__.remove(name)


    def export_to_dict(self, exclude_undefined=False,
                       exclude_transient=False,
                       exclude_none=False,
                       exclude_empty=False,
                       dict_class=dict):
        """ return the controller state to a dictionary, replacing controller
        values in sub-trees to dicts also.

        Parameters
        ----------
        exclude_undefined: bool (optional)
            if set, do not export Undefined values
        exclude_transient: bool (optional)
            if set, do not export values whose trait is marked "transcient"
        exclude_none: bool (optional)
            if set, do not export None values
        exclude_empty: bool (optional)
            if set, do not export empty lists/dicts values
        dict_class: class type (optional, default: soma.sorted_dictionary.OrderedDict)
            use this type of mapping type to represent controllers. It should
            follow the mapping protocol API.
        """
        return controller_to_dict(self, exclude_undefined=exclude_undefined,
                                  exclude_transient=exclude_transient,
                                  exclude_none=exclude_none,
                                  exclude_empty=exclude_empty,
                                  dict_class=dict_class)

    def import_from_dict(self, state_dict, clear=False):
        """ Set Controller variables from a dictionary. When setting values on
        Controller instances (in the Controller sub-tree), replace dictionaries
        by Controller instances appropriately.

        Parameters
        ----------
        state_dict: dict, sorted_dictionary or OrderedDict
            dict containing the variables to set
        clear: bool (optional, default: False)
            if True, older values (in keys not listed in state_dict) will be
            cleared, otherwise they are left in place.
        """
        if clear:
            for trait_name in self.user_traits():
                if trait_name not in state_dict:
                    delattr(self, trait_name)
        for trait_name, value in state_dict.items():
            trait = self.traits.get(trait_name)
            if trait_name == 'protected_parameters' and trait is None:
                self.add_trait(Trait(List[str], name='protected_parameters', default=[], hidden=True))
                trait = self.traits['protected_parameters']
            if trait is None and not isinstance(self, _OpenKeyController):
                raise KeyError(
                    "item %s is not a trait in the Controller" % trait_name)
            if isinstance(trait.type_, type) \
                    and issubclass(trait.type_, Controller):
                controller = trait.type_.create_default_value(
                    trait.trait_type.klass)
                controller.import_from_dict(value)
            else:
                if value in (None, undefined):
                    # None / Undefined may be an acceptable value for many
                    # traits types
                    setattr(self, trait_name, value)
                else:
                    # check trait type for conversions
                    if trait and isinstance(trait.type_, set):
                        setattr(self, trait_name, set(value))
                    elif trait and isinstance(trait.type_, tuple):
                        setattr(self, trait_name, tuple(value))
                    else:
                        setattr(self, trait_name, value)

    def copy(self, with_values=True):
        """ Copy traits definitions to a new Controller object

        Parameters
        ----------
        with_values: bool (optional, default: False)
            if True, traits values will be copied, otherwise the defaut trait
            value will be left in the copy.

        Returns
        -------
        copied: Controller instance
            the returned copy will have the same class as the copied object
            (which may be a derived class from Controller). Traits definitions
            will be copied. Traits values will only be copied if with_values is
            True.
        """
        import copy

        initargs = ()
        if hasattr(self, '__getinitargs__'):
            # if the Controller class is subclassed and needs init parameters
            initargs = self.__getinitargs__()
        copied = self.__class__(*initargs)
        for name, trait in self.traits.items():
            copied.add_trait(trait.clone(name=name))
            if with_values:
                setattr(copied, name, getattr(self, name))
        if self.traits.get('protected_parameters'):
            trait = self.traits['protected_parameters']
            copied.add_trait(trait.clone(name='protected_parameters'))
            if with_values:
                copied.protected_parameters = self.protected_parameters
        return copied


    def reorder_traits(self, traits_list):
        """ Reorder traits in the controller according to a new ordered list.

        If the new list does not contain all user traits, the remaining ones
        will be appended at the end (sorted by their order attribute or hash 
        value).

        Parameters
        ----------
        traits_list: list
            New list of trait names. This list order will be kept.
        """
        result = OrderedDict((i, self.traits.pop(i)) for i in traits_list)
        for trait in sorted(self.traits.values(), key=lambda x: getattr(x, 'order', hash(x))):
            result[trait.name] = trait
        self.traits = result


    def protect_parameter(self, param, state=True):
        """ Protect the named parameter.

        Protecting is not a real lock, it just marks the parameter a list of
        "protected" parameters. This is typically used to mark values that have
        been set manually by the user (using the ControllerWidget for instance)
        and that should not be later modified by automatic parameters tweaking
        (such as completion systems).

        Protected parameters are listed in an additional trait,
        "protected_parameters".

        If the "state" parameter is False, then we will unprotect it
        (calling unprotect_parameter())
        """
        if not state:
            return self.unprotect_parameter(param)
        if not self.trait('protected_parameters'):
            # add a 'protected_parameters' trait bypassing the
            # Controller.add_trait mechanism (it will not be a "user_trait")
            self.add_trait(self, 
                           Trait(List[str],
                                 name='protected_parameters',
                                 default=[],
                                 hidden=True))
        protected = set(self.protected_parameters)
        protected.update([param])
        self.protected_parameters = sorted(protected)

    def unprotect_parameter(self, param):
        """ Unprotect the named parameter
        """
        if self.trait('protected_parameters'):
            try:
                self.protected_parameters.remove(param)
            except ValueError:
                pass  # it was not protected.

    def is_parameter_protected(self, param):
        """ Tells whether the given parameter is protected or not
        """
        if not self.trait('protected_parameters'):
            return False
        return param in self.protected_parameters


class OpenKeyController:
    def __new__(cls, value_type=str):
        return type('OpenKeyController({})'.format(value_type.__name__), (_OpenKeyController,), {'_value_trait': Trait(value_type)})


class _OpenKeyController(Controller):

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

    def __init__(self, *args, **kwargs):
        """ Build an OpenKeyController controller.

        Parameters
        ----------
        value_trait: Trait instance (optional, default: Any())
            trait type to be used when creating traits on the fly
        """
        super().__init__(*args, **kwargs)

    def __setattr__(self, name, value):
        print('!OpenKeyController.setattr!', name, '=', repr(value))
        if not name.startswith('_') and name not in self.__dict__ \
                and name not in self.traits \
                and not name in self._reserved_names:
            vt = getattr(self, '_value_trait', None)
            if vt:
                cloned_trait = vt.clone(name=name)
                self.add_trait(cloned_trait)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.trait(name):
            self.remove_trait(name)
        else:
            super().__delattr__(name)

def controller_to_dict(item, exclude_undefined=False,
                       exclude_transient=False,
                       exclude_none=False,
                       exclude_empty=False,
                       dict_class=OrderedDict):
    """
    Convert an item to a Python value where controllers had been converted
    to dictionary. It can recursively convert the values contained in a
    Controller instances or a  dict instances. All other items are returned
    untouched.

    Parameters
    ----------
    exclude_undefined: bool (optional)
        if set, do not export Undefined values
    exclude_transient: bool (optional)
        if set, do not export values whose trait is marked "transcient"
    exclude_none: bool (optional)
        if set, do not export None values
    exclude_empty: bool (optional)
        if set, do not export empty lists/dicts values
    dict_class: class type (optional, default: collections.OrderedDict)
        use this type of mapping type to represent controllers. It should
        follow the mapping protocol API.
    """
    if isinstance(item, Controller):
        result = dict_class()
        for name, trait in item.traits.items():
            if exclude_transient and trait.transient:
                continue
            value = getattr(item, name)
            if (exclude_undefined and value is undefined) \
                or (exclude_none and value is None):
                continue
            if exclude_empty and (value == [] or value == {}):
                continue
            value = controller_to_dict(value,
                                       exclude_undefined=exclude_undefined,
                                       exclude_transient=exclude_transient,
                                       exclude_none=exclude_none,
                                       exclude_empty=exclude_empty,
                                       dict_class=dict_class)
            result[name] = value
        if 'protected_parameters' in item.traits:
            result['protected_parameters'] = item.protected_parameters
    elif isinstance(item, dict):
        result = dict_class()
        for name, value in item.items():
            if (exclude_undefined and value is undefined) \
                or (exclude_none and value is None):
                continue
            if exclude_empty and (value == [] or value == {}):
                continue
            value = controller_to_dict(value,
                                       exclude_undefined=exclude_undefined,
                                       exclude_transient=exclude_transient,
                                       exclude_none=exclude_none,
                                       exclude_empty=exclude_empty,
                                       dict_class=dict_class)
            result[name] = value
    else:
        result = item

    return result


try:
    import json

    class JsonControllerEncoder(json.JSONEncoder):
        def default(self, obj):
            if obj is undefined:
                return {'__class__': '<undefined>'}
            if isinstance(obj, set):
                return list(obj) # {'__class__': 'traits.TraitSetObject',
                        #'items': list(obj)}
            if not isinstance(obj, Controller):
                return super(JsonControllerEncoder, self).default(obj)
            d = obj.export_to_dict(exclude_undefined=True,
                exclude_transient=True,
                exclude_none=True,
                exclude_empty=True,
                dict_class=OrderedDict)
            d['__class__'] = obj.__class__.__name__
            return d

    class JsonControllerDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            # install a new object_hoook.
            self._old_object_hook = None
            if 'object_hook' in kwargs:
                self._old_object_hook = kwargs['object_hook']
                kwargs = {k: v for k, v in kwargs.items()
                          if k != 'object_hook'}
            super(JsonControllerDecoder, self).__init__(
                *args, object_hook=self.obj_hook, **kwargs)

        def obj_hook(self, obj):
            if self._old_object_hook is not None:
                obj = self._old_object_hook(obj)
            if isinstance(obj, dict) and '__class__' in obj:
                c = obj['__class__']
                if c == '<undefined>':
                    return undefined
                # Controller objects are decoded as dicts, without the
                # __class__ item, because we cannot rebuild their traits in
                # the general case. They should be converted later by
                # import_from_dict()
                d = {k: v for k, v in obj.items() if k != '__class__'}
                return d
                #controller = Controller()  ## FIXME instantiate __Class__
                #controller.import_from_dict(d)
                #return controller
            return obj

    if type(json._default_encoder) is json.JSONEncoder \
            or json._default_encoder.__class__.__name__ \
                == 'JsonControllerEncoder':
        json._default_encoder = JsonControllerEncoder()
    if type(json._default_decoder) is json.JSONDecoder \
            or json._default_decoder.__class__.__name__ \
                == 'JsonControllerDecoder':
        json._default_decoder = JsonControllerDecoder()

except ImportError:
    pass
