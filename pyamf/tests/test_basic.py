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
        self.assertEquals(x.encoding, None)

        x = pyamf.ClassAlias(Foo, 'org.example.foo.Foo', read_func=ord,
            write_func=str, encoding='123')

        self.assertEquals(x.klass, Foo)
        self.assertEquals(x.alias, 'org.example.foo.Foo')
        self.assertEquals(x.read_func, ord)
        self.assertEquals(x.write_func, str)
        self.assertEquals(x.encoding, '123')

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

class HelperTestCase(unittest.TestCase):
    """
    Tests all helper functions in pyamf.__init__
    """
    def test_get_decoder(self):
        from pyamf import amf0, amf3

        decoder = pyamf._get_decoder(pyamf.AMF0)
        self.assertEquals(decoder, amf0.Decoder)

        decoder = pyamf._get_decoder(pyamf.AMF3)
        self.assertEquals(decoder, amf3.Decoder)

        self.assertRaises(ValueError, pyamf._get_decoder, 'foo')

    def test_get_encoder(self):
        from pyamf import amf0, amf3

        encoder = pyamf._get_encoder(pyamf.AMF0)
        self.assertEquals(encoder, amf0.Encoder)

        encoder = pyamf._get_encoder(pyamf.AMF3)
        self.assertEquals(encoder, amf3.Encoder)

        self.assertRaises(ValueError, pyamf._get_encoder, 'foo')

def suite():
    import pyamf

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(BagTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
