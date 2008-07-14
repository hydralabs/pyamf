# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
General tests.

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf.tests.util import ClassCacheClearingTestCase

class Spam(object):
    """
    A generic class used in class registering etc.
    """

class ASObjectTestCase(unittest.TestCase):
    """
    I exercise all functionality relating to the L{ASObject<pyamf.ASObject>}
    class.
    """

    def test_init(self):
        bag = pyamf.ASObject(spam='eggs', baz='spam')

        self.assertEquals(bag, dict(spam='eggs', baz='spam'))
        self.assertEquals(bag.spam, 'eggs')
        self.assertEquals(bag.baz, 'spam')

    def test_eq(self):
        bag = pyamf.ASObject()

        self.assertEquals(bag, {})
        self.assertNotEquals(bag, {'spam': 'eggs'})

        bag2 = pyamf.ASObject()

        self.assertEquals(bag2, {})
        self.assertEquals(bag, bag2)
        self.assertNotEquals(bag, None)

    def test_setitem(self):
        bag = pyamf.ASObject()

        self.assertEquals(bag, {})

        bag['spam'] = 'eggs'

        self.assertEquals(bag.spam, 'eggs')

    def test_delitem(self):
        bag = pyamf.ASObject({'spam': 'eggs'})

        self.assertEquals(bag.spam, 'eggs')
        del bag['spam']

        self.assertRaises(AttributeError, lambda: bag.spam)

    def test_getitem(self):
        bag = pyamf.ASObject({'spam': 'eggs'})

        self.assertEquals(bag['spam'], 'eggs')

    def test_iter(self):
        bag = pyamf.ASObject({'spam': 'eggs'})

        x = []

        for k, v in bag.iteritems():
            x.append((k, v))

        self.assertEquals(x, [('spam', 'eggs')])

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

        self.assertRaises(ValueError, pyamf.ClassMetaData, ['spam'])
        self.assertRaises(ValueError, pyamf.ClassMetaData, 'spam')

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

        self.assertRaises(ValueError, x.append, 'spam')

    def test_contains(self):
        x = pyamf.ClassMetaData()

        self.assertFalse('dynamic' in x)
        x.append('dynamic')
        self.assertTrue('dynamic' in x)

