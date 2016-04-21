
from __future__ import print_function

import unittest
import shutil
import os
import tempfile
from soma.controller import Controller
import traits.api as traits



class TestController(unittest.TestCase):

    def test_controller(self):
        c1 = Controller()
        c1.add_trait('gogo', traits.Str())
        c1.add_trait('bozo', traits.Int(12))
        self.assertEqual(c1.gogo, '')
        self.assertEqual(c1.bozo, 12)
        self.assertEqual(c1.user_traits().keys(), ['gogo', 'bozo'])
        c1.gogo = 'blop krok'
        self.assertEqual(c1.gogo, 'blop krok')

    def test_controller2(self):
        class Zuzur(Controller):
            glop = traits.Str('zut')

        c2 = Zuzur()
        c3 = Zuzur()
        self.assertEqual(c2.glop, 'zut')
        c2.glop = 'I am c2'
        c3.glop = 'I am c3'
        self.assertEqual(c2.glop, 'I am c2')
        self.assertEqual(c3.glop, 'I am c3')


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestController)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()

