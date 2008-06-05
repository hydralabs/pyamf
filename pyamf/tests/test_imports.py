# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests pyamf.util.imports

@since: 0.3.1
"""

import unittest, sys, os.path

from pyamf.util import imports
from pyamf.tests import util as _util

class JoinPathTestCase(unittest.TestCase):
    def test_empty(self):
        self.assertEquals(imports.joinPath('a.b', ''), '')

    def test_root(self):
        self.assertEquals(imports.joinPath('a.b', '/'), '')

    def test_cwd(self):
        self.assertEquals(imports.joinPath('a.b', '.'), 'a.b')
        self.assertEquals(imports.joinPath('a.b.c.d.e.f.g', '.'), 'a.b.c.d.e.f.g')

    def test_prev_dir(self):
        self.assertEquals(imports.joinPath('a.b', '..'), 'a')
        self.assertEquals(imports.joinPath('a.b.c.d.e.f.g', '..'), 'a.b.c.d.e.f')

    def test_name(self):
        self.assertEquals(imports.joinPath('a.b', 'c/d'), 'a.b.c.d')

    def test_relative(self):
        self.assertEquals(imports.joinPath('a.b', 'c/../d/e/../../f'), 'a.b.f')

class PostLoadHookClearingTestCase(unittest.TestCase):
    def setUp(self):
        self.plHooks, imports.postLoadHooks = imports.postLoadHooks, imports.postLoadHooks.copy()
        self.ldMods, imports.loadedModules = imports.loadedModules, imports.loadedModules[:]

    def tearDown(self):
        imports.postLoadHooks = self.plHooks
        imports.loadedModules = self.ldMods

class GetModuleHooksTestCase(PostLoadHookClearingTestCase):
    def test_default(self):
        self.assertFalse('spam.eggs' in imports.postLoadHooks.keys())

        self.assertEquals(imports.getModuleHooks('spam.eggs'), [])

    def test_existant(self):
        obj = object()
        imports.postLoadHooks['spam.eggs'] = obj

        self.assertEquals(imports.getModuleHooks('spam.eggs'), obj)

    def test_none(self):
        imports.postLoadHooks['spam.eggs'] = None

        self.assertRaises(imports.AlreadyRead, imports.getModuleHooks, 'spam.eggs')

class LazyModuleTestCase(unittest.TestCase):
    def loadModule(self, name):
        self.moduleLoaded = True
        self.moduleName = name

    def setUp(self):
        self.moduleLoaded = False
        self.moduleName = None

        self.func = imports._loadModule

        imports._loadModule = self.loadModule

    def tearDown(self):
        imports._loadModule = self.func

    def test_slots(self):
        self.assertEquals(imports.LazyModule('spam', 'eggs').__slots__, tuple())

    def test_init(self):
        mod = imports.LazyModule('spam', 'eggs')

        self.assertEquals(mod.__name__, 'spam')
        self.assertEquals(mod.__file__, 'eggs')
        self.assertRaises(AttributeError, getattr, mod, '__path__')

        mod = imports.LazyModule('foo', 'bar', [])

        self.assertEquals(mod.__name__, 'foo')
        self.assertEquals(mod.__file__, 'bar')
        self.assertEquals(mod.__path__, [])

    def test_type(self):
        import types

        mod = imports.LazyModule('spam', 'eggs')

        self.assertTrue(isinstance(mod, types.ModuleType))

    def test_getattr(self):
        mod = imports.LazyModule('spam', 'eggs')

        self.assertEquals(mod.__name__, 'spam')
        self.assertEquals(mod.__file__, 'eggs')

        self.assertFalse(self.moduleLoaded)

        self.assertEquals(mod.__dict__, {'__name__': 'spam', '__file__': 'eggs'})
        self.assertTrue(self.moduleLoaded)
        self.assertEquals(self.moduleName, mod)

    def test_setattr(self):
        mod = imports.LazyModule('spam', 'eggs')

        mod.__name__ = 'foo'
        mod.__file__ = 'bar'
        mod.__path__ = ['baz']

        self.assertFalse(self.moduleLoaded)

        mod.a = 'b'
        self.assertTrue(self.moduleLoaded)
        self.assertEquals(mod.__dict__, {'__name__': 'foo', '__file__': 'bar', '__path__': ['baz'], 'a': 'b'})
        self.assertEquals(self.moduleName, mod)

class IsLazyTestCase(PostLoadHookClearingTestCase):
    def test_lazy(self):
        imports.postLoadHooks['spam'] = []

        mod = imports.LazyModule('spam', 'eggs')

        self.assertTrue(imports._isLazy(mod))

    def test_loaded(self):
        imports.postLoadHooks['spam'] = None

        mod = imports.LazyModule('spam', 'eggs')

        self.assertFalse(imports._isLazy(mod))

class WhenImportedTestCase(PostLoadHookClearingTestCase):
    def setUp(self):
        PostLoadHookClearingTestCase.setUp(self)

        self.path = os.path.join(os.path.dirname(__file__), 'imports')
        self.mods = sys.modules.copy()
        self.executed = False

        sys.path.insert(0, self.path)

    def tearDown(self):
        PostLoadHookClearingTestCase.tearDown(self)

        del sys.path[0]

        _util.replace_dict(self.mods, sys.modules)

    def _hook(self, module):
        self.executed = True

    def test_module(self):
        self._clearModules('spam')
        imports.whenImported('spam', self._hook)

        self.assertTrue('spam' in imports.postLoadHooks.keys())
        self.assertEquals(imports.postLoadHooks['spam'], [self._hook])

        import spam
        imports._loadModule(spam)

        self.assertTrue(self.executed)

    def _clearModules(self, *args):
        for mod in args:
            try:
                del sys.modules[mod]
            except KeyError:
                pass

    def test_submodule(self):
        self._clearModules('foo', 'foo.bar', 'foo.bar.baz')
        imports.whenImported('foo.bar.baz', self._hook)

        self.assertTrue('foo' in imports.postLoadHooks.keys())
        self.assertFalse('foo.bar' in imports.postLoadHooks.keys())
        self.assertFalse('foo.bar.baz' in imports.postLoadHooks.keys())

        self.assertEquals(len(imports.postLoadHooks['foo']), 1)

        import foo
        imports._loadModule(foo)

        self.assertTrue('foo' in imports.postLoadHooks.keys())
        self.assertTrue('foo.bar' in imports.postLoadHooks.keys())
        self.assertFalse('foo.bar.baz' in imports.postLoadHooks.keys())
        self.assertEquals(imports.postLoadHooks['foo'], None)
        self.assertEquals(len(imports.postLoadHooks['foo.bar']), 1)
        self.assertTrue(hasattr(foo, 'bar'))
        self.assertEquals(self.executed, False)

        # ensure that the module was actually loaded
        self.assertEquals(foo.spam, 'eggs')

        import foo.bar
        imports._loadModule(foo.bar)

        self.assertTrue('foo' in imports.postLoadHooks.keys())
        self.assertTrue('foo.bar' in imports.postLoadHooks.keys())
        self.assertTrue('foo.bar.baz' in imports.postLoadHooks.keys())
        self.assertEquals(imports.postLoadHooks['foo'], None)
        self.assertEquals(imports.postLoadHooks['foo.bar'], None)
        self.assertEquals(len(imports.postLoadHooks['foo.bar.baz']), 1)
        self.assertTrue(hasattr(foo.bar, 'baz'))
        self.assertEquals(self.executed, False)

        import foo.bar.baz
        imports._loadModule(foo.bar.baz)

        self.assertTrue('foo' in imports.postLoadHooks.keys())
        self.assertTrue('foo.bar' in imports.postLoadHooks.keys())
        self.assertTrue('foo.bar.baz' in imports.postLoadHooks.keys())
        self.assertEquals(imports.postLoadHooks['foo'], None)
        self.assertEquals(imports.postLoadHooks['foo.bar'], None)
        self.assertEquals(imports.postLoadHooks['foo.bar.baz'], None)
        self.assertEquals(self.executed, True)

    def test_multipleChildDeepParent(self):
        self._clearModules('foo', 'foo.bar', 'foo.bar.baz', 'foo.bar.gak')
        self._mods = []

        imports.whenImported('foo.bar.baz', lambda m: self._mods.append(m))
        imports.whenImported('foo.bar.gak', lambda m: self._mods.append(m))

        import foo.bar.baz
        import foo.bar.gak

        imports._loadModule(foo.bar.baz)
        imports._loadModule(foo.bar.gak)

        self.assertEquals(self._mods, [foo.bar.baz, foo.bar.gak])

class FindModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__), 'imports')
        sys.path.insert(0, self.path)

    def tearDown(self):
        sys.path.remove(self.path)

    def test_root(self):
        fm = imports.find_module('spam')

        self.assertEquals(type(fm[0]), file)
        self.assertTrue(fm[1].startswith(os.path.join(self.path, 'spam.py')))

    def test_package(self):
        fm = imports.find_module('foo')

        self.assertEquals(fm[0], None)
        self.assertEquals(fm[1], os.path.join(self.path, 'foo'))

    def test_subpackage(self):
        fm = imports.find_module('bar', [os.path.join(self.path, 'foo')])

        self.assertEquals(fm[0], None)
        self.assertEquals(fm[1], os.path.join(self.path, 'foo', 'bar'))

    def test_error(self):
        self.assertRaises(ImportError, imports.find_module, 'eggs')

def suite():
    """
    Unit tests for AMF utilities.
    """
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(JoinPathTestCase))
    suite.addTest(unittest.makeSuite(GetModuleHooksTestCase))
    suite.addTest(unittest.makeSuite(LazyModuleTestCase))
    suite.addTest(unittest.makeSuite(IsLazyTestCase))
    suite.addTest(unittest.makeSuite(WhenImportedTestCase))
    suite.addTest(unittest.makeSuite(FindModuleTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
