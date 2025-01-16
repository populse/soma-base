"""
This module provides a notification system that can be used to register
callbacks (*i.e* Python callables) that will all be called by a single
:meth:`Notifier.notify` call.
"""

__docformat__ = "restructuredtext en"

from soma.functiontools import checkParameterCount, numberOfParameterRange
from soma.sorted_dictionary import SortedDictionary
from soma.translation import translate as _
from soma.undefined import Undefined

# -------------------------------------------------------------------------


class Notifier:
    """
    Register a series of functions (or Notifier instances) which are all called
    with the :meth:`notify` method. The calling order is the registering
    order. If a Notifier is registered, its :meth:`notify` method is called
    whenever *self.notify()* is called.
    """

    def __init__(self, parameterCount=None):
        """
        Parameters
        ----------
        parameterCount: int
            if not None, each registered function must be callable with that
            number of arguments (checking is done on registration).
        """
        self._listeners = []
        self._parameterCount = parameterCount
        self._delayedNotification = None

    def add(self, listener):
        """
        Register a callable or a Notifier that will be called whenever
        :meth:`notify` is called. If the notifier has a *parameterCount*,
        :func:`checkParameterCount <soma.utils.functiontools.checkParameterCount>` is used to verify that
        *listener* can be called with *parameterCount* parameters.

        Parameters
        ----------
        listener: Python callable (function, method, *etc*.) or :class:`Notifier` instance
            item to add to the notification list.
        """

        if listener not in self._listeners:
            if self._parameterCount is not None:
                if isinstance(listener, Notifier):
                    if (
                        listener._parameterCount is not None
                        and listener._parameterCount != self._parameterCount
                    ):
                        raise RuntimeError(
                            _(
                                "Impossible to register a notifier with"
                                "%(other)d parameter(s) to a notifier "
                                "with %(self)d parameter(s)"
                            )
                            % {
                                "self": self._parameterCount,
                                "other": listener._parameterCount,
                            }
                        )
                else:
                    checkParameterCount(listener, self._parameterCount)
            self._listeners.append(listener)

    def remove(self, listener):
        """
        Remove an item from the notification list. Do nothing if *listener* is
        not in the list.

        Parameters
        ----------
        listener: Python callable or :class:`Notifier` instance
            item previously registered with :meth:`add`.
        Returns
        -------
        bool:
            *True* if a listener has been removed, *False* otherwise.
        """

        try:
            self._listeners.remove(listener)
            result = True
        except ValueError:
            result = False
        return result

    def notify(self, *args):
        """
        Calls all the registered items in the notification list. All the
        parameters given to :meth:`notify` are passed to the items in the list.
        For items in the list that are :class:`Notifier` instance, their
        :meth:`notify` method is called

        .. seealso:: :meth:`delayNotification`, :meth:`restartNotification`
        """
        if self._delayedNotification is None:
            # if self._listeners: print '!notify!', self, ':', args, '(' + str(len( self._listeners )), 'listeners)'
            # Iterate on a copy of self._listeners because this list can be modified
            # by a listener during notification loop.
            for listener in tuple(self._listeners):
                # print '!notify!  -->', listener
                try:
                    if isinstance(listener, Notifier):
                        listener.notify(*args)
                    else:
                        listener(*args)
                except ReferenceError:
                    # listener is deleted in a weak ref/proxy
                    self._listeners.remove(listener)

        else:
            if self._delayedNotificationIgnoreDoubles:
                if args not in self._delayedNotification:
                    self._delayedNotification.append(args)
            else:
                self._delayedNotification.append(args)

    def delayNotification(self, ignoreDoubles=False):
        """
        Stop notification until :meth:`restartNotification` is called. After a
        call to :meth`delayNotification`, all calls to :meth:`notify` will only
        store the notification parameters until :meth:`restartNotification` is
        called.

        Parameters
        ----------
        ignoreDoubles: bool
            If *True* (the default), all calls to :meth:`notify` with
            the same parameters as a previous call will be ignored (*i.e.*
            notification will be done only once for two identical calls).
        """
        self._delayedNotification = []
        self._delayedNotificationIgnoreDoubles = ignoreDoubles

    def restartNotification(self):
        """
        Restart notifications that have been delayed by
        :meth:`delayNotification`. All the calls to :meth:`notify` that have
        been done between the call to :meth:`delayNotification` and the call to
        :meth:`restartNotification`, are applied immediately.
        """
        delayedNotification = self._delayedNotification
        if delayedNotification is not None:
            self._delayedNotification = None
            for args in delayedNotification:
                self.notify(*args)


# -------------------------------------------------------------------------
class ReorderedCall:
    """
    **todo:** documentation
    """

    def __init__(self, function, parametersOrder):
        self._function = function
        self._order = parametersOrder

    def __call__(self, *args):
        return self._function(*[args[i] for i in self._order])


