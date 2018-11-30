
from __future__ import print_function

import unittest
import shutil
import os
import tempfile
from soma import fom


class TestFOM(unittest.TestCase):

    def test_fom(self):
        atp = fom.AttributesToPaths()
        pta = fom.PathsToAttributes()


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFOM)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
