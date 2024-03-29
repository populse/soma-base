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
Utility functions for HTML format.

* author: Yann Cointepas
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
'''
from __future__ import absolute_import
__docformat__ = "restructuredtext en"

import six
import sys

#------------------------------------------------------------------------------
#: mapping of characters to be escaped for HTML
_htmlEscape = None
_lesserHtmlEscape = None


# ylep 2020-03-24: now that UTF-8 is everywhere, shouldn't we just replace
# HTML-unsafe characters (&<>"') and leave the rest untouched? (i.e. what the
# standard library function html.escape does in Python 3.2 and later).

def htmlEscape(msg):
    """Replace special characters by their corresponding html entity.

    All characters that have a corresponding named HTML entity are replaced.

    - returns: *unicode*
    """
    global _htmlEscape
    if _htmlEscape is None:
        _htmlEscape = {
            codepoint: u'&' + name + u';'
            for codepoint, name
            in six.iteritems(six.moves.html_entities.codepoint2name)
        }
    if not isinstance(msg, six.string_types):
        # htmlEscape is sometimes used on non-string types (as print) like
        # tuples or dicts
        msg = str(msg)
    msg = six.ensure_text(msg)
    return msg.translate(_htmlEscape)


def lesserHtmlEscape(msg):
    """Replace special characters by their corresponding html entity.

    All characters that have a corresponding named HTML entity are replaced,
    except accented characters commonly used in French text (éàèâêôîûàö) and
    the double-quote character (").

    - returns: *unicode*
    """
    global _lesserHtmlEscape
    if _lesserHtmlEscape is None:
        _lesserHtmlEscape = {
            codepoint: u'&' + name + u';'
            for codepoint, name
            in six.iteritems(six.moves.html_entities.codepoint2name)
            if six.unichr(codepoint) not in (u'"', u'é', u'à', u'è', u'â',
                                             u'ê', u'ô', u'î', u'û', u'ù',
                                             u'ö', )
        }
    msg = six.ensure_text(msg)
    return msg.translate(_lesserHtmlEscape)
