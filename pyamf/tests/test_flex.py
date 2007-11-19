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
Flex/Flash compatibility tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import flex, util, amf3

class ArrayCollectionTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ArrayCollection()

        x['foo'] = 'bar'

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\x07foo\x06\x07bar\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\x07foo\x06\x07bar\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ArrayCollection)
        self.assertEquals(x.keys(), ['foo'])
        self.assertEquals(x.items(), [('foo', u'bar')])

class ObjectProxyTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = flex.ObjectProxy({'a': 'foo', 'b': 5})

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x07foo'
            '\x03b\x04\x05\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x07foo'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, flex.ObjectProxy)
        self.assertEquals(x._amf_object, {'a': 'foo', 'b': 5})

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ArrayCollectionTestCase))
    suite.addTest(unittest.makeSuite(ObjectProxyTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
