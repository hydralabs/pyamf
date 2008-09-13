# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for the adapters module.

@since: 0.3.1
"""

import unittest, os, sys

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

    def test_root_import_fail(self):
        self.assertRaises(ImportError, adapters.register_adapter, '__xyz', lambda x: x)

def suite():
    import os.path
    from glob import glob

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(AdapterHelperTestCase))

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
