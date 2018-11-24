
from __future__ import print_function

import unittest
import os
import sys
if sys.version_info[0] >= 3:
    from importlib import reload


class TestUndefined(unittest.TestCase):

    def setUp(self):
        # disable traits module
        if 'traits' in sys.modules:
            self._traits = sys.modules['traits']
        else:
            self._traits = None

    def restore_traits(self):
        # fix / restore traits module
        if self._traits is None:
            del sys.modules['traits']
        else:
            sys.modules['traits'] = self._traits

    def tearDown(self):
        self.restore_traits()
        from soma import undefined
        reload(undefined)

    def test_undefined_builtin(self):
        sys.modules['traits'] = None
        from soma import undefined
        reload(undefined)
        self.assertTrue(hasattr(undefined, 'Undefined'))
        undef = undefined.Undefined
        self.assertTrue(isinstance(undef, undefined.UndefinedClass))
        self.assertEqual(repr(undef), '<undefined>')

    def test_undefined_traits(self):
        self.restore_traits()
        from soma import undefined
        from traits import trait_base
        import traits.api as traits
        reload(undefined)
        self.assertTrue(hasattr(undefined, 'Undefined'))
        undef = undefined.Undefined
        self.assertTrue(isinstance(undef, trait_base._Undefined))
        self.assertEqual(repr(undef), '<undefined>')


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUndefined)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
