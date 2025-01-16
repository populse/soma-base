import copy
import dataclasses
import inspect
from collections import OrderedDict
from typing import Union

try:
    import pydantic as p
    from pydantic import v1 as pydantic
    from pydantic.v1.dataclasses import dataclass

    pydantic_version = p.__version__
    del p
except ImportError:
    import pydantic
    from pydantic.dataclasses import dataclass

    pydantic_version = pydantic.__version__

import sys
from functools import partial

from soma.undefined import undefined
from soma.utils.weak_proxy import get_ref, proxy_method

from .field import Field, FieldProxy, ListProxy, Path, WritableField, field

try:
    import sip
except ImportError:
    sip = None


class _ModelsConfig:
    validate_assignment = True
    arbitrary_types_allowed = True


class Event:
    """Notification class for Controller. An Event can be fired (:meth:`fire`)
    to notify observers who have registered callbacks.
    """

    def __init__(self):
        self.callbacks = []
        self.blocked = False

    def add(
        self,
        callback,
    ):
        """Add a callback for an observer"""
        self.callbacks.append(callback)

    def remove(self, callback):
        """Remove a callback"""
        try:
            self.callbacks.remove(callback)
            return True
        except ValueError:
            # The callback was not in the list
            return False

    def block_signals(self, block):
        self.blocked = block

    def fire(self, *args, **kwargs):
        """Activate notification: call all registered callbacks, using the
        given arguments. Thus all callbacks must follow the same calling
        conventions.
        """
        if self.blocked:
            return

        for callback in self.callbacks:
            try:
                callback(*args, **kwargs)
            except Exception:
                print("Exception in Event callback:", callback, file=sys.stderr)
                print(args, kwargs, file=sys.stderr)
                # debug GUI deletions - most common failure case
                if hasattr(callback, "__self__"):
                    obj = callback.__self__
                    import sip

                    if isinstance(obj, sip.simplewrapper) and sip.isdeleted(obj):
                        print("sip object deleted:", id(obj), obj, file=sys.stderr)
                        print("all callbacks:", self.callbacks, file=sys.stderr)
                raise

    @property
    def has_callback(self):
        """True if any callback has been registered."""
        return bool(self.callbacks)

    @staticmethod
    def _is_dead_ref(function):
        if isinstance(function, partial) and len(function.args) != 0:
            function = function.args[0]
        if (
            isinstance(function, proxy_method)
            and get_ref(function.proxy, False) is None
        ):
            return True
        if sip is not None and hasattr(function, "__self__"):
            obj = function.__self__
            if isinstance(obj, sip.simplewrapper) and sip.isdeleted(obj):
                return True
        return False

    def gc_callbacks(self):
        """Garbage-collect callbacks which contain weak references to
        deleted objects.
        """
        callbacks = []
        for callback in self.callbacks:
            if not self._is_dead_ref(callback):
                callbacks.append(callback)
        self.callbacks = callbacks


