# -*- coding: iso-8859-1 -*-

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
- organization: `NeuroSpin <http://www.neurospin.org>`_ and
  `IFR 49 <http://www.ifr49.org>`_
- license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import
__docformat__ = 'restructuredtext en'


class Singleton(object):

    '''
    Implements the singleton pattern. A class deriving from ``Singleton`` can
    have only one instance. The first instanciation will create an object and
    other instanciations return the same object. Note that the :py:meth:`__init__`
    method (if any) is still called at each instanciation (on the same object).
    Therefore, :py:class:`Singleton` derived classes should define
    :py:meth:`__singleton_init__`
    instead of :py:meth:`__init__` because the former is only called once.

    Example::

      from singleton import Singleton

      class MyClass( Singleton ):
        def __singleton_init__( self ):
          self.attribute = 'value'

      o1 = MyClass()
      o2 = MyClass()
      print(o1 is o2)

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
            singleton_init = getattr(cls._singleton_instance,
                                     '__singleton_init__', None)
            if singleton_init is not None:
                singleton_init(*args, **kwargs)
        return cls._singleton_instance

    def __init__(self, *args, **kwargs):
        '''
        The __init__ method of :py:class:`Singleton` derived class should do
        nothing.
        Derived classes must define :py:meth:`__singleton_init__` instead of __init__.
        '''

    def __singleton_init__(self, *args, **kwargs):
        super(Singleton, self).__init__(*args, **kwargs)