# -------------------------------------------------------------------------
class VariableParametersNotifier(Notifier):
    """
    This class is a notifier that can register functions with various arguments
    count.
    """

    def __init__(self, mainParameters, *otherParameters):
        """
        .. seealso:: :class:`Notifier`

        **todo** documentation
        """
        Notifier.__init__(self, len(mainParameters))
        self.__parameters = {len(mainParameters): list(range(len(mainParameters)))}
        self.__min = len(mainParameters)
        self.__max = len(mainParameters)
        # Converting to list because it has the index method (which tuple has
        # not)
        mainParameters = list(mainParameters)
        main = set(mainParameters)
        for p in otherParameters:
            other = set(p)
            if other - main:
                raise RuntimeError(
                    _(
                        "Invalid parameters definition (%(other)s is"
                        " not a subset of %(main)s)"
                    )
                    % {"other": str(other), "main": str(main)}
                )
            if len(p) in self.__parameters:
                raise RuntimeError(
                    _(
                        "Invalid parameters definition (several sets"
                        " of %d parameters defined)"
                    )
                    % (len(p),)
                )
            self.__parameters[len(p)] = [mainParameters.index(i) for i in p]
            self.__min = min(self.__min, len(mainParameters))

    def add(self, listener):
        """
        .. seealso:: :meth:`Notifier.add`

        **todo:** documentation
        """
        if isinstance(listener, Notifier):
            realListener = listener
        else:
            min, max = numberOfParameterRange(listener)
            if max is None:
                paramCount = self.__max
            else:
                paramCount = max
            paramOrder = self.__parameters.get(paramCount)
            if paramOrder is None:
                raise RuntimeError(
                    _("%(f)s has an invalid parameter count (%(c)d)")
                    % {"f": str(listener), "c": paramCount}
                )
            realListener = ReorderedCall(listener, paramOrder)
        Notifier.add(self, realListener)

    def remove(self, listener):
        """
        .. seealso:: :meth:`Notifier.remove`

        **todo:** documentation
        """

        for i in range(len(self._listeners)):
            c = self._listeners[i]
            if (
                isinstance(c, ReorderedCall) and c._function == listener
            ) or c == listener:
                del self._listeners[i]
                return True
        return False


