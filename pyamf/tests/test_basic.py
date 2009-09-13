# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
General tests.

@since: 0.1.0
"""

import unittest
import new

import pyamf
from pyamf.tests.util import ClassCacheClearingTestCase, replace_dict, Spam


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

    def test_hash(self):
        bag = pyamf.ASObject({'spam': 'eggs'})

        self.assertNotEquals(None, hash(bag))


class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in C{pyamf.__init__}
    """

    def setUp(self):
        self.default_encoding = pyamf.DEFAULT_ENCODING

    def tearDown(self):
        pyamf.DEFAULT_ENCODING = self.default_encoding

    def test_get_decoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF0), amf0.Decoder)
        self.assertEquals(pyamf._get_decoder_class(pyamf.AMF3), amf3.Decoder)
        self.assertRaises(ValueError, pyamf._get_decoder_class, 'spam')

        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF0), amf0.Decoder))
        self.assertTrue(isinstance(pyamf.get_decoder(pyamf.AMF3), amf3.Decoder))
        self.assertRaises(ValueError, pyamf.get_decoder, 'spam')

        context = amf0.Context()
        decoder = pyamf.get_decoder(pyamf.AMF0, stream='123', context=context, strict=True)
        self.assertEquals(decoder.stream.getvalue(), '123')
        self.assertEquals(decoder.context, context)
        self.assertTrue(decoder.strict)

        context = amf3.Context()
        decoder = pyamf.get_decoder(pyamf.AMF3, stream='456', context=context, strict=True)
        self.assertEquals(decoder.stream.getvalue(), '456')
        self.assertEquals(decoder.context, context)
        self.assertTrue(decoder.strict)

    def test_get_encoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF0), amf0.Encoder)
        self.assertEquals(pyamf._get_encoder_class(pyamf.AMF3), amf3.Encoder)
        self.assertRaises(ValueError, pyamf._get_encoder_class, 'spam')

        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF0), amf0.Encoder))
        self.assertTrue(isinstance(pyamf.get_encoder(pyamf.AMF3), amf3.Encoder))
        self.assertRaises(ValueError, pyamf.get_encoder, 'spam')

        context = amf0.Context()
        encoder = pyamf.get_encoder(pyamf.AMF0, stream='spam', context=context)
        self.assertEquals(encoder.stream.getvalue(), 'spam')
        self.assertEquals(encoder.context, context)
        self.assertFalse(encoder.strict)

        context = amf3.Context()
        encoder = pyamf.get_encoder(pyamf.AMF3, stream='eggs', context=context)
        self.assertFalse(encoder.strict)

        encoder = pyamf.get_encoder(pyamf.AMF0, strict=True)
        self.assertTrue(encoder.strict)

        encoder = pyamf.get_encoder(pyamf.AMF3, strict=True)
        self.assertTrue(encoder.strict)

    def test_encode(self):
        self.assertEquals('\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00',
            pyamf.encode(u'connect', 1.0).getvalue())

    def test_decode(self):
        expected = [u'connect', 1.0]
        bytes = '\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00'

        returned = [x for x in pyamf.decode(bytes)]

        self.assertEquals(expected, returned)

    def test_default_encoding(self):
        pyamf.DEFAULT_ENCODING = pyamf.AMF3

        x = pyamf.encode('foo').getvalue()

        self.assertEquals(x, '\x06\x07foo')

        pyamf.DEFAULT_ENCODING = pyamf.AMF0

        x = pyamf.encode('foo').getvalue()

        self.assertEquals(x, '\x02\x00\x03foo')


class UnregisterClassTestCase(ClassCacheClearingTestCase):
    def test_klass(self):
        alias = pyamf.register_class(Spam, 'spam.eggs')

        pyamf.unregister_class(Spam)
        self.assertTrue('spam.eggs' not in pyamf.CLASS_CACHE.keys())
        self.assertTrue(Spam not in pyamf.CLASS_CACHE.keys())
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


class DummyAlias(pyamf.ClassAlias):
    pass