class AttributeValueEvent(Event):
    """Event subclass notifier for fields in a Controller. It can notify
    values changes for a set of attributes. Callbacks are thus registered in
    association of a list of attributes, or for all attributes if they are
    associated to an empty (None) attribute name.

    Callbacks are called with the following parameters:

    ``new_value, old_value, attribute_name, controller, index``

    All parameters are optional, but are positional arguments, thus if a
    callback needs the controller parameter, it should also declare
    ``new_value``,  ``old_value``, and ``attribute_name`` parameters first.
    """

    def __init__(self):
        super().__init__()
        self.callbacks_mapping = {}
        self.callbacks = {}

    @staticmethod
    def normalized_callback0(
        callback, new_value, old_value, attribute_name, controller, index
    ):
        return callback()

    @staticmethod
    def normalized_callback1(
        callback, new_value, old_value, attribute_name, controller, index
    ):
        return callback(new_value)

    @staticmethod
    def normalized_callback2(
        callback, new_value, old_value, attribute_name, controller, index
    ):
        return callback(new_value, old_value)

    @staticmethod
    def normalized_callback3(
        callback, new_value, old_value, attribute_name, controller, index
    ):
        return callback(new_value, old_value, attribute_name)

    @staticmethod
    def normalized_callback4(
        callback, new_value, old_value, attribute_name, controller, index
    ):
        return callback(new_value, old_value, attribute_name, controller)

    @staticmethod
    def normalize_callback_parameters(callback):
        pcallback = callback
        if isinstance(callback, proxy_method):
            # proxy_method exposes a different signature from its original
            # method. Get the underlying method to inspect it
            pcallback = getattr(callback.proxy, callback.method)
        signature = inspect.signature(pcallback)
        if len(signature.parameters) == 0:
            return partial(AttributeValueEvent.normalized_callback0, callback)
        elif len(signature.parameters) == 1:
            return partial(AttributeValueEvent.normalized_callback1, callback)
        elif len(signature.parameters) == 2:
            return partial(AttributeValueEvent.normalized_callback2, callback)
        elif len(signature.parameters) == 3:
            return partial(AttributeValueEvent.normalized_callback3, callback)
        elif len(signature.parameters) == 4:
            return partial(AttributeValueEvent.normalized_callback4, callback)
        elif len(signature.parameters) == 5:
            return callback
        raise ValueError("Invalid callback signature")

    def add(self, callback, attribute_name=None):
        """Register a callback associated to given attribute names.
        Callbacks registered with the name None will be called every time.
        """
        real_callback = self.normalize_callback_parameters(callback)
        if real_callback is not callback:
            self.callbacks_mapping[callback] = real_callback
        if isinstance(attribute_name, (list, tuple)):
            for attribute_name1 in attribute_name:
                self.callbacks.setdefault(attribute_name1, []).append(real_callback)
        else:
            self.callbacks.setdefault(attribute_name, []).append(real_callback)

    def remove(self, callback, attribute_name=None):
        """Remove a callback for one or several attribute names"""
        real_callback = self.callbacks_mapping.pop(callback, callback)
        if isinstance(attribute_name, (list, tuple)):
            result = True
            for attribute_name1 in attribute_name:
                try:
                    self.callbacks[attribute_name1].remove(real_callback)
                except ValueError:
                    result = False
            return result
        else:
            try:
                self.callbacks[attribute_name].remove(real_callback)
                return True
            except ValueError:
                # The callback was not in the list
                return False

    def fire(self, attribute_name, new_value, old_value, controller, index=None):
        """Fire callbacks associated with a given attribute name.
        Callbacks without an attribute name (None) are also fired.
        """
        if self.blocked:
            return

        del_cbk = set()
        for callback in self.callbacks.get(attribute_name, []):
            try:
                callback(new_value, old_value, attribute_name, controller, index)
            except ReferenceError:
                del_cbk.add(callback)
        if del_cbk:
            self.callbacks[attribute_name] = [
                cbk for cbk in self.callbacks[attribute_name] if cbk not in del_cbk
            ]
        del_cbk = set()
        for callback in self.callbacks.get(None, []):
            try:
                callback(new_value, old_value, attribute_name, controller, index)
            except ReferenceError:
                del_cbk.add(callback)
        if del_cbk:
            self.callbacks[None] = [
                cbk for cbk in self.callbacks[None] if cbk not in del_cbk
            ]

    @property
    def has_callback(self):
        return bool(self.callbacks)

    def gc_callbacks(self):
        """Garbage-collect callbacks which contain weak references to
        deleted objects.
        """
        callbacks = {}
        for key, callback_l in self.callbacks.items():
            cbl = []
            for callback in callback_l:
                if not self._is_dead_ref(callback):
                    cbl.append(callback)
            if cbl:
                callbacks[key] = cbl
        self.callbacks = callbacks


