import sys
import unittest
from importlib import reload as reload_module


class TestUndefined(unittest.TestCase):
    def setUp(self):
        # disable traits module
        if "traits" in sys.modules:
            self._traits = sys.modules["traits"]
        else:
            self._traits = None
        if "traits.api" in sys.modules:
            self._traits_api = sys.modules["traits.api"]
        else:
            self._traits_api = None

    def restore_traits(self):
        # fix / restore traits module
        if self._traits_api is None:
            del sys.modules["traits.api"]
        else:
            sys.modules["traits.api"] = self._traits_api
        if self._traits is None:
            del sys.modules["traits"]
        else:
            sys.modules["traits"] = self._traits

    def tearDown(self):
        self.restore_traits()
        from soma import undefined

        reload_module(undefined)

    def test_undefined_builtin(self):
        sys.modules["traits"] = None
        sys.modules["traits.api"] = None
        from soma import undefined

        reload_module(undefined)
        self.assertTrue(hasattr(undefined, "Undefined"))
        undef = undefined.Undefined
        self.assertTrue(isinstance(undef, undefined.UndefinedClass))
        self.assertEqual(repr(undef), "<undefined>")
        self.assertTrue(undefined.UndefinedClass.get_instance() is undefined.Undefined)

    # def test_undefined_traits(self):
    # self.restore_traits()
    # from soma import undefined
    # from traits import trait_base
    # import traits.api as traits
    # reload_module(undefined)
    # self.assertTrue(hasattr(undefined, 'Undefined'))
    # undef = undefined.Undefined
    # self.assertTrue(isinstance(undef, trait_base._Undefined))
    # self.assertEqual(repr(undef), '<undefined>')


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUndefined)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
