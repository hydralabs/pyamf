# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Specific module tests

@since: 0.4
"""

import unittest


def suite():
    from glob import glob
    import os.path

    suite = unittest.TestSuite()
    mod_base = 'pyamf.tests.modules'

    for testcase in glob(os.path.join(os.path.dirname(__file__), 'modules', 'test_*.py')):
        mod_name = os.path.basename(testcase).split('.')[0]
        full_name = '%s.%s' % (mod_base, mod_name,)

        try:
            mod = __import__(full_name)
        except ImportError:
            continue

        for part in full_name.split('.')[1:]:
            mod = getattr(mod, part)

        suite.addTest(mod.suite())

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
