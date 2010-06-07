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