class ControllerMeta(type):
    """Metaclass for Controller subclasses"""

    def __new__(cls, name, bases, namespace, class_field=True, ignore_metaclass=False):
        if ignore_metaclass:
            return super().__new__(cls, name, bases, namespace)
        base_controllers = [i for i in bases if issubclass(i, Controller)]
        if len(base_controllers) != 1:
            raise TypeError("There must be exactly one Controller in base classes")
        controller_class = base_controllers[0]
        annotations = namespace.pop("__annotations__", None)
        dataclass_namespace = {}
        this_class_fields = []
        _order = 1000000
        for base_class in bases:
            if issubclass(base_class, Controller):
                base_order = getattr(base_class, "_order", 0)
                _order = max(_order, base_order)
        if annotations:
            dataclass_namespace["__annotations__"] = annotations
            this_class_fields = list(annotations)
            for i in this_class_fields:
                _order += 1
                type_ = annotations[i]
                value = namespace.pop(i, undefined)
                dataclass_namespace[i] = value
                if isinstance(type_, Field):
                    field_type = type_
                    type_ = field_type._dataclass_field.type
                    del annotations[i]
                else:
                    field_type = None
                    type_ = annotations[i] = Union[type_, type(undefined)]
                if isinstance(value, Field):
                    t = getattr(value, "type", None)
                    if t is not type_:
                        value = field(
                            type_=value,
                            force_field_type=type_.__args__[0],
                            order=_order,
                        )
                    field_type = value
                    value = undefined
                if field_type:
                    if isinstance(field_type, FieldProxy):
                        dataclass_namespace[i] = field_type
                    else:
                        annotations[i] = type_
                        mdata = field_type._dataclass_field.metadata["_metadata"]
                        mdata["class_field"] = class_field
                        if "order" not in mdata:
                            mdata["order"] = _order
                        if field_type._dataclass_field.default is undefined:
                            field_type._dataclass_field.default = value
                        elif (
                            value is not undefined
                            and value is not field_type._dataclass_field.default
                        ):
                            raise TypeError(
                                "Two default values given for "
                                f'field "{i}": {repr(value)} and '
                                f"{repr(field_type._dataclass_field.default)}"
                            )
                    dataclass_namespace[i] = field_type._dataclass_field
                else:
                    dataclass_namespace[i] = field(
                        type_=type_.__args__[0],
                        default=value,
                        class_field=class_field,
                        order=_order,
                    )._dataclass_field
        controller_dataclass = getattr(controller_class, "_controller_dataclass", None)
        if controller_dataclass:
            dataclass_bases = (controller_dataclass,)
        else:
            dataclass_bases = ()
        for n in list(namespace):
            v = namespace[n]
            if hasattr(v, "__validator_config__"):
                dataclass_namespace[n] = v
                del namespace[n]
        c = type(name + "_dataclass", dataclass_bases, dataclass_namespace)
        c = dataclass(c, config=_ModelsConfig)
        namespace["_controller_dataclass"] = c
        namespace["__hash__"] = Controller.__hash__
        namespace["_order"] = _order
        c = super().__new__(cls, name, bases + (c,), namespace)
        c._this_class_field_names = this_class_fields
        return c


