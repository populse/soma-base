"""
This module contains some classes to manage python tests.

Our tests may need to create a reference for later comparison. As we want to be
able to use the same code, there are several "modes":
  - in the ref mode, the code is supposed to create the reference data
  - in the run mode, the code is supposed to create data and perform the
    comparison
The different modes are invoked by bv_maker. This works by using some CLI
arguments and by setting environment variables.

To do so, we need our own test loader that will configure the test cases. This
is done by modifying attributes at the class level (so that setUpClass can
know in which mode it is).
"""

import argparse
import os
import unittest

ref_mode = "ref"
run_mode = "run"
test_modes = [run_mode, ref_mode]
default_mode = run_mode


class SomaTestLoader(unittest.TestLoader):
    """Base class for test loader that allows to pass keyword arguments to the
    test case class and use the environment to set the location of reference
    files. Inspired from https://stackoverflow.com/questions/11380413/ (but
    here we modify the test case classes themselves).
    The ArgumentParser is defined in the __init__ method. While it could be
    a class atrtibute, this makes easier to modify it in subclasses.
    The static method `default_parser` is used to create a new instance of
    the basic parser.
    """

    @staticmethod
    def default_parser(description):
        parser = argparse.ArgumentParser(
            description=description,
            epilog=("Note that the options are usually passed by make via bv_maker."),
        )
        parser.add_argument(
            "--test_mode",
            choices=test_modes,
            default=default_mode,
            help=(
                "Mode to use ('run' for normal tests, "
                "'ref' for generating the reference files)."
            ),
        )
        return parser

    def __init__(self):
        self.parser = SomaTestLoader.default_parser("Soma test program.")

    def parse_args_and_env(self, argv):
        args = vars(self.parser.parse_args(argv))
        args["base_ref_data_dir"] = os.environ.get("BRAINVISA_TEST_REF_DATA_DIR")
        args["base_run_data_dir"] = os.environ.get("BRAINVISA_TEST_RUN_DATA_DIR")
        if args["test_mode"] == run_mode and not args["base_run_data_dir"]:
            msg = (
                "BRAINVISA_TEST_RUN_DATA_DIR must be set in environment "
                "when using 'run' mode"
            )
            raise ValueError(msg)
        return args

    def loadTestsFromTestCase(self, testCaseClass, argv=None):
        """Return a suite of all tests cases contained in
        testCaseClass."""
        if issubclass(testCaseClass, unittest.TestSuite):
            raise TypeError(
                "Test cases should not be derived from "
                "TestSuite. Maybe you meant to derive from"
                " TestCase?"
            )
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, "runTest"):
            testCaseNames = ["runTest"]

        args = self.parse_args_and_env(argv)

        # Modification here: configure testCaseClass.
        test_cases = []
        for test_case_name in testCaseNames:
            for k, v in args.items():
                setattr(testCaseClass, k, v)
            test_cases.append(testCaseClass(test_case_name))
        loaded_suite = self.suiteClass(test_cases)

        return loaded_suite


class BaseSomaTestCase(unittest.TestCase):
    """
    Base class for test cases that honor the options to create reference files.
    The base location for reference data and run data are set in the class by
    the loader. Subclasses can define private_dir to have a specific
    sub-directory inside those directories.
    This class don't define any setUp method so direct subclasses of this class
    can implement any scenario.
    """

    # Declare base class attributes
    test_mode = None
    base_ref_data_dir = None
    base_run_data_dir = None

    # Subclasses should define this variable to create a private folder (if
    # it's None, the base directory for run or ref will be used).
    private_dir = None

    # Computed in property
    _private_ref_data_dir = None
    _private_run_data_dir = None

    def __init__(self, testName):
        super().__init__(testName)
        if self.test_mode == run_mode and not self.base_run_data_dir:
            msg = f"base_run_data_dir must be provided when using '{run_mode}' mode"
            raise ValueError(msg)

    @classmethod
    def private_ref_data_dir(cls):
        if cls.private_dir:
            if not cls._private_ref_data_dir:
                cls._private_ref_data_dir = os.path.join(
                    cls.base_ref_data_dir, cls.private_dir
                )
            return cls._private_ref_data_dir
        else:
            return cls.base_ref_data_dir

    @classmethod
    def private_run_data_dir(cls):
        # base_run_data_dir is None in run mode
        if cls.test_mode == ref_mode:
            return None
        if cls.private_dir:
            if not cls._private_run_data_dir:
                cls._private_run_data_dir = os.path.join(
                    cls.base_run_data_dir, cls.private_dir
                )
            return cls._private_run_data_dir
        else:
            return cls.base_run_data_dir


class SomaTestCaseWithoutRefFiles(BaseSomaTestCase):
    """
    Special test case that don't need reference file (i.e. should not be run in
    ref mode).
    """

    def __init__(self, testName):
        super().__init__(testName)
        if self.test_mode == ref_mode:
            msg = (
                f"Test {self.__class__.__name__} should not be run in '{ref_mode}' mode"
            )
            raise OSError(msg)


# Should we skip all tests in ref mode (all computation in setUp_ref_mode?)
class SomaTestCase(BaseSomaTestCase):
    """
    Base class for tests that need simple customization for ref and run modes.
    Subclasses can redefine `setUpClass_ref_mode`, `setUpClass_run_mode`,
    `setUp_ref_mode` and `setUp_run_mode` (and corresponding methods for tear
    down).

    Note that the test will be skipped if ref data dir is not defined.
    """

    @classmethod
    def setUpClass_ref_mode(cls):
        """
        This method is called by setUpClass in ref mode.
        """
        pass

    @classmethod
    def setUpClass_run_mode(cls):
        """
        This method is called by setUpClass in run mode.
        """
        pass

    @classmethod
    def setUpClass(cls):
        if not cls.base_ref_data_dir:
            msg = f"base_ref_data_dir must be provided for test {cls.__name__}"
            raise OSError(msg)
        if cls.test_mode == ref_mode:
            try:
                os.makedirs(cls.private_ref_data_dir())
            except OSError:
                pass
            cls.setUpClass_ref_mode()
        else:
            try:
                os.makedirs(cls.private_run_data_dir())
            except OSError:
                pass
            cls.setUpClass_run_mode()

    @classmethod
    def tearDownClass_ref_mode(cls):
        """
        This method is called by tearDownClass in ref mode.
        """
        pass

    @classmethod
    def tearDownClass_run_mode(cls):
        """
        This method is called by tearDownClass in run mode.
        """
        pass

    @classmethod
    def tearDownClass(cls):
        if cls.test_mode == ref_mode:
            cls.tearDownClass_ref_mode()
        else:
            cls.tearDownClass_run_mode()

    def setUp_ref_mode(self):
        """
        This method is called by setUp in ref mode.
        """
        pass

    def setUp_run_mode(self):
        """
        This method is called by setUp in run mode.
        """
        pass

    def setUp(self):
        if self.test_mode == ref_mode:
            self.setUp_ref_mode()
        else:
            self.setUp_run_mode()

    def tearDown_ref_mode(self):
        """
        This method is called by tearDown in ref mode.
        """
        pass

    def tearDown_run_mode(self):
        """
        This method is called by tearDown in run mode.
        """
        pass

    def tearDown(self):
        if self.test_mode == ref_mode:
            self.tearDown_ref_mode()
        else:
            self.tearDown_run_mode()
