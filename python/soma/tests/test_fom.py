import os
import shutil
import tempfile
import unittest

from soma import application, fom


class TestFOM(unittest.TestCase):
    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix="soma_test_fom")

    def tearDown(self):
        try:
            shutil.rmtree(self.work_dir)
            # pass
        except OSError:
            pass

    def test_fom(self):
        app = application.Application("testapp", plugin_modules=["soma.fom"])
        if "soma.fom" not in app.loaded_plugin_modules:
            app.initialize()
        app.fom_path = [os.path.join(self.work_dir, "foms")]
        app.fom_manager.paths = app.fom_path  # BUG: should be automatic
        os.mkdir(app.fom_path[0])
        # print('fom_path:', app.fom_path, file=sys.stderr)
        fom_filename = "test_fom"
        open(os.path.join(app.fom_path[0], fom_filename + ".json"), "w").write(
            """{
    "fom_name": "test_fom",

    "formats": {
        "NIFTI": "nii",
        "GIS": "ima"
    },

    "format_lists": {
        "images": ["NIFTI", "GIS"]
    },

    "attribute_definitions": {
        "acquisition" : {"default_value" : "default_acquisition"},
        "analysis" : {"default_value" : "default_analysis"},
        "sulci_recognition_session" :  {"default_value" : "default_session"},
        "graph_version": {"default_value": "3.1"}
    },

    "shared_patterns": {
      "acquisition": "<center>/<subject>/t1mri/<acquisition>",
      "analysis": "{acquisition}/<analysis>",
      "recognition_analysis": "{analysis}/folds/<graph_version>/<sulci_recognition_session>_auto"
    },

    "processes": {
        "Morphologist": {
            "t1mri":
                [["input:{acquisition}/<subject>", "images"]]
        }
    }
}
"""
        )
        foms = app.fom_manager.load_foms(fom_filename)
        atp = fom.AttributesToPaths(foms)
        pta = fom.PathToAttributes(foms)


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFOM)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
