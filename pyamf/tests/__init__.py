# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Unit tests.

@since: 0.1.0
"""

import os.path

try:
    import unittest2 as unittest
    import sys

    sys.modules['unittest'] = unittest
except ImportError:
    import unittest


if not hasattr(unittest.TestCase, 'assertIdentical'):
    def assertIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is not C{second}.  This is an
        obect-identity-equality test, not an object equality (i.e. C{__eq__}) test.

        @param msg: if msg is None, then the failure message will be
            '%r is not %r' % (first, second)
        """
        if first is not second:
            raise AssertionError(msg or '%r is not %r' % (first, second))

        return first

    unittest.TestCase.assertIdentical = assertIdentical

if not hasattr(unittest.TestCase, 'assertNotIdentical'):
    def assertNotIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is C{second}.  This is an
        object-identity-equality test, not an object equality
        (i.e. C{__eq__}) test.

        @param msg: if msg is None, then the failure message will be
            '%r is %r' % (first, second)
        """
        if first is second:
            raise AssertionError(msg or '%r is %r' % (first, second))

        return first

    unittest.TestCase.assertNotIdentical = assertNotIdentical


def get_suite():
    """
    Discover the entire test suite.
    """
    loader = unittest.TestLoader()

    return loader.discover(os.path.dirname(__file__), top_level_dir='../pyamf')


def main():
    """
    Run all of the tests when run as a module with -m.
    """
    runner = unittest.TextTestRunner()
    runner.run(get_suite())


if __name__ == '__main__':
    main()
