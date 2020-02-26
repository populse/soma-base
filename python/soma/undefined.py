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
:attr:`Undefined` (or :attr:`undefined`) is a constant that can be used as
a special value different from any other Python value including *None*.

If the :traits:`traits <index.html>` library is available, we just use its
:traits:`Undefined <traits_api_reference/trait_base.html#traits.trait_base.Undefined>` implementation.

Example::

    from soma.undefined import undefined

    if object.value is undefined:
        # do something

* author: Yann Cointepas
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import print_function

from __future__ import absolute_import
__docformat__ = "restructuredtext en"

try:
    # If possible, use _Undefined from traits
    from traits.api import Undefined
    # Undefined is also defined for backward compatibility
    undefined = Undefined
except ImportError:
    undefined = None

if undefined is None:
    # _Undefined cannot be imported from traits, provides an implementation

    from soma.singleton import Singleton

    #-------------------------------------------------------------------------
    class UndefinedClass(Singleton):

        '''
        *UndefinedClass* instance is used to represent an undefined attribute
        value when *None* cannot be used because it can be a valid value.

        Should only be used for value checking.
        '''

        def __repr__(self):
            '''
            Returns
            -------
            ``'<undefined>'``
            '''
            return '<undefined>'

    Undefined = undefined = UndefinedClass()