# -------------------------------------------------------------------------
class ObservableAttributes:
    """
    ObservableAttributes allows to track modification of attributes at
    runtime. By registering callbacks, it is possible to be warn of the
    modification (setting and deletion) of any attribute of the instance.
    """

    def __init__(self, *args, **kwargs):
        #: VariableParametersNotifier instance notified whenever any attribute
        #: is modified. Use self.onAttributeChange to register a function on
        #: this notifier.
        #    self.__dict__[ '_onAnyAttributeChange' ] = \
        #      self._createAttributeNotifier()
        super().__setattr__("_onAnyAttributeChange", self._createAttributeNotifier())

        #: Dictionary whose keys are attribute names and values are
        #: L{VariableParametersNotifier} instances. Whenever an attribute is
        #: modified, the corresponding L{VariableParametersNotifier} is notified.
        #: Use L{self.onAttributeChange} to register a function on these notifiers.
        #    self.__dict__[ '_onAttributeChange' ] = {}
        super().__setattr__("_onAttributeChange", {})
        super().__init__(*args, **kwargs)

    @staticmethod
    def _createAttributeNotifier():
        """
        Static method creating a :class:`VariableParametersNotifier` instance
        for attribute modification notification.

        see :meth:`notifyAttributeChange`.
        """
        return VariableParametersNotifier(
            ("object", "attributeName", "newValue", "oldValue"),
            (),
            ("newValue",),
            ("newValue", "oldValue"),
            ("attributeName", "newValue", "oldValue"),
        )

    def notifyAttributeChange(self, name, value, oldValue=Undefined):
        """
        First, calls functions registered for modification of the attribute
        named *name*, then call functions registered for modification of any
        attribute.

        .. seealso:: :meth:`onAttributeChange`
        """
        # Notify the change of this attribute
        if hasattr(self, "_onAttributeChange"):
            notifier = self._onAttributeChange.get(name)
            if notifier is not None:
                notifier.notify(self, name, value, oldValue)

        if hasattr(self, "_onAnyAttributeChange"):
            # Notify the change of one attribute
            self._onAnyAttributeChange.notify(self, name, value, oldValue)

    def __setattr__(self, name, value):
        """
        Changes the value of attribute *name* then calls
        :meth:`notifyAttributeChange`.
        """
        oldValue = getattr(self, name, Undefined)
        super().__setattr__(name, value)
        if value != oldValue:
            self.notifyAttributeChange(name, value, oldValue)

    def __delattr__(self, name):
        """
        Deletes the attribute *name* then calls :meth:`notifyAttributeChange`
        with ``newValue = :class:`Undefined` ``.
        """
        oldValue = getattr(self, name, Undefined)
        super().__delattr__(name)
        self.notifyAttributeChange(name, Undefined, oldValue)
        # Delete notifier for the deleted attribute
        self._onAttributeChange.pop(name, None)

    def onAttributeChange(self, first, second=None):
        """
        Registers a function to be called when an attribute is modified or
        deleted. To call the function for any attribute modification, use the
        following syntax::

            instance.onAttributeChange(function)

        To register a function for a named attribute, use the following
        syntax::

            instance.onAttributeChange(attributeName, function)

        The registered function can have 0 to 4 parameters. Depending on its
        number of parameters, it will be called with the following values:

        - 4 parameters: (object, attributeName, newValue, oldValue)
        - 3 parameters: (attributeName, newValue, oldValue)
        - 2 parameters: (newValue, oldValue)
        - 1 parameter: (newValue)

        Where:

        - **object** is the object whose attribute has been modified or
          deleted.
        - **attributeName** is the name of the modified or deleted attribute.
        - **newValue** is the value of the attribute after modification or
          ``Undefined`` if the attribute has been deleted.
        - **oldValue** is the value of the attribute before modification. If
          the attribute was not defined, ``oldValue = Undefined``.

        If the function accepts a variable number of parameters, it will be
        called with the maximum number of arguments possible.
        """
        if second is None:
            if hasattr(self, "_onAnyAttributeChange"):
                self._onAnyAttributeChange.add(first)
        else:
            if hasattr(self, "_onAttributeChange"):
                notifier = self._onAttributeChange.get(first)
                if notifier is None:
                    notifier = self._createAttributeNotifier()
                    self._onAttributeChange[first] = notifier
                notifier.add(second)

    def removeOnAttributeChange(self, first, second=None):
        """
        Remove a function previously registered with :meth:`onAttributeChange`.
        To remove a function, the arguments of :meth:`removeOnAttributeChange`
        must be the same as those passed to :meth:`onAttributeChange` to
        register the function.
        """
        if second is None:
            result = self._onAnyAttributeChange.remove(first)
        else:
            result = self._onAttributeChange[first].remove(second)
        return result

    def delayAttributeNotification(self, ignoreDoubles=False):
        """
        Stop attribute modification notification until
        :meth:`restartAttributeNotification` is called. After a call to
        :meth:`delayAttributeNotification`, all modification notification will
        only be stored until :meth:`restartAttributeNotification` is called.
        This call is recursive on all attributes values that are instance of
        :class:`ObservableAttributes`.

        Parameters
        ----------
        ignoreDoubles: bool
            If True (False is the default), all notification with the same
            parameters as a previous notification will be ignored (*i.e.* notification will be done only once for two identical events).
        """
        self._delayAttributeNotification(
            ignoreDoubles=ignoreDoubles, checkedObjects=set()
        )

    def _delayAttributeNotification(self, ignoreDoubles=False, checkedObjects=None):
        if checkedObjects is not None:
            checkedObjects.add(self)

        for name, notifier in self._onAttributeChange.items():
            notifier.delayNotification(ignoreDoubles)
        self._onAnyAttributeChange.delayNotification(ignoreDoubles)

        # Recursively delay notification
        for name in dir(self):
            value = getattr(self, name, Undefined)

            if isinstance(value, ObservableAttributes):
                if checkedObjects is not None:
                    # This allow to not recursively call
                    # _delayAttributeNotification
                    if value not in checkedObjects:
                        value._delayAttributeNotification(
                            ignoreDoubles=ignoreDoubles, checkedObjects=checkedObjects
                        )
                else:
                    value._delayAttributeNotification(ignoreDoubles=ignoreDoubles)

        if checkedObjects is not None:
            checkedObjects.pop()

    def restartAttributeNotification(self):
        """
        Restarts notifications that have been delayed by
        :meth:`delayAttributeNotification`. All the modifications that happened
        between the call to :meth:`delayAttributeNotification` and the call to
        :meth:`restartAttributeNotification`, are notified immediately.
        """
        self._restartAttributeNotification(checkedObjects=set())

    def _restartAttributeNotification(self, checkedObjects=None):
        if checkedObjects is not None:
            checkedObjects.add(self)

        for name, notifier in self._onAttributeChange.items():
            notifier.restartNotification()
        self._onAnyAttributeChange.restartNotification()
        # Recursively restart notification
        for name in dir(self):
            value = getattr(self, name, Undefined)
            if isinstance(value, ObservableAttributes):
                if checkedObjects is not None:
                    # This allow to not recursively call
                    # _delayAttributeNotification
                    if value not in checkedObjects:
                        value.restartAttributeNotification()
                else:
                    value._delayAttributeNotification()

        if checkedObjects:
            checkedObjects.pop()


# ----------------------------------------------------------------------------


