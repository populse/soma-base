
from __future__ import print_function

import unittest
import os
import sys
import tempfile
import shutil
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
    have_crypt = True
except ImportError:
    # Crypto (pycrypto package) missing
    have_crypt = False
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


if sys.version_info[0] < 3:
    bytes = str

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

    if have_crypt:
        def test_crypt(self):
            private_key, public_key = crypt.generate_RSA()
            self.assertTrue(isinstance(private_key, bytes))
            self.assertTrue(isinstance(public_key, bytes))
            d = tempfile.mkdtemp()
            try:
                pubfile = os.path.join(d, 'id_rsa.pub')
                privfile = os.path.join(d, 'id_rsa')
                open(pubfile, 'wb').write(public_key)
                open(privfile, 'wb').write(private_key)

                msg = u'I write a super secret message that nobody should '\
                    'see, never.'.encode('utf-8')
                crypt_msg = crypt.encrypt_RSA(pubfile, msg)
                self.assertTrue(crypt_msg != msg)
                uncrypt_msg = crypt.decrypt_RSA(privfile, crypt_msg)
                self.assertEqual(uncrypt_msg, msg)
            finally:
                shutil.rmtree(d)

    def test_partial(self):
        def my_func(x, y, z, t, **kwargs):
            res = x + y + z + t
            if 'suffix' in kwargs:
                res += kwargs['suffix']
            return res

        p = functiontools.SomaPartial(my_func, 12, 15)
        self.assertEqual(p(10, 20), 57)
        q = functiontools.SomaPartial(my_func, 'start_', t='_t', suffix='_end')
        self.assertEqual(q('ab', z='ba'), 'start_abba_t_end')
        self.assertTrue(functiontools.hasParameter(my_func, 'y'))
        self.assertTrue(functiontools.hasParameter(my_func, 'b'))
        self.assertEqual(functiontools.numberOfParameterRange(my_func), (4, 4))

        def other_func(x, y, z, t):
            return  x + y + z + t

        self.assertTrue(functiontools.hasParameter(other_func, 'y'))
        self.assertFalse(functiontools.hasParameter(other_func, 'b'))
        self.assertTrue(functiontools.checkParameterCount(other_func, 4)
                        is None)
        self.assertRaises(RuntimeError,
                          functiontools.checkParameterCount, other_func, 3)

    def test_drange(self):
        l = [x for x in functiontools.drange(2.5, 4.8, 0.6)]
        self.assertEqual(l, [2.5, 3.1, 3.7, 4.3])



def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSomaMisc)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
