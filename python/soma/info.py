"""Information module, containing version variables, plus some
setuptools-related variables
Attributes
----------
version_major
version_minor
version_micro
version_extra
"""

version_major = 6
version_minor = 0
version_micro = 0
version_extra = ""
_version_major = version_major
_version_minor = version_minor
_version_micro = version_micro
_version_extra = version_extra

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = f"{version_major}.{version_minor}.{version_micro}{version_extra}"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering",
    "Topic :: Utilities",
]

description = "soma-base"

long_description = """
=========
SOMA-BASE
=========

Miscellaneous all-purpose classes and functions in Python.

"""

# versions for dependencies
SPHINX_MIN_VERSION = "1.0"

# Main setup parameters
NAME = "soma-base"
PROJECT = "soma"
ORGANISATION = "CEA"
MAINTAINER = "CEA"
MAINTAINER_EMAIL = ""
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = ""
DOWNLOAD_URL = ""
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "CEA"
AUTHOR_EMAIL = ""
PLATFORMS = "OS Independent"
ISRELEASE = version_extra == ""
VERSION = __version__
PROVIDES = ["soma-base"]
REQUIRES = [
    "pydantic <2",
]
PYTHON_REQUIRES = ">=3.9"
EXTRAS_REQUIRE = {
    "doc": ["sphinx >=%s" % SPHINX_MIN_VERSION],
    "crypto": ["pycrypto"],
    "test_utils": ["argparse"],
}