class ObservableList(list):
    """
    A list that notifies its changes to registered listeners.
    Inherits from python list and contains an instance of :class:`Notifier`
    (:attr:`onChangeNotifier`).

    Example::

        l = ObservableList()
        l.addListener(update)
        l.append(e)

    * calls :meth:`onChangeNotifier.notify(INSERT_ACTION, [e], len(l)) <Notifier.notify>`
    * calls ``update(INSERT_ACTION, [e], len(l))``

    Attributes
    ----------
    INSERT_ACTION: int
        used to notify insertion of new elements  in the list
    REMOVE_ACTION: int
        used to notify elements deletion
    MODIFY_ACTION: int
        used to notify elements modification

    onChangeNotifier: Notifier
        the Notifier's notify method is called when the list
        has changed.
    """

    # actions to notify
    INSERT_ACTION = 0
    REMOVE_ACTION = 1
    MODIFY_ACTION = 2

    def __init__(self, content=None):
        """
        Parameters
        ----------
        content: list
            elements to initialize the list content
        """
        # call a super class method can be done two different ways:
        # - superClass.method(self, ...)
        # - super().method(...)
        # It's better to use the second way because if derived class inherits from several classes,
        # super will try to find the method in other super classes before
        super().__init__()
        # views can register update callbacks on this notifier
        # to be aware of any change in the model
        # On change, this object calls Notifier.notify(args)
        # which calls every registered function with args
        # args = action (insert, remove, modify), elems list, position
        self.onChangeNotifier = Notifier()
        if content:
            self.extend(content)

    def __getnewargs__(self):
        """Returns the args to pass to the __init__ method to construct this
        object.
        It is useful to save an :class:`ObservableList` object to :mod:`minf`
        format.

        Returns
        -------
        tuple:
            arg content to pass to the __init__ method for creating a copy of this object
        """
        content = []
        content.extend(self)
        return content

    def __reduce__(self):
        """This method is redefined for enable deepcopy of this object (and
        potentially pickle).
        It gives the arguments to pass to the init method of the object when
        creating a copy

        Returns
        -------
        tuple:
            class name, init args, state, iterator on elements to copy,
            dictionary iterator
        """
        # class name, init args, parameters for setstate, elements iterator,
        # dictionary iterator
        return (self.__class__, (), None, iter(self), None)

    def addListener(self, listener):
        """Registers the listener callback method in the notifier.
        The method must take 3 arguments: action, elems list, position

        *action* should be one of:

        - INSERT_ACTION: elems have been inserted at position in the list
        - REMOVE_ACTION: elems have been removed [at position] in the list
        - MODIFY_ACTION: at position, some elements have been replaced by
          elems

        The position given in the notify method will be between 0 and
        ``len(self)``

        Parameters
        ----------
        listener: function
            function to call to notify changes
        """
        self.onChangeNotifier.add(listener)

    def append(self, elem):
        """Adds the element at the end of the list.
        Notifies an insert action.
        """
        index = len(self)
        super().append(elem)
        self.onChangeNotifier.notify(self.INSERT_ACTION, [elem], index)

    def extend(self, l):
        """Adds the content of the list l at the end of current list.
        Notifies an insert action."""
        index = len(self)
        super().extend(l)
        self.onChangeNotifier.notify(self.INSERT_ACTION, l, index)

    def insert(self, pos, elem):
        """Inserts elem at position pos in the list.
        Notifies an insert action.
        """
        index = self.getPositiveIndex(pos)
        super().insert(pos, elem)
        self.onChangeNotifier.notify(self.INSERT_ACTION, [elem], index)

    def remove(self, elem):
        """Removes the first occurrence of elem in the list.

        Notifies a remove action."""
        super().remove(elem)
        self.onChangeNotifier.notify(self.REMOVE_ACTION, [elem])

    def pop(self, pos=None):
        """Removes the element at position pos or the last element if pos is
        *None*.

        Notifies a remove action.

        Returns
        -------
        object:
            the removed element
        """
        if pos is not None:
            index = self.getPositiveIndex(pos)
            elem = super().pop(pos)
        else:
            index = len(self) - 1
            elem = super().pop()
        self.onChangeNotifier.notify(self.REMOVE_ACTION, [elem], index)
        return elem

    def sort(self, key=None, reverse=False):
        """Sorts the list using key function key.

        Notifies a modify action.

        Returns
        -------
        key: function
            key function: elem->key
        """
        super().sort(key=key, reverse=reverse)
        # all the elements of the list could be modified
        self.onChangeNotifier.notify(self.MODIFY_ACTION, self, 0)

    def reverse(self):
        """Inverses the order of the list.
        Notifies a modify action."""
        super().reverse()
        self.onChangeNotifier.notify(self.MODIFY_ACTION, self, 0)

    def __setitem__(self, key, value):
        """Sets value to element at position key in the list.

        Notifies a modify action::

            l[key] = value
        """
        index = self.getPositiveIndex(key)
        super().__setitem__(key, value)
        self.onChangeNotifier.notify(self.MODIFY_ACTION, [value], index)

    def __delitem__(self, key):
        """Removes the element at position key in the list.

        Notifies a remove action::

            del l[key]
        """
        index = self.getPositiveIndex(key)
        super().__delitem__(key)
        self.onChangeNotifier.notify(self.REMOVE_ACTION, [], index)

    def __setslice__(self, i, j, seq):
        """Sets values in seq to elements in the interval i,j.

        If i and j are negative numbers, there are converted before this call
        in ``index + len(self)``

        Notifies a modify action:

            l[i:j] = seq
        """
        indexI = self.getIndexInRange(i)
        indexJ = self.getIndexInRange(j)
        super().__setslice__(i, j, seq)
        # if the interval is empty, action is insertion at the first position
        if indexI >= indexJ:
            self.onChangeNotifier.notify(self.INSERT_ACTION, seq, indexI)
        else:
            lenSeq = len(seq)
            lenInter = indexJ - indexI
            # if values sequence has same or lower length as the interval in the list,
            # all values are written to the list from the first index
            # the rest of the interval (if interval is longer than sequence) is
            # left unchanged
            if lenInter >= lenSeq:
                self.onChangeNotifier.notify(self.MODIFY_ACTION, seq, indexI)
            else:
                # if the interval is shorter than the sequence of values,
                # values in the interval are used to modify the list,
                # the rest is inserted at indexJ position
                self.onChangeNotifier.notify(
                    self.MODIFY_ACTION, seq[0:lenInter], indexI
                )
                self.onChangeNotifier.notify(
                    self.INSERT_ACTION, seq[lenInter:lenSeq], indexJ
                )

    def __delslice__(self, i, j):
        """Removes elements in the interval i,j.

        If i and j are negative numbers, there are converted before this call
        in ``index + len(self)``.

        Notifies a remove action::

            del l[i:j]
        """
        indexI = self.getIndexInRange(i)
        indexJ = self.getIndexInRange(j)
        seq = self[indexI:indexJ]
        super().__delslice__(i, j)
        # if the interval is empty, the list is not modified
        if indexI < indexJ:
            self.onChangeNotifier.notify(self.REMOVE_ACTION, seq, indexI)

    def __iadd__(self, l):
        """``list += l`` <=> ``list.extend(l)``

        Notifies insert action."""
        index = len(self)
        newList = super().__iadd__(l)
        self.onChangeNotifier.notify(self.INSERT_ACTION, l, index)
        return newList

    def __imul__(self, n):
        """``list *= n``

        Notifies insert action."""
        index = len(self)
        newList = super().__imul__(n)
        self.onChangeNotifier.notify(self.INSERT_ACTION, self[index:], index)
        return newList

    def getPositiveIndex(self, i):
        """Returns an index between 0 and ``len(self)``

        - if *i* is negative, it is replaced by ``len(self) + i``
        - if *index* is again negative, it is replaced by 0
        - if *index* is beyond ``len(self)`` it is replaced by ``len(self)``
        """
        l = len(self)
        if i < 0:
            index = max(0, l + i)
        else:
            index = min(i, l)
        return index

    def getIndexInRange(self, i):
        """Returns an index in the range of the list.

        * if ``i < 0`` returns 0
        * if ``i > len(self)``, returns ``len(self)``
        """
        if i < 0:
            index = 0
        else:
            l = len(self)
            if i > l:
                index = l
            else:
                index = i
        return index

    def itemIndex(self, item):
        """
        Returns item's index in the list. It is different from the
        :meth:`list.index` method that returns the index of the first element
        that has the same value as *item*.
        """
        i = 0
        for it in self:
            if it is item:
                break
            i = i + 1
        if i == len(self):
            i = -1
        return i


