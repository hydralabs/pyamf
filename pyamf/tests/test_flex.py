# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Flex compatibility tests.

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import flex, util, amf3, amf0

class ArrayCollectionTestCase(unittest.TestCase):
    def test_create(self):
        ac = flex.ArrayCollection([1, 2, 3])
        self.assertEquals(ac, {0: 1, 1: 2, 2: 3})

        ac = flex.ArrayCollection(('a', 'b', 'b'))
        self.assertEquals(ac, {0: 'a', 1: 'b', 2: 'b'})

        ac = flex.ArrayCollection({'first': 'Matt', 'last': 'Matthews'})
        self.assertEquals(ac, {'first': 'Matt', 'last': 'Matthews'})

    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ArrayCollection()

        x['spam'] = 'eggs'

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\tspam\x06\teggs\x01')

        stream = util.BufferedByteStream()
        encoder = amf0.Encoder(stream)

        x = flex.ArrayCollection()

        x['spam'] = 'eggs'

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\x11\n\x07Cflex.messaging.io.ArrayCollection\t\x01\tspam\x06\x09'
            'eggs\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\x09spam\x06\x09eggs\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ArrayCollection)
        self.assertEquals(x.keys(), ['spam'])
        self.assertEquals(x.items(), [('spam', u'eggs')])

class ObjectProxyTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ObjectProxy(pyamf.MixedArray(a='spam', b=5))

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x09spam'
            '\x03b\x04\x05\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x09spam'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ObjectProxy)
        self.assertEquals(x._amf_object, {'a': 'spam', 'b': 5})

    def test_get_attrs(self):
        x = flex.ObjectProxy()

        self.assertEquals(x._amf_object, pyamf.ASObject())

        x._amf_object = None
        self.assertEquals(x._amf_object, None)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ArrayCollectionTestCase))
    suite.addTest(unittest.makeSuite(ObjectProxyTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
