#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

_version_major = 0
_version_minor = 0
_version_micro = 1
_version_extra = '.dev'

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = "%s.%s.%s%s" % (_version_major,
                              _version_minor,
                              _version_micro,
                              _version_extra)
CLASSIFIERS = ["Development Status :: 1 - Planning",
               "Environment :: Console",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering",
               "Topic :: Utilities"]

description = 'CASPER'

long_description = """
========
SOMA 
========

[soma] CollAborative System for Platform Engineering and Reasearch.
SOMA pipeline offers a catalogue of tools mastered by the platform team.
"""

# versions for dependencies
SPHINX_MIN_VERSION = 1.0
NIBABEL_MIN_VERSION = '1.3.0'
NUMPY_MIN_VERSION = '1.3'
SCIPY_MIN_VERSION = '0.7.2'
PYDICOM_MIN_VERSION = '0.9.7'
NIPYPE_VERSION = '0.8.0'
MATPLOTLIB_MIN_VERSION = '1.1.1rc'

# Main setup parameters
NAME = 'soma'
ORGANISATION = "CEA"
MAINTAINER = "Antoine Grigis"
MAINTAINER_EMAIL = "antoine.grigis@cea.fr"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = ""
DOWNLOAD_URL = ""
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "CASPER developers"
AUTHOR_EMAIL = "antoine.grigis@cea.fr"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
ISRELEASE = _version_extra == ''
VERSION = __version__
PROVIDES = ["soma"]
REQUIRES = ["numpy>={0}".format(NUMPY_MIN_VERSION),
            "scipy>={0}".format(SCIPY_MIN_VERSION),
            "matplotlib>={0}".format(MATPLOTLIB_MIN_VERSION),
            "pydicom>={0}".format(PYDICOM_MIN_VERSION),
            "nibabel>={0}".format(NIBABEL_MIN_VERSION),
            "nipype=={0}".format(NIPYPE_VERSION)]
EXTRA_REQUIRES = {"doc": ["sphinx>=1.0"]}
