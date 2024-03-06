"""
Utility functions for HTML format.
"""

__docformat__ = "restructuredtext en"

from html.entities import codepoint2name

# ------------------------------------------------------------------------------
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
            codepoint: "&" + name + ";" for codepoint, name in codepoint2name.items()
        }
    if not isinstance(msg, str):
        # htmlEscape is sometimes used on non-string types (as print) like
        # tuples or dicts
        msg = str(msg)
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
            codepoint: "&" + name + ";"
            for codepoint, name in codepoint2name.items()
            if chr(codepoint)
            not in (
                '"',
                "é",
                "à",
                "è",
                "â",
                "ê",
                "ô",
                "î",
                "û",
                "ù",
                "ö",
            )
        }
    msg = str(msg)
    return msg.translate(_lesserHtmlEscape)