class RegisterAliasTypeTestCase(unittest.TestCase):
    def setUp(self):
        self.old_aliases = pyamf.ALIAS_TYPES.copy()

    def tearDown(self):
        replace_dict(self.old_aliases, pyamf.ALIAS_TYPES)

    def test_bad_klass(self):
        self.assertRaises(TypeError, pyamf.register_alias_type, 1)

    def test_subclass(self):
        self.assertFalse(issubclass(self.__class__, pyamf.ClassAlias))
        self.assertRaises(ValueError, pyamf.register_alias_type, self.__class__)

    def test_no_args(self):
        self.assertTrue(issubclass(DummyAlias, pyamf.ClassAlias))
        self.assertRaises(ValueError, pyamf.register_alias_type, DummyAlias)

    def test_type_args(self):
        self.assertTrue(issubclass(DummyAlias, pyamf.ClassAlias))
        self.assertRaises(TypeError, pyamf.register_alias_type, DummyAlias, 1)

    def test_single(self):
        class A(object):
            pass

        pyamf.register_alias_type(DummyAlias, A)

        self.assertTrue(DummyAlias in pyamf.ALIAS_TYPES.keys())
        self.assertEquals(pyamf.ALIAS_TYPES[DummyAlias], (A,))

    def test_multiple(self):
        class A(object):
            pass

        class B(object):
            pass

        self.assertRaises(TypeError, pyamf.register_alias_type, DummyAlias, A, 'hello')

        pyamf.register_alias_type(DummyAlias, A, B)
        self.assertTrue(DummyAlias in pyamf.ALIAS_TYPES.keys())
        self.assertEquals(pyamf.ALIAS_TYPES[DummyAlias], (A, B))

    def test_duplicate(self):
        class A(object):
            pass

        pyamf.register_alias_type(DummyAlias, A)

        self.assertRaises(RuntimeError, pyamf.register_alias_type, DummyAlias, A)


class BaseContextTestCase(unittest.TestCase):
    def test_no_alias(self):
        x = pyamf.BaseContext()

        self.assertEquals(x.class_aliases, {})

        class A:
            pass

        self.assertNotEquals(x.getClassAlias(A), None)

    def test_registered_alias(self):
        x = pyamf.BaseContext()

        self.assertEquals(x.class_aliases, {})

        class A:
            pass

        pyamf.register_class(A)
        alias = x.getClassAlias(A)

        self.assertTrue(isinstance(alias, pyamf.ClassAlias))
        self.assertEquals(alias.__class__, pyamf.ClassAlias)
        self.assertEquals(alias.klass, A)

    def test_registered_deep(self):
        x = pyamf.BaseContext()

        self.assertEquals(x.class_aliases, {})

        class A:
            pass

        class B(A):
            pass

        pyamf.register_alias_type(DummyAlias, A)
        alias = x.getClassAlias(B)

        self.assertTrue(isinstance(alias, pyamf.ClassAlias))
        self.assertEquals(alias.__class__, DummyAlias)
        self.assertEquals(alias.klass, B)

    def test_create(self):
        x = pyamf.BaseContext()

        self.assertTrue(x.exceptions)
        self.assertFalse(x.objects.exceptions)

    def test_object_references(self):
        x = pyamf.BaseContext()

        self.assertRaises(pyamf.ReferenceError, x.getObject, 62)

        x.exceptions = False
        self.assertEquals(x.getObject(62), None)

        x = pyamf.BaseContext()

        self.assertRaises(pyamf.ReferenceError, x.getObjectReference, object())

        x.exceptions = False
        self.assertEquals(x.getObjectReference(object()), None)


class TypedObjectTestCase(unittest.TestCase):
    def test_externalised(self):
        o = pyamf.TypedObject(None)

        self.assertRaises(pyamf.DecodeError, o.__readamf__, None)
        self.assertRaises(pyamf.EncodeError, o.__writeamf__, None)

    def test_alias(self):
        class Foo:
            pass

        alias = pyamf.TypedObjectClassAlias(Foo, 'bar')

        self.assertEquals(alias.klass, pyamf.TypedObject)
        self.assertNotEqual(alias.klass, Foo)