class Controller(metaclass=ControllerMeta, ignore_metaclass=True):
    """Controller is an object with fields.

    Fields are typed attributes, with validation when setting them, and
    notification.

    The implementation is based on the
    `pydantic <https://pydantic-docs.helpmanual.io/>`_ library.

    It allows to declare "fields", either as class fields or instance fields,
    in a python3 syntax::

        class C(Controller):
            a: int = 0
            b: float = 1.
            c: list[str]

    or::

        class D(Controller):
            class_param: str

            def __init__(self):
                self.add_field('instance_param', list[int], optional=True,
                               default_factory=list)

    :class:`~.field.Field` may have metadata to define or characterize them
    more precisely. The :class:`~.field.Field` class doc lists some of them
    which are normalized.
    """

    _this_class_field_names = []

    def __new__(cls, *args, **kwargs):
        if cls is Controller:
            return EmptyController()
        return super().__new__(cls)

    @classmethod
    def class_field(cls, name):
        f = cls._controller_dataclass.__dataclass_fields__[name]
        return f.metadata["_field_class"](f)

    @classmethod
    def class_fields(cls):
        """
        Iterate over all fields defined on class including ones defined on
        parent classes
        """
        yield from (
            i.metadata["_field_class"](i)
            for i in cls._controller_dataclass.__dataclass_fields__.values()
        )

    @classmethod
    def this_class_fields(cls):
        """
        Iterate over fields defined in this class but not in parent classes
        """
        yield from (cls.class_field(i) for i in cls._this_class_field_names)

    def __init__(self, _set_attrs=(), **kwargs):
        object.__setattr__(self, "_dyn_fields", {})
        # self.__dict__ content is replaced somewhere in the initialization
        # process. Therefore, it is saved here and restored just after
        # initialization.
        d = self.__dict__
        super().__init__()
        self.__dict__.update({k: v for k, v in d.items() if k not in self.__dict__})
        for k, v in kwargs.items():
            setattr(self, k, v)

        object.__setattr__(self, "on_attribute_change", AttributeValueEvent())
        object.__setattr__(self, "on_inner_value_change", Event())
        object.__setattr__(self, "on_fields_change", Event())
        object.__setattr__(self, "enable_notification", True)

    def has_instance_fields(self):
        return bool(self._dyn_fields)

    def instance_fields(self):
        return self.fields(class_fields=False)

    def add_field(
        self, name, type_, default=undefined, metadata=None, override=False, **kwargs
    ):
        """Add an instance field.

        Parameters are a type, an optional default value and metadata dict, an
        optional `override` parameter specifying if an existing field of the
        same name should be silently overridden or an exception will be raised.
        Additional keyword arguments are additional metadata.

        `type_` may be a field type such as `int`, `str` or `list[float]`. It
        may also be a compound type: `Union[str, list[str]]`,
        `Literal["one", "two"]`, or a :class:`~field.Field` object which may
        already contain a complex type definition and metadata.

        The field type will be actually replaced with a :class:`~field.Union`
        of the given type and the `undefined` value, in order to allow
        undefined values at initialization time.
        """

        # avoid duplicate fields
        if self.field(name) is not None:
            if override:
                if name in super().__getattribute__("_dyn_fields"):
                    del super().__getattribute__("_dyn_fields")[name]
            else:
                raise ValueError(f"a field named {name} already exists")

        if isinstance(type_, FieldProxy):
            self.add_proxy(
                name,
                proxy_controller=type_._proxy_controller,
                proxy_field=type_._proxy_field,
            )
        else:
            # Dynamically create a class equivalent to:
            # (without default if it is undefined)
            #
            # class {name}(Controller):
            #     value: type_ = default

            # avoid having both default and default_factory defined
            if "default_factory" in kwargs and kwargs["default_factory"] not in (
                dataclasses.MISSING,
                undefined,
            ):
                if default in (dataclasses.MISSING, undefined):
                    default = dataclasses.MISSING
                else:
                    del kwargs["default_factory"]

            if "order" not in kwargs:
                self.__class__._order += 1
                kwargs["order"] = self.__class__._order
            new_field = field(type_=type_, default=default, metadata=metadata, **kwargs)
            namespace = {
                "__annotations__": {
                    name: new_field,
                }
            }

            field_class = type(name, (Controller,), namespace, class_field=False)
            field_instance = field_class()
            default_value = getattr(field_instance, name, undefined)
            super().__setattr__(name, default_value)
            super().__getattribute__("_dyn_fields")[name] = field_instance
            if (
                getattr(self, "enable_notification", False)
                and self.on_fields_change.has_callback
            ):
                try:
                    self.on_fields_change.fire()
                except Exception as e:
                    # print('Exception in Event.fire:', self, file=sys.stderr)
                    # print(self.on_fields_change, file=sys.stderr)
                    raise

    def add_proxy(self, name, proxy_controller, proxy_field):
        """
        Adds a proxy field that is a link to another attribute of
        another controller. Except for the proxy field name, any
        access to field metadata or corresponding attribute value
        are directed to the other controller.

        The linked controller and field can be changed with :meth:`change_proxy`
        """
        proxy = FieldProxy(name, proxy_controller, proxy_field)
        namespace = {
            name: proxy,
        }
        super().__getattribute__("_dyn_fields")[name] = proxy
        if (
            getattr(self, "enable_notification", False)
            and self.on_fields_change.has_callback
        ):
            try:
                self.on_fields_change.fire()
            except Exception as e:
                print("Exception in Event.fire:", self, file=sys.stderr)
                print(self.on_fields_change, file=sys.stderr)
                raise

    def add_list_proxy(self, name, proxy_controller, proxy_field):
        """
        Adds a proxy field that is a list version of another controller field.
        The created field is a real field of type
        `list[other controller field type]` . The proxy has its own attribute
        value but its type is is linked to target field and metadata are taken
        from target field.

        The linked controller and field can be changed with :meth:`change_proxy`
        """
        list_type = list[
            Union[proxy_controller.field(proxy_field).type, type(undefined)]
        ]
        self.add_field(
            name,
            type_=list_type,
            field_class=ListProxy,
            proxy_controller=proxy_controller,
            proxy_field=proxy_field,
        )

    def change_proxy(self, name, proxy_controller=None, proxy_field=None):
        """
        Change the controller and field of a proxy previously created by
        :meth:`add_proxy` or :meth:`add_list_proxy`. For list proxy, the
        current list attribute value is checked on the new list type. If
        value is incompatilbe, it is silently removed. But Pydantic
        underlying library may also convert list elements and therefore
        change the value. Here is an example of this behavior:

        ```
        from soma.controller import Controller

        class C(Controller):
            i: int
            s: str

        class ListOfC(Controller):
            ...

        c = C()
        lc = ListOfC()
        # Create a list proxy on a field of type int
        lc.add_list_proxy('l', c, 'i')
        # Set a value for the list
        lc.l = [1, 2, 3]
        # Change the list proxy to a field of type str
        lc.change_proxy('l', c, 's')
        # The value of the list is converted by Pydantic
        print(lc.l)
        # This prints ['1', '2', '3']
        """
        proxy = self.field(name)
        if proxy_controller is None:
            if isinstance(proxy, FieldProxy):
                proxy_controller = proxy._proxy_controller
            else:
                proxy_controller = proxy._dataclass_field.metadata["_proxy_controller"]
        if proxy_field is None:
            if isinstance(proxy, FieldProxy):
                proxy_field = proxy.proxy_field
            else:
                proxy_field = proxy._dataclass_field.metadata["_proxy_field"]
        if isinstance(proxy, FieldProxy):
            self.remove_field(name)
            self.add_proxy(name, proxy_controller, proxy_field)
        else:
            value = getattr(self, name, undefined)
            self.remove_field(name)
            self.add_list_proxy(name, proxy_controller, proxy_field)
            try:
                setattr(self, name, value)
            except Exception:
                setattr(self, name, undefined)

    def remove_field(self, name):
        """Remove the given field"""
        del self._dyn_fields[name]
        if (
            getattr(self, "enable_notification", False)
            and self.on_fields_change.has_callback
        ):
            self.on_fields_change.fire()

    def __getattr__(self, name):
        if name != "_dyn_fields":
            dyn_fields = getattr(self, "_dyn_fields", None)
            if dyn_fields:
                field = dyn_fields.get(name)
                if field:
                    result = getattr(field, name)
                    return result
        raise AttributeError(f"{self.__class__!r} object has no attribute {name!r}")

    def getattr(self, name, default=undefined):
        """
        This method always return the default value whereas the attribute
        is not defined or has the value `undefined`.
        """
        value = getattr(self, name, ...)
        if value is ... or value is undefined:
            value = default
        return value

    def __setattr__(self, name, value):
        if pydantic_version[0] >= "2":
            pyd_fields = self.__pydantic_fields__
        else:
            pyd_fields = self.__pydantic_model__.__fields__
        if name in pyd_fields or (
            hasattr(self, "_dyn_fields")
            and name in super().__getattribute__("_dyn_fields")
        ):
            if (
                getattr(self, "enable_notification", False)
                and self.on_attribute_change.has_callback
            ):
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
        dyn_field = super().__getattribute__("_dyn_fields").get(name)
        if dyn_field:
            delattr(dyn_field, name)
        else:
            super().__delattr__(name)

    def __repr__(self):
        fields = []
        s = f"{self.__class__.__name__}"
        size = len(s) + 2
        maxsize = 100
        for f in self.fields():
            value = getattr(self, f.name, undefined)
            if value is undefined:
                svalue = "undefined"
            else:
                try:
                    svalue = repr(value)
                except Exception:
                    svalue = "<non_printable>"
            l = len(svalue)
            if size + l > maxsize:
                svalue = svalue[: (maxsize - size)] + "..."
            fields.append((f.name, svalue))
            size += l
            if size > maxsize:
                break
        drepr = ", ".join([f"{n}={v}" for n, v in fields])
        return f"{self.__class__.__name__}({drepr})"

    def _unnotified_setattr(self, name, value):
        dyn_field = super().__getattribute__("_dyn_fields").get(name)
        if dyn_field:
            setattr(dyn_field, name, value)
            super().__setattr__(name, getattr(dyn_field, name))
        else:
            field = self.__dataclass_fields__[name]
            if field.type is not None:
                type_ = field.type.__args__[0]
                if (
                    not isinstance(value, Controller)
                    and isinstance(value, dict)
                    and isinstance(type_, type)
                    and issubclass(type_, Controller)
                ):
                    controller = getattr(self, name, undefined)
                    if controller is undefined:
                        controller = type_()
                        controller.import_dict(value)
                        value = controller
                    else:
                        controller.import_dict(value, clear=True)
                        return
            super().__setattr__(name, value)

    def fields(self, instance_fields=True, class_fields=True):
        """Returns an iterator over registered fields (both class fields and
        instance fields)
        """
        dyn_fields = super().__getattribute__("_dyn_fields")
        if class_fields:
            for i in dataclasses.fields(self):
                f = i.metadata["_field_class"](i)
                if f.name not in dyn_fields:
                    yield f
        if instance_fields:
            for i in super().__getattribute__("_dyn_fields").values():
                if isinstance(i, FieldProxy):
                    yield i
                else:
                    f = dataclasses.fields(i)[0]
                    yield f.metadata["_field_class"](f)

    def _field(self, name):
        field = super().__getattribute__("_dyn_fields").get(name)
        if field is not None:
            if isinstance(field, FieldProxy):
                return field
            field = dataclasses.fields(field)[0]
        if field is None:
            field = self.__dataclass_fields__.get(name)
        return field

    def has_field(self, name):
        return bool(self._field(name))

    def field(self, name):
        """Query the fiend associated with the given name"""
        field = self._field(name)
        if field is None:
            return None
        if isinstance(field, FieldProxy):
            return field
        return field.metadata["_field_class"](field)

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
        dyn_fields = super().__getattribute__("_dyn_fields")
        new_fields = OrderedDict((i, dyn_fields.pop(i)) for i in fields)
        for k, v in sorted(
            dyn_fields.items(),
            key=lambda x: x[1].field(x[0]).metadata("order", hash(x[1])),
        ):
            new_fields[k] = v
        object.__setattr__(self, "_dyn_fields", new_fields)

    def asdict(self, **kwargs):
        """Returns fields values in a dictionary."""
        return asdict(self, **kwargs)

    def import_dict(self, state, clear=False):
        """Set fields values from a dict"""
        if clear:
            for field in list(self.fields()):
                try:
                    delattr(self, field.name)
                except AttributeError:
                    # this attribute was already not present, it's OK
                    pass
        for name, value in state.items():
            field = self.field(name)
            if field:
                # Field type is Union[real_type,UndefinedClass], get real type
                type_ = field.type
                if isinstance(type_, type) and issubclass(type_, Controller):
                    controller = getattr(self, name, undefined)
                    if controller is not undefined:
                        controller.import_dict(value, clear=clear)
                        continue
            setattr(self, name, value)

    def copy(self, with_values=True):
        """Copy the Controller and all its fields, and return the copy."""
        result = self.__class__()
        for name, field in super().__getattribute__("_dyn_fields").items():
            result.add_field(name, field)
        if with_values:
            result.import_dict(self.asdict())
        return result

    def field_doc(self, field_or_name):
        """Get the doc for a field, with some metadata precisions"""
        if isinstance(field_or_name, str):
            field = self.field(field_or_name)
        else:
            field = field_or_name
        if not field:
            raise ValueError(f"No such field: {field_or_name}")
        result = [f"{field.name} [{field.type_str()}]"]
        optional = field.optional
        if optional is None:
            optional = (
                field.default not in (undefined, dataclasses.MISSING)
                or field.default_factory is not dataclasses.MISSING
            )
        if not optional:
            result.append(" mandatory")
        default = field.default
        if default not in (undefined, dataclasses.MISSING):
            result.append(f" ({default!r})")
        doc = field.metadata("doc")
        if doc:
            result.append(": " + doc)
        return "".join(result)

    def ensure_field(self, field_or_name):
        """Get a :class:`field.Field` object for a given Field or name"""
        if isinstance(field_or_name, str):
            return self.field(field_or_name)
        else:
            return field_or_name

    def writable_field(self, field_or_name):
        """Return an instance field that can be modified. If it is a
        class field, it is copied to instance."""
        f = self.ensure_field(field_or_name)
        if f and f.class_field:
            blocked = self.on_fields_change.blocked
            vblocked = self.on_attribute_change.blocked
            self.on_fields_change.block_signals(True)
            self.on_attribute_change.block_signals(True)
            value = getattr(self, f.name, undefined)
            if value is not undefined:
                delattr(self, f.name)
            self.add_field(
                f.name,
                type_=f,
                override=True,
                class_field=False,
                field_class=WritableField,
            )
            if value is not undefined:
                setattr(self, f.name, value)
            f = self.field(f.name)
            self.on_attribute_change.block_signals(vblocked)
            self.on_fields_change.block_signals(blocked)
        return f

    def json_controller(self):
        """Return a JSON dict for the current Controller"""
        result = {}
        for field in self.fields():
            value = getattr(self, field.name, undefined)
            if value is not undefined:
                result[field.name] = to_json_controller(value)
        return result

    def import_json(self, json):
        """Set the Controller state from a JSON dict"""
        for field_name, json_value in json.items():
            setattr(self, field_name, json_value)

    def gc_callbacks(self):
        """Garbage-collect callbacks which contain weak references to
        deleted objects.
        """
        self.on_attribute_change.gc_callbacks()
        self.on_fields_change.gc_callbacks()
        self.on_inner_value_change.gc_callbacks()

    # implementation as in capsul2 (additional field, will be saved)
    # def set_parameter_protected(self, param, state=True):
    # """ Protect /unprotect the named parameter.

    # Protecting is not a real lock, it just marks the parameter a list of
    # "protected" parameters. This is typically used to mark values that have
    # been set manually by the user (using the ControllerWidget for instance)
    # and that should not be later modified by automatic parameters tweaking
    # (such as completion systems).

    # Protected parameters are listed in an additional field,
    # "protected_parameters".

    # If the "state" parameter is False, then we will unprotect it
    # (calling unprotect_parameter())
    # """
    # if not self.field('protected_parameters'):
    ## add a 'protected_parameters' field
    # self.add_field('protected_parameters', type_=list[str],
    # default_factory=list, hidden=True)
    # protected = set(self.protected_parameters)
    # if state:
    # protected.add(param)
    # else:
    # protected.remove(param)
    # self.protected_parameters = sorted(protected)

    # def is_parameter_protected(self, param):
    # """ Tells whether the given parameter is protected or not
    # """
    # print('is_parameter_protected', param)
    # protected = getattr(self, 'protected_parameters', None)
    # print('protected:', protected)
    # if protected is None:
    # print('None')
    # return False
    # print('res:', param in protected)
    # return param in protected

    # implementation as in capsul3/Node, field metadata: not saved
    def is_parameter_protected(self, plug_name):
        return self.field(plug_name).metadata("protected", False)

    def protect_parameter(self, plug_name, state=True):
        self.writable_field(plug_name).protected = state


