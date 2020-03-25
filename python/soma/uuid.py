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
Universal unique identifier.

- author: Yann Cointepas
- organization: NeuroSpin
- license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import
import six
__docformat__ = "epytext en"

import struct
import random
import binascii
import sys

#-------------------------------------------------------------------------


class Uuid(object):

    '''
    An Uuid instance is a universal unique identifier. It is a 128 bits
    random value.
    '''
    def __new__(cls, value=None):
        if isinstance(value, Uuid):
            return value
        return object.__new__(cls)

    def __init__(self, uuid=None):
        '''
        Uuid constructor. If *uuid* is ommited or *None*, a new random
        Uuid is created; if it is a string if must be 36 characters long and
        follow the pattern::

            XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

        where ``X`` is an
        hexadecimal digit (example:
        ``'ad2d8fb0-7831-50bc-2fb6-5df048304001'``).

        If *uuid* is an Uuid instance, no new instance is created, in this
        case, *Uuid(uuid)* returns *uuid*.
        '''
        if isinstance(uuid, Uuid):
            return
        if uuid is None:
            # Generate a new 128 bits uuid
            self.__uuid = struct.pack('QQ', random.randrange(2 ** 64 - 1),
                                      random.randrange(2 ** 64 - 1))
        else:
            try:
                uuid = six.ensure_binary(uuid, encoding='ascii')
                self.__uuid = binascii.unhexlify(uuid[0:8] + uuid[9:13] +
                                                 uuid[14:18] + uuid[19:23] +
                                                 uuid[24:36])
            except Exception:
                raise ValueError("Invalid uuid string %s" % (repr(uuid), ))

    def __getnewargs__(self):
        return (str(self), )

    def __str__(self):
        if not isinstance(self.__uuid, bytes):
            # this should not happen, but has been seen in some places
            import warnings
            warnings.warn('soma.uuid.Uuid: self.__uuid is not of type bytes, '
                          'but {0}. This is not supposed to happen.'
                          .format(type(self.__uuid)))
            self.__uuid = bytes(self.__uuid, encoding='utf-8')
        return six.ensure_str(
            binascii.hexlify(self.__uuid[0:4]) + b'-' +
            binascii.hexlify(self.__uuid[4:6]) + b'-' +
            binascii.hexlify(self.__uuid[6:8]) + b'-' +
            binascii.hexlify(self.__uuid[8:10]) + b'-' +
            binascii.hexlify(self.__uuid[10:16])
        )

    def __repr__(self):
        return repr(str(self))

    def __hash__(self):
        return hash(self.__uuid)

    def __eq__(self, other):
        if isinstance(other, Uuid):
            return self.__uuid == other.__uuid
        elif isinstance(other, six.string_types):  # assume string-like object (str or unicode)
            try:
                uuid_other = Uuid(other)
            except ValueError:
                return False
            return self.__uuid == uuid_other.__uuid
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, Uuid):
            return self.__uuid != other.__uuid
        elif isinstance(other, six.string_types):  # assume string-like object (str or unicode)
            try:
                uuid_other = Uuid(other)
            except ValueError:
                return True
            return self.__uuid != uuid_other.__uuid
        else:
            return True
