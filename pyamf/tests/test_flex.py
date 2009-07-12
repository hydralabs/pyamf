# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Flex compatibility tests.

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import flex, util, amf3, amf0
from pyamf.tests.util import check_buffer


class ArrayCollectionTestCase(unittest.TestCase):
    def test_create(self):
        self.assertEquals(flex.ArrayCollection(), [])
        self.assertEquals(flex.ArrayCollection([1, 2, 3]), [1, 2, 3])
        self.assertEquals(flex.ArrayCollection(('a', 'b', 'b')), ['a', 'b', 'b'])

        class X(object):
            def __iter__(self):
                return iter(['foo', 'bar', 'baz'])

        self.assertEquals(flex.ArrayCollection(X()), ['foo', 'bar', 'baz'])

        self.assertRaises(TypeError, flex.ArrayCollection, {'first': 'Matt', 'last': 'Matthews'})

    def test_encode_amf3(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ArrayCollection()
        x.append('eggs')

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n\x07Cflex.messaging.io.ArrayCollection\t\x03\x01\x06\teggs')

    def test_encode_amf0(self):
        x = flex.ArrayCollection()
        x.append('eggs')

        stream = util.BufferedByteStream()
        encoder = amf0.Encoder(stream)
        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\x11\n\x07Cflex.messaging.io.ArrayCollection\t\x03\x01\x06\teggs')

    def test_decode_amf3(self):
        stream = util.BufferedByteStream(
            '\n\x07Cflex.messaging.io.ArrayCollection\t\x03\x01\x06\teggs')
        decoder = amf3.Decoder(stream)
        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ArrayCollection)
        self.assertEquals(x, ['eggs'])

    def test_decode_proxy(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x09spam'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)
        decoder.use_proxies = True

        x = decoder.readElement()

        self.assertEquals(x.__class__, pyamf.MixedArray)
        self.assertEquals(x, {'a': 'spam', 'b': 5})

    def test_decode_amf0(self):
        stream = util.BufferedByteStream(
            '\x11\n\x07Cflex.messaging.io.ArrayCollection\t\x03\x01\x06\teggs')
        decoder = amf0.Decoder(stream)
        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ArrayCollection)
        self.assertEquals(x, ['eggs'])

    def test_source_attr(self):
        s = '\n\x07Cflex.messaging.io.ArrayCollection\n\x0b\x01\rsource' \
            '\t\x05\x01\x06\x07foo\x06\x07bar\x01'

        x = pyamf.decode(s, encoding=pyamf.AMF3).next()

        self.assertTrue(isinstance(x, flex.ArrayCollection))
        self.assertEquals(x, ['foo', 'bar'])


class ArrayCollectionAPITestCase(unittest.TestCase):
    def test_addItem(self):
        a = flex.ArrayCollection()
        self.assertEquals(a, [])
        self.assertEquals(a.length, 0)

        a.addItem('hi')
        self.assertEquals(a, ['hi'])
        self.assertEquals(a.length, 1)

    def test_addItemAt(self):
        a = flex.ArrayCollection()
        self.assertEquals(a, [])

        self.assertRaises(IndexError, a.addItemAt, 'foo', -1)
        self.assertRaises(IndexError, a.addItemAt, 'foo', 1)

        a.addItemAt('foo', 0)
        self.assertEquals(a, ['foo'])
        a.addItemAt('bar', 0)
        self.assertEquals(a, ['bar', 'foo'])
        self.assertEquals(a.length, 2)

    def test_getItemAt(self):
        a = flex.ArrayCollection(['a', 'b', 'c'])

        self.assertEquals(a.getItemAt(0), 'a')
        self.assertEquals(a.getItemAt(1), 'b')
        self.assertEquals(a.getItemAt(2), 'c')

        self.assertRaises(IndexError, a.getItemAt, -1)
        self.assertRaises(IndexError, a.getItemAt, 3)

    def test_getItemIndex(self):
        a = flex.ArrayCollection(['a', 'b', 'c'])

        self.assertEquals(a.getItemIndex('a'), 0)
        self.assertEquals(a.getItemIndex('b'), 1)
        self.assertEquals(a.getItemIndex('c'), 2)
        self.assertEquals(a.getItemIndex('d'), -1)

    def test_removeAll(self):
        a = flex.ArrayCollection(['a', 'b', 'c'])
        self.assertEquals(a.length, 3)

        a.removeAll()

        self.assertEquals(a, [])
        self.assertEquals(a.length, 0)

    def test_removeItemAt(self):
        a = flex.ArrayCollection(['a', 'b', 'c'])

        self.assertRaises(IndexError, a.removeItemAt, -1)
        self.assertRaises(IndexError, a.removeItemAt, 3)

        self.assertEquals(a.removeItemAt(1), 'b')
        self.assertEquals(a, ['a', 'c'])
        self.assertEquals(a.length, 2)
        self.assertEquals(a.removeItemAt(1), 'c')
        self.assertEquals(a, ['a'])
        self.assertEquals(a.length, 1)
        self.assertEquals(a.removeItemAt(0), 'a')
        self.assertEquals(a, [])
        self.assertEquals(a.length, 0)

    def test_setItemAt(self):
        a = flex.ArrayCollection(['a', 'b', 'c'])

        self.assertEquals(a.setItemAt('d', 1), 'b')
        self.assertEquals(a, ['a', 'd', 'c'])
        self.assertEquals(a.length, 3)


class ObjectProxyTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ObjectProxy(pyamf.MixedArray(a='spam', b=5))

        encoder.writeElement(x)

        self.assertTrue(check_buffer(stream.getvalue(), (
            '\n\x07;flex.messaging.io.ObjectProxy\t\x01',
            ('\x03a\x06\x09spam', '\x03b\x04\x05'), '\x01')))

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x09spam'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ObjectProxy)
        self.assertEquals(x._amf_object, {'a': 'spam', 'b': 5})

    def test_decode_proxy(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x09spam'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)
        decoder.use_proxies = True

        x = decoder.readElement()

        self.assertEquals(x.__class__, pyamf.MixedArray)
        self.assertEquals(x, {'a': 'spam', 'b': 5})

    def test_get_attrs(self):
        x = flex.ObjectProxy()

        self.assertEquals(x._amf_object, pyamf.ASObject())

        x._amf_object = None
        self.assertEquals(x._amf_object, None)


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ArrayCollectionTestCase))
    suite.addTest(unittest.makeSuite(ArrayCollectionAPITestCase))
    suite.addTest(unittest.makeSuite(ObjectProxyTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
