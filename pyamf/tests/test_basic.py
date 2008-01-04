# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
General tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf

class Foo(object):
    """
    A generic class used in class registering etc.
    """

class ASObjectTestCase(unittest.TestCase):
    """
    I exercise all functionality relating to the L{pyamf.ASObject} class.
    """

    def test_init(self):
        bag = pyamf.ASObject(foo='bar', baz='foo')

        self.assertEquals(bag, dict(foo='bar', baz='foo'))
        self.assertEquals(bag.foo, 'bar')
        self.assertEquals(bag.baz, 'foo')

    def test_eq(self):
        bag = pyamf.ASObject()

        self.assertEquals(bag, {})
        self.assertNotEquals(bag, {'foo': 'bar'})

        bag2 = pyamf.ASObject()

        self.assertEquals(bag2, {})
        self.assertEquals(bag, bag2)
        self.assertNotEquals(bag, None)

    def test_setitem(self):
        bag = pyamf.ASObject()

        self.assertEquals(bag, {})

        bag['foo'] = 'bar'

        self.assertEquals(bag.foo, 'bar')

    def test_delitem(self):
        bag = pyamf.ASObject({'foo': 'bar'})

        self.assertEquals(bag.foo, 'bar')
        del bag['foo']

        self.assertRaises(AttributeError, lambda: bag.foo)

    def test_getitem(self):
        bag = pyamf.ASObject({'foo': 'bar'})

        self.assertEquals(bag['foo'], 'bar')

    def test_iter(self):
        bag = pyamf.ASObject({'foo': 'bar'})

        x = []

        for k, v in bag.iteritems():
            x.append((k, v))

        self.assertEquals(x, [('foo', 'bar')])

class ClassMetaDataTestCase(unittest.TestCase):
    def test_create(self):
        x = pyamf.ClassMetaData()

        self.assertEquals(x, [])
        self.assertEquals(len(x), 0)

        x = pyamf.ClassMetaData('dynamic')

        self.assertEquals(x, ['dynamic'])
        self.assertEquals(len(x), 1)

        x = pyamf.ClassMetaData(['static'])

        self.assertEquals(x, ['static'])
        self.assertEquals(len(x), 1)

        self.assertRaises(ValueError, pyamf.ClassMetaData, ['foo'])
        self.assertRaises(ValueError, pyamf.ClassMetaData, 'foo')

    def test_append(self):
        x = pyamf.ClassMetaData()

        x.append('dynamic')

        self.assertEquals(x, ['dynamic'])
        self.assertEquals(len(x), 1)

        x.append('dynamic')

        self.assertEquals(x, ['dynamic'])
        self.assertEquals(len(x), 1)

        #x.append('static')
        # XXX nick: how to trap the warning?

        self.assertRaises(ValueError, x.append, 'foo')

    def test_contains(self):
        x = pyamf.ClassMetaData()

        self.assertFalse('dynamic' in x)
        x.append('dynamic')
        self.assertTrue('dynamic' in x)

