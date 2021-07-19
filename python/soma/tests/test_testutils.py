# -*- coding: utf-8 -*-

from __future__ import print_function

from __future__ import absolute_import
import unittest
import os
import sys
from soma import test_utils
from soma.test_utils import base_classes
from soma.test_utils import test_notebook

class TestTestUtils(unittest.TestCase):

    def test_test_classes(self):
        pass

    if test_notebook.main_jupyter is not None:
        def test_test_notebook(self):
            pass


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTestUtils)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