def asdict(obj, dict_factory=dict, exclude_empty=False, exclude_none=False):
    if isinstance(obj, Controller):
        result = []
        for f in obj.fields():
            value = getattr(obj, f.name, undefined)
            if value is undefined:
                continue
            value = asdict(value, dict_factory, exclude_empty, exclude_none)
            if (not exclude_empty or value not in ([], {}, ())) and (
                not exclude_none or value is not None
            ):
                result.append((f.name, value))
        return dict_factory(result)
    elif isinstance(obj, (list, tuple)):
        return type(obj)(
            asdict(v, dict_factory, exclude_empty, exclude_none) for v in obj
        )
    elif isinstance(obj, dict):
        result = []
        for k, v in obj.items():
            dk = asdict(k, dict_factory, exclude_empty, exclude_none)
            dv = asdict(v, dict_factory, exclude_empty, exclude_none)
            if not exclude_empty or dv not in ([], {}, ()):
                result.append((dk, dv))
        return dict_factory(result)
    else:
        return copy.deepcopy(obj)


def to_json_controller(value):
    """Convert the value to a JSON-compatible representation"""
    if isinstance(value, Controller):
        return value.json_controller()
    elif isinstance(value, (tuple, set, list)):
        return [to_json_controller(i) for i in value]
    elif isinstance(value, dict):
        return dict((i, to_json_controller(j)) for i, j in value.items())
    elif isinstance(value, Path):
        # Subclasses of str are not supported by QWebChannel. When
        # transferred to Javascript, the received value is null
        # (i.e. None). Therefore value is converted to a true
        # str instance.
        return str(value)
    return value


