"""replacement for :func:`ctypes.util.find_library`.
Provides a better version of :func:`find_library`, and allows to patch the
:mod:`ctypes` module to use our version: see :func:`patch_ctypes_find_library`.
"""

import ctypes.util
import glob
import os
import sys

ctypes_find_library = ctypes.util.find_library


def find_library(name):
    """:func:`ctypes.util.find_library` is broken on linux at least: it relies
    on ``ldconfig``, which only searches system paths, not user paths nor
    ``LD_LIBRARY_PATH``, or alternatively uses ``gcc``, which is not always
    installed nor configured.

    Here we are looking in ``[[DY]LD_LIBRARY_]PATH`` (depending on the system)
    """

    def sorted_match(filenames):
        return sorted(filenames)[-1]  # probably not the best

    exts = [".so"]
    patterns = [ext + ".*" for ext in exts]
    fname = "lib" + name
    if sys.platform.startswith("linux"):
        envar = "LD_LIBRARY_PATH"
    elif sys.platform == "darwin":
        envar = "DYLD_LIBRARY_PATH"
        exts = [".dylib"]
        patterns = [".*" + ext for ext in exts]
    elif sys.platform.startswith("win"):
        envar = "PATH"
        exts = [".dll", ".DLL"]
        patterns = [".*" + ext for ext in exts]
    else:
        # other undetermined system (BSD, other unix...?), assume ELF
        envar = "LD_LIBRARY_PATH"
    paths = os.environ.get(envar)
    if paths is None:
        # no path: fallback to ctypes
        return ctypes_find_library(name)

    paths = paths.split(os.pathsep)
    names = [fname + ext for ext in exts] + [name + ext for ext in exts]
    patterns = [fname + pattern for pattern in patterns] + [
        name + pattern for pattern in patterns
    ]
    found = None
    for path in paths:
        for tname in names:
            filename = os.path.join(path, tname)
            if os.path.exists(filename):
                found = filename
                break
        for tname in patterns:
            filenames = glob.glob(os.path.join(path, tname))
            if len(filenames) != 0:
                found = sorted_match(filenames)
                break

    if found is not None:
        return os.path.basename(os.path.realpath(found))

    # not found: fallback to ctypes
    return ctypes_find_library(name)


def patch_ctypes_find_library():
    """replace :func:`ctypes.util.find_library` by our version"""
    if ctypes.util.find_library is ctypes_find_library:
        ctypes.util.find_library = find_library
