"""
A minf tree is used to convert Python objects into a structure that can be written in any minf format. When a Python object is written into a minf file, if it cannot be directly stored in the chosen minf format, it is transformed in a minf tree by a L{MinfReducer}. During reading, minf trees are converted into Python objects by a L{MinfExpander}. Whatever the minf format used (XML, Python, HDF5, etc.) reading and writing objects is always done with a L{MinfReducer}/L{MinfExpander} pair. Each L{MinfReducer}/L{MinfExpander} pair is identified by a name. The name of one L{MinfReducer}/L{MinfExpander} pair must be chosen when writing a minf file, this name is recorded in the minf file and used for reading.

A minf tree is always accessed via an iterator on its content. This content is composed of atoms and special structure objects. Atoms are any Python objects that can be directly stored in the minf file format (without need for reducing or expanding these objects). Other objects are reduced in a structure starting with a L{StartStructure} instance and terminated by an L{EndStructure} instance. Between the L{StartStructure}/L{EndStructure} pair, there can be any atoms and/or special structure objects.

* author: Yann Cointepas
* organization: `NeuroSpin <http://www.neurospin.org>`_
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
"""

__docformat__ = "restructuredtext en"

import sys

from soma.minf.error import MinfError
from soma.translation import translate as _
from soma.undefined import Undefined

try:
    from soma.signature.api import HasSignature, Sequence
except ImportError:

    class HasSignature:
        pass

    class Sequence:
        pass


#: Type name of a minf structure.
#: @see: L{StartStructure}
minfStructure = "minf"
#: Type name of a list structure.
#: @see: L{StartStructure}
listStructure = "list"
#: Type name of a dictionary structure.
#: @see: L{StartStructure}
dictStructure = "dict"


# ------------------------------------------------------------------------------
class StartStructure:
    """
    When iterating over a minf tree, a L{StartStructure} indicate the beginning of
    a subtree. Subtrees are identified by their type which is a string
    defining how the object has been reduced (and how to expand it). There are
    three built-in structures:
      - L{minfStructure}: this is the first element of a minf tree. The content
        of this tree is a series of objects (i.e. atoms) or reduced objects.
        The L{StartStructure} instances of type L{minfStructure} have a mandatory
        'reduction' attribute containing the name of the L{MinfReducer}/L{MinfExpander} pair
        corresponding to this minf file.
      - L{listStructure}: the content of the subtree is a series of objects or
        reduced objects. By default, a L{listStructure} is expanded as a Python
        list.
        The L{StartStructure} instances of type L{listStructure} accepts an
        optional 'length' attribute containing the number of elements in the
        list.
      - dictStructure: the content of the subtree is a series of pair of objects or
        reduced objects. In each pair, the first item represent a key and the
        second item represent a value. By default, a L{dictStructure} is expanded
        as a Python dictionary.
        The L{StartStructure} instances of type L{dictStructure} accepts an
        optional 'length' attribute containing the number of key/value pairs in
        the dictionary.

    Any non-builtin structure type must be registered in the L{MinfReducer}/L{MinfExpander}
    defined in the main L{minfStructure} tree.

    """

    def __init__(self, structureNodeType, identifier=None, **attributes):
        """
        @param structureNodeType: type of the structure (see L{StartStructure}).
        @type  structureNodeType: string
        @param identifier: EXPERIMENTAL: identifier of the subtree (used for
          referencing).
        @type  identifier: string or C{None}
        @param attributes: attributes of the structure. Possible name/values
          for attributes are dependent on the structure type.
        @type  attributes: dict
        """
        self.type = structureNodeType
        self.identifier = identifier
        self.attributes = attributes

    def __repr__(self):
        if self.identifier:
            l = ['identifier="' + self.identifier + '"']
        else:
            l = []
        l += [str(i) + '="' + str(j) + '"' for i, j in self.attributes.items()]
        return "<" + self.type + " " + ", ".join(l) + ">"


# ------------------------------------------------------------------------------
class EndStructure:
    """
    When iterating over a minf tree, an L{EndStructure} indicate the end of
    a subtree.
    """

    def __init__(self, structureNodeType):
        self.type = structureNodeType

    def __repr__(self):
        return "</" + self.type + ">"


