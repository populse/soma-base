import pickle
import unittest

from soma import uuid


class TestUUID(unittest.TestCase):
    def test_uuid(self):
        u1 = uuid.Uuid()
        u2 = uuid.Uuid()
        self.assertNotEqual(u1, u2)
        self.assertNotEqual(str(u1), str(u2))
        self.assertEqual(len(str(u1)), 36)
        self.assertEqual(len(repr(u1)), 38)
        self.assertEqual(u1, uuid.Uuid(str(u1)))
        self.assertIs(u1, uuid.Uuid(u1))
        self.assertEqual(u1, str(u1))
        self.assertTrue(u1 != str(u2))
        self.assertTrue(u1 != "bloblo")
        self.assertTrue(u1 != 12)
        self.assertTrue(not (u1 == "bloblo"))
        self.assertTrue(not (u1 == 12))
        with self.assertRaises(ValueError):
            uuid.Uuid("blablah0-bouh-bidi-bada-popogugurbav")
        p = pickle.dumps(u1)
        self.assertEqual(u1, pickle.loads(p))
        p = pickle.dumps(u1, 2)  # test Pickle protocol version 2
        self.assertEqual(u1, pickle.loads(p))
        u3 = uuid.Uuid(b"1cab3907-9056-4694-a1d5-266ed5b6ebe3")
        u4 = uuid.Uuid("1cab3907-9056-4694-a1d5-266ed5b6ebe3")
        self.assertEqual(u3, u4)


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUUID)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
