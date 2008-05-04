# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for the adapters module.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.3.1
"""

import unittest

def suite():
    import os.path
    from glob import glob

    suite = unittest.TestSuite()

    for testcase in glob(os.path.join(os.path.dirname(__file__), 'adapters', 'test_*.py')):
        name = os.path.basename(testcase).split('.')[0]

        try:
            mod = __import__('.'.join(['adapters', name]))
            mod = getattr(mod, name)
            suite.addTest(mod.suite())
        except:
            continue

    return suite

def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
