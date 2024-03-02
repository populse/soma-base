import os
import shutil
import tempfile
import unittest

import soma.minf.api as minf


class TestMinfIO(unittest.TestCase):
    """test .minf IO"""

    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        # print('dir:', self.directory)
        shutil.rmtree(self.directory)

    def test_minf_xml_io(self):
        d = {
            "titi": {"bubu": "50", "turlute": 12},
            "toto": "val\"u'e",
            "tutu": [0, 1, 2, ["papa", 5]],
        }
        minf_file = os.path.join(self.directory, "minf_xml_file.minf")
        minf.writeMinf(minf_file, (d,))
        dd = minf.readMinf(minf_file)
        self.assertEqual(d, dd[0])

    def test_minf_py_io(self):
        d = {
            "titi": {"bubu": "50", "turlute": 12},
            "toto": "val\"u'e",
            "tutu": [0, 1, 2, ["papa", 5]],
        }
        minf_file = os.path.join(self.directory, "minf_py_file.minf")
        open(minf_file, "w").write("attributes = " + repr(d) + "\n")
        dd = minf.readMinf(minf_file)
        self.assertEqual(d, dd[0])


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMinfIO)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