def from_json_controller(value, value_type):
    """
    Recursively convert a JSON value to a Python value
    and also check values.
    """
    if isinstance(value_type, type) and issubclass(value_type, Controller):
        if not isinstance(value, dict):
            raise ValueError(
                f"found a value of type {type(value)} while expecting dict"
            )
        return value_type(
            **dict(
                (k, to_json_controller(v, value.field(k).type))
                for k, v in value.items()
            )
        )

    if value_type.__name__ in {"list", "set", "tuple"}:
        if not isinstance(value, list):
            raise ValueError(
                f"found a velue of type {type(value)} while expecting list"
            )
        item_type = getattr(value_type, "__args__", None)
        if item_type:
            item_type = item_type[0]
            return value_type(from_json_controller(i, item_type) for i in value)
        else:
            return value_type(*value)

    if value_type.__name__ == "dict":
        if not isinstance(value, dict):
            raise ValueError(
                f"found a value of type {type(value)} while expecting dict"
            )
        item_type = getattr(value_type, "__args__", None)
        if item_type:
            item_type = item_type[1]
            return dict(
                (k, from_json_controller(v, item_type)) for k, v in value.items()
            )
        else:
            return value

    if value_type.__name__ == "Literal":
        if value not in value_type.__args__:
            raise ValueError("Invalid value")
        return value

    if isinstance(value, (list, dict)):
        raise ValueError(
            f"found a value of type {type(value)} while expecting {value_type}"
        )
    return value_type(value)


