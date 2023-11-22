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

      class MyClass( Singleton ):
        def __singleton_init__( self ):
          self.attribute = 'value'

      o1 = MyClass()
      o2 = MyClass()
      print(o1 is o2)

    """

    @classmethod
    def get_instance(cls):
        try:
            return getattr(cls, "_singleton_instance")
        except AttributeError:
            msg = f"Class {cls.__name__} has not been initialized"
            raise ValueError(msg)

    def __new__(cls, *args, **kwargs):
        if "_singleton_instance" not in cls.__dict__:
            cls._singleton_instance = super().__new__(cls)
            singleton_init = getattr(
                cls._singleton_instance, "__singleton_init__", None
            )
            if singleton_init is not None:
                singleton_init(*args, **kwargs)
            atexit.register(cls.delete_singleton)
        return cls._singleton_instance

    def __init__(self, *args, **kwargs):
        """
        The __init__ method of :py:class:`Singleton` derived class should do
        nothing.
        Derived classes must define :py:meth:`__singleton_init__` instead of __init__.
        """

    def __singleton_init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def delete_singleton(cls):
        if hasattr(cls, "_singleton_instance"):
            del cls._singleton_instance
