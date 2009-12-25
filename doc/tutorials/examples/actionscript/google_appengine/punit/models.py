
import unittest, sys, logging, time, os.path
from StringIO import StringIO

import pyamf.tests

from unittest import defaultTestLoader

expected_failures = [
    'test_sol.HelperTestCase.test_load_file',
    'test_sol.HelperTestCase.test_load_name',
    'test_sol.HelperTestCase.test_save_file',
    'test_sol.HelperTestCase.test_save_name',
    'test_sol.SOLTestCase.test_save'
]

skipped_tests = [
    'adapters.test_django.TypeMapTestCase.test_objects_all'
]

class TestProgram:
    def __init__(self, module='__main__', defaultTest=None,
                 argv=None, testRunner=None, testLoader=defaultTestLoader):
        if type(module) == type(''):
            self.module = __import__(module)
            for part in module.split('.')[1:]:
                self.module = getattr(self.module, part)
        else:
            self.module = module

        self.verbosity = 1
        self.defaultTest = defaultTest
        self.testRunner = testRunner
        self.testLoader = testLoader

        if self.defaultTest is None:
            self.test = self.testLoader.loadTestsFromModule(self.module)
        else:
            self.testNames = (self.defaultTest,)
            self.createTests()

    def createTests(self):
        self.test = self.testLoader.loadTestsFromNames(self.testNames,
                                                       self.module)

    def runTests(self):
        old_stdin, sys.stdin = sys.stdin, StringIO()
        old_stderr, sys.stderr = sys.stderr, StringIO()

        if self.testRunner is None:
            self.testRunner = TestRunner()
        
        try:
            return self.testRunner.run(self.test)
        except:
            raise
        finally:
            sys.stdin = old_stdin
            sys.stderr = old_stderr

class TestRunner:
    tests = []
    def __init__(self, stdin=None, stderr=None):
        if stdin is None:
            self.stdin = sys.stdin
        else:
            self.stdin = stdin

        if stderr is None:
            self.stderr = sys.stderr
        else:
            self.stderr = stderr

    def run(self, test):
        "Run the given test case or test suite."
        result = unittest.TestResult()
        test(result)

        if len(result.errors) > 0:
            for i in range(len(result.errors)):
                result.errors[i] = result.errors[i][1]

        if len(result.failures) > 0:
            for i in range(len(result.failures)):
                result.failures[i] = result.failures[i][1]

        return result

class NamedCollection(list):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return str(other) == str(self)

    def get(self, obj):
        for x in self:
            if obj == x:
                return x

        raise KeyError

tests = None

def get_all_tests():
    global tests

    def _getTestsFromSuite(suite, ret=None):
        if ret is None:
            ret = {}

        for test in suite:
            if isinstance(test, unittest.TestSuite):
                _getTestsFromSuite(test, ret)
            else:
                mod_name = test.__module__

                if mod_name.startswith(pyamf.tests.__name__):
                    mod_name = mod_name[len(pyamf.tests.__name__) + 1:]

                if mod_name not in ret:
                    ret[mod_name] = {}

                mod = ret[mod_name]

                if test.__class__.__name__ not in mod:
                    mod[test.__class__.__name__] = []

                klass = mod[test.__class__.__name__]
                klass.append(test._testMethodName)

        return ret

    if tests is None:
        tests = _getTestsFromSuite(pyamf.tests.suite())

    return tests


def run_test(module, test_case, method):
    mod = __import__('pyamf.tests.%s' % module)

    for m in ['tests'] + module.split('.'):
        mod = getattr(mod, m)

    reload(mod)
    reload(pyamf.tests)

    for m in [test_case, method]:
        mod = getattr(mod, m)

    tp = TestProgram(module=pyamf.tests, testRunner=TestRunner(),
        defaultTest='%s.%s.%s' % (module, test_case, method))

    return tp.runTests()