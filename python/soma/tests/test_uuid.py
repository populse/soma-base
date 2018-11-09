
from __future__ import print_function

import unittest
import shutil
import os
import tempfile
from soma import uuid
import pickle



class TestUUID(unittest.TestCase):

    def test_uuid(self):
        u1 = uuid.Uuid()
        u2 = uuid.Uuid()
        self.assertTrue(u1 != u2)
        self.assertTrue(str(u1) != str(u2))
        self.assertEqual(len(str(u1)), 36)
        self.assertEqual(len(repr(u1)), 38)
        self.assertEqual(u1, uuid.Uuid(str(u1)))
        self.assertTrue(u1 is uuid.Uuid(u1))
        self.assertEqual(u1, str(u1))
        self.assertTrue(u1 != str(u2))
        self.assertTrue(u1 != 'bloblo')
        self.assertTrue(u1 != 12)
        self.assertTrue(not(u1 == 'bloblo'))
        self.assertTrue(not(u1 == 12))
        self.assertRaises(ValueError, uuid.Uuid,
                          'blablah0-bouh-bidi-bada-popogugurbav')
        p = pickle.dumps(u1)
        self.assertEqual(u1, pickle.loads(p))
        d = {u1: 'u1'}
        self.assertTrue(u1 in d)
        d[u1] = 'u1-bis'
        self.assertEqual(len(d), 1)
        self.assertEqual(d[u1], 'u1-bis')


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUUID)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