class EmptyController(Controller):
    pass


class DictControllerBase(dict):
    """
    Inherit DictControllerBase _in addition_ to :class:`Controller` (or
    subclass) if you need to access fields as dict items.

    It inherits dict, because without dict iheritance, YAQL raises an error.

    This class is meant to be used only as an additional inheritance to
    Controller subclasses, it does not work alone.
    """

    def get(self, value, default=None):
        return getattr(self, value, default)

    def __getitem__(self, name):
        value = getattr(self, name, undefined)
        if value is undefined:
            raise KeyError(name)
        return value

    def items(self):
        for field in self.fields():  # noqa F402
            yield (field.name, getattr(self, field.name))

    def values(self):
        for field in self.fields():  # noqa F402
            yield getattr(self, field.name)

    def keys(self):
        for field in self.fields():  # noqa F402
            yield field.name

    def __contains__(self, key):
        return self.field(key) is not None

    def __len__(self):
        return len(list(self.fields()))

    def __iter__(self):
        for field in self.fields():  # noqa F402
            yield field.name


class OpenKeyControllerMeta(ControllerMeta):
    _cache = {}

    def __getitem__(cls, value_type):
        cls_value_type = getattr(cls, "_value_type", None)
        if value_type is cls_value_type:
            return cls
        result = cls._cache.get(value_type)
        if result is None:
            result = type(
                f"OpenKeyController[{value_type.__name__}]",
                (OpenKeyController,),
                {"_value_type": value_type},
                ignore_metaclass=False,
            )
            result.__name__ = "OpenKeyController"
            result.__args__ = (value_type,)
            cls._cache[value_type] = result
        return result


