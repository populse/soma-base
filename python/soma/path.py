"""
Some useful functions to manage file or directorie names.
"""

__docformat__ = "restructuredtext en"

import fnmatch
import glob
import hashlib
import os
import re
import shutil


def split_path(path):
    """
    Iteratively apply :func:`os.path.split` to build a list. Ignore trailing directory separator.

    Examples
    --------
    ::

        split_path('/home/myaccount/data/file.csv') returns ['/', 'home', 'myaccount', 'data', 'file.csv']
        split_path('home/myaccount/data/file.csv') returns ['home', 'myaccount', 'data', 'file.csv']
        split_path('/home/myaccount/data/') returns ['/', 'home', 'myaccount', 'data']
        split_path('/home/myaccount/data') returns ['/', 'home', 'myaccount', 'data']
        split_path('') returns ['']
    """
    result = []
    a, b = os.path.split(path)
    if not b:
        a, b = os.path.split(a)
    while a and b:
        result.insert(0, b)
        a, b = os.path.split(a)
    if a:
        result.insert(0, a)
    else:
        result.insert(0, b)
    return result


def relative_path(path, referenceDirectory):
    """
    Return a relative version of a path given a
    reference directory.

    ::

        os.path.join(referenceDirectory, relative_path(path, referenceDirectory))
        returns os.path.abspath(pat)

    Example
    =======
    ::

        relative_path('/usr/local/brainvisa-3.1/bin/brainvisa', '/usr/local')
        returns 'brainvisa-3.1/bin/brainvisa'

        relative_path('/usr/local/brainvisa-3.1/bin/brainvisa', '/usr/local/bin')
        returns '../brainvisa-3.1/bin/brainvisa'

        relative_path('/usr/local/brainvisa-3.1/bin/brainvisa', '/tmp/test/brainvisa')
        returns '../../../usr/local/brainvisa-3.1/bin/brainvisa'
    """
    sPath = split_path(os.path.abspath(path))
    sReferencePath = split_path(os.path.abspath(referenceDirectory))
    i = 0
    while i < len(sPath) and i < len(sReferencePath) and sPath[i] == sReferencePath[i]:
        i += 1
    plist = ([".."] * (len(sReferencePath) - i)) + sPath[i:]
    if len(plist) == 0:
        return ""
    return os.path.join(*plist)


query_string_re = re.compile(r"\?([^\?\&]+\=[^\&]*)(\&[^\?\&]+\=[^\&]*)*$")


def split_query_string(path):
    """
    Split a path and its query string.

    Example
    =======
    A path containing a query string is::

        /dir1/file1?param1=val1&param2=val2&paramN=valN

    ::

        split_query_string( '/dir1/file1?param1=val1&param2=val2&paramN=valN' )

    would return::

        ('/dir1/file1', '?param1=val1&param2=val2&paramN=valN')

    """
    m = query_string_re.search(path)
    if m is not None:
        return (path[0 : m.start()], path[m.start() :])

    else:
        return (path, "")


def remove_query_string(path):
    """
    Remove the query string from a path.

    Example
    =======
    A path containing a query string is::

        /dir1/file1?param1=val1&param2=val2&paramN=valN

    ::

        remove_query_string( '/dir1/file1?param1=val1&param2=val2&paramN=valN' )

    would return::

        '/dir1/file1'

    """
    return query_string_re.sub("", path)


def strict_urlparse(path):
    """
    A "fixed" version of urlparse.urlparse() which preserves the case of the
    drive letter in windows paths. The standard urlparse changes 'Z:/some/path'
    to 'z:/some/path'
    """
    from urllib import parse as urlparse

    url_parsed = urlparse.urlparse(path)
    if (
        len(url_parsed.scheme) == 1
        and url_parsed.scheme >= "a"
        and url_parsed.scheme <= "z"
        and path[1] == ":"
        and path[0] == url_parsed.scheme.upper()
    ):
        url_parsed = type(url_parsed)(
            scheme=url_parsed.scheme.upper(),
            netloc=url_parsed.netloc,
            path=url_parsed.path,
            params=url_parsed.params,
            query=url_parsed.query,
            fragment=url_parsed.fragment,
        )
    return url_parsed


