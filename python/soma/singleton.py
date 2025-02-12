# -*- coding: utf-8 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL-B license as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.

'''
Singleton pattern.

- author: Yann Cointepas
- organization: NeuroSpin
- license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import

import atexit

__docformat__ = 'restructuredtext en'


class Singleton(object):

    '''
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

    '''

    @classmethod
    def get_instance(cls):
        try:
            return getattr(cls, '_singleton_instance')
        except AttributeError:
            msg = "Class %s has not been initialized" % cls.__name__
            raise ValueError(msg)

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
        '''
        The __init__ method of :py:class:`Singleton` derived class should do
        nothing.

        Derived classes must define :py:meth:`__singleton_init__` instead of
        __init__.
        '''

    def __singleton_init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def delete_singleton(cls):
        if hasattr(cls, '_singleton_instance'):
            del cls._singleton_instance
