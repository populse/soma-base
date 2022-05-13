# -*- coding: utf-8 -*-

import json
import unittest

from soma.api import DictWithProxy


class TestProxy(unittest.TestCase):

    def test_proxy(self):
        d = DictWithProxy()

        p1 = d.proxy(1)
        p2 = d.proxy(2)

        d['1'] = p1
        d['2'] = p2
        d['3'] = 3
        d['l'] = [p1, p2, 3, {'1': p1, '2': p2, '3': 3, 'l': [p1, p2, 3]}]
        with_int = {
            '1': 1, 
            '2': 2, 
            '3': 3, 
            'l': [1, 2, 3, {
                '1': 1, 
                '2': 2, 
                '3': 3, 
                'l': [1, 2, 3]}
            ]
        }
        with_str = {
            '1': 'one', 
            '2': 'two', 
            '3': 3, 
            'l': ['one', 'two', 3, {
                '1': 'one', 
                '2': 'two', 
                '3': 3, 
                'l': ['one', 'two', 3]}
            ]
        }

        self.assertEqual(d.no_proxy(), with_int)
        self.assertEqual(d['l'][3]['l'][0], 1)
        d['l'][3]['1'] = 'one'
        d['2'] = 'two'
        self.assertEqual(d.no_proxy(), with_str)
        self.assertEqual(d['l'][3]['l'][0], 'one')
        d = d.from_json(json.loads(json.dumps(d.json())))
        self.assertEqual(d.no_proxy(), with_str)
        d['l'][3]['1'] = 1
        d['2'] = 2
        self.assertEqual(d.no_proxy(), with_int)

        d = DictWithProxy()
        shared_value = d.proxy('a shared value')
        d['a list'] = ['a value', shared_value]
        d['another list'] = ['another value', shared_value]
        d['a list'][1] = 'modified shared value'
        self.assertEqual(d['another list'][1], 'modified shared value')

def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProxy)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