class OpenKeyController(
    Controller, metaclass=OpenKeyControllerMeta, ignore_metaclass=True
):
    """A dictionary-like controller, with "open keys": items may be added
    on the fly, fields are created upon assignation.

    A value field type should be specified to build the items.

    Usage:

    >>> dict_controller = OpenKeyController[str]()
    >>> print(dict_controller.fields())
    []
    >>> dict_controller.my_item = 'bubulle'
    >>> print([f.name for f in dict_controller.fields()])
    ['my_item']
    >>> print(dict_controller.asdict())
    {'my_item': 'bubulle'}
    >>> del dict_controller.my_item
    >>> print(dict_controller.asdict())
    {}
    """

    _reserved_names = {"enable_notification"}

    def __new__(cls, *args, **kwargs):
        if cls is OpenKeyController:
            return EmptyOpenKeyController()
        return super().__new__(cls)

    def __setattr__(self, name, value):
        if (
            not name.startswith("_")
            and name not in self.__dict__
            and self.field(name) is None
            and name not in self._reserved_names
        ):
            self.add_field(name, self._value_type)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if self.field(name) is not None:
            self.remove_field(name)
        else:
            super().__delattr__(name)


class EmptyOpenKeyController(OpenKeyController[str]):
    pass


class OpenKeyDictControllerMeta(OpenKeyControllerMeta):
    _cache = {}

    def __getitem__(cls, value_type):
        cls_value_type = getattr(cls, "_value_type", None)
        if value_type is cls_value_type:
            return cls
        result = cls._cache.get(value_type)
        if result is None:
            result = type(
                f"OpenKeyDictController[{value_type.__name__}]",
                (OpenKeyDictController,),
                {"_value_type": value_type},
                ignore_metaclass=False,
            )
            result.__name__ = "OpenKeyDictController"
            result.__args__ = (value_type,)
            cls._cache[value_type] = result
        return result


class OpenKeyDictController(
    OpenKeyController,
    DictControllerBase,
    metaclass=OpenKeyDictControllerMeta,
    ignore_metaclass=True,
):
    """
    An :class:`OpenKeyController` with dict access (see
    :class:`DictControllerBase`)
    """

    def __new__(cls, *args, **kwargs):
        if cls is OpenKeyDictController:
            return EmptyOpenKeyDictController()
        return super().__new__(cls)


class EmptyOpenKeyDictController(OpenKeyDictController[str]):
    pass
