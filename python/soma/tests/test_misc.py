# -*- coding: utf-8 -*-

from __future__ import print_function

# obsolete modules which seem never to be used:
#

from __future__ import absolute_import
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
    # Crypto (pycrypto package) missing or outdated
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
            return x + y + z + t
        
        class TmpObject(object):
            def meth(self, x, y, z, t):
                return x + y + z + t

        self.assertTrue(functiontools.hasParameter(other_func, 'y'))
        self.assertFalse(functiontools.hasParameter(other_func, 'b'))
        self.assertTrue(functiontools.checkParameterCount(other_func, 4)
                        is None)
        self.assertTrue(functiontools.checkParameterCount(TmpObject().meth, 4)
                        is None)
        self.assertRaises(RuntimeError,
                          functiontools.checkParameterCount, other_func, 3)

    def test_drange(self):
        l = [x for x in functiontools.drange(2.5, 4.8, 0.6)]
        self.assertEqual(l, [2.5, 3.1, 3.7, 4.3])

    def test_archive(self):
        d = tempfile.mkdtemp()
        try:
            fullfile1 = os.path.join(d, 'archive.bop')
            open(fullfile1, 'wb').write(b'bloblop')
            self.assertFalse(archive.is_archive(fullfile1))
            dir1 = os.path.join(d, 'subdir')
            fullfile2 = os.path.join(dir1, 'archive2.txt')
            os.mkdir(dir1)
            open(fullfile2, 'w').write(u'bebert is happy')
            for ext in ('.zip', '.tar', '.tgz', 'tar.bz2'):
                arfile = os.path.join(d, 'archive' + ext)
                open(arfile, 'wb').write(b'bloblop')
                unpacked = os.path.join(d, 'unpacked')
                # the following does not behave correctly, is_archive(*.zip)
                # returns True
                #self.assertFalse(archive.is_archive(arfile))
                self.assertRaises(OSError, archive.unpack, arfile, unpacked)
                self.assertRaises(OSError, archive.unzip, arfile, unpacked)
                archive.pack(arfile, [fullfile1, dir1])
                self.assertTrue(archive.is_archive(arfile))
                try:
                    archive.unpack(arfile, unpacked)
                    self.assertTrue(os.path.isfile(
                        os.path.join(unpacked, 'archive.bop')))
                    self.assertTrue(os.path.isfile(
                        os.path.join(unpacked, 'subdir', 'archive2.txt')))
                    content1 = open(os.path.join(
                        unpacked, 'archive.bop'), 'rb').read()
                    self.assertEqual(content1, b'bloblop')
                    content2 = open(os.path.join(
                        unpacked, 'subdir', 'archive2.txt'), 'r').read()
                    self.assertEqual(content2, u'bebert is happy')
                finally:
                    try:
                        shutil.rmtree(unpacked)
                    except OSError:
                        pass
                # trunkcate archive
                content = open(arfile, 'rb').read()
                open(arfile, 'wb').write(content[:50])
                self.assertTrue(archive.is_archive(arfile)) # shoud rather fail
                unpacked = os.path.join(d, 'unpacked')
                try:
                    self.assertRaises(OSError, archive.unpack, arfile,
                                      unpacked)
                finally:
                    try:
                        shutil.rmtree(unpacked)
                    except OSError:
                        pass
                # zip one file
                archive.pack(arfile, fullfile1)
                self.assertTrue(archive.is_archive(arfile))
                try:
                    archive.unpack(arfile, unpacked)
                    self.assertTrue(os.path.isfile(
                        os.path.join(unpacked, 'archive.bop')))
                    content1 = open(os.path.join(
                        unpacked, 'archive.bop'), 'rb').read()
                    self.assertEqual(content1, b'bloblop')
                finally:
                    try:
                        shutil.rmtree(unpacked)
                    except OSError:
                        pass


        finally:
            shutil.rmtree(d)



def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSomaMisc)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
