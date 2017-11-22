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

'''Utility functions to make a weak proxy which also keeps an access to its original object reference. weakref.proxy() doesn't allow this, but functions that check types (C+/Python biudings for instance) cannot work with proxies.

We build such a proxy by setting a weakref.ref() object in the proxy (actually in the object itself).
'''

import weakref

def get_ref(obj):
    ''' Get a regular reference to an object, whether it is already a regular
    reference, a weak reference, or a weak proxy which holds an access to the
    original reference (built using weak_proxy())
    '''
    if isinstance(obj, weakref.ReferenceType):
        return obj()
    elif isinstance(obj, weakref.ProxyType) and hasattr(obj, '_weakref'):
        return obj._weakref()
    return obj


def weak_proxy(obj):
    ''' Build a weak proxy (weakref.proxy) from an object, if it is not already
    one, and keep a reference to the original object (via a weakref.ref) in it.
    '''
    if isinstance(obj, weakref.ProxyType):
        return obj
    real_obj = get_ref(obj)
    wr = weakref.proxy(real_obj)
    wr._weakref = weakref.ref(real_obj)
    return wr

