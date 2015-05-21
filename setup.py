#! /usr/bin/env python

from ez_setup import use_setuptools
use_setuptools()

import os
from setuptools import setup, find_packages
from datetime import datetime

python_dir = os.path.join(os.path.dirname(__file__), "python")
release_info = {}
execfile(os.path.join(python_dir, "soma", "info.py"), release_info)

setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    package_dir = {'': python_dir},
    packages=find_packages(python_dir),
    platforms=release_info["PLATFORMS"],
    #scripts=["../../bin/bv_minf_2_XML", ]
)