class ClassAliasTestCase(unittest.TestCase):
    """
    Test all functionality relating to the class L{ClassAlias}.
    """

    def test_init(self):
        x = pyamf.ClassAlias(Foo, 'org.example.foo.Foo')

        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'org.example.foo.Foo')
        self.assertEquals(x.read_func, None)
        self.assertEquals(x.write_func, None)
        self.assertEquals(x.attrs, None)
        self.assertEquals(x.metadata, [])

        x = pyamf.ClassAlias(Foo, 'org.example.foo.Foo', read_func=ord,
            write_func=str)

        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'org.example.foo.Foo')
        self.assertEquals(x.read_func, ord)
        self.assertEquals(x.write_func, str)
        self.assertEquals(x.attrs, None)
        self.assertEquals(x.metadata, ['external'])

        x = pyamf.ClassAlias(Foo, 'org.example.foo.Foo', attrs=['foo', 'bar'],
            metadata=['dynamic'])

        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'org.example.foo.Foo')
        self.assertEquals(x.read_func, None)
        self.assertEquals(x.write_func, None)
        self.assertEquals(x.attrs, ['foo', 'bar'])
        self.assertEquals(x.metadata, ['dynamic'])

    def test_bad_class(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'bar', 'blah')

    def test_bad_read_func(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'bar', 'blah',
            read_func='asdfasdf')

    def test_bad_write_func(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'bar', 'blah',
            write_func='asdfasdf')

    def test_call(self):
        x = pyamf.ClassAlias(Foo, 'org.example.foo.Foo')

        y = x()

        self.assertTrue(isinstance(y, Foo))

    def test_str(self):
        class Bar(object):
            pass

        x = pyamf.ClassAlias(Bar, 'org.example.bar.Bar')

        self.assertEquals(str(x), 'org.example.bar.Bar')

    def test_eq(self):
        class A(object):
            pass

        class B(object):
            pass

        x = pyamf.ClassAlias(A, 'org.example.A')
        y = pyamf.ClassAlias(A, 'org.example.A')
        z = pyamf.ClassAlias(B, 'org.example.B')

        self.assertEquals(x, A)
        self.assertEquals(x, y)
        self.assertNotEquals(x, z)

    def test_get_class_alias(self):
        self.assertTrue(Foo not in pyamf.CLASS_CACHE)

        self.assertRaises(pyamf.UnknownClassAlias, pyamf.get_class_alias,
            'foo.bar')

        pyamf.register_class(Foo, 'foo.bar')
        x = pyamf.get_class_alias('foo.bar')

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'foo.bar')

        x = pyamf.get_class_alias(Foo)

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'foo.bar')

        pyamf.unregister_class(Foo)

    def test_anonymous(self):
        pyamf.register_class(Foo)

        x = pyamf.get_class_alias(Foo)

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, '%s.%s' % (Foo.__module__, Foo.__name__,))

        pyamf.unregister_class(Foo)

