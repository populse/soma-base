# -*- coding: utf-8 -*-

from __future__ import print_function

from __future__ import absolute_import
import unittest
from soma import html



class TestHtml(unittest.TestCase):

    def test_html_escape(self):
        s1 = u'totô < 0 ét tùtu bàbär >= 3 & etc.'
        s2 = html.htmlEscape(s1)
        self.assertEqual(
            s2,
            u'tot&ocirc; &lt; 0 &eacute;t t&ugrave;tu b&agrave;b&auml;r &gt;'
            '= 3 &amp; etc.')
        s3 = html.lesserHtmlEscape(s1)
        self.assertEqual(
            s3,
            u'totô &lt; 0 ét tùtu bàb&auml;r &gt;= 3 &amp; etc.')


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHtml)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
