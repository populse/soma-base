import dataclasses
import re
import sys
import typing

# Import all supported types from typing
from typing import (
    Any,
    Literal,
    Union,
)

from soma.undefined import undefined


def _conlist_str(name, type_):
    tdef = type_str(type_.item_type)
    if type_.min_items:
        tdef += f", min_items={type_.min_items}"
    if type_.max_items:
        tdef += f", max_items={type_.max_items}"
    result = f"pydantic.conlist({tdef})"
    return result


def type_str(type_):
    from soma.controller import Controller

    final_mapping = {
        "list[any]": "list",
        "typing.any": "Any",
        "tuple[any]": "tuple",
        "dict[any,any]": "dict",
        "Controller[Controller]": "Controller",
    }
    postmap = {
        "types.ConstrainedListValue": _conlist_str,
    }

    name = getattr(type_, "__name__", None)
    ignore_args = False
    if not name:
        name = getattr(type_, "_name", None)
        if name == "dict":
            args = getattr(type_, "__args__", None)
            ignore_args = args == getattr(dict, "__args__", None)
        elif name == "set":
            args = getattr(type_, "__args__", None)
            ignore_args = args == getattr(set, "__args__", None)
    if name:
        name = name
    if not name and getattr(type_, "__origin__", None) is Union:
        name = "Union"
    if not name:
        if isinstance(type_, str):
            name = repr(type_)
        else:
            name = str(type_).replace(" ", "")
            if name.startswith("typing."):
                name = name[7:]
                ignore_args = True
    module = getattr(type_, "__module__", None)
    controller = isinstance(type_, type) and issubclass(type_, Controller)
    if module and module not in {
        "builtins",
        "typing",
        "soma.controller.controller",
        "soma.controller.field",
    }:
        name = f"{module}.{name}"
    postproc_fn = postmap.get(name)
    if postproc_fn:
        return postproc_fn(name, type_)
    args = getattr(type_, "__args__", ())
    if not ignore_args and args:
        result = f"{name}[{','.join(type_str(i) for i in args)}]"
    else:
        if controller:
            result = f"Controller[{name}]"
        else:
            result = name  # .lower()
    return final_mapping.get(result, result)


def type_from_str(type_str):
    """Return a type object from a string representation."""
    # TODO: avoid eval()
    return eval(type_str)


def literal_values(type):
    return type.__args__


def subtypes(type):
    return getattr(type, "__args__", ())


def is_list(type_):
    return (
        getattr(type_, "_name", None) == "List"
        or getattr(type_, "__name__", None) == "list"
        or (isinstance(type_, type) and issubclass(type_, list))
    )


def parse_type_str(type_str):
    """
    Returns a tuple with two elements:
    - The main type name
    - A (possibly empty) list of parameter types

    Examples:
    'str' -> ('str', [])
    'List[str]' -> ('List', ['str'])
    'union[list[str],dict[str,controller[Test]]]' -> ('union', ['list[str]', 'dict[str,controller[Test]]'])
    """
    p = re.compile(r"(^[^\[\],]*)(?:\[(.*)\])?$")
    m = p.match(type_str)
    if m:
        type, inner = p.match(type_str).groups()
        if inner:
            p = re.compile(r"\[[^\[\]]*\]")
            substitution = {}
            i = 0
            while True:
                c = 0
                new_inner = []
                for m in p.finditer(inner):
                    skey = f"s{i}"
                    i += 1
                    substitution[skey] = m.group(0).format(**substitution)
                    new_inner += [inner[c : m.start()], f"{{{skey}}}"]
                    c = m.end()
                if new_inner:
                    new_inner.append(inner[c:])
                    inner = "".join(new_inner)
                else:
                    if type == "Literal":
                        subtypes = [eval(i) for i in inner.split(",")]
                    else:
                        subtypes = [i.format(**substitution) for i in inner.split(",")]
                    return (type, subtypes)
        else:
            return (type, [])
    else:
        # shape like conlist(int, ...)
        p = re.compile(r"(^[^\[\],]*)(?:\((.*)\))?$")
        type, inner = p.match(type_str).groups()
        if inner:
            p = re.compile(r"\([^\[\]]*\)")
            substitution = {}
            i = 0
            while True:
                c = 0
                new_inner = []
                for m in p.finditer(inner):
                    skey = f"s{i}"
                    i += 1
                    substitution[skey] = m.group(0).format(**substitution)
                    new_inner += [inner[c : m.start()], f"{{{skey}}}"]
                    c = m.end()
                if new_inner:
                    new_inner.append(inner[c:])
                    inner = "".join(new_inner)
                else:
                    subtypes = [i.format(**substitution) for i in inner.split(",")]
                    return (type, subtypes)
        else:
            return (type, [])


