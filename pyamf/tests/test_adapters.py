# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the adapters module.

@since: 0.3.1
"""

import unittest
import os
import sys

from pyamf import adapters
from pyamf.tests import util
from pyamf.tests.test_imports import PostLoadHookClearingTestCase


class AdapterHelperTestCase(PostLoadHookClearingTestCase):
    def setUp(self):
        PostLoadHookClearingTestCase.setUp(self)

        self.old_env = os.environ.copy()
        self.mods = sys.modules.copy()

        self.path = os.path.join(os.path.dirname(__file__), 'imports')
        sys.path.append(self.path)

    def tearDown(self):
        PostLoadHookClearingTestCase.tearDown(self)

        util.replace_dict(os.environ, self.old_env)
        util.replace_dict(sys.modules, self.mods)
        sys.path.remove(self.path)

    def test_basic(self):
        class Foo(object):
            def __call__(self, *args, **kwargs):
                pass

        def bar(*args, **kargs):
            pass

        self.assertRaises(TypeError, adapters.register_adapter, 'foo', 1)
        self.assertRaises(TypeError, adapters.register_adapter, 'foo', 'asdf')
        adapters.register_adapter('foo', Foo())
        adapters.register_adapter('foo', bar)
        adapters.register_adapter('foo', lambda x: x)

    def test_import(self):
        self.imported = False

        def x(mod):
            self.imported = True
            self.foo = mod

        adapters.register_adapter('foo', x)

        import foo

        self.assertTrue(self.imported)
        self.assertEquals(self.foo, foo)


def suite():
    import os.path
    from glob import glob

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(AdapterHelperTestCase))

    for testcase in glob(os.path.join(os.path.dirname(__file__), 'adapters', 'test_*.py')):
        name = os.path.basename(testcase).split('.')[0]
        base_mod = ['pyamf', 'tests', 'adapters', name]

        try:
            __import__(name[5:])
            mod = __import__('.'.join(base_mod))

            for x in base_mod[1:]:
                mod = getattr(mod, x)

            suite.addTest(mod.suite())
        except ImportError:
            continue

    return suite


def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
