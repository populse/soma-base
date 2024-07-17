"""
Utility classes and functions for Python callable.
"""

__docformat__ = "restructuredtext en"

import inspect
from functools import partial

from soma.translation import translate as _

# handle deprecation of getargspec in python3
# inspect.getargspec() is deprecated in Python 3
# (in favor of inspect.getfullargspec until 3.2 and in favor of
# inspect.signature since 3.3) => perhaps we could abandon getargspec and
# include signature???
getfullargspec = getattr(
    inspect, "getfullargspec", getattr(inspect, "getargspec", None)
)


# -------------------------------------------------------------------------
class Empty:
    pass


# -------------------------------------------------------------------------
# Obsolete, kept fonly or backward compatibility. Do not use it.
SomaPartial = partial

# -------------------------------------------------------------------------


def getArgumentsSpecification(callable):
    """
    This is an extension of Python module :py:mod:`inspect.getargspec` that
    accepts classes and returns only information about the parameters that can
    be used in a call to *callable* (*e.g.* the first *self* parameter of bound
    methods is ignored). If *callable* has not an appropriate type, a
    :class:`TypeError <exceptions.TypeError>` exception is raised.

    Parameters
    ----------
    callable: callable
        *function*, *method*, *class* or *instance* to inspect

    Returns
    -------
    tuple:
        As :func:`inspect.getfullargspec`, returns
        *(args, varargs, varkw, defaults)* where *args* is a list of the
        argument names (it may contain nested lists). *varargs* and *varkw* are
        the names of the ``*`` and ``**`` arguments or *None*. *defaults* is a
        n-tuple of the default values of the last *n* arguments.
    """
    if inspect.isfunction(callable):
        return getfullargspec(callable)[:4]
    elif inspect.ismethod(callable):
        args, varargs, varkw, defaults = getfullargspec(callable)[:4]
        args = args[1:]  # ignore the first "self" parameter
        return args, varargs, varkw, defaults
    elif inspect.isclass(callable):
        try:
            init = callable.__init__
        except AttributeError:
            return [], None, None, None
        return getArgumentsSpecification(init)
    elif isinstance(callable, (partial, SomaPartial)):
        args, varargs, varkw, defaults = getArgumentsSpecification(callable.func)
        if defaults:
            d = dict(zip(reversed(args), reversed(defaults)))
        else:
            d = {}
        d.update(zip(reversed(args), reversed(callable.args)))
        if callable.keywords:
            d.update(callable.keywords)

        if len(d):
            defaults = tuple(d[i] for i in args[-len(d) :])
        else:
            defaults = d

        return (args, varargs, varkw, defaults)
    else:
        try:
            call = callable.__call__
        except AttributeError as e:
            raise TypeError(_("%r is not callable") % callable) from e
        return getArgumentsSpecification(call)


# -------------------------------------------------------------------------


def getCallableString(callable):
    """
    Returns a translated human readable string representing a callable.

    Parameters
    ----------
    callable: callable
        *function*, *method*, *class* or *instance* to inspect

    Returns
    --------
    string:
        type and name of the callable
    """
    if inspect.isfunction(callable):
        name = _("function %s") % (callable.__name__,)
    elif inspect.ismethod(callable):
        name = _("method %s") % (
            callable.__self__.__class__.__name__ + "." + callable.__name__,
        )
    elif inspect.isclass(callable):
        name = _("class %s") % (callable.__name__,)
    else:
        name = str(callable)
    return name


# -------------------------------------------------------------------------


def hasParameter(callable, parameterName):
    """
    Returns *True* if *callable* can be called with a parameter named
    *parameterName*. Otherwise, returns *False*.

    .. seealso:: :py:func:`getArgumentsSpecification`

    Parameters
    ----------
    callable: callable
        *function*, *method*, *class* or *instance* to inspect
    parameterName: string
        name of the parameter

    Returns
    -------
    bool:

    """
    args, varargs, varkw, defaults = getArgumentsSpecification(callable)
    return varkw is not None or parameterName in args


# -------------------------------------------------------------------------


def numberOfParameterRange(callable):
    """
    Returns the minimum and maximum number of parameter that can be used to
    call a function. If the maximum number of argument is not defined, it is
    set to *None*.

    .. seealso:: :func:`getArgumentsSpecification`

    Parameters
    ----------
    callable: callable
        *function*, *method*, *class* or *instance* to inspect

    Returns
    -------
    tuple:
        two elements (minimum, maximum)

    """
    args, varargs, varkw, defaults = getArgumentsSpecification(callable)
    if defaults is None or len(defaults) > len(args):
        lenDefault = 0
    else:
        lenDefault = len(defaults)
    minimum = len(args) - lenDefault
    if varargs is None:
        maximum = len(args)
    else:
        maximum = None
    return minimum, maximum


# -------------------------------------------------------------------------
def checkParameterCount(callable, paramCount):
    """
    Checks that a callable can be called with *paramCount* arguments. If not, a
    RuntimeError is raised.

    .. seealso:: :func:`getArgumentsSpecification`

    Parameters
    ----------
    callable: callable
        *function*, *method*, *class* or *instance* to inspect
    paramCount: int
        number of parameters

    """
    minimum, maximum = numberOfParameterRange(callable)
    if (maximum is not None and paramCount > maximum) or paramCount < minimum:
        raise RuntimeError(
            _("%(callable)s cannot be called with %(paramCount)d arguments")
            % {"callable": getCallableString(callable), "paramCount": paramCount}
        )


# -------------------------------------------------------------------------


def drange(start, stop, step=1):
    """
    Creates lists containing arithmetic progressions of any number type (int,
    float, ...)
    """
    r = start
    while r < stop:
        yield r
        r += step