type_default_value_functions = {
    "str": lambda t: "",
    "int": lambda t: 0,
    "float": lambda t: 0.0,
    "bool": lambda t: False,
    "list": lambda t: [],
    "controller": lambda t: t(),
    "literal": lambda t: literal_values(t)[0],
}


def type_default_value(type):  # noqa: F811
    global type_default_value

    full_type = type_str(type)
    main_type = full_type.split("[", 1)[0]
    f = type_default_value_functions.get(main_type)
    if f:
        return f(type)
    try:
        # try default type constructor
        return type()
    except Exception as e:
        raise TypeError(f"Cannot get default value for type {full_type}") from e


class Field:
    """Field wrapper class

    wraps a :class:`dataclasses.Field` object. This wrapper is temporary, is
    not stored in any :class:`~.controller.Controller` structure, and is
    built on-the-fly when :meth:`.controller.Controller.field` or
    :meth:`.controller.Controller.fields` methods are called.

    The Field wrapper is only useful for convenience: it offers attribute and
    property-based access to metadata, and a few methods to easily get some
    state information.

    A `Field` may have metadata to define or characterize it more precisely.
    Metadata are organized in a dictionary, and may be accessed
    as attributes on the `Field` object. A number of field metadata are
    normalized:

    doc: str
        field documentation
    optional: bool
        if the field parameter is optional in the Controller.
    output: bool
        if the field parameter is an output parameter.

        Note that for paths (files, directories) an output parameter means two
        different things: is the filename an output (its value will be
        determined internally during processing) ? Or is the file it refers to
        an output file which will be wtitten ?

        We follow the convention here that the `output` metadata means that the
        file name (the parameter is actually the file name, not the file
        itself) is an output. Thus for files we also have `read` and `write`
        metadata. A file which will be written, but at a location given as
        input, will have `write` set to True, but `output` will be False. In a
        pipelining point of view, this field will still be an output, however,
        thus this pipeline output state should be questioned using the Field
        method :meth:`is_output` rather than querying the `output`
        metadata.
    path_type: bool
        If the field `contains` a :class:`Path` type (file or directory).
        It is True for lists of Path, or compound type containing a Path type.
    read:
        If the field parameter is a path, or contains paths, and if paths will
        be actually read during processing.
    write:
        If the field parameter is a path, or contains paths, and if paths will
        be actually written during processing.
    hidden: bool
        if GUI should not display it
    protected: bool
        if the parameter value has been set manually, and parameters links (in
        a pipelining context) should not modify it any longer.
    allowed_extensions: list[str]
        for path fields, list the allowed file extensions for it. This metadata
        should be replaced with a proper format handling, in the future.
    """

    def __init__(self, dataclass_field):
        super().__setattr__("_dataclass_field", dataclass_field)

    @property
    def name(self):
        """field name, should match its parent
        :class:`~.controller.Controller` field name.
        """
        return self._dataclass_field.name

    @property
    def type(self):
        """field type"""
        types = self._dataclass_field.type.__args__[:-1]
        if len(types) == 1:
            return types[0]
        else:
            return Union.__getitem__(types)

    @property
    def default(self):
        """For internal use only. Use default_value() instead."""
        return self._dataclass_field.default

    @property
    def default_factory(self):
        """default value factory. See :func:`dataclasses.field` for more
        details.
        """
        return self._dataclass_field.default_factory

    def type_str(self):
        """string representation of the field type"""
        return type_str(self.type)

    def literal_values(self):
        """Values for a literal (enum or choice with fixed values)"""
        return literal_values(self.type)

    def subtypes(self):
        """sub-types for field type"""
        return subtypes(self.type)

    def metadata(self, name=None, default=None):
        """metadata dict"""
        if name is None:
            return self._dataclass_field.metadata["_metadata"]
        return self._dataclass_field.metadata["_metadata"].get(name, default)

    def __getattr__(self, name):
        value = self.metadata(name, undefined)
        if value is undefined:
            raise AttributeError(f"{self} has not attribute {name}")
        return value

    def __setattr__(self, name, value):
        raise AttributeError(
            f"can't set attribute {name} of a class field ({self.name})"
        )

    def __delattr__(self, name):
        del self._dataclass_field.metadata["_metadata"][name]

    def is_subclass(self, cls):
        """test the field type subclassing"""
        type_ = self.type
        return isinstance(type_, type) and issubclass(type_, cls)

    def is_path(self):
        """True if the field type is a :class:`Path` (file or directory). See
        also the `path_type` metadata.
        """
        return self.is_subclass(Path)

    def is_file(self):
        """True if the field type is a :class:`File`. See
        also the `path_type` metadata.
        """
        return self.is_subclass(File)

    def is_directory(self):
        """True if the field type is a :class:`Directory`. See
        also the `path_type` metadata.
        """
        return self.is_subclass(Directory)

    def is_input(self):
        """True if the field is an input."""
        if self.output:
            return False
        if self.path_type:
            return self.read
        return True

    @property
    def output(self):
        return self.metadata("output", False)

    def is_output(self):
        """Tells is the field is an output, from a pipelining point of view.

        A field is an output if either its `output` metadata or `write`
        metadata is True.
        """
        if self.output or self.metadata("write", False):
            return True
        return False

    def has_default(self):
        """True if the field has a default value, that is if it has either a
        default or default_factory.
        """
        return (
            self._dataclass_field.default not in (undefined, dataclasses.MISSING)
            or self._dataclass_field.default_factory is not dataclasses.MISSING
        )

    def default_value(self):
        """Default value"""
        if self._dataclass_field.default is not dataclasses.MISSING:
            return self._dataclass_field.default
        if self._dataclass_field.default_factory is not dataclasses.MISSING:
            return self._dataclass_field.default_factory()
        return undefined

    def valid_value(self):
        """Build a valid value for the field. Used either the default value
        or the default constructor od the field type (i.e. self.type())
        """
        value = self.default_value()
        if value is undefined:
            value = self.type()
        return value

    def is_list(self):
        """True if the field type is a list"""
        return is_list(self.type)

    @property
    def optional(self):
        """True if the field is optional, that is a value is not needed for the parent :class:`~.controller.Controller` to be valid."""
        optional = self.metadata("optional", None)
        if optional is None:
            optional = self.has_default()
        return optional

    @property
    def doc(self):
        """Field documentation string"""
        return self.__getattr__("doc")

    def parse_type_str(self):
        return parse_type_str(self.type_str())