# ------------------------------------------------------------------------------
class Reference:
    """
    EXPERIMENTAl: the reference system is not fully functional.
    When iterating over a minf tree, an L{Reference} correspond to a structure
    previously identified in the minf tree.
    """

    def __init__(self, identifier):
        """
        @param identifier: identifier of the referenced object.
        @type identifier: string
        """
        self.identifier = identifier

    def __repr__(self):
        return '<ref identifier="' + self.identifier + '">'


# ------------------------------------------------------------------------------
def createMinfReducer(name):
    """
    Return an instance of L{MinfReducer} previously registered.

    @param name: name of the reducer
    @type  name: string
    """
    reducer = MinfReducer._allReducers.get(name)
    if reducer is None:
        raise MinfError(_("Unknown Minf reducer: %s") % (name,))
    return reducer


# ------------------------------------------------------------------------------
class MinfReducer:
    """
    Class to convert a Python object into a minf tree.
    """

    #: todo: documentation
    _allReducers = {}

    #: todo: documentation
    _defaultClassReducer = {}

    class DefaultObjectReducer:
        def __init__(self, structureName):
            self.structureName = structureName

        def __call__(self, reducer, object):
            getinitkwargs = getattr(object, "__getnewargs_ex__", None) or getattr(
                object, "__getinitkwargs__", None
            )
            if getinitkwargs is None:
                getinitargs = getattr(object, "__getnewargs__", None) or getattr(
                    object, "__getinitargs__", None
                )
                if not getinitargs:
                    raise TypeError(
                        f"Object of type {type(object)} cannot be serialized by MinfReducer"
                    )
                args = getinitargs()
                kwargs = {}
            else:
                args, kwargs = getinitkwargs()
            start = StartStructure(self.structureName)
            yield start
            for item in args:
                yield None
                for minfNode in reducer.reduce(item):
                    yield minfNode
            if kwargs:
                for key, value in kwargs.items():
                    for minfNode in reducer.reduce(key):
                        yield minfNode
                    for minfNode in reducer.reduce(value):
                        yield minfNode
            end = EndStructure(self.structureName)
            yield end

    def __init__(self, name, bases=()):
        self.name = name
        self.bases = tuple([self._allReducers[i] for i in bases])
        self.typeReducers = {}
        self._allReducers[name] = self

    def getTypeReducer(self, classOrName):
        if not isinstance(classOrName, str):
            className = classOrName.__module__ + "." + classOrName.__name__
        else:
            className = classOrName
        reducer = self.typeReducers.get(className)
        if reducer is None:
            for base in self.bases:
                reducer = base.getTypeReducer(className)
                if reducer is not None:
                    break
            else:
                if issubclass(classOrName, HasSignature):
                    return self.hasSignatureReducer
                    raise MinfError(
                        _("Automatic reduction of HasSignature not implemented")
                    )
                raise MinfError(
                    _(
                        "Object of type %(class)s cannot be reduced "
                        'in Minf "%(minf)s" structure'
                    )
                    % {"class": className, "minf": self.name}
                )
        return reducer

    def reduce(self, *args):
        for o in args:
            typeReducer = self.getTypeReducer(o.__class__)
            yield from typeReducer(self, o)

    def atomReducer(reducer, atom):
        return (atom,)

    atomReducer = staticmethod(atomReducer)

    def sequenceReducer(reducer, sequence):
        try:
            yield StartStructure(listStructure, length=len(sequence))
        except TypeError:
            yield StartStructure(listStructure)
        yield from reducer.reduce(*sequence)
        yield EndStructure(listStructure)

    sequenceReducer = staticmethod(sequenceReducer)

    def dictReducer(reducer, dict):
        try:
            yield StartStructure(dictStructure)
        except TypeError:
            yield StartStructure(dictStructure)
        for key, value in dict.items():
            for minfNode in reducer.reduce(key):
                yield minfNode
            for minfNode in reducer.reduce(value):
                yield minfNode
        yield EndStructure(dictStructure)

    dictReducer = staticmethod(dictReducer)

    def hasSignatureNonDefaultValues(o):
        it = o.signature.items()
        next(it)
        for key, sigItem in it:
            value = getattr(o, key, Undefined)
            if value is not Undefined and (
                value != sigItem.defaultValue
                or getattr(sigItem, "writeIfDefault", False)
            ):
                yield (key, value)

    hasSignatureNonDefaultValues = staticmethod(hasSignatureNonDefaultValues)

    def hasSignatureToDict(o):
        d = {}
        for key, value in MinfReducer.hasSignatureNonDefaultValues(o):
            if isinstance(value, HasSignature):
                content = MinfReducer.hasSignatureToDict(value)
                if content:
                    d[key] = content
            else:
                d[key] = value
        return d

    hasSignatureToDict = staticmethod(hasSignatureToDict)

    def hasSignatureReducer(reducer, o):
        yield from reducer.reduce(MinfReducer.hasSignatureToDict(o))

    hasSignatureReducer = staticmethod(hasSignatureReducer)

    def registerAtomType(self, cls):
        className = cls.__module__ + "." + cls.__name__
        self.typeReducers[cls.__module__ + "." + cls.__name__] = self.atomReducer
        self._defaultClassReducer[className] = self.name

    def registerClass(self, cls, reducer):
        className = cls.__module__ + "." + cls.__name__
        self.typeReducers[className] = reducer
        self._defaultClassReducer[className] = self.name

    def defaultReducer(value):
        """
        Return a minf reducer that can reduce C{value}.

        @returns: string or None
        """
        if isinstance(value, type):
            # value is a class
            cls = value
        else:
            cls = value.__class__
        className = cls.__module__ + "." + cls.__name__
        return MinfReducer._defaultClassReducer.get(className, None)

    defaultReducer = staticmethod(defaultReducer)