# ----------------------------------------------------------------------------


class ObservableSortedDictionary(SortedDictionary):
    """
    A sorted dictionary that notifies its changes.
    Inherits from python list and contains an instance of
    :class:`Notifier` (:attr:`onChangeNotifier`).

    Example::

        d=ObservableSortedDictionary()
        d.addListener(update)
        d.insert(index, key, e)

    * calls :meth:`onChangeNotifier.notify(INSERT_ACTION, [e], index) <Notifier.notify>`
    * calls ``update(INSERT_ACTION, [e], index)``

    Attributes
    ----------
    INSERT_ACTION: int
        used to notify insertion of new elements  in the dictionary
    REMOVE_ACTION: int
        used to notify elements deletion
    MODIFY_ACTION: int
        used to notify elements modification

    onChangeNotifier: Notifier
        the Notifier's notify method is called when the dictionaty has changed.
    """

    # actions to notify
    INSERT_ACTION = 0
    REMOVE_ACTION = 1
    MODIFY_ACTION = 2

    def __init__(self, *args):
        """
        Initialize the dictionary with a list of ( key, value ) pairs.
        """
        self.onChangeNotifier = Notifier()
        super().__init__(*args)

    def __getnewargs__(self):
        """Returns the args to pass to the __init__ method to construct this object.
        It is useful to save ObservableList object to minf format.
        Returns
        -------
        tuple:
            arg content to pass to the __init__ method for creating a copy of
            this object
        """
        content = list(self.items())
        return content

    def addListener(self, listener):
        """Registers the listener callback method in the notifier.
        The method must take 3 arguments: action, elems list, position

        *action* should be one of:

        - INSERT_ACTION: elems have been inserted at position in the dictionary
        - REMOVE_ACTION: elems have been removed [at position] in the dict
        - MODIFY_ACTION: at position, some elements have been replaced by elems

        The position given in the notify method will be between 0 and len(self)

        Parameters
        ----------
        listener: function
            function to call to notify changes
        """
        self.onChangeNotifier.add(listener)

    def __setitem__(self, key, value):
        insertion = key not in self
        super().__setitem__(key, value)
        if insertion:
            self.onChangeNotifier.notify(self.INSERT_ACTION, [value], len(self) - 1)
        else:
            self.onChangeNotifier.notify(
                self.MODIFY_ACTION, [value], self.sortedKeys.index(key)
            )

    def __delitem__(self, key):
        index = self.sortedKeys.index(key)
        super().__delitem__(key)
        self.onChangeNotifier.notify(self.REMOVE_ACTION, [], index)

    def insert(self, index, key, value):
        """
        inserts a (*key*, *value*) pair in the sorted dictionary before
        position *index*. If *key* is already in the dictionary, a
        :class:`KeyError <exceptions.KeyError>` is raised.

        Parameters
        ----------
        key:
            key to insert
        value:
            value associated to *key*

        Returns
        -------
        index: integer
            index of C{key} in the sorted keys
        """
        super().insert(index, key, value)
        self.onChangeNotifier.notify(self.INSERT_ACTION, [value], index)

    def clear(self):
        """
        Removes all items from dictionary
        """
        super().clear()
        self.onChangeNotifier.notify(self.REMOVE_ACTION, list(self.values()), 0)

    def sort(self, key=None, reverse=False):
        """Sorts the dictionary using function *key* to compare keys.

        Notifies a modify action.

        Parameters
        ----------
        key: function
            key function key->key
        """
        super().sort(key=key, reverse=reverse)
        self.onChangeNotifier.notify(self.MODIFY_ACTION, list(self.values()), 0)


