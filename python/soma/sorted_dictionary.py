"""
Sorted dictionary behave like a dictionary but keep the item insertion
order.

* author: Yann Cointepas
* organization: NeuroSpin
* license: CeCILL B (http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html)

In addition OrderedDict is provided here, either as the standard
collections.OrderedDict class if python version >= 2.7, or based on
SortedDictionary if python version < 2.7.
"""

__docformat__ = "restructuredtext en"

import inspect
from collections.abc import ItemsView

from soma.undefined import Undefined


class SortedDictionary(dict):
    """
    Sorted dictionary behave like a dictionary but keep the item insertion
    order. In addition to python 2.7 OrderedDict, SortedDictionary also has
    an :py:meth:`insert` method allowing insersion at a specified index
    position.

    Example:

    ::

        from SortedDictionary import SortedDictionary
        sd = SortedDictionary(('fisrt', 1), ('second', 2))
        sd['third'] = 3
        sd.insert(0, 'zero', 0)
        sd.items() == [('zero', 0), ('fisrt', 1), ('second', 2), ('third', 3)]
    """

    def __init__(self, *args):
        """
        Initialize the dictionary with a list of (key, value) pairs.
        """
        super().__init__()
        self.sortedKeys = []
        if len(args) == 1 and (
            isinstance(args[0], list)
            or inspect.isgenerator(args[0])
            or (isinstance(args[0], ItemsView))
        ):
            elements = args[0]  # dict / OrderedDict compatibility
        else:
            elements = args
        for key, value in elements:
            self[key] = value

    def keys(self):
        """
        Returns
        -------
        list
            sorted list of keys
        """
        return self.sortedKeys

    def items(self):
        """
        Returns
        -------
        list
            sorted list of (key, value) pairs
        """
        return self.iteritems()

    def values(self):
        """
        Returns
        -------
        values: list
            sorted list of values
        """
        return self.itervalues()

    def __setitem__(self, key, value):
        if key not in self:
            if "sortedKeys" not in self.__dict__:
                # this happens during pickle.load() with python3
                self.sortedKeys = []
            self.sortedKeys.append(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.sortedKeys.remove(key)

    def __getstate__(self):
        return list(self.items())

    def __setstate__(self, state):
        SortedDictionary.__init__(self, *state)

    def __iter__(self):
        """
        returns an iterator over the sorted keys
        """
        return iter(self.sortedKeys)

    def iterkeys(self):
        """
        returns an iterator over the sorted keys
        """
        return iter(self.sortedKeys)

    def itervalues(self):
        """
        returns an iterator over the sorted values
        """
        for k in self:
            yield self[k]

    def iteritems(self):
        """
        returns an iterator over the sorted (key, value) pairs
        """
        for k in self:
            yield (k, self[k])

    def insert(self, index, key, value):
        """
        insert a (key, value) pair in sorted dictionary before position
        ``index``. If ``key`` is already in the dictionary, a KeyError is
        raised.

        Parameters
        ----------
        index: integer
            index of key in the sorted keys
        key: key to insert
            value associated to key
        """
        if key in self:
            raise KeyError(key)
        self.sortedKeys.insert(index, key)
        super().__setitem__(key, value)

    def index(self, key):
        """
        Returns the index of the key in the sorted dictionary, or -1 if this key
        isn't in the dictionary.
        """
        try:
            i = self.sortedKeys.index(key)
        except Exception:
            i = -1
        return i

    def clear(self):
        """
        Remove all items from dictionary
        """
        del self.sortedKeys[:]
        super().clear()

    def sort(self, key=None, reverse=False):
        """Sorts the dictionary using key function key.

        Parameters
        ----------
        key: function key
        """
        self.sortedKeys.sort(key=key, reverse=reverse)

    def compValues(self, key1, key2):
        """
        Use this comparison function in sort method parameter in order to sort
        the dictionary by values.
        if data[key1]<data[key2] return -1
        if data[key1]>data[key2] return 1
        if data[key1]==data[key2] return 0
        """
        e1 = self[key1]
        e2 = self[key2]
        if e1 < e2:
            return -1
        elif e1 > e2:
            return 1
        return 0

    def setdefault(self, key, value=None):
        result = self.get(key, Undefined)
        if result is Undefined:
            self[key] = value
            result = value
        return result

    def pop(self, key, default=Undefined):
        if default is Undefined:
            result = super().pop(key)
        else:
            result = super().pop(key, Undefined)
            if result is Undefined:
                return default
        self.sortedKeys.remove(key)
        return result

    def popitem(self):
        result = super().popitem()
        try:
            self.sortedKeys.remove(result[0])
        except ValueError:
            pass
        return result

    def __repr__(self):
        return (
            "{" + ", ".join(repr(k) + ": " + repr(v) for k, v in self.iteritems()) + "}"
        )

    def update(self, dict_obj):
        for k, v in dict_obj.items():
            self[k] = v

    def copy(self):
        copied = self.__class__()
        copied.update(self)
        return copied
