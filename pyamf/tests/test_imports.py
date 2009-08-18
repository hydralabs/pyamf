# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests pyamf.util.imports

@since: 0.3.1
"""

import unittest
import sys
import os.path

from pyamf.util import imports


class PostLoadHookClearingTestCase(unittest.TestCase):
    def setUp(self):
        self.plHooks, imports.post_load_hooks = imports.post_load_hooks, imports.post_load_hooks.copy()
        self.ldMods, imports.loaded_modules = imports.loaded_modules, imports.loaded_modules[:]

        self.path = os.path.join(os.path.dirname(__file__), 'imports')

        sys.path.insert(0, self.path)

    def tearDown(self):
        imports.post_load_hooks = self.plHooks
        imports.loaded_modules = self.ldMods

        del sys.path[0]

        self._clearModules('foo', 'spam')

    def _clearModules(self, *args):
        for mod in args:
            for k, v in sys.modules.copy().iteritems():
                if k.startswith(mod) or k == 'pyamf.tests.%s' % (mod,):
                    del sys.modules[k]


class SplitModuleTestCase(unittest.TestCase):
    """
    Tests for L{imports.split_module}
    """

    def test_no_parent(self):
        self.assertEquals(imports.split_module('foo'), (None, 'foo'))

    def test_one_parent(self):
        self.assertEquals(imports.split_module('foo.bar'), ('foo', 'bar'))

    def test_deep(self):
        self.assertEquals(imports.split_module('foo.bar.baz.gak'),
            ('foo.bar.baz', 'gak'))


class RunHooksTestCase(PostLoadHookClearingTestCase):
    """
    Tests for L{imports.run_hooks}
    """

    def test_iterate(self):
        module = object()
        self.executed = []

        def foo(mod):
            self.assertTrue(module is mod)
            self.executed.append('foo')

        def bar(mod):
            self.assertTrue(module is mod)
            self.executed.append('bar')

        imports.post_load_hooks['foo'] = [foo, bar]

        imports.run_hooks('foo', module)

        self.assertEquals(self.executed, ['foo', 'bar'])

    def test_clear(self):
        module = object()
        imports.post_load_hooks['foo'] = []

        imports.run_hooks('foo', module)

        self.assertFalse('foo' in imports.post_load_hooks)

    def test_error(self):
        """
        Make sure that if an error occurs that post_load_hooks is still
        deleted correctly.
        """
        module = object()
        self.executed = []

        def foo(mod):
            raise RuntimeError

        imports.post_load_hooks['foo'] = [foo]

        self.assertRaises(RuntimeError, imports.run_hooks, 'foo', module)
        self.assertFalse('foo' in imports.post_load_hooks)


class WhenImportedTestCase(PostLoadHookClearingTestCase):
    """
    Tests for L{imports.when_imported}
    """

    def setUp(self):
        PostLoadHookClearingTestCase.setUp(self)

        self.executed = False

    def _hook(self, module):
        self.executed = True

    def test_import(self):
        imports.loaded_modules = []

        imports.when_imported('spam', self._hook)

        import logging
        logging.debug(sys.meta_path)

        self.assertFalse(self.executed)

        import spam

        self.assertTrue(self.executed)
        self.assertEquals(imports.loaded_modules, ['spam'])

    def test_register(self):
        imports.when_imported('spam', self._hook)

        self.assertTrue('spam' in imports.post_load_hooks)
        self.assertEquals(imports.post_load_hooks['spam'], [self._hook])

    def test_already_imported(self):
        import spam

        imports.when_imported('spam', self._hook)

        self.assertTrue(self.executed)

    def test_already_loaded(self):
        import spam
        imports.loaded_modules = ['spam']

        imports.when_imported('spam', self._hook)

        self.assertTrue(self.executed)


class BaseModuleFinderTestCase(PostLoadHookClearingTestCase):
    """
    """

    def setUp(self):
        PostLoadHookClearingTestCase.setUp(self)

        self.finder = imports.ModuleFinder()


class ModuleFinderFindModuleTestCase(BaseModuleFinderTestCase):
    """
    Tests for L{imports.ModuleFinder.find_module}
    """

    def test_found(self):
        imports.post_load_hooks['foo'] = None

        self.assertTrue(self.finder is self.finder.find_module('foo', None))

    def test_not_found(self):
        self.assertFalse('foo' in imports.post_load_hooks)

        self.assertEquals(None, self.finder.find_module('foo', None))


class ModuleFinderLoadModuleTestCase(BaseModuleFinderTestCase):
    """
    Tests for L{imports.ModuleFinder.load_module}
    """

    def setUp(self):
        BaseModuleFinderTestCase.setUp(self)

        imports.loaded_modules = []

    def test_file(self):
        self.assertFalse('spam' in sys.modules)

        imports.post_load_hooks['spam'] = []
        mod = self.finder.load_module('spam')

        self.assertTrue(mod is sys.modules['spam'])
        self.assertEquals(imports.loaded_modules, ['spam'])

    def test_package(self):
        self.assertFalse('foo' in sys.modules)

        imports.post_load_hooks['foo'] = []
        mod = self.finder.load_module('foo')

        self.assertTrue(mod is sys.modules['foo'])
        self.assertEquals(imports.loaded_modules, ['foo'])

    def test_package_child(self):
        self.assertFalse('foo.bar' in sys.modules)

        import foo

        imports.post_load_hooks['foo.bar'] = []
        mod = self.finder.load_module('foo.bar')

        self.assertTrue(mod is sys.modules['foo.bar'])
        self.assertEquals(imports.loaded_modules, ['foo.bar'])

        self.assertTrue(sys.modules['foo'].bar is mod)

    def test_hook(self):
        self.executed = False

        def h(mod):
            self.executed = True

        imports.post_load_hooks['foo'] = [h]

        mod = self.finder.load_module('foo')

        self.assertTrue(self.executed)
        self.assertTrue(mod is sys.modules['foo'])


def suite():
    suite = unittest.TestSuite()

    tcs = [
        SplitModuleTestCase,
        RunHooksTestCase,
        WhenImportedTestCase,
        ModuleFinderFindModuleTestCase,
        ModuleFinderLoadModuleTestCase
    ]

    for tc in tcs:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