# ------------------------------------------------------------------------------
def createMinfExpander(name):
    """
    Return an instance of L{MinfExpander} previously registered.

    @param name: name of the expander
    @type  name: string
    """
    expander = MinfExpander._allExpanders.get(name)
    if expander is None:
        raise KeyError(_("Unknown Minf expander: %s") % (name,))
    return expander


# ------------------------------------------------------------------------------
class MinfExpander:
    """
    Class to convert a minf tree into a Python object.
    """

    _allExpanders = {}

    class DefaultObjectExpander:
        def __init__(self, factory):
            self.factory = factory

        def __call__(
            self,
            expander,
            minfNode,
            minfNodeIterator,
            target,
            targetType,
            stop_on_error=True,
            exceptions=None,
        ):
            structureName = minfNode.type
            args = []
            kwargs = {}
            for minfNode in minfNodeIterator:
                if isinstance(minfNode, EndStructure):
                    if minfNode.type != structureName:
                        raise MinfError(
                            _(
                                "Wrong Minf structure ending, expecting %(exp)s instead of %(rcv)s"
                            )
                            % {"exp": structureName, "rcv": minfNode.type}
                        )
                    break
                else:
                    key = expander.expand(
                        minfNodeIterator,
                        minfNode,
                        stop_on_error=stop_on_error,
                        exceptions=exceptions,
                    )
                    try:
                        value = expander.expand(
                            minfNodeIterator,
                            stop_on_error=stop_on_error,
                            exceptions=exceptions,
                        )
                        if key is None:
                            args.append(value)
                        else:
                            kwargs[str(key)] = value
                    except Exception as e:
                        if stop_on_error:
                            raise e
                        else:
                            if exceptions is None:
                                exceptions = [sys.exc_info()]
                            else:
                                exceptions.append(sys.exc_info())
            return self.factory(*args, **kwargs)

    def __init__(self, name, bases=()):
        self.name = name
        self.bases = tuple([self._allExpanders[i] for i in bases])
        self.typeExpanders = {}
        self._allExpanders[name] = self
        self.objectsWithIdentifier = {}

    def getTypeExpander(self, structureName):
        expander = self.typeExpanders.get(structureName)
        if expander is None:
            for base in self.bases:
                expander = base.getTypeExpander(structureName)
                if expander is not None:
                    break
            else:
                raise MinfError(
                    _(
                        "Minf structure %(struct)s cannot be expanded "
                        'from Minf "%(minf)s" structure'
                    )
                    % {"struct": structureName, "minf": self.name}
                )
        return expander

    def expand(
        self,
        minfNodeIterator,
        minfNode=Undefined,
        target=None,
        targetType=Undefined,
        stop_on_error=True,
        exceptions=None,
    ):
        if minfNode is Undefined:
            minfNode = next(minfNodeIterator)
        if isinstance(minfNode, StartStructure):
            identifier = minfNode.identifier
            typeExpander = self.getTypeExpander(minfNode.type)
            try:
                result = typeExpander(
                    self,
                    minfNode,
                    minfNodeIterator,
                    target=target,
                    targetType=targetType,
                    stop_on_error=stop_on_error,
                    exceptions=exceptions,
                )
            except Exception as e:
                if stop_on_error:
                    raise
                else:
                    result = None
                    exceptions.append(sys.exc_info())
            if identifier is not None:
                self.objectsWithIdentifier[identifier] = result
            return result
        elif isinstance(minfNode, EndStructure):
            raise MinfError(
                _("Minf structure %s ended but not started") % (minfNode.type,)
            )
        elif isinstance(minfNode, Reference):
            return self.objectsWithIdentifier[minfNode.identifier]
        else:
            return minfNode

    def sequenceExpander(
        expander,
        minfNode,
        minfNodeIterator,
        target,
        targetType,
        stop_on_error=True,
        exceptions=None,
    ):
        if target is None:
            result = []
        else:
            result = target
            while len(result) != 0:
                result.pop()
        if isinstance(targetType, Sequence) and targetType.elementType.mutable:
            length = minfNode.attributes.get("length")
            if length and len(result) < int(length):
                result += [
                    targetType.elementType.createValue()
                    for i in range(int(length) - len(result))
                ]
        itTarget = iter(result)
        for minfNode in minfNodeIterator:
            if isinstance(minfNode, EndStructure):
                if minfNode.type != listStructure:
                    raise MinfError(
                        _(
                            "Wrong Minf structure ending, expecting %(exp)s instead of %(rcv)s"
                        )
                        % {"exp": listStructure, "rcv": minfNode.type}
                    )
                break
            else:
                target = None
                if itTarget is not None:
                    try:
                        target = next(itTarget)
                    except StopIteration:
                        itTarget = None
                if target is not None:
                    r = expander.expand(
                        minfNodeIterator,
                        minfNode,
                        target=target,
                        targetType=targetType.elementType,
                        stop_on_error=stop_on_error,
                        exceptions=exceptions,
                    )
                    result.append(r)
                else:
                    try:
                        result.append(
                            expander.expand(
                                minfNodeIterator,
                                minfNode,
                                stop_on_error=stop_on_error,
                                exceptions=exceptions,
                            )
                        )
                    except Exception as e:
                        if stop_on_error:
                            raise e
                        else:
                            result.append(None)
                            exceptions.append(sys.exc_info())
        return result

    sequenceExpander = staticmethod(sequenceExpander)

    def dictExpander(
        expander,
        minfNode,
        minfNodeIterator,
        target,
        targetType,
        stop_on_error=True,
        exceptions=None,
    ):
        if target is None:
            result = {}
        else:
            result = target
        for minfNode in minfNodeIterator:
            if isinstance(minfNode, EndStructure):
                if minfNode.type != dictStructure:
                    raise MinfError(
                        _(
                            "Wrong Minf structure ending, expectinf %(exp)s instead of %(rcv)s"
                        )
                        % {"exp": dictStructure, "rcv": minfNode.type}
                    )
                break
            else:
                key = expander.expand(
                    minfNodeIterator,
                    minfNode,
                    stop_on_error=stop_on_error,
                    exceptions=exceptions,
                )
                if isinstance(key, list):
                    # list objects are unhashable and cannot be used as dictionary key
                    # in this case they are converted to tuple
                    key = tuple(key)
                if isinstance(result, HasSignature):
                    targetType = result.signature.get(key, Undefined)
                    if targetType is not Undefined:
                        targetType = targetType.type
                    target = getattr(result, key, None)
                    try:
                        if isinstance(target, HasSignature) or isinstance(
                            targetType, Sequence
                        ):
                            value = expander.expand(
                                minfNodeIterator,
                                target=target,
                                targetType=targetType,
                                stop_on_error=stop_on_error,
                                exceptions=exceptions,
                            )
                        else:
                            value = expander.expand(
                                minfNodeIterator,
                                stop_on_error=stop_on_error,
                                exceptions=exceptions,
                            )
                        setattr(result, key, value)
                    except Exception as e:
                        if stop_on_error:
                            raise
                        else:
                            exceptions.append(sys.exc_info())

                else:
                    try:
                        value = expander.expand(
                            minfNodeIterator,
                            stop_on_error=stop_on_error,
                            exceptions=exceptions,
                        )
                        result[key] = value
                    except Exception as e:
                        if stop_on_error:
                            raise
                        else:
                            exceptions.append(sys.exc_info())

        return result

    dictExpander = staticmethod(dictExpander)

    def registerStructure(self, typeName, expander):
        self.typeExpanders[typeName] = expander


