import json
import unittest

from soma.api import DictWithProxy


class TestProxy(unittest.TestCase):
    def test_proxy(self):
        d = DictWithProxy()

        p1 = d.proxy(1)
        p2 = d.proxy(2)

        d["1"] = p1
        d["2"] = p2
        d["3"] = 3
        d["l"] = [p1, p2, 3, {"1": p1, "2": p2, "3": 3, "l": [p1, p2, 3]}]
        with_int = {
            "1": 1,
            "2": 2,
            "3": 3,
            "l": [1, 2, 3, {"1": 1, "2": 2, "3": 3, "l": [1, 2, 3]}],
        }
        with_str = {
            "1": "one",
            "2": "two",
            "3": 3,
            "l": [
                "one",
                "two",
                3,
                {"1": "one", "2": "two", "3": 3, "l": ["one", "two", 3]},
            ],
        }

        self.assertEqual(d.no_proxy(d), with_int)
        self.assertEqual(d["l"][3]["l"][0], 1)
        d["l"][3]["1"] = "one"
        d["2"] = "two"
        self.assertEqual(d.no_proxy(d), with_str)
        self.assertEqual(d["l"][3]["l"][0], "one")
        d = d.from_json_controller(json.loads(json.dumps(d.json_controller())))
        self.assertEqual(d.no_proxy(d), with_str)
        d["l"][3]["1"] = 1
        d["2"] = 2
        self.assertEqual(d.no_proxy(d), with_int)

        d = DictWithProxy()
        shared_value = d.proxy("a shared value")
        d["a list"] = ["a value", shared_value]
        d["another list"] = ["another value", shared_value]
        d["a list"][1] = "modified shared value"
        self.assertEqual(d["another list"][1], "modified shared value")

    def test_recursive_proxy(self):
        d = DictWithProxy()
        proxy_1 = d.proxy(1)
        proxy_2 = d.proxy(2)
        l_proxy = d.proxy([proxy_1, proxy_2])
        d["1"] = proxy_1
        d["2"] = d.proxy(proxy_2)
        d["l"] = l_proxy
        self.assertEqual(d.no_proxy(d), {"1": 1, "2": 2, "l": [1, 2]})
        d["l"][0] = "one"
        d["l"][1] = "two"
        self.assertEqual(d.no_proxy(d), {"1": "one", "2": "two", "l": ["one", "two"]})
        d["l"][0] = d["l"][1]
        self.assertEqual(d.no_proxy(d), {"1": "two", "2": "two", "l": ["two", "two"]})
        self.assertEqual(d.content, {"1": ["&", 0], "2": ["&", 3], "l": ["&", 2]})
        self.assertEqual(d.proxy_values, ["two", "two", [["&", 0], ["&", 1]], ["&", 1]])

    def test_all_proxies(self):
        d = DictWithProxy()
        self.assertEqual(d.all_proxies, None)
        d = DictWithProxy(all_proxies=True)
        self.assertEqual(d.all_proxies, {})
        d["l"] = [d.proxy("one"), d.proxy("two")]
        d["d"] = {}
        dd = d["d"]
        dd["3"] = dd.proxy("three")
        dd["x"] = [d["l"], dd["3"]]
        self.assertEqual(
            d.all_proxies,
            {
                0: [["&", 0]],
                1: [["&", 1]],
                2: [["&", 2]],
            },
        )


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProxy)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
