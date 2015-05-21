##########################################################################
# Soma-base - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

'''Importation of this module activate a virtualenv if 
os.environ['SOMA_VIRTUALENV'] contains the directory path of the virutalenv.
This module makes it possible to use a specific virtualenv directory in
contexts where it is difficult activate it (for instance in crontab). For
instance, a script importing cubicweb the following way :

from soma import activate_virtualenv
import cubicweb

can be set to use a specifiv virutalenv install of cubicweb:

env SOMA_VIRTUALENV=/path/to/virutalenv python /path/to/script.py
'''

import os

venv = os.environ.get('SOMA_VIRTUALENV')
if venv:
    activate = os.path.join(venv, 'bin', 'activate_this.py')
    if os.path.exists(activate):
        # This is the way to activate a virtualenv from Python
        execfile(activate, dict(__file__=activate))
    del activate