class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in pyamf.__init__
    """

    def test_get_decoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF0), amf0.Decoder)
        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF3), amf3.Decoder)
        self.assertRaises(ValueError, pyamf._get_decoder_class, 'foo')

        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF0), amf0.Decoder))
        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF3), amf3.Decoder))
        self.assertRaises(ValueError, pyamf.get_decoder, 'foo')

    def test_get_encoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF0), amf0.Encoder)
        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF3), amf3.Encoder)
        self.assertRaises(ValueError, pyamf._get_encoder_class, 'foo')

        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF0), amf0.Encoder))
        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF3), amf3.Encoder))
        self.assertRaises(ValueError, pyamf.get_encoder, 'foo')

    def test_encode(self):
        self.assertEquals('\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00',
            pyamf.encode(u'connect', 1.0).getvalue())

    def test_decode(self):
        expected = [u'connect', 1.0]
        bytes = '\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00'

        returned = [x for x in pyamf.decode(bytes)]

        self.assertEquals(expected, returned)

class RegisterClassTestCase(unittest.TestCase):
    def setUp(self):
        import copy

        self.copy = copy.copy(pyamf.CLASS_CACHE)
        self.unregister = True

    def tearDown(self):
        if self.unregister:
            pyamf.unregister_class(Foo)

    def test_simple(self):
        self.assertTrue('foo.bar' not in pyamf.CLASS_CACHE.keys())
        alias = pyamf.register_class(Foo, 'foo.bar')

        self.assertTrue('foo.bar' in pyamf.CLASS_CACHE.keys())
        self.assertEquals(pyamf.CLASS_CACHE['foo.bar'], alias)

        self.assertTrue(isinstance(alias, pyamf.ClassAlias))
        self.assertEquals(alias.klass, Foo)
        self.assertEquals(alias.alias, 'foo.bar')
        self.assertEquals(alias.attrs, None)
        self.assertEquals(alias.metadata, [])
        self.assertEquals(alias.read_func, None)
        self.assertEquals(alias.write_func, None)

    def test_attrs(self):
        pyamf.register_class(Foo, 'foo.bar', attrs=['x', 'y', 'z'])
        alias = pyamf.CLASS_CACHE['foo.bar']

        self.assertEquals(alias.attrs, ['x', 'y', 'z'])

    def test_funcs(self):
        pyamf.register_class(Foo, 'foo.bar', read_func=ord, write_func=chr)
        alias = pyamf.CLASS_CACHE['foo.bar']

        self.assertEquals(alias.read_func, ord)
        self.assertEquals(alias.write_func, chr)

    def test_metadata(self):
        pyamf.register_class(Foo, 'foo.bar', metadata=['static'])
        alias = pyamf.CLASS_CACHE['foo.bar']

        self.assertEquals(alias.metadata, ['static'])
        self.assertTrue(isinstance(alias.metadata, pyamf.ClassMetaData))

    def test_bad_metadata(self):
        self.assertRaises(ValueError, pyamf.register_class, Foo, 'foo.bar',
            metadata=['blah'])

        self.unregister = False

    def test_anonymous(self):
        pyamf.register_class(Foo)
        alias = pyamf.CLASS_CACHE['%s.%s' % (Foo.__module__, Foo.__name__,)]

        self.assertEquals(alias.metadata, ['anonymous'])

    def test_has_alias(self):
        self.assertEquals(pyamf.has_alias(Foo), False)
        pyamf.register_class(Foo)

        self.assertEquals(pyamf.has_alias(Foo), True)

class UnregisterClassTestCase(unittest.TestCase):
    def test_klass(self):
        alias = pyamf.register_class(Foo, 'foo.bar')

        pyamf.unregister_class(Foo)
        self.assertTrue('foo.bar' not in pyamf.CLASS_CACHE.keys())
        self.assertTrue(alias not in pyamf.CLASS_CACHE)

    def test_alias(self):
        alias = pyamf.register_class(Foo, 'foo.bar')

        pyamf.unregister_class('foo.bar')
        self.assertTrue('foo.bar' not in pyamf.CLASS_CACHE.keys())
        self.assertTrue(alias not in pyamf.CLASS_CACHE)

class ClassLoaderTestCase(unittest.TestCase):
    def setUp(self):
        import copy

        self.cl = copy.copy(pyamf.CLASS_LOADERS)

        pyamf.CLASS_LOADERS = []

    def tearDown(self):
        pyamf.CLASS_LOADERS = self.cl

    def test_register(self):
        self.assertTrue(chr not in pyamf.CLASS_LOADERS)
        pyamf.register_class_loader(chr)
        self.assertTrue(chr in pyamf.CLASS_LOADERS)

    def test_bad_register(self):
        self.assertRaises(TypeError, pyamf.register_class_loader, 1)
        pyamf.register_class_loader(ord)
        self.assertRaises(ValueError, pyamf.register_class_loader, ord)

    def test_unregister(self):
        pyamf.register_class_loader(chr)
        self.assertTrue(chr in pyamf.CLASS_LOADERS)

        pyamf.unregister_class_loader(chr)
        self.assertTrue(chr not in pyamf.CLASS_LOADERS)

        self.assertRaises(LookupError, pyamf.unregister_class_loader, chr)

    def test_load_class(self):
        def class_loader(x):
            self.assertEquals(x, 'foo.bar')

            return Foo

        pyamf.register_class_loader(class_loader)

        self.assertTrue('foo.bar' not in pyamf.CLASS_CACHE.keys())
        pyamf.load_class('foo.bar')
        self.assertTrue('foo.bar' in pyamf.CLASS_CACHE.keys())

        pyamf.unregister_class('foo.bar')

    def test_load_unknown_class(self):
        def class_loader(x):
            return None

        pyamf.register_class_loader(class_loader)

        self.assertRaises(pyamf.UnknownClassAlias, pyamf.load_class, 'foo.bar')

    def test_load_class_by_alias(self):
        def class_loader(x):
            self.assertEquals(x, 'foo.bar')
            return pyamf.ClassAlias(Foo, 'foo.bar')

        pyamf.register_class_loader(class_loader)

        self.assertTrue('foo.bar' not in pyamf.CLASS_CACHE.keys())
        pyamf.load_class('foo.bar')
        self.assertTrue('foo.bar' in pyamf.CLASS_CACHE.keys())

        pyamf.unregister_class('foo.bar')

    def test_load_class_bad_return(self):
        def class_loader(x):
            return 'xyz'

        pyamf.register_class_loader(class_loader)

        self.assertRaises(TypeError, pyamf.load_class, 'foo.bar')

    def test_load_class_by_module(self):
        pyamf.load_class('__builtin__.tuple')

        pyamf.unregister_class('__builtin__.tuple')

    def test_load_class_by_module_bad(self):
        self.assertRaises(pyamf.UnknownClassAlias, pyamf.load_class,
            '__builtin__.tuple.')

class TypeMapTestCase(unittest.TestCase):
    def setUp(self):
        self.tm = dict(pyamf.TYPE_MAP)

    def tearDown(self):
        pyamf.TYPE_MAP = self.tm

    def test_add_invalid(self):
        import imp

        mod = imp.new_module('foo')
        self.assertRaises(TypeError, pyamf.add_type, mod)
        self.assertRaises(TypeError, pyamf.add_type, {})
        self.assertRaises(TypeError, pyamf.add_type, 'foo')
        self.assertRaises(TypeError, pyamf.add_type, u'bar')
        self.assertRaises(TypeError, pyamf.add_type, 1)
        self.assertRaises(TypeError, pyamf.add_type, 234234L)
        self.assertRaises(TypeError, pyamf.add_type, 34.23)
        self.assertRaises(TypeError, pyamf.add_type, None)
        self.assertRaises(TypeError, pyamf.add_type, object())

        class A:
            pass

        self.assertRaises(TypeError, pyamf.add_type, A())

    def test_add_same(self):
        td = pyamf.add_type(chr)
        self.assertRaises(KeyError, pyamf.add_type, chr)
        
    def test_add_class(self):
        class A:
            pass

        class B(object):
            pass

        pyamf.add_type(A)
        self.assertTrue(A in pyamf.TYPE_MAP)

        td2 = pyamf.add_type(B)
        self.assertTrue(B in pyamf.TYPE_MAP)

    def test_add_callable(self):
        td = pyamf.add_type(ord)

        self.assertTrue(ord in pyamf.TYPE_MAP)
        self.assertTrue(td in pyamf.TYPE_MAP.values())

    def test_add_multiple(self):
        td = pyamf.add_type((chr,))

        class A(object):
            pass

        class B(object):
            pass

        class C(object):
            pass

        td = pyamf.add_type([A, B, C])

    def test_get_type(self):
        self.assertRaises(KeyError, pyamf.get_type, chr)
        td = pyamf.add_type((chr,))
        self.assertRaises(KeyError, pyamf.get_type, chr)

        td2 = pyamf.get_type((chr,))
        self.assertEquals(td, td2)

        td2 = pyamf.get_type([chr,])
        self.assertEquals(td, td2)

    def test_remove(self):
        self.assertRaises(KeyError, pyamf.remove_type, chr)
        td = pyamf.add_type((chr,))

        self.assertRaises(KeyError, pyamf.remove_type, chr)
        td2 = pyamf.remove_type((chr,))

        self.assertEquals(td, td2)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ASObjectTestCase))
    suite.addTest(unittest.makeSuite(ClassMetaDataTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))
    suite.addTest(unittest.makeSuite(RegisterClassTestCase))
    suite.addTest(unittest.makeSuite(UnregisterClassTestCase))
    suite.addTest(unittest.makeSuite(ClassLoaderTestCase))
    suite.addTest(unittest.makeSuite(TypeMapTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
