#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

import os
import shutil


def ensure_is_dir(d, clear_dir=False):
    """ If the directory doesn't exist, use os.makedirs """
    if not os.path.exists(d):
        os.makedirs(d)
    elif clear_dir:
        shutil.rmtree(d)
        os.makedirs(d)