class ClassAliasTestCase(ClassCacheClearingTestCase):
    """
    Test all functionality relating to the class L{ClassAlias}.
    """

    def test_init(self):
        x = pyamf.ClassAlias(Spam, 'org.example.spam.Spam')

        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, 'org.example.spam.Spam')
        self.assertEquals(x.attrs, None)
        self.assertEquals(x.metadata, [])
        self.assertEquals(x.attr_func, None)

        x = pyamf.ClassAlias(Spam, 'org.example.spam.Spam', attrs=['spam', 'eggs'],
            metadata=['static'])

        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, 'org.example.spam.Spam')
        self.assertEquals(x.attrs, ['spam', 'eggs'])
        self.assertEquals(x.metadata, ['static'])
        self.assertEquals(x.attr_func, None)

        x = pyamf.ClassAlias(Spam, 'org.example.foo.Spam', attrs=['spam', 'eggs'],
            attr_func=ord, metadata=['dynamic'])

        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, 'org.example.foo.Spam')
        self.assertEquals(x.attrs, ['spam', 'eggs'])
        self.assertEquals(x.metadata, ['dynamic'])
        self.assertEquals(x.attr_func, ord)

    def test_bad_class(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'eggs', 'blah')

    def test_bad_read_func(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'eggs', 'blah',
            read_func='asdfasdf')

    def test_bad_write_func(self):
        self.assertRaises(TypeError, pyamf.ClassAlias, 'eggs', 'blah',
            write_func='asdfasdf')

    def test_call(self):
        x = pyamf.ClassAlias(Spam, 'org.example.spam.Spam')

        y = x()

        self.assertTrue(isinstance(y, Spam))

    def test_str(self):
        class Eggs(object):
            pass

        x = pyamf.ClassAlias(Eggs, 'org.example.eggs.Eggs')

        self.assertEquals(str(x), 'org.example.eggs.Eggs')

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
        self.assertTrue(Spam not in pyamf.CLASS_CACHE)

        self.assertRaises(pyamf.UnknownClassAlias, pyamf.get_class_alias,
            'spam.eggs')

        pyamf.register_class(Spam, 'spam.eggs')
        x = pyamf.get_class_alias('spam.eggs')

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, 'spam.eggs')

        x = pyamf.get_class_alias(Spam)

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, 'spam.eggs')

    def test_anonymous(self):
        pyamf.register_class(Spam)

        x = pyamf.get_class_alias(Spam)

        self.assertTrue(isinstance(x, pyamf.ClassAlias))
        self.assertEquals(x.klass, Spam)
        self.assertEquals(x.alias, '%s.%s' % (Spam.__module__, Spam.__name__,))

    def test_external(self):
        class A(object):
            pass

        class B:
            pass

        self.assertRaises(AttributeError, pyamf.register_class, A,
            metadata=['external'])
        self.assertRaises(AttributeError, pyamf.register_class, B,
            metadata=['external'])

        A.__readamf__ = None
        B.__readamf__ = None

        self.assertRaises(AttributeError, pyamf.register_class, A,
            metadata=['external'])
        self.assertRaises(AttributeError, pyamf.register_class, B,
            metadata=['external'])

        A.__readamf__ = lambda x: None
        B.__readamf__ = lambda x: None

        self.assertRaises(AttributeError, pyamf.register_class, A,
            metadata=['external'])
        self.assertRaises(AttributeError, pyamf.register_class, B,
            metadata=['external'])

        A.__writeamf__ = 'foo'
        B.__writeamf__ = 'bar'

        self.assertRaises(TypeError, pyamf.register_class, A,
            metadata=['external'])
        self.assertRaises(TypeError, pyamf.register_class, B,
            metadata=['external'])

        A.__writeamf__ = lambda x: None
        B.__writeamf__ = lambda x: None

        pyamf.register_class(A, metadata=['external'])
        pyamf.register_class(B, metadata=['external'])

    def test_get_attrs(self):
        pyamf.register_class(Spam)
        alias = pyamf.get_class_alias(Spam)

        x = Spam()
        self.assertEquals(alias.getAttrs(x), None)

        pyamf.unregister_class(Spam)

        pyamf.register_class(Spam, attrs=['foo'])
        alias = pyamf.get_class_alias(Spam)

        x = Spam()
        self.assertEquals(alias.getAttrs(x), ['foo'])

        pyamf.unregister_class(Spam)

        pyamf.register_class(Spam, metadata=['dynamic'])
        alias = pyamf.get_class_alias(Spam)

        x = Spam()
        self.assertEquals(alias.getAttrs(x), None)

        pyamf.unregister_class(Spam)

        def af(x):
            self.assertEquals(self._obj, x)

            return ['bar']

        pyamf.register_class(Spam, attr_func=af, metadata=['dynamic'])
        alias = pyamf.get_class_alias(Spam)

        self._obj = Spam()
        self.assertEquals(alias.getAttrs(self._obj), ['bar'])

        pyamf.unregister_class(Spam)

        def af(x):
            self.assertEquals(self._obj, x)

            return ['bar']

        pyamf.register_class(Spam, attrs=['foo', 'bar'], attr_func=af, metadata=['dynamic'])
        alias = pyamf.get_class_alias(Spam)

        self._obj = Spam()
        self.assertEquals(alias.getAttrs(self._obj), ['foo', 'bar'])