def parse_query_string(path):
    """
    Parses the query string from a path and returns a dictionary.

    Example
    =======
    """
    from urllib import parse as urlparse

    url_parsed = urlparse.urlparse(path)
    qs_parsed = urlparse.parse_qs(url_parsed.query)

    return dict(
        [
            (k, v[0]) if isinstance(v, list) and len(v) == 1 else (k, v)
            for k, v in qs_parsed.items()
        ]
    )


class QueryStringParamUpdateMode:
    REPLACE = 0
    APPEND = 1
    REMOVE = 2


def update_query_string(
    path, params, params_update_mode=QueryStringParamUpdateMode.REPLACE
):
    """
    Update the query string parameters in a path.

    Parameters
    ----------
    path: string
          The path to update parameters within.

    params: dict|list
          A dictionary that contains keys and parameters to set in the query
          string

    params_update_mode: dict|string|list|int
          The default value is QueryStringParamUpdateMode.REPLACE that lead to
          replace value in the query string path by the one given in the params
          dictionary.

          It is possible to change the default behaviour giving the value
          QueryStringParamUpdateMode.APPEND. This will lead to always append
          values of the params dictionary to values of the query string path.
          The default behaviour can also be changed by specifying a parameter
          name as string, in this case only values for that parameter name will
          be appended. It can also contains a list or a tuple of parameter names
          for which values will be appended.

          Finally, this parameter can be a dictionary that specifies which
          parameter has to be appended or replaced. The dictionary contains
          parameter names in its keys and QueryStringParamUpdateMode in values.

    Returns
    -------
    path: string
          The path updated with given parameters

    Example
    -------
    A path containing a query string is::

        /dir1/file1?param1=val1&param2=val2&paramN=valN

    the params dictionary contains::

        {'param1':'newval1', param2=newval2', param3':'newval3'}

    ::

        update_query_string('/dir1/file1?param1=val1&param2=val2&paramN=valN',
                            {'param1':'newval1', 'param2':'newval2', 'param3':'newval3'})

    would return::

        '/dir1/file1?param1=newval1&param2=newval2&paramN=valN&param3=newval3'

    ::

        update_query_string('/dir1/file1?param1=val1&param2=val2&paramN=valN',
                            {'param1':'newval1', 'param2':'newval2', 'param3':'newval3'},
                            QueryStringParamUpdateMode.APPEND)

    would return::

        '/dir1/file1?param1=val1&param1=newval1&param2=val2&param2=newval2&paramN=valN&param3=newval3'

    ::

        update_query_string('/dir1/file1?param1=val1&param2=val2&paramN=valN',
                            {'param1':'newval1', 'param2':'newval2', 'param3':'newval3'},
                            'param2')

    would return::

        '/dir1/file1?param1=newval1&param2=val2&param2=newval2&paramN=valN&param3=newval3'

    ::

        update_query_string('/dir1/file1?param1=val1&param2=val2&paramN=valN',
                            {'param1':'newval1', 'param2':'newval2', 'param3':'newval3'},
                            ('param1', 'param2'))

    would return::

        '/dir1/file1?param1=val1&param1=newval1&param2=val2&param2=newval2&paramN=valN&param3=newval3'

    ::

        update_query_string('/dir1/file1?param1=val1&param2=val2&paramN=valN',
                            {'param1':'newval1', 'param2':'newval2', 'param3':'newval3'},
                            {'param1': QueryStringParamUpdateMode.APPEND,
                            'param2': QueryStringParamUpdateMode.REPLACE})

    would return::

        '/dir1/file1?param1=val1&param1=newval1&param2=val2&param2=newval2&paramN=valN&param3=newval3'
    """
    from urllib import parse as urllib

    urlparse = urllib

    # Convert params_update_mode to a dictionary that contains the update mode
    # for each parameter
    if type(params_update_mode) in (list, tuple):
        # Update mode is specified using a list of parameter names
        default_update_mode = QueryStringParamUpdateMode.REPLACE
        params_update = params_update_mode
        params_update_mode = dict()

        for p in params_update:
            if type(p) in (list, tuple):
                if len(p) > 1:
                    params_update_mode[p[0]] = p[1]
                elif len(p) > 0:
                    params_update_mode[p[0]] = QueryStringParamUpdateMode.APPEND
            else:
                params_update_mode[p] = QueryStringParamUpdateMode.APPEND

    elif isinstance(params_update_mode, str):
        # A parameter name was given directly
        default_update_mode = QueryStringParamUpdateMode.REPLACE
        params_update_mode = dict(
            ((params_update_mode, QueryStringParamUpdateMode.APPEND),)
        )

    elif params_update_mode in (
        QueryStringParamUpdateMode.APPEND,
        QueryStringParamUpdateMode.REPLACE,
        QueryStringParamUpdateMode.REMOVE,
    ):
        # Update mode was specified for all parameters
        default_update_mode = params_update_mode
        params_update_mode = dict()

    elif isinstance(params_update_mode, dict):
        default_update_mode = QueryStringParamUpdateMode.REPLACE

    else:
        raise RuntimeError(
            "params_update_mode is not specified correctly. "
            "It must be either a dictionary that contains parameter names "
            "and the corresponding QueryStringParamUpdateMode, "
            "either a list that contains parameter names, either"
            "QueryStringParamUpdateMode."
        )

    url_parsed = strict_urlparse(path)
    url_params = urlparse.parse_qs(url_parsed.query)

    if isinstance(params, (list, tuple)):
        params = dict([(p, "") for p in params])

    # Update parameters dictionary
    for p, v in params.items():
        update_mode = params_update_mode.get(p, default_update_mode)

        if update_mode == QueryStringParamUpdateMode.REPLACE:
            url_params[p] = v

        elif update_mode == QueryStringParamUpdateMode.APPEND:
            if type(v) in (list, tuple):
                if type(v) is tuple:
                    url_params[p] += list(v)
                else:
                    url_params[p] += v

            else:
                url_params.setdefault(p, list()).append(v)

        elif update_mode == QueryStringParamUpdateMode.REMOVE:
            del url_params[p]

        else:
            raise RuntimeError(
                f"params_update_mode is not specified correctly. {v} is "
                f"not a valid value for parameter {p}. Valid values are "
                "either QueryStringParamUpdateMode.APPEND or"
                "QueryStringParamUpdateMode.REPLACE."
            )

    url_new = list(url_parsed)
    url_new[4] = urllib.urlencode(url_params, doseq=True)

    return urlparse.urlunparse(url_new)


