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
Env variables parsing tools
"""


def parse_env_lines(text, asdict=False):
    """Separate text (generally the output of the ``env`` command) into multi-
    line elements, avoiding separations inside () or {} blocks.

    If ``asdict`` is ``True``, then the result is returned as a dict
    ``{variable: value}`` (see :func:`env_to_dict`)
    """

    def push(obj, l, depth, tags, start_tag=None):
        while depth:
            l = l[-1]
            tags = tags[-1]
            depth -= 1

        if start_tag:
            tags.append([start_tag, []])
        if isinstance(obj, str):
            if len(l) == 0 or isinstance(l[-1], list):
                l.append(obj)
            else:
                l[-1] += obj
        else:
            l.append(obj)

    def current_tag(tags, depth):
        while depth:
            tags = tags[-1]
            depth -= 1
        return tags[0]

    def parse_parentheses(s):
        rev_char = {"(": ")", "{": "}", '"': '"', "'": "'"}  #'[': ']',
        groups = []
        tags = [None, []]
        depth = 0
        escape = None

        try:
            for char in s:
                if s == "\\":
                    escape = not escape
                    if escape:
                        push(char, groups, depth, tags)

                if char == rev_char.get(current_tag(tags, depth)):
                    # close tag (counterpart of the tag)
                    push(char, groups, depth, tags)
                    depth -= 1

                elif char in rev_char:
                    # open/start tag
                    push([char], groups, depth, tags, char)
                    depth += 1

                else:
                    push(char, groups, depth, tags)

        except IndexError as e:
            raise ValueError("Parentheses mismatch", depth, groups) from e
        if depth > 0:
            raise ValueError("Parentheses mismatch 2", depth, groups) from e
        else:
            return groups

    def rebuild_lines(parsed, breaks=True):
        lines = []
        for item in parsed:
            if isinstance(item, str):
                if breaks:
                    newlines = item.split("\n")
                else:
                    newlines = [item]
            else:
                newlines = rebuild_lines(item, breaks=False)
            if lines:
                lines[-1] += newlines[0]
                lines += newlines[1:]
            else:
                lines = newlines
        return lines

    lines = rebuild_lines(parse_parentheses(text))
    if asdict:
        lines = env_to_dict(lines)

    return lines


def env_to_dict(lines):
    """Separate each text line in the lines list into variable: value.
    Each line is expected to be in the shape ``VAR=value``, as expected from
    the output of the ``env`` command, parsed by the :func:`parse_env_lines`
    function. Note that :func:`parse_env_lines` with the option ``asdict=True``
    will already call this function.
    """
    denv = {}
    for line in lines:
        var, value = line.split("=", 1)
        denv[var.strip()] = value.strip()

    return denv
