# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Unit tests.

@since: 0.1.0
"""

import os.path

import unittest


def get_suite():
    """
    Return a unittest.TestSuite.
    """
    loader = unittest.TestLoader()

    return loader.discover(os.path.dirname(__file__))


def main():
    """
    Run all of the tests when run as a module with -m.
    """
    runner = unittest.TextTestRunner()
    runner.run(get_suite())


if __name__ == '__main__':
    main()
