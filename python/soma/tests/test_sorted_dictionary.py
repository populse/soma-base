import pickle
import unittest

from soma.sorted_dictionary import SortedDictionary


class TestSortedDictionary(unittest.TestCase):
    def test_sorted_dictionary(self):
        d0 = SortedDictionary()
        self.assertEqual(dict(d0), {})

        d1 = SortedDictionary(
            ("titi", {"bubu": "50", "turlute": 12}),
            ("toto", "val\"u'e"),
            ("tutu", [0, 1, 2, ["papa", 5]]),
        )
        d2 = SortedDictionary(
            ("tutu", [0, 1, 2, ["papa", 5]]),
            ("toto", "val\"u'e"),
            ("titi", {"bubu": "50", "turlute": 12}),
        )

        self.assertEqual(dict(d1), dict(d2))
        self.assertNotEqual(list(d1.keys()), list(d2.keys()))
        self.assertEqual(d1, dict(d1))
        self.assertEqual(d1, SortedDictionary(list(dict(d1).items())))

        d1["titi"] = "babar"
        d2["titi"] = "bubur"
        self.assertNotEqual(dict(d1), dict(d2))
        d2["titi"] = "babar"
        self.assertEqual(dict(d1), dict(d2))
        d1["ababo"] = 43.65
        self.assertEqual(list(d1.keys()), ["titi", "toto", "tutu", "ababo"])

        del d1["titi"]
        del d1["ababo"]
        del d2["titi"]
        self.assertEqual(dict(d1), dict(d2))
        self.assertEqual(list(d2.keys()), ["tutu", "toto"])
        p = pickle.dumps(d1)
        p2 = pickle.loads(p)
        self.assertTrue(isinstance(p2, SortedDictionary))
        self.assertEqual(d1, p2)

        d1.insert(1, "babar", "new item")
        self.assertEqual(list(d1.keys()), ["toto", "babar", "tutu"])
        self.assertRaises(KeyError, d1.insert, 2, "babar", "other")
        self.assertEqual(d1.index("babar"), 1)


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSortedDictionary)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
