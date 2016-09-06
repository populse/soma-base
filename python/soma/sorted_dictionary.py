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
Sorted dictionary behave like a dictionary but keep the item insertion
order.

* author: Yann Cointepas
* organization: NeuroSpin (http://www.neurospin.org)
* license: CeCILL B (http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html)

In addition OrderedDict is provided here, either as the standard
collections.OrderedDict class if python version >= 2.7, or based on
SortedDictionary if python version < 2.7.
'''
from __future__ import print_function

__docformat__ = "restructuredtext en"

import sys
import six
from soma.undefined import Undefined


class SortedDictionary(dict):

    '''
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
    '''

    def __init__(self, *args):
        '''
        Initialize the dictionary with a list of ( key, value ) pairs.
        '''
        super(SortedDictionary, self).__init__()
        self.sortedKeys = []
        if len(args) == 1 and isinstance(args[0], list):
            elements = args[0]  # dict / OrderedDict compatibility
        else:
            elements = args
        for key, value in elements:
            self[key] = value

    def keys(self):
        '''
        Returns
        -------
        list
            sorted list of keys
        '''
        return self.sortedKeys

    def items(self):
        '''
        Returns
        -------
        list
            sorted list of (key, value) pairs
        '''
        if sys.version_info[0] >= 3:
            return self.iteritems()
        else:
            return [x for x in self.iteritems()]

    def values(self):
        '''
        Returns
        -------
        values: list
            sorted list of values
        '''
        return [x for x in self.itervalues()]

    def __setitem__(self, key, value):
        if key not in self:
            self.sortedKeys.append(key)
        super(SortedDictionary, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(SortedDictionary, self).__delitem__(key)
        self.sortedKeys.remove(key)

    def __getstate__(self):
        return self.items()

    def __setstate__(self, state):
        SortedDictionary.__init__(self, *state)

    def __iter__(self):
        '''
        returns an iterator over the sorted keys
        '''
        return iter(self.sortedKeys)

    def iterkeys(self):
        '''
        returns an iterator over the sorted keys
        '''
        return iter(self.sortedKeys)

    def itervalues(self):
        '''
        returns an iterator over the sorted values
        '''
        for k in self:
            yield self[k]

    def iteritems(self):
        '''
        returns an iterator over the sorted (key, value) pairs
        '''
        for k in self:
            try:
                yield (k, self[k])
            except KeyError:
                print('!SortedDictionary error!', self.keys(), self.sortedKeys)
                raise

    def insert(self, index, key, value):
        '''
        insert a (key, value) pair in sorted dictionary before position
        ``index``. If ``key`` is already in the dictionary, a KeyError is
        raised.

        Parameters
        ----------
        index: integer
            index of key in the sorted keys
        key: key to insert
            value associated to key
        '''
        if key in self:
            raise KeyError(key)
        self.sortedKeys.insert(index, key)
        super(SortedDictionary, self).__setitem__(key, value)

    def index(self, key):
        """
        Returns the index of the key in the sorted dictionary, or -1 if this key
        isn't in the dictionary.
        """
        try:
            i = self.sortedKeys.index(key)
        except:
            i = -1
        return i

    def clear(self):
        '''
        Remove all items from dictionary
        '''
        del self.sortedKeys[:]
        super(SortedDictionary, self).clear()

    def sort(self, key=None, reverse=False):
        """Sorts the dictionary using key function key.

        Parameters:
        -----------
        key: function key
        """
        self.sortedKeys.sort(key=key, reverse=reverse)

    def compValues(self, key1, key2):
        """
        Use this comparaison function in sort method parameter in order to sort
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
            result = super(SortedDictionary, self).pop(key)
        else:
            result = super(SortedDictionary, self).pop(key, Undefined)
            if result is Undefined:
                return default
        self.sortedKeys.remove(key)
        return result

    def popitem(self):
        result = super(SortedDictionary, self).popitem()
        try:
            self.sortedKeys.remove(result[0])
        except ValueError:
            pass
        return result

    def __repr__(self):
        return '{' + ', '.join(repr(k) + ': ' + repr(v)
                               for k, v in self.iteritems()) + '}'

    def update(self, dict_obj):
        for k, v in six.iteritems(dict_obj):
            self[k] = v

    def copy(self):
        copied = self.__class__()
        copied.update(self)
        return copied


if sys.version_info[0:2] >= (2, 7):
    # with python >= 2.7, use the standard collections.OrderedDict

    from collections import OrderedDict

else:

    class OrderedDict(SortedDictionary):

        '''
        OrderedDict is fully compatible with Python 2.7 collections.OrderedDict.
        It is a SordedDictionary with a modified constructor API.
        '''

        def __init__(self, args=()):
            super(OrderedDict, self).__init__(*args)