# ----------------------------------------------------------------------------
class EditableTree(ObservableAttributes, ObservableSortedDictionary):
    """The base class to model a tree of items.
    This class can be derived to change implementation.

    An EditableTree contains items which can be

    - an item branch: it contains other items as children
    - an item leaf: doesn't have children

    The list of items is an :class:`ObservableSortedDictionary` which notifies
    its changes to registered listeners.

    If the tree is modifiable, new items can be added.

    Every item is an :class:`EditableTree.Item`.

    *EditableTree* is iterable over its items.

    *EditableTree* also inherits from :class:`ObservableAttributes`, so
    registered listeners can be notified of attributes value change.

    To call a method when item list changes::

      editableTree.addListener(callbackMethod)

    To call a method when an item list changes at any depth in the tree::

        editableTree.addListenerRec(callbackMethod)

    To call a method when an attribute of the tree changes::

        editableTree.onAttributeChange(attributeName, callbackMethod)

    To call a method when an attribute changes at any depth in the tree::

        editableTree.onAttributeChangeRec(attributeName, callbackMethod)

    Attributes
    ----------
    defaultName: string
        default name of the tree
    name: string
        the name of the tree
    id: string
        tree identifier (a hash by default)
    modifiable: bool
        if *True*, new items can be added, items can be deleted and modified
    unnamed: bool
        indicates if *name* parameter was none, so the tree has the default
        name.
    visible: bool
        indicates if the tree is visible (if not it may be hidden in a
        graphical representation)
    """

    defaultName = "tree"

    def __init__(
        self,
        name=None,
        id=None,
        modifiable=True,
        content=(),
        visible=True,
        enabled=True,
    ):
        """
        Parameters
        ----------
        name: string
            the name of the tree
        id: string
            tree identifier (a hash by default)
        modifiable: bool
            if *True*, new items can be added, items can be deleted and
            modified
        content: list
            children items (:class:`EditableTree.Item`)
        visible: bool
            indicates if the tree is visible (if not it may be hidden in a
            graphical representation)
        enabled: bool
        """
        dictContent = [(i.id, i) for i in content]
        super().__init__(*dictContent)
        if name is None:
            self.name = self.defaultName
            self.unnamed = True
        else:
            self.name = name
            self.unnamed = False
        if id is None:
            self.id = str(hash(self))
        else:
            self.id = id
        self.modifiable = modifiable
        self.visible = visible
        self.enabled = enabled

    def __getnewargs__(self):
        """Returns the args to pass to the __init__ method to construct this object.
        It is useful in order to save EditableTree object to minf format.
        Returns
        -------
        tuple:
            arg content to pass to the __init__ method for creating a copy of this object
        """
        # elements in the tuple must be serializable with minf, so the content
        # must be of type list
        content = list(self.values())
        return (
            self.name,
            self.id,
            self.modifiable,
            content,
            self.visible,
            self.enabled,
        )

    def __str__(self):
        s = self.name + " ("
        for i in self:
            s += str(i) + " "
        s += ")"
        return s

    def __hash__(self):
        return ObservableAttributes.__hash__(self)

    def add(self, item):
        """
        Adds an item in the tree. If this item's id is already present in the
        tree as a key, add the item's content in the corresponding key.

        recursive method
        """
        key = item.id
        if key in self:
            if (
                not item.isLeaf()
            ):  # if the item is a leaf and is already in the tree, nothing to do
                for v in item.values():  # item is also a dictionary and contains several elements, add each value in the tree item
                    self[key].add(v)
            # also set current name for the current object
            self[key].name = item.name
        else:  # new item
            self[key] = item

    def isDescendant(self, item):
        """Returns *True* if the current item is a child or a child's child...
        of the item in parameter

        Always *False* for the root of the tree"""
        return False

    def isLeaf(self):
        return False

    def removeEmptyBranches(self):
        """If a branch item doesn't contain any leaf or branch that contains
        leaf recursively, the item is removed from the tree."""
        toRemove = []
        for child in self.values():
            if not child.isLeaf():
                child.removeEmptyBranches()
                if (
                    list(child.values()) == []
                ):  # it isn't possible to remove an element during iteration on the list
                    toRemove.append(
                        child
                    )  # so it's put on a remove list and will be removed from the tree outside the loop
        for item in toRemove:
            del self[item.id]

    def sort(self, key=None, reverse=False):
        """Recursive sort of the tree: items are sorted in all branches."""
        ObservableSortedDictionary.sort(self, self._keyItems)
        for item in self.values():
            if not item.isLeaf():
                item.sort(key=key, reverse=reverse)

    def _keyItems(self, id):
        """Key function"""
        i1 = self[id]
        # names are translated in lowercase to make an alphabetical sort independent of the case
        # by default (uppercase letters are < to lowecase letters)
        n1 = i1.name.lower()
        # print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
        return (not i1.isLeaf(), n1)

    def compItems(self, id1, id2):
        """Comparison function

        Returns:

        - 1 if ``i1 > i2``
        - -1 if ``i1 < i2``
        - 0 if they are equal"""
        res = 0
        i1 = self[id1]
        i2 = self[id2]
        if not i1.isLeaf() and i2.isLeaf():
            # if one item is a branch and the other is a leaf, the branch must
            # be before the leaf
            res = -1
        elif i1.isLeaf() and not i2.isLeaf():
            res = 1
        else:
            # names are translated in lowercase to make an alphabetical sort independent of the case
            # by default (uppercase letters are < to lowecase letters)
            n1 = i1.name.lower()
            n2 = i2.name.lower()
            if n1 < n2:
                res = -1
            elif n1 > n2:
                res = 1
        # print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
        return res

    def addListenerRec(self, listener):
        """Add a listener to the tree recursively at every level.
        The listener is added to the notifier of all branches of the tree."""
        self.addListener(listener)
        for item in self.values():
            if not item.isLeaf():
                item.addListenerRec(listener)

    def onAttributeChangeRec(self, attributeName, listener):
        """Add a listener of the changes of this attribute value in the tree
        recursively at every level.

        The listener is added to the attribute change notifier of all branches
        of the tree.
        """
        self.onAttributeChange(attributeName, listener)
        for item in self.values():
            if not item.isLeaf():
                item.onAttributeChangeRec(attributeName, listener)

    # -------------------------------------------------------------------------
    class Item(ObservableAttributes):
        """Base element of an :class:`EditableTree`

        *Item* inherits from :class:`ObservableAttributes`, so it can notify
        registered listeners of attributes changes (for example :attr:`name`).

        Attributes
        ----------
        icon: string
            filename of the image that can be used to represent the item
        name: string
            Text representation of the item
        movable: bool
            True if the item can be moved in the tree
        modifiable: bool
            True if the item can changed (add children, change text, icon)
        delEnabled: bool
            True if deletion of the item is allowed
        tooltip: string
            description associated to the item
        copyEnabled: bool
            indicates if this item can be copied
        visible: bool
            indicates if current item is visible (if not it may be hidden in a
            graphical representation)
        enabled: bool
            indicates if the item is enabled, it could be visible but disabled

        """

        def __init__(
            self,
            name=None,
            id=None,
            icon=None,
            tooltip=None,
            copyEnabled=True,
            modifiable=True,
            delEnabled=True,
            visible=True,
            enabled=True,
            *args,
        ):
            super().__init__(*args)
            self.icon = icon
            self.name = name
            if id is None:
                self.id = str(hash(self))
            else:
                self.id = id
            self.tooltip = tooltip
            self.copyEnabled = copyEnabled
            self.modifiable = modifiable
            self.delEnabled = delEnabled
            self.visible = visible
            self.enabled = enabled
            self.onChangeNotifier = Notifier()
            self.unnamed = False

        def __getnewargs__(self):
            """Returns the args to pass to the __init__ method to construct this object.
            It is useful to save L{ObservableList} object to minf format.
            Returns
            -------
            tuple:
                arg content to pass to the __init__ method for creating a copy
                of this object
            """
            return (
                self.name,
                self.id,
                self.icon,
                self.tooltip,
                self.copyEnabled,
                self.modifiable,
                self.delEnabled,
                self.visible,
                self.enabled,
            )

        def __reduce__(self):
            """This method is redefined for enable deepcopy of this object (and
            potentially pickle).

            It gives the arguments to pass to the init method of the object when creating a copy

            Returns
            -------
            tuple:
                class name, init args, state, iterator on elements to copy,
                dictionary iterator
            """
            return (self.__class__, self.__getnewargs__(), None, None, None)

        def __str__(self):
            return self.name

        def isLeaf(self):
            """Must be redefined in subclasses to say if the item is a leaf"""
            pass

        def setAllModificationsEnabled(self, bool):
            """Recursively enables or disables item's modification."""
            # self.copyEnabled=bool # copy is always enabled. there's no use to
            # have 3 different booleans, an editable should be sufficient
            self.modifiable = bool
            self.delEnabled = bool
            if not self.isLeaf():
                for child in self.values():
                    child.setAllModificationsEnabled(bool)

        def isDescendant(self, item):
            """Returns *True* if the current item is a child or a child's
            child... of the item in parameter
            """
            found = False
            # print self.name, "is descendant", item.name, "? "
            if not item.isLeaf():
                for child in item.values():
                    # search self in item's children and recursively in
                    # children's children (deep first search)
                    if self == child:
                        found = True
                    elif not child.isLeaf():
                        found = self.isDescendant(child)
                    if found:
                        break
            return found

    # -------------------------------------------------------------------------
    class Branch(Item, ObservableSortedDictionary):
        """A Branch is an :class:`Item <EditableTree.Item>` that can contain
        other items.

        It inherits from :class:`Item <EditableTree.Item>` and from
        :class:`ObservableSortedDictionary`, so it can have children items.
        """

        defaultName = "new"

        def __init__(
            self,
            name=None,
            id=None,
            icon=None,
            tooltip=None,
            copyEnabled=True,
            modifiable=True,
            delEnabled=True,
            content=(),
            visible=True,
            enabled=True,
        ):
            """All parameters must have default values to be able to create new
            elements automatically"""
            # super().__init__(content)  #, name, icon, tooltip, copyEnabled, modifiable, delEnabled)
            # EditableTree.Item.__init__(self, name, icon, tooltip,
            # copyEnabled, modifiable, delEnabled)
            dictContent = [(i.id, i) for i in content]
            super().__init__(
                name,
                id,
                icon,
                tooltip,
                copyEnabled,
                modifiable,
                delEnabled,
                visible,
                enabled,
                *dictContent,
            )
            if name is None:
                self.name = self.defaultName
                self.unnamed = True
            else:
                self.name = name
                self.unnamed = False

        def __getnewargs__(self):
            content = list(self.values())
            return (
                self.name,
                self.id,
                self.icon,
                self.tooltip,
                self.copyEnabled,
                self.modifiable,
                self.delEnabled,
                content,
                self.visible,
                self.enabled,
            )

        def __reduce__(self):
            """This method is redefined for enable deepcopy of this object (and
            potentially pickle).
            It gives the arguments to pass to the init method of the object
            when creating a copy
            """
            return (self.__class__, self.__getnewargs__(), None, None, None)

        def __str__(self):
            s = self.name + " ("
            for i in self:
                s += str(i) + " "
            s += ")"
            return s

        def __hash__(self):
            return EditableTree.Item.__hash__(self)

        def isLeaf(self):
            return False

        def add(self, item):
            """
            Adds an item in the tree. If this item's id is already present in
            the tree as a key, add the item's content in the corresponding key.

            recursive method
            """
            key = item.id
            if key in self:
                if (
                    not self[key].isLeaf()
                ):  # if the item is a leaf and is already in the tree, nothing to do
                    for v in item.values():  # item is also a dictionary and contains several elements, add each value in the tree item
                        self[key].add(v)

                # also set current name for the current object
                self[key].name = item.name

            else:  # new item
                self[key] = item

        def removeEmptyBranches(self):
            toRemove = []
            for child in self.values():
                if not child.isLeaf():
                    child.removeEmptyBranches()
                    if list(child.values()) == []:
                        toRemove.append(child)
            for item in toRemove:
                del self[item.id]

        def sort(self, key=None, reverse=False):
            """Recursive sort of the tree: items are sorted in all branches."""
            ObservableSortedDictionary.sort(self, self._keyItems)
            for item in self.values():
                if not item.isLeaf():
                    item.sort(key=key, reverse=reverse)

        def _keyItems(self, id):
            """Sorting key function"""
            i1 = self[id]
            # names are translated in lowercase to make an alphabetical sort independent of the case
            # by default (uppercase letters are < to lowecase letters)
            n1 = i1.name.lower()
            # print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
            # leafs must go after subtrees
            return (not i1.isLeaf(), n1)

        def compItems(self, id1, id2):
            """Comparison function

            Returns

            - 1 if i1 > i2
            - -1 if i1 < i2
            - 0 if they are equal"""
            res = 0
            i1 = self[id1]
            i2 = self[id2]
            if not i1.isLeaf() and i2.isLeaf():
                # if one item is a branch and the other is a leaf, the branch
                # must be before the leaf
                res = -1
            elif i1.isLeaf() and not i2.isLeaf():
                res = 1
            else:
                # names are translated in lowercase to make an alphabetical sort independent of the case
                # by default (uppercase letters are < to lowecase letters)
                n1 = i1.name.lower()
                n2 = i2.name.lower()
                if n1 < n2:
                    res = -1
                elif n1 > n2:
                    res = 1
            # print "comp", i1.name,i1.isLeaf(), i2.name,i2.isLeaf(), res
            return res

        def addListenerRec(self, listener):
            self.addListener(listener)
            for item in self.values():
                if not item.isLeaf():
                    item.addListenerRec(listener)

        def onAttributeChangeRec(self, attributeName, listener):
            self.onAttributeChange(attributeName, listener)
            for item in self.values():
                if not item.isLeaf():
                    item.onAttributeChangeRec(attributeName, listener)

    # -------------------------------------------------------------------------
    class Leaf(Item):
        """A tree item that cannot have children items"""

        def __init__(
            self,
            name="new",
            id=None,
            icon=None,
            tooltip=None,
            copyEnabled=True,
            modifiable=True,
            delEnabled=True,
            visible=True,
            enabled=True,
        ):
            super().__init__(
                name,
                id,
                icon,
                tooltip,
                copyEnabled,
                modifiable,
                delEnabled,
                visible,
                enabled,
            )

        def isLeaf(self):
            return True

    # -------------------------------------------------------------------------


