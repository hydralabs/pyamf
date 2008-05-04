# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Unit tests.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

# some Python 2.3 unittest compatibility fixes
if not hasattr(unittest.TestCase, 'assertTrue'):
    unittest.TestCase.assertTrue = unittest.TestCase.failUnless
if not hasattr(unittest.TestCase, 'assertFalse'):
    unittest.TestCase.assertFalse = unittest.TestCase.failIf

def suite():
    import os.path, sys
    from glob import glob

    sys.path.append(os.path.dirname(__file__))

    suite = unittest.TestSuite()

    for testcase in glob(os.path.join(os.path.dirname(__file__), 'test_*.py')):
        mod = __import__(os.path.basename(testcase).split('.')[0])

        suite.addTest(mod.suite())

    return suite

def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
