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

"""
This module contains text related functions.

* author: Yann Cointepas
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
"""

__docformat__ = "restructuredtext en"


def string_to_list(s):
    """ """
    s = s.strip(" ")
    while s:
        if s[0] == '"':
            i = 1
            while True:
                j = s[i:].find('"')
                if j == -1:
                    # Syntax error, missing closing quote.
                    # return the rest of the string and exit
                    yield s[1:]
                    return
                if s[i + j - 1] == "\\":
                    i = i + j + 1
                else:
                    break
            yield s[1 : i + j]
            s = s[i + j + 2 :].strip(" ")
        else:
            s_list = s.split(" ", 1)
            yield s_list[0]
            if len(s_list) > 1:
                s = s_list[1].strip(" ")
            else:
                s = ""


def list_to_string(s_list):
    """ """
    return " ".join(quote_string(s) for s in s_list)


def quote_string(unquoted):
    """ """
    if unquoted:
        if unquoted.find(" ") > -1:
            return '"' + unquoted.replace('"', '\\"') + '"'
        else:
            return unquoted
    return ""


def unquote_string(quoted):
    """ """
    if quoted and quoted[0] == '"':
        if quoted[-1] == '"':
            quoted = quoted[1:-1]
        else:
            # There is a syntax error here, quoted should
            # be terminated by a double quote
            quoted = quoted[1:]
        return eval('r"' + quoted + '"').replace('\\"', '"')
    else:
        return quoted