class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in C{pyamf.__init__}
    """

    def test_get_decoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF0), amf0.Decoder)
        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF3), amf3.Decoder)
        self.assertRaises(ValueError, pyamf._get_decoder_class, 'spam')

        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF0), amf0.Decoder))
        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF3), amf3.Decoder))
        self.assertRaises(ValueError, pyamf.get_decoder, 'spam')

        context = amf0.Context()
        decoder = pyamf.get_decoder(pyamf.AMF0, data='123', context=context)
        self.assertEquals(decoder.stream.getvalue(), '123')
        self.assertEquals(decoder.context, context)

        context = amf3.Context()
        decoder = pyamf.get_decoder(pyamf.AMF3, data='456', context=context)
        self.assertEquals(decoder.stream.getvalue(), '456')
        self.assertEquals(decoder.context, context)

    def test_get_encoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF0), amf0.Encoder)
        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF3), amf3.Encoder)
        self.assertRaises(ValueError, pyamf._get_encoder_class, 'spam')

        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF0), amf0.Encoder))
        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF3), amf3.Encoder))
        self.assertRaises(ValueError, pyamf.get_encoder, 'spam')

        context = amf0.Context()
        encoder = pyamf.get_encoder(pyamf.AMF0, data='spam', context=context)
        self.assertEquals(encoder.stream.getvalue(), 'spam')
        self.assertEquals(encoder.context, context)

        context = amf3.Context()
        encoder = pyamf.get_encoder(pyamf.AMF3, data='eggs', context=context)
        self.assertEquals(encoder.stream.getvalue(), 'eggs')
        self.assertEquals(encoder.context, context)

    def test_encode(self):
        self.assertEquals('\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00',
            pyamf.encode(u'connect', 1.0).getvalue())

    def test_decode(self):
        expected = [u'connect', 1.0]
        bytes = '\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00'

        returned = [x for x in pyamf.decode(bytes)]

        self.assertEquals(expected, returned)

class RegisterClassTestCase(ClassCacheClearingTestCase):
    def test_simple(self):
        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        alias = pyamf.register_class(Spam, 'spam.eggs')

        self.assertTrue('spam.eggs' in pyamf.CLASS_CACHE.keys())
        self.assertEquals(pyamf.CLASS_CACHE['spam.eggs'], alias)

        self.assertTrue(isinstance(alias, pyamf.ClassAlias))
        self.assertEquals(alias.klass, Spam)
        self.assertEquals(alias.alias, 'spam.eggs')
        self.assertEquals(alias.attrs, None)
        self.assertEquals(alias.metadata, [])

    def test_attrs(self):
        pyamf.register_class(Spam, 'spam.eggs', attrs=['x', 'y', 'z'])
        alias = pyamf.CLASS_CACHE['spam.eggs']

        self.assertEquals(alias.attrs, ['x', 'y', 'z'])

    def test_metadata(self):
        self.assertRaises(ValueError, pyamf.register_class, Spam, 'spam.eggs',
            metadata=['static'])
        pyamf.register_class(Spam, 'spam.eggs', metadata=['static'], attrs=['x'])
        alias = pyamf.CLASS_CACHE['spam.eggs']

        self.assertEquals(alias.metadata, ['static'])
        self.assertEquals(alias.attrs, ['x'])
        self.assertTrue(isinstance(alias.metadata, pyamf.ClassMetaData))

    def test_bad_metadata(self):
        self.assertRaises(ValueError, pyamf.register_class, Spam, 'spam.eggs',
            metadata=['blah'])

    def test_anonymous(self):
        pyamf.register_class(Spam)
        alias = pyamf.CLASS_CACHE['%s.%s' % (Spam.__module__, Spam.__name__,)]

        self.assertEquals(alias.metadata, ['anonymous'])

    def test_dynamic(self):
        pyamf.register_class(Spam, attr_func=ord, metadata=['dynamic'])

        alias = pyamf.CLASS_CACHE['%s.%s' % (Spam.__module__, Spam.__name__,)]

        self.assertTrue('dynamic' in alias.metadata)
        self.assertEquals(alias.attr_func, ord)

    def test_bad_attr_fun(self):
        self.assertRaises(TypeError, pyamf.register_class, Spam, attr_func='boo', metadata=['dynamic'])

    def test_has_alias(self):
        self.assertEquals(pyamf.has_alias(Spam), False)
        pyamf.register_class(Spam)

        self.assertEquals(pyamf.has_alias(Spam), True)

    def test_required_arguments(self):
        class Foo(object):
            def __init__(self, bar, valid=1):
                pass
        self.assertRaises(TypeError, pyamf.register_class, Foo)

        class Foo(object):
            def __init__(self, bar, valid):
                pass
        self.assertRaises(TypeError, pyamf.register_class, Foo)

        class Foo(object):
            def __init__(self, bar=1, valid=1):
                pass
        pyamf.register_class(Foo)


class UnregisterClassTestCase(ClassCacheClearingTestCase):
    def test_klass(self):
        alias = pyamf.register_class(Spam, 'spam.eggs')

        pyamf.unregister_class(Spam)
        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        self.assertTrue(alias not in pyamf.CLASS_CACHE)

    def test_alias(self):
        alias = pyamf.register_class(Spam, 'spam.eggs')

        pyamf.unregister_class('spam.eggs')
        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        self.assertTrue(alias not in pyamf.CLASS_CACHE)

class ClassLoaderTestCase(ClassCacheClearingTestCase):
    def test_register(self):
        self.assertTrue(chr not in pyamf.CLASS_LOADERS)
        pyamf.register_class_loader(chr)
        self.assertTrue(chr in pyamf.CLASS_LOADERS)

    def test_bad_register(self):
        self.assertRaises(TypeError, pyamf.register_class_loader, 1)
        pyamf.register_class_loader(ord)
        self.assertRaises(ValueError, pyamf.register_class_loader, ord)

    def test_unregister(self):
        self.assertTrue(chr not in pyamf.CLASS_LOADERS)
        pyamf.register_class_loader(chr)
        self.assertTrue(chr in pyamf.CLASS_LOADERS)

        pyamf.unregister_class_loader(chr)
        self.assertTrue(chr not in pyamf.CLASS_LOADERS)

        self.assertRaises(LookupError, pyamf.unregister_class_loader, chr)

    def test_load_class(self):
        def class_loader(x):
            self.assertEquals(x, 'spam.eggs')

            return Spam

        pyamf.register_class_loader(class_loader)

        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        pyamf.load_class('spam.eggs')
        self.assertTrue('spam.eggs' in pyamf.CLASS_CACHE.keys())

    def test_load_unknown_class(self):
        def class_loader(x):
            return None

        pyamf.register_class_loader(class_loader)

        self.assertRaises(pyamf.UnknownClassAlias, pyamf.load_class, 'spam.eggs')

    def test_load_class_by_alias(self):
        def class_loader(x):
            self.assertEquals(x, 'spam.eggs')
            return pyamf.ClassAlias(Spam, 'spam.eggs')

        pyamf.register_class_loader(class_loader)

        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        pyamf.load_class('spam.eggs')
        self.assertTrue('spam.eggs' in pyamf.CLASS_CACHE.keys())

    def test_load_class_bad_return(self):
        def class_loader(x):
            return 'xyz'

        pyamf.register_class_loader(class_loader)

        self.assertRaises(TypeError, pyamf.load_class, 'spam.eggs')

    def test_load_class_by_module(self):
        pyamf.load_class('__builtin__.tuple')

    def test_load_class_by_module_bad(self):
        self.assertRaises(pyamf.UnknownClassAlias, pyamf.load_class,
            '__builtin__.tuple.')

class TypeMapTestCase(unittest.TestCase):
    def setUp(self):
        self.tm = dict(pyamf.TYPE_MAP)

    def tearDown(self):
        pyamf.TYPE_MAP = self.tm

    def test_add_invalid(self):
        import new

        mod = new.module('spam')
        self.assertRaises(TypeError, pyamf.add_type, mod)
        self.assertRaises(TypeError, pyamf.add_type, {})
        self.assertRaises(TypeError, pyamf.add_type, 'spam')
        self.assertRaises(TypeError, pyamf.add_type, u'eggs')
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

class ErrorClassMapTestCase(unittest.TestCase):
    """
    I test all functionality related to manipulating L{pyamf.ERROR_CLASS_MAP}
    """

    def setUp(self):
        self.map_copy = pyamf.ERROR_CLASS_MAP.copy()

    def tearDown(self):
        pyamf.ERROR_CLASS_MAP = self.map_copy

    def test_add(self):
        class A:
            pass

        class B(Exception):
            pass

        self.assertRaises(TypeError, pyamf.add_error_class, None, 'a')

        # class A does not sub-class Exception
        self.assertRaises(TypeError, pyamf.add_error_class, A, 'a')

        pyamf.add_error_class(B, 'b')
        self.assertEquals(pyamf.ERROR_CLASS_MAP['b'], B)

        pyamf.add_error_class(B, 'a')
        self.assertEquals(pyamf.ERROR_CLASS_MAP['a'], B)

        class C(Exception):
            pass

        self.assertRaises(ValueError, pyamf.add_error_class, C, 'b')

    def test_remove(self):
        class B(Exception):
            pass

        pyamf.ERROR_CLASS_MAP['abc'] = B

        self.assertRaises(TypeError, pyamf.remove_error_class, None)

        pyamf.remove_error_class('abc')
        self.assertFalse('abc' in pyamf.ERROR_CLASS_MAP.keys())
        self.assertRaises(KeyError, pyamf.ERROR_CLASS_MAP.__getitem__, 'abc')

        pyamf.ERROR_CLASS_MAP['abc'] = B

        pyamf.remove_error_class(B)

        self.assertRaises(KeyError, pyamf.ERROR_CLASS_MAP.__getitem__, 'abc')
        self.assertRaises(ValueError, pyamf.remove_error_class, B)
        self.assertRaises(ValueError, pyamf.remove_error_class, 'abc')

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
    suite.addTest(unittest.makeSuite(ErrorClassMapTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
