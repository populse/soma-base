 
from __future__ import print_function

import unittest
import shutil
import os
import tempfile
from soma.sorted_dictionary import SortedDictionary



class TestSortedDictionary(unittest.TestCase):

    def test_sorted_dictionary(self):
        d1 = SortedDictionary(
            ('titi', {'bubu': '50', 'turlute': 12}),
            ('toto', 'val"u\'e'),
            ('tutu', [0, 1, 2, [u'papa', 5]]))
        d2 = SortedDictionary(
            ('tutu', [0, 1, 2, [u'papa', 5]]),
            ('toto', 'val"u\'e'),
            ('titi', {'bubu': '50', 'turlute': 12}))

        self.assertEqual(dict(d1), dict(d2))
        self.assertNotEqual(d1.keys(), d2.keys())

        d1['titi'] = 'babar'
        d2['titi'] = 'bubur'
        self.assertNotEqual(dict(d1), dict(d2))
        d2['titi'] = 'babar'
        self.assertEqual(dict(d1), dict(d2))
        d1['ababo'] = 43.65
        self.assertEqual(d1.keys(), ['titi', 'toto', 'tutu', 'ababo'])

        del d1['titi']
        del d1['ababo']
        del d2['titi']
        self.assertEqual(dict(d1), dict(d2))
        self.assertEqual(d2.keys(), ['tutu', 'toto'])


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSortedDictionary)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
