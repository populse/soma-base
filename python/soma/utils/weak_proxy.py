"""Utility functions to make a weak proxy which also keeps an access to its original object reference. :func:`weakref.proxy` doesn't allow this, but functions that check types (C+/Python bindings for instance) cannot work with proxies.

We build such a proxy by setting a :func:`weakref.ref` object in the proxy (actually in the object itself).
"""

import weakref


def get_ref(obj, raise_err=True):
    """Get a regular reference to an object, whether it is already a regular
    reference, a weak reference, or a weak proxy which holds an access to the
    original reference (built using :func:`weak_proxy`).
    In case of a weak proxy not built using :func:`weak_proxy`, we try to get
    the ``self`` from a bound method of the object, namely
    ``obj.__init__.__self__``, if it exists.

    If raise_err is False, in case of ReferenceError (the proxy points to a
    deleted object), then None is returned and no error is raised.
    """
    try:
        if isinstance(obj, weakref.ReferenceType):
            return obj()
        elif isinstance(obj, weakref.ProxyTypes):
            if hasattr(obj, "_weakref"):
                return obj._weakref()
            elif hasattr(obj, "__init__"):
                # try to get the 'self' of a bound method
                return obj.__init__.__self__
        return obj
    except ReferenceError:
        if raise_err:
            raise
        return None


def weak_proxy(obj, callback=None):
    """Build a weak proxy (:class:`weakref.ProxyType`) from an object, if it
    is not already one, and keep a reference to the original object (via a
    :class:`weakref.ReferenceType`) in it.

    *callback* is passed to :func:`weakref.proxy`.
    """
    if isinstance(obj, weakref.ProxyTypes):
        return obj
    real_obj = get_ref(obj)
    if callback:
        wr = weakref.proxy(real_obj, callback)
    else:
        wr = weakref.proxy(real_obj)
    wr._weakref = weakref.ref(real_obj)
    return wr


class proxy_method:
    """Indirect proxy for a bound method

    It replaces a bound method, ie ``a.method`` with a proxy callable which
    does not take a reference on ``a``.

    Especially useful for callbacks.
    If we want to set a notifier with a callback on a proxy object (without
    adding a new reference on it), we can use proxy_method::

        a = anatomist.Anatomist()
        a.onCursorNotifier.onAddFirstListener.add(
            partial(proxy_method(a.enableListening),
            "LinkedCursor", a.onCursorNotifier)))
        del a

    Without this mechanism, using::

        a.onCursorNotifier.onAddFirstListener.add(
            partial(a.enableListening, "LinkedCursor", a.onCursorNotifier)))

    would increment the reference count on a, because ``a.enableListening``,
    as a *bound method*, contains a reference to a, and will prevent the
    deletion of ``a`` (here the Anatomist application)
    """

    def __init__(self, obj, method=None):
        """
        The constructor takes as parameters, either the object and its method
        name (as a string), or the bound method itself.
        """
        if method is None:
            method = obj.__name__
            obj = obj.__self__
        self.proxy = weak_proxy(obj)
        self.method = method

    def __call__(self, *args, **kwargs):
        return getattr(self.proxy, self.method)(*args, **kwargs)

    def __eq__(self, o):
        return o.method == self.method and get_ref(o.proxy, False) == get_ref(
            self.proxy, False
        )

    def __hash__(self):
        return id(self)