def find_in_path(file, path=None):
    """
    Look for a file in a series of directories. By default, directories are
    contained in ``PATH`` environment variable. But another environment
    variable name or a sequence of directories names can be given in *path*
    parameter.

    Examples::

      find_in_path('sh') could return '/bin/sh'
      find_in_path('libpython3.10.so', 'LD_LIBRARY_PATH') could return '/usr/lib/x86_64-linux-gnu/libpython3.10.so'
    """
    if path is None:
        path = os.environ.get("PATH").split(os.pathsep)
    elif isinstance(path, str):
        var = os.environ.get(path)
        if var is None:
            var = path
        path = var.split(os.pathsep)
    for i in path:
        p = os.path.normpath(os.path.abspath(i))
        if p:
            r = glob.glob(os.path.join(p, file))
            if r:
                return r[0]


def locate_file(pattern, root=os.curdir):
    """
    Locates a file in a directory tree

    :param string pattern:
        The pattern to find

    :param string root:
        The search root directory

    :returns:
        The first found occurrence
    """
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            return os.path.join(path, filename)


def update_hash_from_directory(directory, hash):
    """
    Update a hash object from the content of a directory. The hash will
    reflect the recursive content of all files as well as the paths in all
    directories.
    """
    for root, dirs, files in sorted(os.walk(directory)):
        for file in sorted(files):
            hash.update(file.encode("utf-8"))
            hash.update(open(os.path.join(root, file), "rb").read())
        for dir in sorted(dirs):
            hash.update(dir.encode("utf-8"))
            update_hash_from_directory(os.path.join(root, dir), hash)


def path_hash(path, hash=None):
    """
    Return a hash hexdigest for a file or a directory.
    """
    if hash is None:
        hash = hashlib.md5()
    if os.path.isdir(path):
        update_hash_from_directory(path, hash)
    else:
        hash.update(open(path, "rb").read())
    return hash.hexdigest()


def ensure_is_dir(d, clear_dir=False):
    """If the directory doesn't exist, use os.makedirs"""
    if not os.path.exists(d):
        os.makedirs(d)
    elif clear_dir:
        shutil.rmtree(d)
        os.makedirs(d)
