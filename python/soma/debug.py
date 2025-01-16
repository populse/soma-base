"""
Utility classes and functions for debugging.
"""

__docformat__ = "restructuredtext en"

import sys
from pprint import pprint

from soma.undefined import Undefined


def function_call_info(frame=None):
    """
    Return a dictionary that gives information about a frame corresponding to a function call.
    The directory contains the following items:

    - 'function': name of the function called
    - 'filename': name of the python file containing the function
    - 'lineno': line number executed in 'filename'
    - 'arguments': arguments passed to the function. It is a list containing
      pairs of (argument name, argument value).
    """
    try:
        if frame is None:
            frame = sys._getframe(1)
        result = {
            "function": frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "filename": frame.f_code.co_filename,
        }
        args = frame.f_code.co_varnames[: frame.f_code.co_argcount]
        result["arguments"] = [
            (p, frame.f_locals.get(p, frame.f_globals.get(p, Undefined))) for p in args
        ]
    finally:
        del frame
    return result


def stack_calls_info(frame=None):
    """
    Return a list containing function_call_info(frame) for all frame in the stack.
    """
    try:
        if frame is None:
            frame = sys._getframe(1)
        result = []
        while frame is not None:
            result.insert(0, function_call_info(frame))
            frame = frame.f_back
        return result
    finally:
        del frame


def print_stack(out=sys.stdout, frame=None):
    """
    Print information about the stack, including argument passed to functions called.
    """
    try:
        if frame is None:
            frame = sys._getframe(1)
        for info in stack_calls_info(frame):
            print(
                'File "{filename}", line {lineno} in {function}'.format(**info),
                file=out,
            )
            for name, value in info["arguments"]:
                out.write("   " + name + " = ")
                pprint(value, out, 3)
        out.flush()
    finally:
        del frame