class PackageTestCase(ClassCacheClearingTestCase):
    """
    Tests for L{pyamf.register_package}
    """

    class NewType(object):
        pass

    class ClassicType:
        pass

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.module = new.module('foo')

        self.module.Classic = self.ClassicType
        self.module.New = self.NewType
        self.module.s = 'str'
        self.module.i = 12323
        self.module.f = 345.234
        self.module.u = u'unicode'
        self.module.l = ['list', 'of', 'junk']
        self.module.d = {'foo': 'bar', 'baz': 'gak'}
        self.module.obj = object()
        self.module.mod = self.module
        self.module.lam = lambda _: None

        self.NewType.__module__ = 'foo'
        self.ClassicType.__module__ = 'foo'

        self.spam_module = Spam.__module__
        Spam.__module__ = 'foo'

        self.names = (self.module.__name__,)

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        Spam.__module__ = self.spam_module

        self.module.__name__ = self.names

    def check_module(self, r, base_package):
        self.assertEquals(len(r), 2)

        for c in [self.NewType, self.ClassicType]:
            alias = r[c]

            self.assertTrue(isinstance(alias, pyamf.ClassAlias))
            self.assertEquals(alias.klass, c)
            self.assertEquals(alias.alias, base_package + c.__name__)

    def test_module(self):
        r = pyamf.register_package(self.module, 'com.example')
        self.check_module(r, 'com.example.')

    def test_all(self):
        self.module.Spam = Spam

        self.module.__all__ = ['Classic', 'New']

        r = pyamf.register_package(self.module, 'com.example')
        self.check_module(r, 'com.example.')

    def test_ignore(self):
        self.module.Spam = Spam

        r = pyamf.register_package(self.module, 'com.example', ignore=['Spam'])
        self.check_module(r, 'com.example.')

    def test_separator(self):
        r = pyamf.register_package(self.module, 'com.example', separator='/')

        self.ClassicType.__module__ = 'com.example'
        self.NewType.__module__ = 'com.example'
        self.check_module(r, 'com.example/')

    def test_name(self):
        self.module.__name__ = 'spam.eggs'
        self.ClassicType.__module__ = 'spam.eggs'
        self.NewType.__module__ = 'spam.eggs'

        r = pyamf.register_package(self.module)
        self.check_module(r, 'spam.eggs.')

    def test_dict(self):
        """
        @see: #585
        """
        d = dict()
        d['Spam'] = Spam

        r = pyamf.register_package(d, 'com.example', strict=False)

        self.assertEquals(len(r), 1)

        alias = r[Spam]

        self.assertTrue(isinstance(alias, pyamf.ClassAlias))
        self.assertEquals(alias.klass, Spam)
        self.assertEquals(alias.alias, 'com.example.Spam')

    def test_odd(self):
        self.assertRaises(TypeError, pyamf.register_package, object())
        self.assertRaises(TypeError, pyamf.register_package, 1)
        self.assertRaises(TypeError, pyamf.register_package, 1.2)
        self.assertRaises(TypeError, pyamf.register_package, 23897492834L)
        self.assertRaises(TypeError, pyamf.register_package, [])
        self.assertRaises(TypeError, pyamf.register_package, '')
        self.assertRaises(TypeError, pyamf.register_package, u'')

    def test_strict(self):
        self.module.Spam = Spam

        Spam.__module__ = self.spam_module

        r = pyamf.register_package(self.module, 'com.example', strict=True)
        self.check_module(r, 'com.example.')

    def test_not_strict(self):
        self.module.Spam = Spam

        Spam.__module__ = self.spam_module

        r = pyamf.register_package(self.module, 'com.example', strict=False)

        self.assertEquals(len(r), 3)

        for c in [self.NewType, self.ClassicType, Spam]:
            alias = r[c]

            self.assertTrue(isinstance(alias, pyamf.ClassAlias))
            self.assertEquals(alias.klass, c)
            self.assertEquals(alias.alias, 'com.example.' + c.__name__)

    def test_list(self):
        class Foo:
            pass

        class Bar:
            pass

        ret = pyamf.register_package([Foo, Bar], 'spam.eggs')

        self.assertEquals(len(ret), 2)

        for c in [Foo, Bar]:
            alias = ret[c]

            self.assertTrue(isinstance(alias, pyamf.ClassAlias))
            self.assertEquals(alias.klass, c)
            self.assertEquals(alias.alias, 'spam.eggs.' + c.__name__)


def suite():
    suite = unittest.TestSuite()

    test_cases = [
        ASObjectTestCase,
        HelperTestCase,
        UnregisterClassTestCase,
        ClassLoaderTestCase,
        TypeMapTestCase,
        ErrorClassMapTestCase,
        RegisterAliasTypeTestCase,
        BaseContextTestCase,
        TypedObjectTestCase,
        PackageTestCase
    ]

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
