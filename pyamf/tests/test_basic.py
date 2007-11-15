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

class Foo(object):
    pass

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

        self.assertEquals(x, y)
        self.assertNotEquals(x, z)

class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in pyamf.__init__
    """

    def test_get_decoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_decoder(pyamf.AMF0), amf0.Decoder)
        self.assertEquals(pyamf._get_decoder(pyamf.AMF3), amf3.Decoder)
        self.assertRaises(ValueError, pyamf._get_decoder, 'foo')

    def test_get_encoder(self):
        from pyamf import amf0, amf3

        self.assertEquals(pyamf._get_encoder(pyamf.AMF0), amf0.Encoder)
        self.assertEquals(pyamf._get_encoder(pyamf.AMF3), amf3.Encoder)
        self.assertRaises(ValueError, pyamf._get_encoder, 'foo')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(BagTestCase))
    suite.addTest(unittest.makeSuite(ClassMetaDataTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
