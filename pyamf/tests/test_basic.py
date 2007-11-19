# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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

class BagTestCase(unittest.TestCase):
    """
    I exercise all functionality relating to the L{Bag} class.
    """

    def test_init(self):
        bag = pyamf.Bag(dict(foo='bar', baz='foo'))

        self.assertEquals(bag, dict(foo='bar', baz='foo'))
        self.assertEquals(bag.foo, 'bar')
        self.assertEquals(bag.baz, 'foo')

    def test_eq(self):
        bag = pyamf.Bag()

        self.assertEquals(bag, {})
        self.assertNotEquals(bag, {'foo': 'bar'})

        bag2 = pyamf.Bag()

        self.assertEquals(bag2, {})
        self.assertEquals(bag, bag2)
        self.assertNotEquals(bag, None)

    def test_setitem(self):
        bag = pyamf.Bag()

        self.assertEquals(bag, {})
        
        bag['foo'] = 'bar'

        self.assertEquals(bag.foo, 'bar')

    def test_delitem(self):
        bag = pyamf.Bag({'foo': 'bar'})

        self.assertEquals(bag.foo, 'bar')
        del bag['foo']

        self.assertRaises(AttributeError, lambda: bag.foo)
    
    def test_getitem(self):
        bag = pyamf.Bag({'foo': 'bar'})

        self.assertEquals(bag['foo'], 'bar')

    def test_iter(self):
        bag = pyamf.Bag({'foo': 'bar'})

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

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(BagTestCase))
    suite.addTest(unittest.makeSuite(ClassMetaDataTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))
    suite.addTest(unittest.makeSuite(RegisterClassTestCase))
    suite.addTest(unittest.makeSuite(UnregisterClassTestCase))
    suite.addTest(unittest.makeSuite(ClassLoaderTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
