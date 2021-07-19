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

'''Utility functions to make a weak proxy which also keeps an access to its original object reference. :func:`weakref.proxy` doesn't allow this, but functions that check types (C+/Python bindings for instance) cannot work with proxies.

We build such a proxy by setting a :func:`weakref.ref` object in the proxy (actually in the object itself).
'''

from __future__ import absolute_import
import weakref

def get_ref(obj):
    ''' Get a regular reference to an object, whether it is already a regular
    reference, a weak reference, or a weak proxy which holds an access to the
    original reference (built using :func:`weak_proxy`).
    In case of a weak proxy not built using :func:`weak_proxy`, we try to get
    the ``self`` from a bound method of the object, namely
    ``obj.__init__.__self__``, if it exists.
    '''
    if isinstance(obj, weakref.ReferenceType):
        return obj()
    elif isinstance(obj, weakref.ProxyTypes):
        if hasattr(obj, '_weakref'):
            return obj._weakref()
        elif hasattr(obj, '__init__'):
            # try to get the 'self' of a bound method
            return obj.__init__.__self__
    return obj


def weak_proxy(obj, callback=None):
    ''' Build a weak proxy (:class:`weakref.ProxyType`) from an object, if it
    is not already one, and keep a reference to the original object (via a
    :class:`weakref.ReferenceType`) in it.

    *callback* is passed to :func:`weakref.proxy`.
    '''
    if isinstance(obj, weakref.ProxyTypes):
        return obj
    real_obj = get_ref(obj)
    if callback:
        wr = weakref.proxy(real_obj, callback)
    else:
        wr = weakref.proxy(real_obj)
    wr._weakref = weakref.ref(real_obj)
    return wr


class proxy_method(object):
    ''' Indirect proxy for a bound method

    It replaces a bound method, ie ``a.method`` with a proxy callable which
    does not take a reference on ``a``.

    Especially useful for callbacks.
    If we want to set a notifier with a callback on a proxy object (without
    adding a new reference on it), we can use proxy_method::

        a = anatomist.Anatomist()
        a.onCursorNotifier.onAddFirstListener.add(
            partial(proxy_method(a, 'enableListening'),
            "LinkedCursor", a.onCursorNotifier)))
        del a

    Without this mechanism, using::

        a.onCursorNotifier.onAddFirstListener.add(
            partial(a.enableListening, "LinkedCursor", a.onCursorNotifier)))

    would increment the reference count on a, because ``a.enableListening``,
    as a *bound method*, contains a reference to a, and will prevent the
    deletion of ``a`` (here the Anatomist application)
    '''
    def __init__(self, obj, method=None):
        '''
        The constructor takes as parameters, either the object and its method
        name (as a string), or the bound method itself.
        '''
        if method is None:
            method = obj.__name__
            obj = obj.__self__
        self.proxy = weak_proxy(obj)
        self.method = method

    def __call__(self, *args, **kwargs):
        return getattr(self.proxy, self.method)(*args, **kwargs)
