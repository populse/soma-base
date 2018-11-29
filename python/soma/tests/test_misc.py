
from __future__ import print_function

import unittest
import os
import sys
from soma import singleton


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
