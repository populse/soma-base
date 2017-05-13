"""
This module contains some classes to manage python tests.

Our tests may need to create a reference for later comparison. As we want to be
able to use the same code, there are several "modes":
  - in the ref mode, the code is supposed to create the reference data
  - in the run mode, the code is supposed to create data and perform the
    comparison
The different modes are invoked by bv_maker. This works by using some CLI
arguments and by setting environement variables.

To do so, we need our own test loader that will pass some argument to the test
cases. Note that the documentation of unittest.TestCase states that the
subclasses should not change the signature of __init__ but in our case, it
should be safe as long as we use the specialized test loader.
"""

import os
import argparse

import unittest

ref_mode = 'ref'
run_mode = 'run'
test_modes = [run_mode, ref_mode]
default_mode = run_mode


class SomaTestLoader(unittest.TestLoader):
    """Base class for test loader that allows to pass keyword arguments to the
       test case class and use the environment to set the location of reference
       files.
       Inspired from http://stackoverflow.com/questions/11380413/python-unittest-passing-arguments
    """

    parser = argparse.ArgumentParser(
        epilog="Note that the options are usually passed by make via bv_maker."
    )
    parser.add_argument('--test_mode', choices=test_modes,
                        default=default_mode,
                        help=('Mode to use (\'run\' for normal tests, '
                              '\'ref\' for generating the reference files).'))

    def parse_args_and_env(self, argv):
        args = vars(self.parser.parse_args(argv))
        args['base_ref_data_dir'] = os.environ.get(
            'BRAINVISA_TEST_REF_DATA_DIR'
        )
        args['base_run_data_dir'] = os.environ.get(
            'BRAINVISA_TEST_RUN_DATA_DIR'
        )
        if args['test_mode'] == run_mode and not args['base_run_data_dir']:
            msg = "test_run_data_dir must be set in environment when using " \
                "'run' mode"
            raise ValueError(msg)
        return args

    def loadTestsFromTestCase(self, testCaseClass, argv=None):
        """Return a suite of all tests cases contained in
           testCaseClass."""
        if issubclass(testCaseClass, unittest.TestSuite):
            raise TypeError("Test cases should not be derived from "
                            "TestSuite. Maybe you meant to derive from"
                            " TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']

        args = self.parse_args_and_env(argv)

        # Modification here: pass CLI arguments to testCaseClass.
        test_cases = []
        for test_case_name in testCaseNames:
            test_cases.append(
                testCaseClass(test_case_name, **args)
            )
        loaded_suite = self.suiteClass(test_cases)

        return loaded_suite


class BaseSomaTestCase(unittest.TestCase):
    """
    Base class for test cases that honor the options to create reference files.
    The base location for referennce data and run data are passed in the
    constructor (for readability, they are named base_ref_data_dir and
    base_run_data_dir). The classes can define private_dir to have a specific
    sub-directory inside those directories.
    This class don't define any setUp method so direct subclasses of this class
    can implement any scenario.
    """

    # Subclasses should define this variable to create a private folder (if
    # it's None, the base directory for run or ref will be used).
    private_dir = None

    def __init__(self, testName, base_ref_data_dir, base_run_data_dir=None,
                 test_mode=default_mode):
        super(BaseSomaTestCase, self).__init__(testName)
        self.test_mode = test_mode
        self.base_ref_data_dir = base_ref_data_dir
        self.base_run_data_dir = base_run_data_dir
        if self.test_mode == run_mode and not self.base_run_data_dir:
            msg_fmt = \
                "base_run_data_dir must be provided when using '%s' mode"
            msg = msg_fmt % run_mode
            raise ValueError(msg)
        # Computed in property
        self._private_ref_data_dir = None
        self._private_run_data_dir = None

    @property
    def private_ref_data_dir(self):
        if self.private_dir:
            if not self._private_ref_data_dir:
                self._private_ref_data_dir = os.path.join(
                    self.base_ref_data_dir, self.private_dir
                )
            return self._private_ref_data_dir
        else:
            return self.base_ref_data_dir

    @property
    def private_run_data_dir(self):
        # base_run_data_dir is None in run mode
        if self.test_mode == ref_mode:
            return None
        if self.private_dir:
            if not self._private_run_data_dir:
                self._private_run_data_dir = os.path.join(
                    self.base_run_data_dir, self.private_dir
                )
            return self._private_run_data_dir
        else:
            return self.base_run_data_dir


class SomaTestCaseWithoutRefFiles(BaseSomaTestCase):
    """
    Special test case that don't need reference file (i.e. should not be run in
    ref mode).
    """

    def __init__(self, testName, base_ref_data_dir, base_run_data_dir=None,
                 test_mode=default_mode, force=False):
        super(SomaTestCaseWithoutRefFiles, self).__init__(
            testName, base_ref_data_dir, base_run_data_dir, test_mode, force
        )
        if self.test_mode == ref_mode:
            msg_fmt = "Test %s should not be run in '%s' mode"
            msg = msg_fmt % (self.__class__.__name__, ref_mode)
            raise EnvironmentError(msg)


class SomaTestCase(BaseSomaTestCase):
    """
    Base class for tests that need simple customization for ref and run modes.
    As the test mode is an instance property, we can't use it for setUpClass
    and tearDownClass.
    """

    def setUp_ref_mode(self):
        """
        This method is called once the setup is done in ref mode.
        """
        pass

    def setUp_run_mode(self):
        """
        This method is called once the setup is done in run mode.
        """
        pass

    def setUp(self):
        if self.test_mode == ref_mode:
            try:
                os.makedirs(self.private_ref_data_dir)
            except:
                pass
            self.setUp_ref_mode()
        else:
            try:
                os.makedirs(self.private_run_data_dir)
            except:
                pass
            self.setUp_run_mode()

    def tearDown_ref_mode(self):
        """
        This method is called once the setup is done in ref mode.
        """
        pass

    def tearDown_run_mode(self):
        """
        This method is called once the setup is done in run mode.
        """
        pass

    def tearDown(self):
        if self.test_mode == ref_mode:
            os.makedirs(self.private_ref_data_dir)
            self.tearDown_ref_mode()
        else:
            os.makedirs(self.private_run_data_dir)
            self.tearDown_run_mode()
