 
from __future__ import print_function

import unittest
import json
from soma.serialization import JSONSerializable


class TestSerializable(JSONSerializable):
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
    def __cmp__(self, other):
        return cmp((self.a, self.b), (other.a, other.b))

    def to_json(self):
        return ['soma.tests.test_serialization.test_serializable',
                [self.a, self.b]]
    
    def __str__(self):
        return 'TestSerializable({0}, {1}'.format(self.a, self.b)
    
def test_serializable(a=None, b=None):
    return TestSerializable(a, b)


class TestJSONSerialization(unittest.TestCase):

    def test_instance_serialization(self):
        x = TestSerializable(12345, 67890)
        j = json.dumps(x.to_json())
        y = JSONSerializable.from_json(json.loads(j))
        self.assertEqual(x,y)


    def test_serialization_formats(self):
        y = JSONSerializable.from_json('soma.tests.test_serialization.test_serializable')
        self.assertEqual(y, TestSerializable(None, None))
        x = TestSerializable(12345, 67890)
        y = JSONSerializable.from_json(['soma.tests.test_serialization.test_serializable',
                                        [12345, 67890]])
        self.assertEqual(x, y)
        y = JSONSerializable.from_json(['soma.tests.test_serialization.test_serializable',
                                        {'a': 12345, 'b': 67890}])
        self.assertEqual(x, y)
        y = JSONSerializable.from_json(['soma.tests.test_serialization.test_serializable',
                                        [12345], {'b': 67890}])
        self.assertEqual(x, y)

    def test_serialization_failure(self):
        with self.assertRaises(ValueError):
            JSONSerializable.from_json('missing_dot')
        with self.assertRaises(ValueError):
            JSONSerializable.from_json('invalid.module.name')
        with self.assertRaises(ValueError):
            JSONSerializable.from_json('soma.tests.test_serialization.not_existing')

def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJSONSerialization)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
