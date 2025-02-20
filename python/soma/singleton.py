"""
Singleton pattern.
"""

import atexit

__docformat__ = "restructuredtext en"


class Singleton:
    """
    Implements the singleton pattern. A class deriving from ``Singleton`` can
    have only one instance. The first instantiation will create an object and
    other instantiations return the same object. Note that the :meth:`__init__`
    method (if any) is still called at each instantiation (on the same object).
    Therefore, :class:`Singleton` derived classes should define
    :meth:`__singleton_init__`
    instead of :py:meth:`__init__` because the former is only called once.

    Example::

        from singleton import Singleton

        class MyClass(Singleton):
            def __singleton_init__(self):
                self.attribute = 'value'

        o1 = MyClass()
        o2 = MyClass()
        print(o1 is o2)

    A Singleton subclass will inherit Singleton.

    In a multiple inheritance situation, the subclass should preferably inherit
    Singleton **first**, so that ``Singleton.__new__()`` will be called and the
    singleton machinery will be activated.

    However, in some situations another parent will ask to be inherited first,
    like in Qt: QObject should be inherited first, at least in PyQt6. In that
    case, ``QObject.__new__`` will be called instead, and the singleton
    mechanism will be skipped: this will fail. The solution is to overload the
    ``__new__`` method in the subclass, and force the singleton system again,
    as done in ``Singleton.__new__``, but ``calling QObject.__new__`` to
    actually instantiate the object, then using :meth:`_post_new_`. The typical
    example is :class:`qtThead.QtThreadedCall`.

    Example::

        class QtThreadCall(QObject, Singleton):
            def __new__(cls, *args, **kwargs):
                if '_singleton_instance' not in cls.__dict__:
                    cls._singleton_instance = QObject.__new__(cls)
                    cls._post_new_(cls, *args, **kwargs)
                return cls._singleton_instance

    """

    @classmethod
    def get_instance(cls):
        try:
            return cls._singleton_instance
        except AttributeError as e:
            msg = f"Class {cls.__name__} has not been initialized"
            raise ValueError(msg) from e

    def __new__(cls, *args, **kwargs):
        if '_singleton_instance' not in cls.__dict__:
            cls._singleton_instance = super(Singleton, cls).__new__(cls)
            cls._post_new_(cls, *args, **kwargs)
        return cls._singleton_instance

    @staticmethod
    def _post_new_(cls, *args, **kwargs):
        ''' This method is called from __new__. It is separated in order to
        make it available for subclasses which would also overload __new__.
        See the doc of Singleton for an explanation.
        '''
        singleton_init = getattr(cls._singleton_instance,
                                 '__singleton_init__', None)
        if singleton_init is not None:
            singleton_init(*args, **kwargs)
        atexit.register(cls.delete_singleton)
        return cls._singleton_instance

    def __init__(self, *args, **kwargs):
        """
        The __init__ method of :py:class:`Singleton` derived class should do
        nothing.

        Derived classes must define :py:meth:`__singleton_init__` instead of
        __init__.
        """

    def __singleton_init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def delete_singleton(cls):
        if hasattr(cls, "_singleton_instance"):
            del cls._singleton_instance