class WritableField(Field):
    def __setattr__(self, name, value):
        self._dataclass_field.metadata["_metadata"][name] = value

    @Field.optional.setter
    def optional(self, optional):
        self._dataclass_field.metadata["_metadata"]["optional"] = optional

    @Field.optional.deleter
    def optional(self):  # noqa: F811
        del self._dataclass_field.metadata["_metadata"]["optional"]

    @Field.doc.setter
    def doc(self, doc):
        self.__setattr__("doc", doc)

    @Field.doc.deleter
    def doc(self):  # noqa: F811
        self.__delattr__("doc")


def field(
    name=None,
    type_=None,
    default=dataclasses.MISSING,
    default_factory=dataclasses.MISSING,
    init=None,
    repr=None,
    hash=None,
    compare=None,
    metadata=None,
    field_class=Field,
    proxy_controller=None,
    proxy_field=None,
    force_field_type=None,
    **kwargs,
):
    """:class:`Field` construction factory function. Similar to
    :func:`̀dataclasses.field` but handles :class:`~.controller.Controller`-
    specific metadata, and returns a :class:`Field` instance (from soma) which
    wraps :class:`dataclasses.Field`.
    """
    if isinstance(type_, Field):
        if default is dataclasses.MISSING or default is undefined:
            default = type_._dataclass_field.default
        if default_factory is dataclasses.MISSING:
            default_factory = type_._dataclass_field.default_factory
        if init is None:
            init = type_._dataclass_field.init
        if repr is None:
            repr = type_._dataclass_field.repr
        if hash is None:
            init = type_._dataclass_field.hash
        if compare is None:
            init = type_._dataclass_field.compare
        if metadata is None:
            metadata = type_.metadata().copy()
        else:
            metadata = metadata.copy()
        if force_field_type is None:
            type_ = getattr(type_, "type", None)
        else:
            type_ = force_field_type
    elif metadata is None:
        metadata = {}
    else:
        metadata = metadata.copy()
    metadata.update(kwargs)
    if init is None:
        init = True
    if repr is None:
        repr = True
    if compare is None:
        compare = True
    if default is dataclasses.MISSING and default_factory is dataclasses.MISSING:
        default = undefined
    path_type = None
    if type_ is not None:
        if isinstance(type_, type) and issubclass(type_, Path):
            path_type = type_.__name__.lower()
        elif is_list(type_):
            current_type = type_
            while is_list(current_type):
                s = subtypes(current_type)
                if s:
                    current_type = s[0]
                else:
                    break
            if isinstance(current_type, type) and issubclass(current_type, Path):
                path_type = current_type.__name__.lower()
    if field_class in (Field, WritableField):
        if not metadata.get("class_field"):
            field_class = WritableField
        metadata["path_type"] = path_type
        if path_type:
            metadata.setdefault("read", True)
            metadata.setdefault("write", False)

    result = dataclasses.field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata={
            "_metadata": metadata,
            "_field_class": field_class,
            "_proxy_controller": proxy_controller,
            "_proxy_field": proxy_field,
        },
    )
    if name is not None:
        result.name = name
    result.type = Union[type_, type(undefined)]
    return field_class(result)