class ObservableNotifier(Notifier):
    """
    This notifier can notify when the first listener is added and when the last
    listener is removed.

    It enables to use the notifier only when there are some listeners
    registered.

    Attributes
    ----------
    onAddFirstListener: :class:`Notifier`
        register a listener on this notifier to be called when the first
        listener is registered on ObservableNotifier
    onRemoveLastListener: :class:`Notifier`
        register a listener on this notifier to be called when the last
        listener is removed from ObservableNotifier
    """

    def __init__(self, parameterCount=None):
        """
        Parameters
        ----------
        parameterCount: int
            if not *None*, each registered function must be callable with that
            number of arguments (checking is done on registration).
        """
        Notifier.__init__(self, parameterCount)
        self.onAddFirstListener = Notifier()
        self.onRemoveLastListener = Notifier()

    def add(self, listener):
        nbListenersBefore = len(self._listeners)
        Notifier.add(self, listener)
        if (
            nbListenersBefore == 0
        ):  # before add : 0 listener, after : 1 listener -> add first listener
            if len(self._listeners) == 1:
                self.onAddFirstListener.notify()

    def remove(self, listener):
        nbListenersBefore = len(self._listeners)
        Notifier.remove(self, listener)
        if (
            nbListenersBefore == 1
        ):  # before add : 1 listener, after : 0 listener -> remove last listener
            if len(self._listeners) == 0:
                self.onRemoveLastListener.notify()
