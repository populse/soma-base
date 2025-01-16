from importlib import import_module
from pkgutil import iter_modules


def find_subclasses_in_module(module_name, parent_class):
    """
    Finds all the classes defined in a Python module that derive from a
    given class or class name. If the module is a package, it also look
    into submodules.
    """
    if isinstance(parent_class, str):
        check = lambda item: (
            isinstance(item, type)
            and item.__module__ == module_name
            and parent_class in (i.__name__ for i in item.__mro__)
        )
    else:
        check = lambda item: (
            isinstance(item, type)
            and item.__module__ == module_name
            and issubclass(item, parent_class)
        )
    yield from find_items_in_module(module_name, check)


def find_items_in_module(module_name, check):
    """
    Finds all the items defined in a Python module that where *check(cls)* is
    *True*. If the module is a package, it also look recursively into
    submodules.
    """
    try:
        module = import_module(module_name)
    except ImportError:
        return

    for i in module.__dict__.values():
        if check(i):
            yield i
    path = getattr(module, "__path__", None)
    if path:
        for importer, submodule_name, ispkg in iter_modules(path):
            yield from find_items_in_module(
                f"{module.__name__}.{submodule_name}", check
            )


class ClassFactory:
    """
    *ClassFactory* is the base class for creating factories that can look
    for classes in Python modules and create instances.
    """

    def __init__(self, class_types=()):
        # List of Python modules where classes are looked for
        self.module_path = []
        # Instance-level association between a class_type (which is a string)
        # and the corresponding class. There can also be class-level
        # class_types (see get_class method).
        self.class_types = {}
        # Cache of instances returned by get method. This is a dictionary
        # whose keys are (class_type, factory_id) and values are instances.
        self.instances = {}

    def find_class(self, class_type, factory_id):
        """
        Finds a class deriving of the class corresponding to *class_type* and
        whose *factory_id* attribute has a given value. Look for all
        subclasses of parent class declared in the modules of
        :attr:`self.module_path`
        and returns the first one having ``cls.factory_id == factory_id``. If
        none is found, returns *None*.
        """
        base_class = self.get_class(class_type)
        for module_name in self.module_path:
            for cls in find_subclasses_in_module(module_name, base_class):
                if cls.factory_id == factory_id:
                    return cls
        return None

    def get_class(self, class_type):
        """
        Returns the class corresponding to a given class type. First look
        for a dictionary in self.class_types, then look into parent
        classes.
        """
        class_types = getattr(self, "class_types", None)
        if class_types:
            cls = class_types.get(class_type)
            if cls is not None:
                return cls
        for parent_class in self.__class__.__mro__:
            class_types = getattr(parent_class, "class_types", None)
            if class_types:
                cls = class_types.get(class_type)
                if cls is not None:
                    return cls
        raise ValueError(f"Unknown class type: {class_type}")

    def get(self, class_type, factory_id):
        """
        Returns an instance of the class identified by *class_type* and
        *factory_id*. There can be only one instance per *class_type* and
        *factory_id*. Once created with the first call of this method, it
        is stored in :attr:`self.instances` and simply returned in subsequent
        calls.

        If *get_class* is *True*, returns the class instead of an instance
        """
        instance = self.instances.get((class_type, factory_id))
        if instance is None:
            cls = self.find_class(class_type, factory_id)
            if cls is not None:
                if (
                    hasattr(cls.__init__, "__code__")
                    and cls.__init__.__code__.co_argcount != 1
                ):
                    # The class constructor takes arguments: we cannot
                    # instantiate it: register the class itself
                    instance = cls
                else:
                    instance = cls()
                self.instances[(class_type, factory_id)] = instance
            else:
                raise ValueError(
                    'Cannot find a class for class type "{class_type}" and factory id "{factory_id}"'
                )
        return instance