# ------------------------------------------------------------------------------
def createReducerAndExpander(name, *bases):
    """
    Create a new L{MinfReducer}/L{MinfExpander} pair.

    @param name: name registered and used by L{createMinfReducer} and
      L{createMinfExpander}. By convention this name should match the pattern
      C{<name>_<majorVersion>.<minorVersion>} where C{<name>} is a label
      identifying the content of the minf file, and
      C{<majorVersion>.<minorVersion>} is a version number. When a modification
      is done on the structure of a minf file, the version should increase. If
      the modification is backward compatible C{<minorVersion>} should be
      incremented, otherwise C{<majorVersion>} should be incremented.
      There is a built-in L{MinfReducer}/L{MinfExpander} pair named C{minf_2.0}.
    @type  name: string
    @param bases: L{MinfReducer} (respectively L{MinfExpander}) instances can
      inherit from other instances. C{bases} parameter contains the names of the
      base L{MinfReducer} (respectively L{MinfExpander}).
    @type  bases: tuple containing strings
    """
    reducer = MinfReducer(name, bases)
    expander = MinfExpander(name, bases)
    return (reducer, expander)


# ------------------------------------------------------------------------------
def registerClass(reduction, classToRegister, structureName):
    """
    Register a class to allow reading and writing instances of this class in a
    minf file.

    @param reduction: name of the L{MinfReducer}/L{MinfExpander} pair in which the
      class is to be registered.
    @type  reduction: string
    @param classToRegister: class to register
    @type  classToRegister: class
    @param structureName: name used to identify the class in the minf file
    @type  structureName: string
    """
    reducer = createMinfReducer(reduction)
    expander = createMinfExpander(reduction)
    reducer.registerClass(
        classToRegister, MinfReducer.DefaultObjectReducer(structureName)
    )
    expander.registerStructure(
        structureName, MinfExpander.DefaultObjectExpander(classToRegister)
    )


# ------------------------------------------------------------------------------
def registerClassAs(reduction, subclassToRegister, registeredBaseClass):
    """
    Register a class as written in a minf file as one of its base class. If you
    register a base class, it does not automatically allow the writing of objects
    derived from this base class to be written in a minf file. To allow this, one
    must either call L{registerClass} to register a new C{structureName} for the
    derived class, or call L{registerClassAs} to saved derived class instances as
    instances of the base class.
    @param reduction: name of the L{MinfReducer}/L{MinfExpander} pair in which
      C{subClassToRegister} is to be registered.
    @type  reduction: string
    @param subclassToRegister: class to register.
    @type  subclassToRegister: class
    @param registeredBaseClass: one of the base class of C{subclassToRegister},
      that must have been already registered in the C{reduction}
      {MinfReducer}/L{MinfExpander} pair. Any instance of
      C{subclassToRegister} will be reduced as an instance of
      C{registeredBaseClass}.
    @type  registeredBaseClass: class
    """
    reducer = createMinfReducer(reduction)
    reducer.registerClass(
        subclassToRegister, reducer.getTypeReducer(registeredBaseClass)
    )
