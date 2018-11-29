
from __future__ import print_function

import unittest
import os
import sys
from soma import singleton
# import modules even when they are not tested, just to mark them as
# not tested in coverage tests
from soma import api
from soma import activate_virtualenv
from soma import application
from soma import archive
from soma import bufferandfile
from soma import config
from soma import controller
try:
    from soma import crypt
except ImportError:
    pass # Crypto (pycrypto package) missing
from soma import debug
from soma import factory
from soma import fom
from soma import functiontools
from soma import global_naming
from soma import html
try:
    from soma import qimage2ndarray
    from soma import qt_gui
    from soma import icon_factory
except ImportError:
    pass # PyQt not installed
from soma import importer
from soma import info
from soma import logging
from soma import minf
from soma import notification
from soma import path
from soma import pipeline
from soma import plugins
try:
    from soma import pyro
except ImportError:
    pass # Pyro not installed
from soma import safemkdir
from soma import sandbox
from soma import serialization
from soma import somatime
from soma import sorted_dictionary
from soma import sqlite_tools
from soma import stringtools
from soma import subprocess
from soma import test_utils
from soma import thread_calls
from soma import topological_sort
from soma import translation
from soma import undefined
from soma import utils
from soma import uuid


class TestSomaMisc(unittest.TestCase):

    def test_singleton(self):
        class ASingleton(singleton.Singleton):
            def __singleton_init__(self):
                super(ASingleton, self).__singleton_init__()
                self._shared_num = 12

        self.assertRaises(ValueError, ASingleton.get_instance)
        sing = ASingleton()
        self.assertTrue(sing is ASingleton())
        self.assertTrue(hasattr(sing, '_shared_num'))
        self.assertEqual(sing._shared_num, 12)


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSomaMisc)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