class FieldProxy:
    """
    This class is used internally to implement a link between a controller
     field and another controller field. It replaces a dynamic field and
     transfer all calls to the linked controller.
    """

    def __init__(self, name, proxy_controller, proxy_field):
        super().__setattr__("name", name)
        super().__setattr__("_proxy_controller", proxy_controller)
        super().__setattr__("_proxy_field", proxy_field)

    @property
    def target_field(self):
        return self._proxy_controller.field(self._proxy_field)

    def __getattr__(self, name):
        if name == self.name:
            return getattr(self._proxy_controller, self._proxy_field)
        return getattr(self.target_field, name)

    def __setattr__(self, name, value):
        if name == self.name:
            setattr(self._proxy_controller, self._proxy_field, value)
        else:
            setattr(self.target_field, name, value)

    def __delattr__(self, name):
        if name == self.name:
            raise ValueError(f"Cannot remove attribute {name}")
        delattr(self.target_field, name)


class ListProxy(WritableField):
    """
    This class is used internally to represent a field that has a list value
    but whose type and metadata are linked to another field of another
    controller.
    """

    @property
    def target_field(self):
        metadata = self._dataclass_field.metadata
        return metadata["_proxy_controller"].field(metadata["_proxy_field"])

    @property
    def name(self):
        if self._name is None:
            return self.target_field.name
        return self._name

    @property
    def type(self):
        return list[self.target_field.type]

    @property
    def default(self):
        if self._default is dataclasses.MISSING:
            return self.target_field.default
        return self._default

    @property
    def default_factory(self):
        if self._default_factory is dataclasses.MISSING:
            return self.target_field.default_factory
        return self._default_factory

    def metadata(self, name=None, default=None):
        return self.target_field.metadata(name=name, default=default)

    def __getattr__(self, name):
        value = self._dataclass_field.metadata["_metadata"].get(name, undefined)
        if value is undefined:
            value = getattr(self.target_field, name)
        return value

    def __delattr__(self, name):
        raise TypeError("ListProxy are read-only")

    def has_default(self):
        """True if the field has a default value, that is if it has either a
        default or default_factory.
        """
        return (
            self.default not in (undefined, dataclasses.MISSING)
            or self.default_factory is not dataclasses.MISSING
        )

    def default_value(self):
        """Default value"""
        if self.default is not dataclasses.MISSING:
            return self.default
        if self.default_factory is not dataclasses.MISSING:
            return self.default_factory()
        return undefined

    @property
    def optional(self):
        return self.target_field.optional

    @optional.setter
    def optional(self, optional):
        raise TypeError("ProxyField are read-only")

    @optional.deleter
    def optional(self):
        raise TypeError("ProxyField are read-only")

    @property
    def doc(self):
        """Field documentation string"""
        return self.target_field.doc

    @doc.setter
    def doc(self, doc):
        raise TypeError("ProxyField are read-only")

    @doc.deleter
    def doc(self):
        raise TypeError("ProxyField are read-only")


class ListMeta(type):
    def __getitem__(cls, type):
        if isinstance(type, Field):
            result = field(type_=List[type.type], metadata=type.metadata())
        else:
            result = list[type]
        return result


class List(metaclass=ListMeta):
    """in python >= 3.9, use list[] instead."""

    pass


class Path(str):
    """Path represents a :class:`File` or a :class:`Directory`.
    No actual link with the filesystem is made, since we want to manipulate paths for remote filesystems.
    """


class File(Path):
    """File"""

    pass


class Directory(Path):
    """Directory"""

    pass
