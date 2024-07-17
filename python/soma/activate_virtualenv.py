"""Importation of this module activate a
`virtualenv <https://virtualenv.pypa.io/>`_ if
``os.environ['SOMA_VIRTUALENV']`` contains the directory path of the
*virtualenv*.

This module makes it possible to use a specific *virtualenv* directory in
contexts where it is difficult activate it (for instance in crontab). For
instance, a script importing cubicweb the following way::

    from soma import activate_virtualenv
    import cubicweb

can be set to use a specific *virtualenv* install of *cubicweb*:

.. code-block:: bash

    env SOMA_VIRTUALENV=/path/to/virtualenv python /path/to/script.py
"""

import os

import soma.importer

venv = os.environ.get("SOMA_VIRTUALENV")
if venv:
    activate = os.path.join(venv, "bin", "activate_this.py")
    if os.path.exists(activate):
        # This is the way to activate a virtualenv from Python
        soma.importer.execfile(activate, dict(__file__=activate))
    del activate
